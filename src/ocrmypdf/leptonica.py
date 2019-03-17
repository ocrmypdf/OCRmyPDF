#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# © 2013-16: jbarlow83 from Github (https://github.com/jbarlow83)
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.
#
# Python FFI wrapper for Leptonica library

import argparse
import logging
import os
import sys
import warnings
from collections.abc import Sequence
from contextlib import suppress
from ctypes.util import find_library
from functools import lru_cache
from io import BytesIO
from os import fspath
from tempfile import TemporaryFile

from .lib._leptonica import ffi

# pylint: disable=protected-access

logger = logging.getLogger(__name__)

lept = ffi.dlopen(find_library('lept'))
lept.setMsgSeverity(lept.L_SEVERITY_WARNING)


class _LeptonicaErrorTrap:
    """
    Context manager to trap errors reported by Leptonica.

    Leptonica's error return codes don't provide much informatino about what
    went wrong. Leptonica does, however, write more detailed errors to stderr
    (provided this is not disabled at compile time). The Leptonica source
    code is very consistent in its use of macros to generate errors.

    This context manager redirects stderr to a temporary file which is then
    read and parsed for error messages.  As a side benefit, debug messages
    from Leptonica are also suppressed.

    """

    def __init__(self):
        self.tmpfile = None
        self.copy_of_stderr = -1
        self.no_stderr = False

    def __enter__(self):
        from io import UnsupportedOperation

        self.tmpfile = TemporaryFile()

        # Save the old stderr, and redirect stderr to temporary file
        with suppress(AttributeError):
            sys.stderr.flush()
        try:
            self.copy_of_stderr = os.dup(sys.stderr.fileno())
            os.dup2(self.tmpfile.fileno(), sys.stderr.fileno(), inheritable=False)
        except AttributeError:
            # We are in some unusual context where our Python process does not
            # have a sys.stderr. Leptonica still expects to write to file
            # descriptor 2, so we are going to ensure it is redirected.
            self.copy_of_stderr = None
            self.no_stderr = True
            os.dup2(self.tmpfile.fileno(), 2, inheritable=False)
        except UnsupportedOperation:
            self.copy_of_stderr = None
        return

    def __exit__(self, exc_type, exc_value, traceback):
        # Restore old stderr
        with suppress(AttributeError):
            sys.stderr.flush()

        if self.copy_of_stderr is not None:
            os.dup2(self.copy_of_stderr, sys.stderr.fileno())
            os.close(self.copy_of_stderr)
        if self.no_stderr:
            os.close(2)

        # Get data from tmpfile
        self.tmpfile.seek(0)  # Cursor will be at end, so move back to beginning
        leptonica_output = self.tmpfile.read().decode(errors='replace')
        self.tmpfile.close()
        # If there are Python errors, record them
        if exc_type:
            logger.warning(leptonica_output)

        # If there are Leptonica errors, wrap them in Python excpetions
        if 'Error' in leptonica_output:
            if 'image file not found' in leptonica_output:
                raise FileNotFoundError()
            if 'pixWrite: stream not opened' in leptonica_output:
                raise LeptonicaIOError()
            if 'index not valid' in leptonica_output:
                raise IndexError()
            raise LeptonicaError(leptonica_output)

        return False


class LeptonicaError(Exception):
    pass


class LeptonicaIOError(LeptonicaError):
    pass


class LeptonicaObject:
    """General wrapper for Leptonica objects

    When Leptonica returns an object, we bundled it in a wrapper class, which
    manages its memory. The wrapper class assumes that it will be calling some
    sort of lept.thingDestroy() function when the instance is deleted. Most
    Leptonica objects are reference counted, and destroy decrements the
    refcount.

    Most of the time, when Leptonica returns something, we wrap and it the job
    is done. When wrapping objects that came from a Leptonica container, like
    a PIXA returning PIX, the subclass must clone the object before passing it
    here, to maintain the reference count.

    CFFI ensures that the destroy function is called at garbage collection time
    so we do not need to mess with __del__.
    """

    cdata_destroy = lambda cdata: None
    LEPTONICA_TYPENAME = ''

    def __init__(self, cdata):
        if not cdata:
            raise ValueError('Tried to wrap a NULL ' + self.LEPTONICA_TYPENAME)
        self._cdata = ffi.gc(cdata, self._destroy)

    @classmethod
    def _destroy(cls, cdata):
        """Destroy some cdata"""
        # Leptonica API uses double-pointers for its destroy APIs to prevent
        # dangling pointers. This means we need to put our single pointer,
        # cdata, in a temporary CDATA**.
        pp = ffi.new('{} **'.format(cls.LEPTONICA_TYPENAME), cdata)
        cls.cdata_destroy(pp)


