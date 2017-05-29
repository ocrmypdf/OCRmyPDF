#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE
from decimal import Decimal
from math import hypot, isclose
import re
import sys
import PyPDF2 as pypdf
from collections import namedtuple
from collections.abc import MutableMapping, Mapping
import warnings
from pathlib import Path
from enum import Enum
from .helpers import universal_open


matrix_mult = pypdf.pdf.utils.matrixMultiply

Colorspace = Enum('Colorspace',
                  'gray rgb cmyk lab icc index sep devn pattern jpeg2000')

Encoding = Enum('Encoding',
                'ccitt jpeg jpeg2000 jbig2 asciihex ascii85 lzw flate ' + \
                'runlength')


FRIENDLY_COLORSPACE = {
    '/DeviceGray': Colorspace.gray,
    '/CalGray': Colorspace.gray,
    '/DeviceRGB': Colorspace.rgb,
    '/CalRGB': Colorspace.rgb,
    '/DeviceCMYK': Colorspace.cmyk,
    '/Lab': Colorspace.lab,
    '/ICCBased': Colorspace.icc,
    '/Indexed': Colorspace.index,
    '/Separation': Colorspace.sep,
    '/DeviceN': Colorspace.devn,
    '/Pattern': Colorspace.pattern,
    '/G': Colorspace.gray,  # Abbreviations permitted in inline images
    '/RGB': Colorspace.rgb,
    '/CMYK': Colorspace.cmyk,
    '/I': Colorspace.index,
}

FRIENDLY_ENCODING = {
    '/CCITTFaxDecode': Encoding.ccitt,
    '/DCTDecode': Encoding.jpeg,
    '/JPXDecode': Encoding.jpeg2000,
    '/JBIG2Decode': Encoding.jbig2,
    '/CCF': Encoding.ccitt,  # Abbreviations permitted in inline images
    '/DCT': Encoding.jpeg,
    '/AHx': Encoding.asciihex,
    '/A85': Encoding.ascii85,
    '/LZW': Encoding.lzw,
    '/Fl': Encoding.flate,
    '/RL': Encoding.runlength
}

FRIENDLY_COMP = {
    Colorspace.gray: 1,
    Colorspace.rgb: 3,
    Colorspace.cmyk: 4,
    Colorspace.lab: 3,
    Colorspace.index: 1
}


UNIT_SQUARE = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _matrix_from_shorthand(shorthand):
    """Convert from PDF matrix shorthand to full matrix

    PDF 1.7 spec defines a shorthand for describing the entries of a matrix
    since the last column is always (0, 0, 1).
    """

    a, b, c, d, e, f = map(float, shorthand)
    return ((a, b, 0),
            (c, d, 0),
            (e, f, 1))


def _shorthand_from_matrix(matrix):
    """Convert from transformation matrix to PDF shorthand."""
    a, b = matrix[0][0], matrix[0][1]
    c, d = matrix[1][0], matrix[1][1]
    e, f = matrix[2][0], matrix[2][1]
    return tuple(map(float, (a, b, c, d, e, f)))


def _is_unit_square(shorthand):
    values = map(float, shorthand)
    pairwise = zip(values, UNIT_SQUARE)
    return all([isclose(a, b, rel_tol=1e-3) for a, b in pairwise])

XobjectSettings = namedtuple('XobjectSettings',
    ['name', 'shorthand', 'stack_depth'])

InlineSettings = namedtuple('InlineSettings',
    ['settings', 'shorthand', 'stack_depth'])

ContentsInfo = namedtuple('ContentsInfo', ['xobject_settings', 'inline_images'])


def _normalize_stack(operations):
    """Fix runs of qQ's in the stack

    For some reason PyPDF2 converts runs of qqq, QQ, QQQq, etc. into single
    operations.  Break this silliness up and issue each stack operation
    individually so we don't lose count.

    """
    for operands, command in operations:
        if re.match(br'Q*q+$', command):   # Zero or more Q, one or more q
            for char in command:           # Split into individual bytes
                yield ([], bytes([char]))  # Yield individual bytes
        else:
            yield (operands, command)


