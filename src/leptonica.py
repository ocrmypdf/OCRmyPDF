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


def pixWriteImpliedFormat(filename, pix, jpeg_quality=0, jpeg_progressive=0):
    """Write pix to the filename, with the extension indicating format.

    jpeg_quality -- quality (iff JPEG; 1 - 100, 0 for default)
    jpeg_ progressive -- (iff JPEG; 0 for baseline seq., 1 for progressive)

    """
    with LeptonicaErrorTrap():
        lept.pixWriteImpliedFormat(
            filename.encode(sys.getfilesystemencoding()),
            pix, jpeg_quality, jpeg_progressive)


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