class Pix(LeptonicaObject):
    """
    Wrapper around leptonica's PIX object.

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

    >>>   Pix.open('filename.jpg').scale((0.5, 0.5)).deskew().show()
    """

    LEPTONICA_TYPENAME = "PIX"
    cdata_destroy = lept.pixDestroy

    def __repr__(self):
        if self._cdata:
            s = "<leptonica.Pix image size={0}x{1} depth={2}{4} at 0x{3:x}>"
            return s.format(
                self._cdata.w,
                self._cdata.h,
                self._cdata.d,
                int(ffi.cast('intptr_t', self._cdata)),
                '(colormapped)' if self._cdata.colormap else '',
            )
        else:
            return "<leptonica.Pix image NULL>"

    def _repr_png_(self):
        """iPython display hook

        returns png version of image
        """

        data = ffi.new('l_uint8 **')
        size = ffi.new('size_t *')

        err = lept.pixWriteMemPng(data, size, self._cdata, 0)
        if err != 0:
            raise LeptonicaIOError("pixWriteMemPng")

        char_data = ffi.cast('char *', data[0])
        return ffi.buffer(char_data, size[0])[:]

    def __getstate__(self):
        data = ffi.new('l_uint32 **')
        size = ffi.new('size_t *')

        err = lept.pixSerializeToMemory(self._cdata, data, size)
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

        pix = lept.pixDeserializeFromMemory(cdata_uint32, len(state['data']))
        Pix.__init__(self, pix)

    def __eq__(self, other):
        if not isinstance(other, Pix):
            return NotImplemented
        same = ffi.new('l_int32 *', 0)
        with _LeptonicaErrorTrap():
            err = lept.pixEqual(self._cdata, other._cdata, same)
            if err:
                raise TypeError()
        return bool(same[0])

    @property
    def width(self):
        return self._cdata.w

    @property
    def height(self):
        return self._cdata.h

    @property
    def depth(self):
        return self._cdata.d

    @property
    def size(self):
        return (self._cdata.w, self._cdata.h)

    @property
    def info(self):
        return {'dpi': (self._cdata.xres, self._cdata.yres)}

    @property
    def mode(self):
        "Return mode like PIL.Image"
        if self.depth == 1:
            return '1'
        elif self.depth >= 16:
            return 'RGB'
        elif not self._cdata.colormap:
            return 'L'
        else:
            return 'P'

    @classmethod
    def read(cls, path):
        warnings.warn('Use Pix.open() instead', DeprecationWarning)
        return cls.open(path)

    @classmethod
    def open(cls, path):
        """Load an image file into a PIX object.

        Leptonica can load TIFF, PNM (PBM, PGM, PPM), PNG, and JPEG.  If
        loading fails then the object will wrap a C null pointer.
        """
        filename = fspath(path)
        with _LeptonicaErrorTrap():
            return cls(lept.pixRead(os.fsencode(filename)))

    def write_implied_format(self, path, jpeg_quality=0, jpeg_progressive=0):
        """Write pix to the filename, with the extension indicating format.

        jpeg_quality -- quality (iff JPEG; 1 - 100, 0 for default)
        jpeg_progressive -- (iff JPEG; 0 for baseline seq., 1 for progressive)
        """
        filename = fspath(path)
        with _LeptonicaErrorTrap():
            lept.pixWriteImpliedFormat(
                os.fsencode(filename), self._cdata, jpeg_quality, jpeg_progressive
            )

    @classmethod
    def frompil(self, pillow_image):
        """Create a copy of a PIL.Image from this Pix"""
        bio = BytesIO()
        pillow_image.save(bio, format='png', compress_level=1)
        py_buffer = bio.getbuffer()
        c_buffer = ffi.from_buffer(py_buffer)
        with _LeptonicaErrorTrap():
            pix = Pix(lept.pixReadMem(c_buffer, len(c_buffer)))
            return pix

    def topil(self):
        """Returns a PIL.Image version of this Pix"""
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
                pix = Pix(lept.pixEndianByteSwapNew(pix._cdata))
            else:
                raw_mode = self.mode
                pix = Pix(lept.pixEndianByteSwapNew(pix._cdata))
        else:
            raw_mode = self.mode  # no endian swap needed

        size = (pix._cdata.w, pix._cdata.h)
        bytecount = pix._cdata.wpl * 4 * pix._cdata.h
        buf = ffi.buffer(pix._cdata.data, bytecount)
        stride = pix._cdata.wpl * 4

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
        with _LeptonicaErrorTrap():
            return Pix(lept.pixDeskew(self._cdata, reduction_factor))

    def scale(self, scale_xy):
        "Returns the pix object rescaled according to the proportions given."
        with _LeptonicaErrorTrap():
            return Pix(lept.pixScale(self._cdata, scale_xy[0], scale_xy[1]))

    def rotate180(self):
        with _LeptonicaErrorTrap():
            return Pix(lept.pixRotate180(ffi.NULL, self._cdata))

    def rotate_orth(self, quads):
        "Orthographic rotation, quads: 0-3, number of clockwise rotations"
        with _LeptonicaErrorTrap():
            return Pix(lept.pixRotateOrth(self._cdata, quads))

    def find_skew(self):
        """Returns a tuple (deskew angle in degrees, confidence value).

        Returns (None, None) if no angle is available.
        """
        with _LeptonicaErrorTrap():
            angle = ffi.new('float *', 0.0)
            confidence = ffi.new('float *', 0.0)
            result = lept.pixFindSkew(self._cdata, angle, confidence)
            if result == 0:
                return (angle[0], confidence[0])
            else:
                return (None, None)

    def convert_rgb_to_luminance(self):
        with _LeptonicaErrorTrap():
            gray_pix = lept.pixConvertRGBToLuminance(self._cdata)
            if gray_pix:
                return Pix(gray_pix)
            return None

    def remove_colormap(self, removal_type):
        """Remove a palette (colormap); if no colormap, returns a copy of this
        image

            removal_type - any of lept.REMOVE_CMAP_*

        """
        with _LeptonicaErrorTrap():
            return Pix(
                lept.pixRemoveColormapGeneral(self._cdata, removal_type, lept.L_COPY)
            )

    def otsu_adaptive_threshold(
        self, tile_size=(300, 300), kernel_size=(4, 4), scorefract=0.1
    ):
        with _LeptonicaErrorTrap():
            sx, sy = tile_size
            smoothx, smoothy = kernel_size
            p_pix = ffi.new('PIX **')

            pix = Pix(lept.pixConvertTo8(self._cdata, 0))
            result = lept.pixOtsuAdaptiveThreshold(
                pix._cdata, sx, sy, smoothx, smoothy, scorefract, ffi.NULL, p_pix
            )
            if result == 0:
                return Pix(p_pix[0])
            else:
                return None

    def otsu_threshold_on_background_norm(
        self,
        mask=None,
        tile_size=(10, 15),
        thresh=100,
        mincount=50,
        bgval=255,
        kernel_size=(2, 2),
        scorefract=0.1,
    ):
        with _LeptonicaErrorTrap():
            sx, sy = tile_size
            smoothx, smoothy = kernel_size
            mask = ffi.NULL
            if isinstance(mask, Pix):
                mask = mask._cdata

            pix = Pix(lept.pixConvertTo8(self._cdata, 0))
            thresh_pix = lept.pixOtsuThreshOnBackgroundNorm(
                pix._cdata,
                mask,
                sx,
                sy,
                thresh,
                mincount,
                bgval,
                smoothx,
                smoothy,
                scorefract,
                ffi.NULL,
            )
            return Pix(thresh_pix)

    def masked_threshold_on_background_norm(
        self,
        mask=None,
        tile_size=(10, 15),
        thresh=100,
        mincount=50,
        kernel_size=(2, 2),
        scorefract=0.1,
    ):
        with _LeptonicaErrorTrap():
            sx, sy = tile_size
            smoothx, smoothy = kernel_size
            mask = ffi.NULL
            if isinstance(mask, Pix):
                mask = mask._cdata

            pix = Pix(lept.pixConvertTo8(self._cdata, 0))
            thresh_pix = lept.pixMaskedThreshOnBackgroundNorm(
                pix._cdata,
                mask,
                sx,
                sy,
                thresh,
                mincount,
                smoothx,
                smoothy,
                scorefract,
                ffi.NULL,
            )
            return Pix(thresh_pix)

    def crop_to_foreground(
        self,
        threshold=128,
        mindist=70,
        erasedist=30,
        pagenum=0,
        showmorph=0,
        display=0,
        pdfdir=ffi.NULL,
    ):
        with _LeptonicaErrorTrap():
            cropbox = Box(
                lept.pixFindPageForeground(
                    self._cdata,
                    threshold,
                    mindist,
                    erasedist,
                    pagenum,
                    showmorph,
                    display,
                    pdfdir,
                )
            )

            cropped_pix = lept.pixClipRectangle(self._cdata, cropbox._cdata, ffi.NULL)

            return Pix(cropped_pix)

    def clean_background_to_white(
        self, mask=None, grayscale=None, gamma=1.0, black=0, white=255
    ):
        with _LeptonicaErrorTrap():
            return Pix(
                lept.pixCleanBackgroundToWhite(
                    self._cdata,
                    mask or ffi.NULL,
                    grayscale or ffi.NULL,
                    gamma,
                    black,
                    white,
                )
            )

    def gamma_trc(self, gamma=1.0, minval=0, maxval=255):
        with _LeptonicaErrorTrap():
            return Pix(lept.pixGammaTRC(ffi.NULL, self._cdata, gamma, minval, maxval))

    def background_norm(
        self,
        mask=None,
        grayscale=None,
        tile_size=(10, 15),
        fg_threshold=60,
        min_count=40,
        bg_val=200,
        smooth_kernel=(2, 1),
    ):
        # Background norm doesn't work on color mapped Pix, so remove colormap
        target_pix = self.remove_colormap(lept.REMOVE_CMAP_BASED_ON_SRC)
        with _LeptonicaErrorTrap():
            return Pix(
                lept.pixBackgroundNorm(
                    target_pix._cdata,
                    mask or ffi.NULL,
                    grayscale or ffi.NULL,
                    tile_size[0],
                    tile_size[1],
                    fg_threshold,
                    min_count,
                    bg_val,
                    smooth_kernel[0],
                    smooth_kernel[1],
                )
            )

    @staticmethod
    @lru_cache(maxsize=1)
    def make_pixel_sum_tab8():
        return lept.makePixelSumTab8()

    @staticmethod
    def correlation_binary(pix1, pix2):
        if get_leptonica_version() < 'leptonica-1.72':
            # Older versions of Leptonica (pre-1.72) have a buggy
            # implementation of pixCorrelationBinary that overflows on larger
            # images.  Ubuntu 14.04/trusty has 1.70. Ubuntu PPA
            # ppa:alex-p/tesseract-ocr has leptonlib 1.75.
            raise LeptonicaError("Leptonica version is too old")

        correlation = ffi.new('float *', 0.0)
        result = lept.pixCorrelationBinary(pix1._cdata, pix2._cdata, correlation)
        if result != 0:
            raise LeptonicaError("Correlation failed")
        return correlation[0]

    def generate_pdf_ci_data(self, type_, quality):
        "Convert to PDF data, with transcoding"
        p_compdata = ffi.new('L_COMP_DATA **')
        result = lept.pixGenerateCIData(self._cdata, type_, quality, 0, p_compdata)
        if result != 0:
            raise LeptonicaError("Generate PDF data failed")
        return CompressedData(p_compdata[0])

    def invert(self):
        return Pix(lept.pixInvert(ffi.NULL, self._cdata))

    def locate_barcodes(self):
        try:
            with _LeptonicaErrorTrap():
                pix = Pix(lept.pixConvertTo8(self._cdata, 0))
                pixa_candidates = PixArray(lept.pixExtractBarcodes(pix._cdata, 0))
                if not pixa_candidates:
                    return
                sarray = StringArray(
                    lept.pixReadBarcodes(
                        pixa_candidates._cdata,
                        lept.L_BF_ANY,
                        lept.L_USE_WIDTHS,
                        ffi.NULL,
                        0,
                    )
                )
        except (LeptonicaError, ValueError, IndexError):
            return
        finally:
            leptonica_junk = ('junkpixt.png', 'junkpixt')
            for junk in leptonica_junk:
                with suppress(FileNotFoundError):
                    os.unlink(junk)  # leptonica may produce this

        for n, s in enumerate(sarray):
            decoded = s.decode()
            if decoded.strip() == '':
                continue
            box = pixa_candidates.get_box(n)
            left, top = box.x, box.y
            right, bottom = box.x + box.w, box.y + box.h
            yield (decoded, (left, top, right, bottom))

    def despeckle(self, size):
        if size == 2:
            speckle2 = """
                oooo
                oC o
                o  o
                oooo
                """
            sel1 = Sel.from_selstr(speckle2, 'speckle2')
            sel2 = Sel.create_brick(2, 2, 0, 0, lept.SEL_HIT)
        elif size == 3:
            speckle3 = """
                ooooo
                oC  o
                o   o
                o   o
                ooooo
                """
            sel1 = Sel.from_selstr(speckle3, 'speckle3')
            sel2 = Sel.create_brick(3, 3, 0, 0, lept.SEL_HIT)
        else:
            raise ValueError(size)

        pixhmt = Pix(lept.pixHMT(ffi.NULL, self._cdata, sel1._cdata))
        pixdilated = Pix(lept.pixDilate(ffi.NULL, pixhmt._cdata, sel2._cdata))

        pixsub = Pix(lept.pixSubtract(ffi.NULL, self._cdata, pixdilated._cdata))
        return pixsub