def _interpret_contents(contentstream, initial_shorthand=UNIT_SQUARE):
    """Interpret the PDF content stream

    The stack represents the state of the PDF graphics stack.  We are only
    interested in the current transformation matrix (CTM) so we only track
    this object; a full implementation would need to track many other items.

    The CTM is initialized to the mapping from user space to device space.
    PDF units are 1/72".  In a PDF viewer or printer this matrix is initialized
    to the transformation to device space.  For example if set to
    (1/72, 0, 0, 1/72, 0, 0) then all units would be calculated in inches.

    Images are always considered to be (0, 0) -> (1, 1).  Before drawing an
    image there should be a 'cm' that sets up an image coordinate system
    where drawing from (0, 0) -> (1, 1) will draw on the desired area of the
    page.

    PDF units suit our needs so we initialize ctm to the identity matrix.

    PyPDF2 replaces inline images with a fake "INLINE IMAGE" operator.

    """

    operations = contentstream.operations
    stack = []
    ctm = _matrix_from_shorthand(initial_shorthand)
    xobject_settings = []
    inline_images = []

    for n, op in enumerate(_normalize_stack(operations)):
        operands, command = op
        if command == b'q':
            stack.append(ctm)
            if len(stack) > 32:
                raise RuntimeError(
                    "PDF graphics stack overflow, command %i" % n)
        elif command == b'Q':
            try:
                ctm = stack.pop()
            except IndexError:
                raise RuntimeError(
                    "PDF graphics stack underflow, command %i" % n)
        elif command == b'cm':
            ctm = matrix_mult(
                _matrix_from_shorthand(operands), ctm)
        elif command == b'Do':
            image_name = operands[0]
            settings = XobjectSettings(
                name=image_name, shorthand=_shorthand_from_matrix(ctm),
                stack_depth=len(stack))
            xobject_settings.append(settings)
        elif command == b'INLINE IMAGE':
            settings = operands['settings']
            inline = InlineSettings(
                settings=settings, shorthand=_shorthand_from_matrix(ctm),
                stack_depth=len(stack))
            inline_images.append(inline)

    return ContentsInfo(
        xobject_settings=xobject_settings,
        inline_images=inline_images)


def _get_dpi(ctm_shorthand, image_size):
    """Given the transformation matrix and image size, find the image DPI.

    PDFs do not include image resolution information within image data.
    Instead, the PDF page content stream describes the location where the
    image will be rasterized, and the effective resolution is the ratio of the
    pixel size to raster target size.

    Normally a scanned PDF has the paper size set appropriately but this is
    not guaranteed. The most common case is a cropped image will change the
    page size (/CropBox) without altering the page content stream. That means
    it is not sufficient to assume that the image fills the page, even though
    that is the most common case.

    A PDF image may be scaled (always), cropped, translated, rotated in place
    to an arbitrary angle (rarely) and skewed. Only equal area mappings can
    be expressed, that is, it is not necessary to consider distortions where
    the effective DPI varies with position.

    To determine the image scale, transform an offset axis vector v0 (0, 0),
    width-axis vector v0 (1, 0), height-axis vector vh (0, 1) with the matrix,
    which gives the dimensions of the image in PDF units. From there we can
    compare to actual image dimensions. PDF uses
    row vector * matrix_tranposed unlike the traditional
    matrix * column vector.

    The offset, width and height vectors can be combined in a matrix and
    multiplied by the transform matrix. Then we want to calculated
        magnitude(width_vector - offset_vector)
    and
        magnitude(height_vector - offset_vector)

    When the above is worked out algebraically, the effect of translation
    cancels out, and the vector magnitudes become functions of the nonzero
    transformation matrix indices. The results of the derivation are used
    in this code.

    pdfimages -list does calculate the DPI in some way that is not completely
    naive, but it does not get the DPI of rotated images right, so cannot be
    used anymore to validate this. Photoshop works, or using Acrobat to
    rotate the image back to normal.

    It does not matter if the image is partially cropped, or even out of the
    /MediaBox.

    """

    a, b, c, d, _, _ = ctm_shorthand

    # Calculate the width and height of the image in PDF units
    image_drawn_width = hypot(a, b)
    image_drawn_height = hypot(c, d)

    # The scale of the image is pixels per unit of default user space (1/72")
    scale_w = image_size[0] / image_drawn_width
    scale_h = image_size[1] / image_drawn_height

    # DPI = scale * 72
    dpi_w = scale_w * 72.0
    dpi_h = scale_h * 72.0

    return dpi_w, dpi_h


