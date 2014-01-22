#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# © 2013-14: jbarlow83 from Github (https://github.com/jbarlow83)
#
#
# Use Leptonica to detect find and remove page skew.  Leptonica uses the method
# of differential square sums, which its author claim is faster and more robust
# than the Hough transform used by ImageMagick.

from __future__ import print_function, absolute_import, division
import argparse
import ctypes as C
import sys
import os
from tempfile import TemporaryFile


def stderr(*objs):
    """Python 2/3 compatible print to stderr.
    """
    print("leptonica.py:", *objs, file=sys.stderr)


from ctypes.util import find_library
lept_lib = find_library('lept')
if not lept_lib:
    stderr("Could not find the Leptonica library")
    sys.exit(3)
try:
    lept = C.cdll.LoadLibrary(lept_lib)
except Exception:
    stderr("Could not load the Leptonica library from %s", lept_lib)
    sys.exit(3)


class _PIXCOLORMAP(C.Structure):
    """struct PixColormap from Leptonica src/pix.h
    """

    _fields_ = [
        ("array", C.c_void_p),
        ("depth", C.c_int32),
        ("nalloc", C.c_int32),
        ("n", C.c_int32)
    ]


class _PIX(C.Structure):
    """struct Pix from Leptonica src/pix.h
    """

    _fields_ = [
        ("w", C.c_uint32),
        ("h", C.c_uint32),
        ("d", C.c_uint32),
        ("wpl", C.c_uint32),
        ("refcount", C.c_uint32),
        ("xres", C.c_int32),
        ("yres", C.c_int32),
        ("informat", C.c_int32),
        ("text", C.POINTER(C.c_char)),
        ("colormap", C.POINTER(_PIXCOLORMAP)),
        ("data", C.POINTER(C.c_uint32))
    ]


PIX = C.POINTER(_PIX)

lept.pixRead.argtypes = [C.c_char_p]
lept.pixRead.restype = PIX
lept.pixScale.argtypes = [PIX, C.c_float, C.c_float]
lept.pixScale.restype = PIX
lept.pixDeskew.argtypes = [PIX, C.c_int32]
lept.pixDeskew.restype = PIX
lept.pixFindSkew.argtypes = [PIX, C.POINTER(C.c_float), C.POINTER(C.c_float)]
lept.pixFindSkew.restype = C.c_int32
lept.pixWriteImpliedFormat.argtypes = [C.c_char_p, PIX, C.c_int32, C.c_int32]
lept.pixWriteImpliedFormat.restype = C.c_int32
lept.pixDestroy.argtypes = [C.POINTER(PIX)]
lept.pixDestroy.restype = None
lept.getLeptonicaVersion.argtypes = []
lept.getLeptonicaVersion.restype = C.c_char_p


class LeptonicaErrorTrap(object):
    """Context manager to trap errors reported by Leptonica.

    Leptonica's error return codes are unreliable to the point of being
    almost useless.  It does, however, write errors to stderr provided that is
    not disabled at its compile time.  Fortunately this is done using error
    macros so it is very self-consistent.

    This context manager redirects stderr to a temporary file which is then
    read and parsed for error messages.  As a side benefit, debug messages
    from Leptonica are also suppressed.

    """
    def __enter__(self):
        self.tmpfile = TemporaryFile()

        # Save the old stderr, and redirect stderr to temporary file
        self.old_stderr_fileno = os.dup(sys.stderr.fileno())
        os.dup2(self.tmpfile.fileno(), sys.stderr.fileno())
        return

    def __exit__(self, exc_type, exc_value, traceback):
        # Restore old stderr
        os.dup2(self.old_stderr_fileno, sys.stderr.fileno())

        # Get data from tmpfile (in with block to ensure it is closed)
        with self.tmpfile as tmpfile:
            tmpfile.seek(0)  # Cursor will be at end, so move back to beginning
            leptonica_output = tmpfile.read().decode(errors='replace')

        # If there are Python errors, let them bubble up
        if exc_type:
            stderr(leptonica_output)
            return False

        # If there are Leptonica errors, wrap them in Python excpetions
        if 'Error' in leptonica_output:
            if 'image file not found' in leptonica_output:
                raise LeptonicaIOError()
            if 'pixWrite: stream not opened' in leptonica_output:
                raise LeptonicaIOError()
            raise LeptonicaError(leptonica_output)

        return False


class LeptonicaError(Exception):
    pass


class LeptonicaIOError(LeptonicaError):
    pass


def pixRead(filename):
    """Load an image file into a PIX object.

    Leptonica can load TIFF, PNM (PBM, PGM, PPM), PNG, and JPEG.  If loading
    fails then the object will wrap a C null pointer.

    """
    with LeptonicaErrorTrap():
        return lept.pixRead(filename.encode(sys.getfilesystemencoding()))


def pixScale(pix, scalex, scaley):
    """Returns the pix object rescaled according to the proportions given."""
    with LeptonicaErrorTrap():
        return lept.pixScale(pix, scalex, scaley)


def pixDeskew(pix, reduction_factor=0):
    """Returns the deskewed pix object.

    A clone of the original is returned when the algorithm cannot find a skew
    angle with sufficient confidence.

    reduction_factor -- amount to downsample (0 for default) when searching
        for skew angle

    """
    with LeptonicaErrorTrap():
        return lept.pixDeskew(pix, reduction_factor)