class CompressedData(LeptonicaObject):
    """Wrapper for L_COMP_DATA - abstract compressed image data"""

    LEPTONICA_TYPENAME = 'L_COMP_DATA'
    cdata_destroy = lept.l_CIDataDestroy

    @classmethod
    def open(cls, path, jpeg_quality=75):
        "Open compressed data, without transcoding"
        filename = fspath(path)

        p_compdata = ffi.new('L_COMP_DATA **')
        result = lept.l_generateCIDataForPdf(
            os.fsencode(filename), ffi.NULL, jpeg_quality, p_compdata
        )
        if result != 0:
            raise LeptonicaError("CompressedData.open")
        return CompressedData(p_compdata[0])

    def __len__(self):
        return self._cdata.nbytescomp

    def read(self):
        buf = ffi.buffer(self._cdata.datacomp, self._cdata.nbytescomp)
        return bytes(buf)

    def __getattr__(self, name):
        if hasattr(self._cdata, name):
            return getattr(self._cdata, name)
        raise AttributeError(name)

    def get_palette_pdf_string(self):
        "Returns palette pre-formatted for use in PDF"
        buflen = len('< ') + len(' rrggbb') * self._cdata.ncolors + len('>')
        buf = ffi.buffer(self._cdata.cmapdatahex, buflen)
        return bytes(buf)