class ImageInfo:
    DPI_PREC = Decimal('1.000')

    def __init__(self, *, name='', pdfimage=None, inline=None,
                 shorthand=None):

        self._name = name
        self._shorthand = shorthand
        if inline:
            # Fixme does not work for inline images with non abbreviated
            # fields
            self._origin = 'inline'
            self._width = inline.settings['/W']
            self._height = inline.settings['/H']
            self._bpc = inline.settings.get('/BPC', 8)
            try:
                self._color = FRIENDLY_COLORSPACE[inline.settings['/CS']]
            except Exception:
                self._color = '-'
            self._comp = FRIENDLY_COMP.get(self._color, '?')
            if '/F' in inline.settings:
                filter_ = inline.settings['/F']
                if isinstance(filter_, pypdf.generic.ArrayObject):
                    filter_ = filter_[0]
                self._enc = FRIENDLY_ENCODING.get(filter_, 'image')
            else:
                self._enc = 'image'
        elif pdfimage:
            self._origin = 'xobject'
            self._width = pdfimage['/Width']
            self._height = pdfimage['/Height']
            if '/BitsPerComponent' in pdfimage:
                self._bpc = pdfimage['/BitsPerComponent']
            else:
                self._bpc = 8

            # Fixme: this is incorrectly treats explicit masks as stencil masks,
            # but good enough for now. Explicit masks have /ImageMask true but are
            # never called for in content stream, instead are drawn as a /Mask on
            # other images. For our purposes finding out the details of /Mask
            # will seldom matter.
            if '/ImageMask' in pdfimage:
                self._type = 'stencil' if pdfimage['/ImageMask'].value \
                    else 'image'
            else:
                self._type = 'image'
            if '/Filter' in pdfimage:
                filter_ = pdfimage['/Filter']
                if isinstance(filter_, pypdf.generic.ArrayObject):
                    filter_ = filter_[0]
                self._enc = FRIENDLY_ENCODING.get(filter_, 'image')
            else:
                self._enc = 'image'
            if '/ColorSpace' in pdfimage:
                cs = pdfimage['/ColorSpace']
                if isinstance(cs, pypdf.generic.ArrayObject):
                    cs = cs[0]
                self._color = FRIENDLY_COLORSPACE.get(cs, '-')
            else:
                self._color = FRIENDLY_COLORSPACE[Colorspace.jpeg2000] \
                    if self._enc == Encoding.jpeg2000 else '?'

            self._comp = FRIENDLY_COMP.get(self._color, '?')

            # Bit of a hack... infer grayscale if component count is uncertain
            # but encoding must be monochrome. This happens if a monochrome image
            # has an ICC profile attached. Better solution would be to examine
            # the ICC profile.
            if self._comp == '?' and self._enc in (Encoding.ccitt, 'jbig2'):
                self._comp = FRIENDLY_COMP[Colorspace.gray]

    @property
    def name(self):
        return self._name

    @property
    def type_(self):
        return self._type

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def bpc(self):
        return self._bpc

    @property
    def color(self):
        return self._color

    @property
    def comp(self):
        return self._comp

    @property
    def enc(self):
        return self._enc

    @property
    def xres(self):
        return _get_dpi(self._shorthand, (self._width, self._height))[0]

    @property
    def yres(self):
        return _get_dpi(self._shorthand, (self._width, self._height))[1]

    def __getitem__(self, item):
        warnings.warn("ImageInfo.__getitem__", DeprecationWarning)
        if item in ('name', 'width', 'height', 'bpc', 'color', 'comp', 'enc'):
            return getattr(self, item)
        elif item == 'dpi_w':
            return Decimal(self.xres).quantize(self.DPI_PREC)
        elif item == 'dpi_h':
            return Decimal(self.yres).quantize(self.DPI_PREC)
        elif item == 'dpi':
            return Decimal(self.xres * self.yres).sqrt().quantize(
                self.DPI_PREC)
        else:
            raise KeyError(item)

    def __repr__(self):
        class_locals = {attr: getattr(self, attr, None) for attr in dir(self)
                        if not attr.startswith('_')}
        return (
            "<ImageInfo '{name}' {type_} {width}x{height} {color} "
            "{comp} {bpc} {enc} {xres}x{yres}>").format(**class_locals)


def _find_inline_images(contentsinfo):
    "Find inline images in the contentstream"

    for n, inline in enumerate(contentsinfo.inline_images):
        yield ImageInfo(name='inline-%02d' % n, shorthand=inline.shorthand,
                        inline=inline)


def _image_xobjects(container):
    """Search for all XObject-based images in the container

    Usually the container is a page, but it could also be a Form XObject
    that contains images. Filter out the Form XObjects which are dealt with
    elsewhere.

    Generate a sequence of tuples (image, xobj container), where container,
    where xobj is the name of the object and image is the object itself,
    since the object does not know its own name.

    """

    if '/Resources' not in container:
        return
    resources = container['/Resources']
    if '/XObject' not in resources:
        return
    for xobj in resources['/XObject']:
        candidate = resources['/XObject'][xobj]
        if candidate['/Subtype'] == '/Image':
            pdfimage = candidate
            yield (pdfimage, xobj)


