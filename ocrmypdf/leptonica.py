#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# © 2013-16: jbarlow83 from Github (https://github.com/jbarlow83)
#
# Python FFI wrapper for Leptonica library

import argparse
import sys
import os
import logging
from tempfile import TemporaryFile
from ctypes.util import find_library
from .lib._leptonica import ffi
from functools import lru_cache
from enum import Enum

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
        from io import UnsupportedOperation
        self.tmpfile = TemporaryFile()

        # Save the old stderr, and redirect stderr to temporary file
        sys.stderr.flush()
        try:
            self.copy_of_stderr = os.dup(sys.stderr.fileno())
            os.dup2(self.tmpfile.fileno(), sys.stderr.fileno(),
                    inheritable=False)
        except UnsupportedOperation:
            self.copy_of_stderr = None
        return

    def __exit__(self, exc_type, exc_value, traceback):
        # Restore old stderr
        sys.stderr.flush()
        if self.copy_of_stderr is not None:
            os.dup2(self.copy_of_stderr, sys.stderr.fileno())
            os.close(self.copy_of_stderr)

        # Get data from tmpfile (in with block to ensure it is closed)
        with self.tmpfile as tmpfile:
            tmpfile.seek(0)  # Cursor will be at end, so move back to beginning
            leptonica_output = tmpfile.read().decode(errors='replace')

        assert self.tmpfile.closed
        assert not sys.stderr.closed

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


class RemoveColormap(Enum):
    to_binary = 0
    to_grayscale = 1
    to_full_color = 2
    based_on_src = 3


