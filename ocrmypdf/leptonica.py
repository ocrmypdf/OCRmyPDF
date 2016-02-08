#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# © 2013-15: jbarlow83 from Github (https://github.com/jbarlow83)
#
#
# Use Leptonica to detect find and remove page skew.  Leptonica uses the method
# of differential square sums, which its author claim is faster and more robust
# than the Hough transform used by ImageMagick.

from __future__ import print_function, absolute_import, division
import argparse
import sys
import os
import logging
from tempfile import TemporaryFile
from ctypes.util import find_library
from .lib._leptonica import ffi

lept = ffi.dlopen(find_library('lept'))

logger = logging.getLogger(__name__)


def stderr(*objs):
    """Python 2/3 compatible print to stderr.
    """
    print("leptonica.py:", *objs, file=sys.stderr)


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
            logger.warning(leptonica_output)
            return False

        # If there are Leptonica errors, wrap them in Python excpetions
        if 'Error' in leptonica_output:
            if 'image file not found' in leptonica_output:
                raise FileNotFoundError()
            if 'pixWrite: stream not opened' in leptonica_output:
                raise LeptonicaIOError()
            raise LeptonicaError(leptonica_output)

        return False


class LeptonicaError(Exception):
    pass


class LeptonicaIOError(LeptonicaError):
    pass


class Pix:
    def __init__(self, cpix):
        self.cpix = ffi.gc(cpix, Pix._pix_destroy)

    def __repr__(self):
        if self.cpix:
            s = "<leptonica.Pix image size={0}x{1} depth={2} at 0x{3:x}>"
            return s.format(self.cpix.w, self.cpix.h, self.cpix.d,
                            int(ffi.cast("intptr_t", self.cpix)))
        else:
            return "<leptonica.Pix image NULL>"

    @classmethod
    def read(cls, filename):
        """Load an image file into a PIX object.

        Leptonica can load TIFF, PNM (PBM, PGM, PPM), PNG, and JPEG.  If
        loading fails then the object will wrap a C null pointer.
        """
        with LeptonicaErrorTrap():
            return cls(lept.pixRead(
                filename.encode(sys.getfilesystemencoding())))

    def write_implied_format(
            self, filename, jpeg_quality=0, jpeg_progressive=0):
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
                self.cpix, jpeg_quality, jpeg_progressive)

        if fix_pnm:
            from shutil import move
            move(filename, filename[:-4])   # Remove .pnm suffix

    def deskew(self, reduction_factor=0):
        """Returns the deskewed pix object.

        A clone of the original is returned when the algorithm cannot find a
        skew angle with sufficient confidence.

        reduction_factor -- amount to downsample (0 for default) when searching
            for skew angle
        """
        with LeptonicaErrorTrap():
            return Pix(lept.pixDeskew(self.cpix, reduction_factor))

    def scale(self, scalex, scaley):
        "Returns the pix object rescaled according to the proportions given."
        with LeptonicaErrorTrap():
            return Pix(lept.pixScale(self.cpix, scalex, scaley))

    def rotate180(self):
        with LeptonicaErrorTrap():
            return Pix(lept.pixRotate180(ffi.NULL, self.cpix))

    def find_skew(self):
        """Returns a tuple (deskew angle in degrees, confidence value).

        Returns (None, None) if no angle is available.
        """
        with LeptonicaErrorTrap():
            angle = ffi.new('float *', 0.0)
            confidence = ffi.new('float *', 0.0)
            result = lept.pixFindSkew(self.cpix, angle, confidence)
            if result == 0:
                return (angle[0], confidence[0])
            else:
                return (None, None)

    @staticmethod
    def correlation_binary(pix1, pix2):
        correlation = ffi.new('float *', 0.0)
        result = lept.pixCorrelationBinary(pix1.cpix, pix2.cpix, correlation)
        if result != 0:
            raise LeptonicaError("Correlation failed")
        return correlation[0]

    @staticmethod
    def _pix_destroy(pix):
        ptr_to_pix = ffi.new('PIX **', pix)
        lept.pixDestroy(ptr_to_pix)
        print('pix destroy ' + repr(pix))


def getLeptonicaVersion():
    """Get Leptonica version string.

    Caveat: Leptonica expects the caller to free this memory.  We don't,
    since that would involve binding to libc to access libc.free(),
    a pointless effort to reclaim 100 bytes of memory.
    """
    return ffi.string(lept.getLeptonicaVersion()).decode()


def deskew(infile, outfile, dpi):
    try:
        pix_source = Pix.read(infile)
        print(repr(pix_source))
    except LeptonicaIOError:
        raise LeptonicaIOError("Failed to open file: %s" % infile)

    if dpi < 150:
        reduction_factor = 1  # Don't downsample too much if DPI is already low
    else:
        reduction_factor = 0  # Use default
    pix_deskewed = pix_source.deskew(reduction_factor)
    print(repr(pix_deskewed))

    try:
        pix_deskewed.write_implied_format(outfile)
    except LeptonicaIOError:
        raise LeptonicaIOError("Failed to open destination file: %s" % outfile)


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
            print('{0} {1}  {2}'.format(rotate_angle, angle, confidence), file=sys.stderr)