def _find_regular_images(container, contentsinfo):
    """Find images stored in the container's /Resources /XObject

    Usually the container is a page, but it could also be a Form XObject
    that contains images.

    Generates images with their DPI at time of drawing.

    """

    for pdfimage, xobj in _image_xobjects(container):

        # For each image that is drawn on this, check if we drawing the
        # current image - yes this is O(n^2), but n == 1 almost always
        for draw in contentsinfo.xobject_settings:
            if draw.name != xobj:
                continue

            if draw.stack_depth == 0 and _is_unit_square(draw.shorthand):
                # At least one PDF in the wild (and test suite) draws an image
                # when the graphics stack depth is 0, meaning that the image
                # gets drawn into a square of 1x1 PDF units (or 1/72",
                # or 0.35 mm).  The equivalent DPI will be >100,000.  Exclude
                # these from our DPI calculation for the page.
                continue

            yield ImageInfo(name=draw.name, pdfimage=pdfimage, shorthand=
                            draw.shorthand)


def _find_form_xobject_images(pdf, container, contentsinfo):
    """Find any images that are in Form XObjects in the container

    The container may be a page, or a parent Form XObject.

    """
    if '/Resources' not in container:
        return
    resources = container['/Resources']
    if '/XObject' not in resources:
        return
    for xobj in resources['/XObject']:
        candidate = resources['/XObject'][xobj]
        if candidate['/Subtype'] != '/Form':
            continue

        form_xobject = candidate
        for settings in contentsinfo.xobject_settings:
            if settings.name != xobj:
                continue

            # Find images once for each time this Form XObject is drawn.
            # This could be optimized to cache the multiple drawing events
            # but in practice both Form XObjects and multiple drawing of the
            # same object are both very rare.
            ctm_shorthand = settings.shorthand
            yield from _find_images(
                pdf=pdf, container=form_xobject, shorthand=ctm_shorthand)


def _find_images(*, pdf, container, shorthand=None):
    """Find all individual instances of images drawn in the container

    Usually the container is a page, but it may also be a Form XObject.

    On a typical page images are stored inline or as regular images
    in an XObject.

    Form XObjects may include inline images, XObject images,
    and recursively, other Form XObjects; and also vector drawing commands.

    Every instance of an image being drawn somewhere is flattened and
    treated as a unique image, since if the same image is drawn multiple times
    on one page it may be drawn at differing resolutions, and our objective
    is to find the resolution at which the page can be rastered without
    downsampling.

    """

    if container.get('/Type') == '/Page' and '/Contents' in container:
        # For a /Page the content stream is attached to the page's /Contents
        page = container
        contentstream = pypdf.pdf.ContentStream(page.getContents(), pdf)
        initial_shorthand = shorthand or UNIT_SQUARE
    elif container.get('/Type') == '/XObject' and \
            container['/Subtype'] == '/Form':
        # For a Form XObject that content stream is attached to the XObject
        contentstream = pypdf.pdf.ContentStream(container, pdf)

        # Set the CTM to the state it was when the "Do" operator was
        # encountered that is drawing this instance of the Form XObject
        ctm = _matrix_from_shorthand(shorthand or UNIT_SQUARE)

        # A Form XObject may provide its own matrix to map form space into
        # user space. Get this if one exists
        form_matrix = _matrix_from_shorthand(
                container.get('/Matrix', UNIT_SQUARE))

        # Concatenate form matrix with CTM to ensure CTM is correct for
        # drawing this instance of the XObject
        ctm = matrix_mult(form_matrix, ctm)
        initial_shorthand = _shorthand_from_matrix(ctm)
    else:
        return

    contentsinfo = _interpret_contents(contentstream, initial_shorthand)

    yield from _find_inline_images(contentsinfo)
    yield from _find_regular_images(container, contentsinfo)
    yield from _find_form_xobject_images(pdf, container, contentsinfo)


def _page_has_text(pdf, page):
    if not '/Contents' in page:
        return False

    # Simple test
    text = page.extractText()
    if text.strip() != '':
        return True

    # More nuanced test to deal with quirks of Tesseract PDF generation
    # Check if there's a Glyphless font
    try:
        font = page['/Resources']['/Font']
    except KeyError:
        pass
    else:
        font_objects = list(font.keys())
        for font_object in font_objects:
            basefont = font[font_object]['/BaseFont']
            if basefont.endswith('GlyphLessFont'):
                return True

    return False