class PixArray(LeptonicaObject, Sequence):
    """Wrapper around PIXA (array of PIX)"""

    LEPTONICA_TYPENAME = 'PIXA'
    cdata_destroy = lept.pixaDestroy

    def __len__(self):
        return self._cdata[0].n

    def __getitem__(self, n):
        with _LeptonicaErrorTrap():
            return Pix(lept.pixaGetPix(self._cdata, n, lept.L_CLONE))

    def get_box(self, n):
        with _LeptonicaErrorTrap():
            return Box(lept.pixaGetBox(self._cdata, n, lept.L_CLONE))


class Box(LeptonicaObject):
    """Wrapper around Leptonica's BOX objects (a pixel rectangle)

    Uses x, y, w, h coordinates.
    """

    LEPTONICA_TYPENAME = 'BOX'
    cdata_destroy = lept.boxDestroy

    def __repr__(self):
        if self._cdata:
            return '<leptonica.Box x={0} y={1} w={2} h={3}>'.format(
                self.x, self.y, self.w, self.h
            )
        return '<leptonica.Box NULL>'

    @property
    def x(self):
        return self._cdata.x

    @property
    def y(self):
        return self._cdata.y

    @property
    def w(self):
        return self._cdata.w

    @property
    def h(self):
        return self._cdata.h