def pixFindSkew(pix):
    """Returns a tuple (deskew angle in degrees, confidence value).

    Returns (None, None) if no angle is available.

    """
    with LeptonicaErrorTrap():
        angle = C.c_float(0.0)
        confidence = C.c_float(0.0)
        result = lept.pixFindSkew(pix, C.byref(angle), C.byref(confidence))
        if result == 0:
            return (angle.value, confidence.value)
        else:
            return (None, None)


def pixWriteImpliedFormat(filename, pix, jpeg_quality=0, jpeg_progressive=0):
    """Write pix to the filename, with the extension indicating format.

    jpeg_quality -- quality (iff JPEG; 1 - 100, 0 for default)
    jpeg_progressive -- (iff JPEG; 0 for baseline seq., 1 for progressive)

    """
    fileroot, extension = os.path.splitext(filename)
    fix_pnm = False
    if extension.lower() in ('.pbm', '.pgm', '.ppm'):
        # Leptonica does not process handle these extensions correctly, but
        # does handle .pnm correctly.  Add another .pnm suffix.
        filename += '.pnm'
        fix_pnm = True

    with LeptonicaErrorTrap():
        lept.pixWriteImpliedFormat(
            filename.encode(sys.getfilesystemencoding()),
            pix, jpeg_quality, jpeg_progressive)

    if fix_pnm:
        from shutil import move
        move(filename, filename[:-4])   # Remove .pnm suffix


def pixDestroy(pix):
    """Destroy the pix object.

    Function signature is pixDestroy(struct Pix **), hence C.byref() to pass
    the address of the pointer.

    """
    with LeptonicaErrorTrap():
        lept.pixDestroy(C.byref(pix))


def getLeptonicaVersion():
    """Get Leptonica version string.

    Caveat: Leptonica expects the caller to free this memory.  We don't,
    since that would involve binding to libc to access libc.free(),
    a pointless effort to reclaim 100 bytes of memory.

    """
    return lept.getLeptonicaVersion().decode()


def deskew(args):
    try:
        pix_source = pixRead(args.infile)
    except LeptonicaIOError:
        stderr("Failed to open file: %s" % args.infile)
        sys.exit(2)

    if args.dpi < 150:
        reduction_factor = 1  # Don't downsample too much if DPI is already low
    else:
        reduction_factor = 0  # Use default
    pix_deskewed = pixDeskew(pix_source, reduction_factor)

    try:
        pixWriteImpliedFormat(args.outfile, pix_deskewed)
    except LeptonicaIOError:
        stderr("Failed to open destination file: %s" % args.outfile)
        sys.exit(5)
    pixDestroy(pix_source)
    pixDestroy(pix_deskewed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Python wrapper to access Leptonica")

    subparsers = parser.add_subparsers(title='commands',
                                       description='supported operations')

    parser_deskew = subparsers.add_parser('deskew')
    parser_deskew.add_argument('-r', '--dpi', dest='dpi', action='store',
                               type=int, default=300, help='input resolution')
    parser_deskew.add_argument('infile', help='image to deskew')
    parser_deskew.add_argument('outfile', help='deskewed output image')
    parser_deskew.set_defaults(func=deskew)

    args = parser.parse_args()

    if getLeptonicaVersion() != u'leptonica-1.69':
        print("Unexpected leptonica version: %s" % getLeptonicaVersion())

    args.func(args)


def _test_output(mode, extension, im_format):
    from PIL import Image
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(prefix='test-lept-pnm', suffix=extension, delete=True) as tmpfile:
        im = Image.new(mode=mode, size=(100, 100))
        im.save(tmpfile)

        pix = pixRead(tmpfile.name)
        pixWriteImpliedFormat(tmpfile.name, pix)
        pixDestroy(pix)

        im_roundtrip = Image.open(tmpfile.name)
        assert im_roundtrip.mode == im.mode, "leptonica mode differs"
        assert im_roundtrip.format == im_format, \
            "{0}: leptonica produced a {1}".format(
                extension,
                im_roundtrip.format)


def test_pnm_output():
    params = [['1', '.pbm', 'PPM'], ['L', '.pgm', 'PPM'],
              ['RGB', '.ppm', 'PPM']]
    for param in params:
        _test_output(*param)


def test_skew_angle():
    from PIL import Image, ImageDraw
    from tempfile import NamedTemporaryFile

    im = Image.new(mode='1', size=(1000, 1000), color=1)

    draw = ImageDraw.Draw(im)
    for n in range(20):
        draw.line([(50, 25 + 50*n), (950, 25 + 50*n)], width=1)
    del draw

    test_angles = [0.1 * ang for ang in range(1, 10)] + \
                  [float(ang) for ang in range(1, 7)]
    test_angles += [-ang for ang in test_angles]
    test_angles = sorted(test_angles)

    for rotate_angle in test_angles:
        rotated_im = im.rotate(rotate_angle)
        with NamedTemporaryFile(prefix='lept-skew', suffix='.png', delete=True) as tmpfile:
            rotated_im.save(tmpfile)
            pix = pixRead(tmpfile.name)
            angle, confidence = pixFindSkew(pix)
            pixDestroy(pix)
            print('{0} {1}  {2}'.format(rotate_angle, angle, confidence), file=sys.stderr)