def _pdf_get_pageinfo(pdf, pageno: int):
    pageinfo = {}
    pageinfo['pageno'] = pageno
    pageinfo['images'] = []

    if isinstance(pdf, Path):
        pdf = pypdf.PdfFileReader(str(pdf))
    elif isinstance(pdf, str):
        pdf = pypdf.PdfFileReader(pdf)

    page = pdf.pages[pageno]

    pageinfo['has_text'] = _page_has_text(pdf, page)

    width_pt = page.mediaBox.getWidth()
    height_pt = page.mediaBox.getHeight()

    userunit = page.get('/UserUnit', Decimal(1.0))
    pageinfo['userunit'] = userunit
    pageinfo['width_inches'] = width_pt * userunit / Decimal(72.0)
    pageinfo['height_inches'] = height_pt * userunit / Decimal(72.0)

    try:
        pageinfo['rotate'] = int(page['/Rotate'])
    except KeyError:
        pageinfo['rotate'] = 0

    userunit_shorthand = (userunit, 0, 0, userunit, 0, 0)
    pageinfo['images'] = [im for im in
                          _find_images(pdf=pdf, container=page,
                                       shorthand=userunit_shorthand)]
    if pageinfo['images']:
        xres = max(image['dpi_w'] for image in pageinfo['images'])
        yres = max(image['dpi_h'] for image in pageinfo['images'])
        pageinfo['xres'], pageinfo['yres'] = xres, yres
        pageinfo['width_pixels'] = \
            int(round(xres * pageinfo['width_inches']))
        pageinfo['height_pixels'] = \
            int(round(yres * pageinfo['height_inches']))

    return pageinfo


def _pdf_get_all_pageinfo(infile):
    with universal_open(infile, 'rb') as f:
        pdf = pypdf.PdfFileReader(f)
        return [PageInfo(pdf, n) for n in range(pdf.numPages)]


class PageInfo:
    def __init__(self, pdf, pageno):
        self._pageno = pageno
        self._pageinfo = _pdf_get_pageinfo(pdf, pageno)

    @property
    def pageno(self):
        return self._pageno

    @property
    def has_text(self):
        return self._pageinfo['has_text']

    @property
    def width_inches(self):
        return self._pageinfo['width_inches']

    @property
    def height_inches(self):
        return self._pageinfo['height_inches']

    @property
    def width_pixels(self):
        return int(round(self.width_inches * self.xres))

    @property
    def height_pixels(self):
        return int(round(self.height_inches * self.yres))

    @property
    def rotation(self):
        return self._pageinfo.get('rotate', None)

    @rotation.setter
    def rotation(self, value):
        if value in (0, 90, 180, 270, 360, -90, -180, -270):
            self._pageinfo['rotate'] = value
        else:
            raise ValueError("rotation must be a cardinal angle")

    @property
    def images(self):
        return self._pageinfo['images']

    @property
    def xres(self):
        return self._pageinfo.get('xres', None)

    @property
    def yres(self):
        return self._pageinfo.get('yres', None)

    @property
    def userunit(self):
        return self._pageinfo.get('userunit', None)

    @property
    def min_version(self):
        if self.userunit is not None:
            return '1.6'
        else:
            return '1.5'

    @property
    def images(self):
        return self._pageinfo['images']

    def __repr__(self):
        return (
            '<PageInfo '
            'pageno={} {}"x{}" rotation={} res={}x{} has_text={}>').format(
            self.pageno, self.width_inches, self.height_inches,
            self.rotation,
            self.xres, self.yres, self.has_text
        )


class PdfInfo:
    """Get summary information about a PDF
    
    """
    def __init__(self, infile):
        self._infile = infile
        self._pages = _pdf_get_all_pageinfo(infile)

    @property
    def pages(self):
        return self._pages

    @property
    def min_version(self):
        # The minimum PDF is the maximum version that any particular page needs
        return max(page.min_version for page in self.pages)

    @property
    def has_userunit(self):
        return any(page.userunit != 1.0 for page in self.pages)

    def __getitem__(self, item):
        return self._pages[item]

    def __len__(self):
        return len(self._pages)

    def __repr__(self):
        return "<PdfInfo('...'), page count={}>".format(len(self))

    # def __getstate__(self):
    #     state = {'_infile': self._infile}
    #     return state
    #
    # def __setstate__(self, state):
    #     self._infile = state['_infile']
    #     self._pages = _pdf_get_all_pageinfo(self._infile)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    args = parser.parse_args()
    info = _pdf_get_all_pageinfo(args.infile)
    from pprint import pprint
    pprint(info)


if __name__ == '__main__':
    main()