class BoxArray(LeptonicaObject, Sequence):
    """Wrapper around Leptonica's BOXA (Array of BOX) objects."""

    LEPTONICA_TYPENAME = 'BOXA'
    cdata_destroy = lept.boxaDestroy

    def __repr__(self):
        if not self._cdata:
            return '<BoxArray>'
        boxes = (repr(box) for box in self)
        return '<BoxArray [' + ', '.join(boxes) + ']>'

    def __len__(self):
        return self._cdata.n

    def __getitem__(self, n):
        if not isinstance(n, int):
            raise TypeError('list indices must be integers')
        if 0 <= n < len(self):
            return Box(lept.boxaGetBox(self._cdata, n, lept.L_CLONE))
        raise IndexError(n)


class StringArray(LeptonicaObject, Sequence):
    """Leptonica SARRAY/string array"""

    LEPTONICA_TYPENAME = 'SARRAY'
    cdata_destroy = lept.sarrayDestroy

    def __len__(self):
        return self._cdata.n

    def __getitem__(self, n):
        if 0 <= n < len(self):
            return ffi.string(self._cdata.array[n])
        raise IndexError(n)


class Sel(LeptonicaObject):
    """Leptonica 'sel'/selection element for hit-miss transform"""

    LEPTONICA_TYPENAME = 'SEL'
    cdata_destroy = lept.selDestroy

    @classmethod
    def from_selstr(cls, selstr, name):
        # TODO this will strip a horizontal line of don't care's
        lines = [line.strip() for line in selstr.split('\n') if line.strip()]
        h = len(lines)
        w = len(lines[0])
        lengths = set(len(line) for line in lines)
        if len(lengths) != 1:
            raise ValueError("All lines in selstr must be same length")

        repacked = ''.join(line.strip() for line in lines)
        buf_selstr = ffi.from_buffer(repacked.encode('ascii'))
        buf_name = ffi.from_buffer(name.encode('ascii'))
        sel = lept.selCreateFromString(buf_selstr, h, w, buf_name)
        return cls(sel)

    @classmethod
    def create_brick(cls, h, w, cy, cx, type_):
        sel = lept.selCreateBrick(h, w, cy, cx, type_)
        return cls(sel)

    def __repr__(self):
        selstr = ffi.gc(lept.selPrintToString(self._cdata), lept.lept_free)
        return '<Sel \n' + ffi.string(selstr).decode('ascii') + '\n>'


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
        pix_source = Pix.open(infile)
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


def remove_background(
    infile,
    outfile,
    tile_size=(40, 60),
    gamma=1.0,
    black_threshold=70,
    white_threshold=190,
):
    try:
        pix = Pix.open(infile)
    except LeptonicaIOError:
        raise LeptonicaIOError("Failed to open file: %s" % infile)

    pix = pix.background_norm(tile_size=tile_size).gamma_trc(
        gamma, black_threshold, white_threshold
    )

    try:
        pix.write_implied_format(outfile)
    except LeptonicaIOError:
        raise LeptonicaIOError("Failed to open destination file: %s" % outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Python wrapper to access Leptonica")

    subparsers = parser.add_subparsers(
        title='commands', description='supported operations'
    )

    parser_deskew = subparsers.add_parser('deskew')
    parser_deskew.add_argument(
        '-r',
        '--dpi',
        dest='dpi',
        action='store',
        type=int,
        default=300,
        help='input resolution',
    )
    parser_deskew.add_argument('infile', help='image to deskew')
    parser_deskew.add_argument('outfile', help='deskewed output image')
    parser_deskew.set_defaults(func=deskew)

    args = parser.parse_args()
    args.func(args)