class Pix:
    """Wrapper around leptonica's PIX object.

    Leptonica uses referencing counting on PIX objects. Also, many Leptonica
    functions return the original object with an increased reference count
    if the operation had no effect (for example, image skew was found to be 0).
    This has complications for memory management in Python. Whenever Leptonica
    returns a PIX object (new or old), we wrap it in this class, which
    registers it with the FFI garbage collector. pixDestroy() decrements the
    reference count and only destroys when the last reference is removed.

    Leptonica's reference counting is not threadsafe. This class can be used
    in a threadsafe manner if a Python threading.Lock protects the data.

    This class treats Pix objects as immutable.  All methods return new
    modified objects.  This allows convenient chaining:

    >>>   Pix.read('filename.jpg').scale((0.5, 0.5)).deskew().show()

    """

    def __init__(self, pix):
        self._pix = ffi.gc(pix, Pix._pix_destroy)

    def __repr__(self):
        if self._pix:
            s = "<leptonica.Pix image size={0}x{1} depth={2} at 0x{3:x}>"
            return s.format(self._pix.w, self._pix.h, self._pix.d,
                            int(ffi.cast("intptr_t", self._pix)))
        else:
            return "<leptonica.Pix image NULL>"

    def _repr_png_(self):
        """iPython display hook

        returns png version of image
        """

        data = ffi.new('l_uint8 **')
        size = ffi.new('size_t *')

        err = lept.pixWriteMemPng(data, size, self._pix, 0)
        if err != 0:
            raise LeptonicaIOError("pixWriteMemPng")

        char_data = ffi.cast('char *', data[0])
        return ffi.buffer(char_data, size[0])[:]

    def __getstate__(self):
        data = ffi.new('l_uint32 **')
        size = ffi.new('size_t *')

        err = lept.pixSerializeToMemory(self._pix, data, size)
        if err != 0:
            raise LeptonicaIOError("pixSerializeToMemory")

        char_data = ffi.cast('char *', data[0])

        # Copy from C bytes to python bytes()
        data_bytes = ffi.buffer(char_data, size[0])[:]

        # Can now free C bytes
        lept.lept_free(char_data)
        return dict(data=data_bytes)

    def __setstate__(self, state):
        cdata_bytes = ffi.new('char[]', state['data'])
        cdata_uint32 = ffi.cast('l_uint32 *', cdata_bytes)

        pix = lept.pixDeserializeFromMemory(
            cdata_uint32, len(state['data']))
        Pix.__init__(self, pix)

    def __eq__(self, other):
        return self.__getstate__() == other.__getstate__()

    @property
    def width(self):
        return self._pix.w

    @property
    def height(self):
        return self._pix.h

    @property
    def depth(self):
        return self._pix.d

    @property
    def size(self):
        return (self._pix.w, self._pix.h)

    @property
    def info(self):
        return {'dpi': (self._pix.xres, self._pix.yres)}

    @property
    def mode(self):
        "Return mode like PIL.Image"
        if self.depth == 1:
            return '1'
        elif self.depth >= 16:
            return 'RGB'
        elif not self._pix.colormap:
            return 'L'
        else:
            return 'P'

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
        with LeptonicaErrorTrap():
            lept.pixWriteImpliedFormat(
                filename.encode(sys.getfilesystemencoding()),
                self._pix, jpeg_quality, jpeg_progressive)

    def topil(self):
        "Returns a PIL.Image version of this Pix"
        from PIL import Image

        # Leptonica manages data in words, so it implicitly does an endian
        # swap.  Tell Pillow about this when it reads the data.
        pix = self
        if sys.byteorder == 'little':
            if self.mode == 'RGB':
                raw_mode = 'XBGR'
            elif self.mode == 'RGBA':
                raw_mode = 'ABGR'
            elif self.mode == '1':
                raw_mode = '1;I'
                pix = Pix(lept.pixEndianByteSwapNew(pix._pix))
            else:
                raw_mode = self.mode
                pix = Pix(lept.pixEndianByteSwapNew(pix._pix))
        else:
            raw_mode = self.mode  # no endian swap needed

        size = (pix._pix.w, pix._pix.h)
        bytecount = pix._pix.wpl * 4 * pix._pix.h
        buf = ffi.buffer(pix._pix.data, bytecount)
        stride = pix._pix.wpl * 4

        im = Image.frombytes(self.mode, size, buf, 'raw', raw_mode, stride)

        return im

    def show(self):
        return self.topil().show()

    def deskew(self, reduction_factor=0):
        """Returns the deskewed pix object.

        A clone of the original is returned when the algorithm cannot find a
        skew angle with sufficient confidence.

        reduction_factor -- amount to downsample (0 for default) when searching
            for skew angle
        """
        with LeptonicaErrorTrap():
            return Pix(lept.pixDeskew(self._pix, reduction_factor))

    def scale(self, scale_xy):
        "Returns the pix object rescaled according to the proportions given."
        with LeptonicaErrorTrap():
            return Pix(lept.pixScale(self._pix, scale_xy[0], scale_xy[1]))

    def rotate180(self):
        with LeptonicaErrorTrap():
            return Pix(lept.pixRotate180(ffi.NULL, self._pix))

    def rotate_orth(self, quads):
        "Orthographic rotation, quads: 0-3, number of clockwise rotations"
        with LeptonicaErrorTrap():
            return Pix(lept.pixRotateOrth(self._pix, quads))

    def find_skew(self):
        """Returns a tuple (deskew angle in degrees, confidence value).

        Returns (None, None) if no angle is available.
        """
        with LeptonicaErrorTrap():
            angle = ffi.new('float *', 0.0)
            confidence = ffi.new('float *', 0.0)
            result = lept.pixFindSkew(self._pix, angle, confidence)
            if result == 0:
                return (angle[0], confidence[0])
            else:
                return (None, None)

    def convert_rgb_to_luminance(self):
        with LeptonicaErrorTrap():
            gray_pix = lept.pixConvertRGBToLuminance(self._pix)
            if gray_pix:
                return Pix(gray_pix)
            return None

    def remove_colormap(self, removal_type):
        """Remove a palette

            removal_type - RemovalColormap()
        """

        with LeptonicaErrorTrap():
            return Pix(lept.pixRemoveColormap(self._pix, removal_type))

    def otsu_adaptive_threshold(
            self, tile_size=(300, 300), kernel_size=(4, 4), scorefract=0.1):
        with LeptonicaErrorTrap():
            sx, sy = tile_size
            smoothx, smoothy = kernel_size
            p_pix = ffi.new('PIX **')

            result = lept.pixOtsuAdaptiveThreshold(
                self._pix,
                sx, sy,
                smoothx, smoothy,
                scorefract,
                ffi.NULL,
                p_pix)
            if result == 0:
                return Pix(p_pix[0])
            else:
                return None

    def otsu_threshold_on_background_norm(
            self, mask=None, tile_size=(10, 15), thresh=100, mincount=50,
            bgval=255, kernel_size=(2, 2), scorefract=0.1):
        with LeptonicaErrorTrap():
            sx, sy = tile_size
            smoothx, smoothy = kernel_size
            if mask is None:
                mask = ffi.NULL
            if isinstance(mask, Pix):
                mask = mask._pix

            thresh_pix = lept.pixOtsuThreshOnBackgroundNorm(
                self._pix,
                mask,
                sx, sy,
                thresh, mincount, bgval,
                smoothx, smoothy,
                scorefract,
                ffi.NULL
                )
            if thresh_pix == ffi.NULL:
                return None
            return Pix(thresh_pix)

    def crop_to_foreground(
            self, threshold=128, mindist=70, erasedist=30, pagenum=0,
            showmorph=0, display=0, pdfdir=ffi.NULL):
        with LeptonicaErrorTrap():
            cropbox = Box(lept.pixFindPageForeground(
                self._pix,
                threshold,
                mindist,
                erasedist,
                pagenum,
                showmorph,
                display,
                pdfdir))

            print(repr(cropbox))

            cropped_pix = lept.pixClipRectangle(
                self._pix,
                cropbox._box,
                ffi.NULL)

            return Pix(cropped_pix)

    def clean_background_to_white(
            self, mask=None, grayscale=None, gamma=1.0, black=0, white=255):
        with LeptonicaErrorTrap():
            return Pix(lept.pixCleanBackgroundToWhite(
                self._pix,
                mask or ffi.NULL,
                grayscale or ffi.NULL,
                gamma,
                black,
                white))

    def gamma_trc(self, gamma=1.0, minval=0, maxval=255):
        with LeptonicaErrorTrap():
            return Pix(lept.pixGammaTRC(
                ffi.NULL,
                self._pix,
                gamma,
                minval,
                maxval
                ))

    def background_norm(
            self, mask=None, grayscale=None, tile_size=(10, 15), fg_threshold=60,
            min_count=40, bg_val=200, smooth_kernel=(2, 1)):
        with LeptonicaErrorTrap():
            return Pix(lept.pixBackgroundNorm(
                self._pix,
                mask or ffi.NULL,
                grayscale or ffi.NULL,
                tile_size[0],
                tile_size[1],
                fg_threshold,
                min_count,
                bg_val,
                smooth_kernel[0],
                smooth_kernel[1]
                ))

    @staticmethod
    @lru_cache(maxsize=1)
    def make_pixel_sum_tab8():
        return lept.makePixelSumTab8()

    @staticmethod
    def correlation_binary(pix1, pix2):
        if get_leptonica_version() < 'leptonica-1.72':
            # Older versions of Leptonica (pre-1.72) have a buggy
            # implementation of pixCorrelationBinary that overflows on larger
            # images.  Ubuntu trusty has 1.70. Ubuntu PPA
            # ppa:rebuntu16/avidemux+unofficial has "leptonlib" 1.73.
            pix1_count = ffi.new('l_int32 *')
            pix2_count = ffi.new('l_int32 *')
            pixn_count = ffi.new('l_int32 *')
            tab8 = Pix.make_pixel_sum_tab8()

            lept.pixCountPixels(pix1._pix, pix1_count, tab8)
            lept.pixCountPixels(pix2._pix, pix2_count, tab8)
            pixn = Pix(lept.pixAnd(ffi.NULL, pix1._pix, pix2._pix))
            lept.pixCountPixels(pixn._pix, pixn_count, tab8)

            # Python converts these int32s to larger units as needed
            # to avoid overflow. Overflow happens easily here.
            correlation = (
                    (pixn_count[0] * pixn_count[0]) /
                    (pix1_count[0] * pix2_count[0])
                    )
            return correlation
        else:
            correlation = ffi.new('float *', 0.0)
            result = lept.pixCorrelationBinary(pix1._pix, pix2._pix,
                                               correlation)
            if result != 0:
                raise LeptonicaError("Correlation failed")
            return correlation[0]

    @staticmethod
    def _pix_destroy(pix):
        p_pix = ffi.new('PIX **', pix)
        lept.pixDestroy(p_pix)
        # print('pix destroy ' + repr(pix))


class Box:
    """Wrapper around Leptonica's BOX objects.

    See class Pix for notes about reference counting.
    """

    def __init__(self, box):
        self._box = ffi.gc(box, Box._box_destroy)

    def __repr__(self):
        if self._box:
            return '<leptonica.Box x={0} y={1} w={2} h={3}>'.format(
                self.x, self.y, self.w, self.h)
        return '<leptonica.Box NULL>'

    @property
    def x(self):
        return self._box.x

    @property
    def y(self):
        return self._box.y

    @property
    def w(self):
        return self._box.w

    @property
    def h(self):
        return self._box.h

    @staticmethod
    def _box_destroy(box):
        p_box = ffi.new('BOX **', box)
        lept.boxDestroy(p_box)


@lru_cache(maxsize=1)
def get_leptonica_version():
    """Get Leptonica version string.

    Caveat: Leptonica expects the caller to free this memory.  We don't,
    since that would involve binding to libc to access libc.free(),
    a pointless effort to reclaim 100 bytes of memory.
    """
    return ffi.string(lept.getLeptonicaVersion()).decode()


def deskew(infile, outfile, dpi):
    try:
        pix_source = Pix.read(infile)
    except LeptonicaIOError:
        raise LeptonicaIOError("Failed to open file: %s" % infile)

    if dpi < 150:
        reduction_factor = 1  # Don't downsample too much if DPI is already low
    else:
        reduction_factor = 0  # Use default
    pix_deskewed = pix_source.deskew(reduction_factor)

    try:
        pix_deskewed.write_implied_format(outfile)
    except LeptonicaIOError:
        raise LeptonicaIOError("Failed to open destination file: %s" % outfile)


def remove_background(infile, outfile, tile_size=(40, 60), gamma=1.0,
                      black_threshold=70, white_threshold=190):
    try:
        pix = Pix.read(infile)
    except LeptonicaIOError:
        raise LeptonicaIOError("Failed to open file: %s" % infile)

    pix = pix.background_norm(tile_size=tile_size).gamma_trc(
            gamma, black_threshold, white_threshold)

    try:
        pix.write_implied_format(outfile)
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

    if get_leptonica_version() != u'leptonica-1.69':
        print("Unexpected leptonica version: %s" % getLeptonicaVersion())

    args.func(args)


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


