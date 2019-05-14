#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83
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

from collections import namedtuple
from decimal import Decimal
from enum import Enum
from math import hypot, isclose
from os import fspath
from pathlib import Path
from unittest.mock import Mock
from warnings import warn
import re

from pikepdf import PdfMatrix
import pikepdf

from . import ghosttext

from ..exceptions import EncryptedPdfError, MissingDependencyError


Colorspace = Enum('Colorspace', 'gray rgb cmyk lab icc index sep devn pattern jpeg2000')

Encoding = Enum(
    'Encoding', 'ccitt jpeg jpeg2000 jbig2 asciihex ascii85 lzw flate ' + 'runlength'
)

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
    '/RL': Encoding.runlength,
}

FRIENDLY_COMP = {
    Colorspace.gray: 1,
    Colorspace.rgb: 3,
    Colorspace.cmyk: 4,
    Colorspace.lab: 3,
    Colorspace.index: 1,
}


UNIT_SQUARE = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _is_unit_square(shorthand):
    values = map(float, shorthand)
    pairwise = zip(values, UNIT_SQUARE)
    return all([isclose(a, b, rel_tol=1e-3) for a, b in pairwise])


XobjectSettings = namedtuple('XobjectSettings', ['name', 'shorthand', 'stack_depth'])

InlineSettings = namedtuple('InlineSettings', ['iimage', 'shorthand', 'stack_depth'])

ContentsInfo = namedtuple(
    'ContentsInfo', ['xobject_settings', 'inline_images', 'found_vector']
)

TextboxInfo = namedtuple('TextboxInfo', ['bbox', 'is_visible', 'is_corrupt'])


class VectorInfo:
    def __init__(self):
        pass


def _normalize_stack(graphobjs):
    """Convert runs of qQ's in the stack into single graphobjs"""
    for operands, operator in graphobjs:
        operator = str(operator)
        if re.match(r'Q*q+$', operator):  # Zero or more Q, one or more q
            for char in operator:  # Split into individual
                yield ([], char)  # Yield individual
        else:
            yield (operands, operator)


def _interpret_contents(contentstream, initial_shorthand=UNIT_SQUARE):
    """Interpret the PDF content stream.

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

    According to the PDF specification, the maximum stack depth is 32. Other
    viewers tolerate some amount beyond this.  We issue a warning if the
    stack depth exceeds the spec limit and set a hard limit beyond this to
    bound our memory requirements.  If the stack underflows behavior is
    undefined in the spec, but we just pretend nothing happened and leave the
    CTM unchanged.
    """

    stack = []
    ctm = PdfMatrix(initial_shorthand)
    xobject_settings = []
    inline_images = []
    found_vector = False
    vector_ops = set('S s f F f* B B* b b*'.split())
    image_ops = set('BI ID EI q Q Do cm'.split())
    operator_whitelist = ' '.join(vector_ops | image_ops)

    for n, graphobj in enumerate(
        _normalize_stack(
            pikepdf.parse_content_stream(contentstream, operator_whitelist)
        )
    ):
        operands, operator = graphobj
        if operator == 'q':
            stack.append(ctm)
            if len(stack) > 32:  # See docstring
                if len(stack) > 128:
                    raise RuntimeError(
                        "PDF graphics stack overflowed hard limit, operator %i" % n
                    )
                warn("PDF graphics stack overflowed spec limit")
        elif operator == 'Q':
            try:
                ctm = stack.pop()
            except IndexError:
                # Keeping the ctm the same seems to be the only sensible thing
                # to do. Just pretend nothing happened, keep calm and carry on.
                warn("PDF graphics stack underflowed - PDF may be malformed")
        elif operator == 'cm':
            ctm = PdfMatrix(operands) @ ctm
        elif operator == 'Do':
            image_name = operands[0]
            settings = XobjectSettings(
                name=image_name, shorthand=ctm.shorthand, stack_depth=len(stack)
            )
            xobject_settings.append(settings)
        elif operator == 'INLINE IMAGE':  # BI/ID/EI are grouped into this
            iimage = operands[0]
            inline = InlineSettings(
                iimage=iimage, shorthand=ctm.shorthand, stack_depth=len(stack)
            )
            inline_images.append(inline)
        elif operator in vector_ops:
            found_vector = True

    return ContentsInfo(
        xobject_settings=xobject_settings,
        inline_images=inline_images,
        found_vector=found_vector,
    )


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

    def __init__(self, *, name='', pdfimage=None, inline=None, shorthand=None):

        self._name = str(name)
        self._shorthand = shorthand

        if inline is not None:
            self._origin = 'inline'
            pim = inline.iimage
        elif pdfimage is not None:
            self._origin = 'xobject'
            pim = pikepdf.PdfImage(pdfimage)
        self._width = pim.width
        self._height = pim.height

        # If /ImageMask is true, then this image is a stencil mask
        # (Images that draw with this stencil mask will have a reference to
        # it in their /Mask, but we don't actually need that information)
        if pim.image_mask:
            self._type = 'stencil'
        else:
            self._type = 'image'

        self._bpc = int(pim.bits_per_component)
        try:
            self._enc = FRIENDLY_ENCODING.get(pim.filters[0], 'image')
        except IndexError:
            self._enc = '?'

        try:
            self._color = FRIENDLY_COLORSPACE.get(pim.colorspace, '?')
        except NotImplementedError:
            self._color = '?'
        if self._enc == Encoding.jpeg2000:
            self._color = Colorspace.jpeg2000

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

    def __repr__(self):
        class_locals = {
            attr: getattr(self, attr, None)
            for attr in dir(self)
            if not attr.startswith('_')
        }
        return (
            "<ImageInfo '{name}' {type_} {width}x{height} {color} "
            "{comp} {bpc} {enc} {xres}x{yres}>"
        ).format(**class_locals)


def _find_inline_images(contentsinfo):
    "Find inline images in the contentstream"

    for n, inline in enumerate(contentsinfo.inline_images):
        yield ImageInfo(
            name='inline-%02d' % n, shorthand=inline.shorthand, inline=inline
        )


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
    xobjs = resources['/XObject'].as_dict()
    for xobj in xobjs:
        candidate = xobjs[xobj]
        if not '/Subtype' in candidate:
            continue
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

            yield ImageInfo(name=draw.name, pdfimage=pdfimage, shorthand=draw.shorthand)


def _find_form_xobject_images(pdf, container, contentsinfo):
    """Find any images that are in Form XObjects in the container

    The container may be a page, or a parent Form XObject.

    """
    if '/Resources' not in container:
        return
    resources = container['/Resources']
    if '/XObject' not in resources:
        return
    xobjs = resources['/XObject'].as_dict()
    for xobj in xobjs:
        candidate = xobjs[xobj]
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
            yield from _process_content_streams(
                pdf=pdf, container=form_xobject, shorthand=ctm_shorthand
            )


def _process_content_streams(*, pdf, container, shorthand=None):
    """Find all individual instances of images drawn in the container

    Usually the container is a page, but it may also be a Form XObject.

    On a typical page images are stored inline or as regular images
    in an XObject.

    Form XObjects may include inline images, XObject images,
    and recursively, other Form XObjects; and also vector graphic objects.

    Every instance of an image being drawn somewhere is flattened and
    treated as a unique image, since if the same image is drawn multiple times
    on one page it may be drawn at differing resolutions, and our objective
    is to find the resolution at which the page can be rastered without
    downsampling.

    """

    if container.get('/Type') == '/Page' and '/Contents' in container:
        initial_shorthand = shorthand or UNIT_SQUARE
    elif container.get('/Type') == '/XObject' and container['/Subtype'] == '/Form':
        # Set the CTM to the state it was when the "Do" operator was
        # encountered that is drawing this instance of the Form XObject
        ctm = PdfMatrix(shorthand) if shorthand else PdfMatrix.identity()

        # A Form XObject may provide its own matrix to map form space into
        # user space. Get this if one exists
        form_shorthand = container.get('/Matrix', PdfMatrix.identity())
        form_matrix = PdfMatrix(form_shorthand)

        # Concatenate form matrix with CTM to ensure CTM is correct for
        # drawing this instance of the XObject
        ctm = form_matrix @ ctm
        initial_shorthand = ctm.shorthand
    else:
        return

    contentsinfo = _interpret_contents(container, initial_shorthand)

    if contentsinfo.found_vector:
        yield VectorInfo()
    yield from _find_inline_images(contentsinfo)
    yield from _find_regular_images(container, contentsinfo)
    yield from _find_form_xobject_images(pdf, container, contentsinfo)


def _page_has_text(text_blocks, page_width, page_height):
    """Smarter text detection that ignores text in margins"""

    pw, ph = float(page_width), float(page_height)

    margin_ratio = 0.125
    interior_bbox = (
        margin_ratio * pw,  # left
        (1 - margin_ratio) * ph,  # top
        (1 - margin_ratio) * pw,  # right
        margin_ratio * ph,  # bottom  (first quadrant: bottom < top)
    )

    def rects_intersect(a, b):
        """
        Where (a,b) are 4-tuple rects (left-0, top-1, right-2, bottom-3)
        https://stackoverflow.com/questions/306316/determine-if-two-rectangles-overlap-each-other
        Formula assumes all boxes are in first quadrant
        """
        return a[0] < b[2] and a[2] > b[0] and a[1] > b[3] and a[3] < b[1]

    has_text = False
    for bbox in text_blocks:
        if rects_intersect(bbox, interior_bbox):
            has_text = True
            break
    return has_text


def simplify_textboxes(miner, textbox_getter):
    """Extract only limited content from text boxes

    We do this to save memory and ensure that our objects are pickleable.
    """
    for box in textbox_getter(miner):
        first_line = box._objs[0]
        first_char = first_line._objs[0]

        visible = first_char.rendermode != 3
        corrupt = first_char.get_text() == '\ufffd'
        yield TextboxInfo(box.bbox, visible, corrupt)


def _pdf_get_pageinfo(pdf, pageno: int, infile, xmltext):
    pageinfo = {}
    pageinfo['pageno'] = pageno
    pageinfo['images'] = []

    page = pdf.pages[pageno]
    mediabox = [Decimal(d) for d in page.MediaBox.as_list()]
    width_pt = mediabox[2] - mediabox[0]
    height_pt = mediabox[3] - mediabox[1]

    if xmltext is not None:
        bboxes = ghosttext.page_get_textblocks(
            fspath(infile), pageno, xmltext=xmltext, height=height_pt
        )
        pageinfo['bboxes'] = bboxes
    else:
        # pdfminer required for this section
        try:
            from .layout import get_page_analysis, get_text_boxes
        except ImportError:
            raise MissingDependencyError(
                "pdfminer is required for this feature. Your distribution "
                "may not have installed it."
            )
        pscript5_mode = str(pdf.docinfo.get('/Creator')).startswith('PScript5')
        miner = get_page_analysis(infile, pageno, pscript5_mode)
        pageinfo['textboxes'] = list(simplify_textboxes(miner, get_text_boxes))
        bboxes = (box.bbox for box in pageinfo['textboxes'])

    pageinfo['has_text'] = _page_has_text(bboxes, width_pt, height_pt)

    userunit = page.get('/UserUnit', Decimal(1.0))
    if not isinstance(userunit, Decimal):
        userunit = Decimal(userunit)
    pageinfo['userunit'] = userunit
    pageinfo['width_inches'] = width_pt * userunit / Decimal(72.0)
    pageinfo['height_inches'] = height_pt * userunit / Decimal(72.0)

    try:
        pageinfo['rotate'] = int(page['/Rotate'])
    except KeyError:
        pageinfo['rotate'] = 0

    userunit_shorthand = (userunit, 0, 0, userunit, 0, 0)
    contentsinfo = [
        ci
        for ci in _process_content_streams(
            pdf=pdf, container=page, shorthand=userunit_shorthand
        )
    ]

    pageinfo['has_vector'] = False
    if any(isinstance(ci, VectorInfo) for ci in contentsinfo):
        pageinfo['has_vector'] = True

    pageinfo['images'] = [im for im in contentsinfo if isinstance(im, ImageInfo)]
    if pageinfo['images']:
        xres = Decimal(max(image.xres for image in pageinfo['images']))
        yres = Decimal(max(image.yres for image in pageinfo['images']))
        pageinfo['xres'], pageinfo['yres'] = xres, yres
        pageinfo['width_pixels'] = int(round(xres * pageinfo['width_inches']))
        pageinfo['height_pixels'] = int(round(yres * pageinfo['height_inches']))

    return pageinfo


def _pdf_get_all_pageinfo(infile, detailed_analysis=False, log=None):
    if not log:
        log = Mock()

    pdf = pikepdf.open(infile)  # Do not close in this function
    if pdf.is_encrypted:
        pdf.close()
        raise EncryptedPdfError()  # Triggered by encryption with empty passwd
    if detailed_analysis:
        pages_xml = None
    else:
        pages_xml = ghosttext.extract_text_xml(infile, pdf, pageno=None, log=log)

    pages = []
    for n in range(len(pdf.pages)):
        page_xml = pages_xml[n] if pages_xml else None
        page = PageInfo(pdf, n, infile, page_xml, detailed_analysis)
        pages.append(page)

    return pages, pdf


class PageInfo:
    def __init__(self, pdf, pageno, infile, xmltext, detailed_analysis=False):
        self._pageno = pageno
        self._infile = infile
        self._pageinfo = _pdf_get_pageinfo(pdf, pageno, infile, xmltext)
        self._detailed_analysis = detailed_analysis

    @property
    def pageno(self):
        return self._pageno

    @property
    def has_text(self):
        return self._pageinfo['has_text']

    @property
    def has_corrupt_text(self):
        if not self._detailed_analysis:
            raise NotImplementedError('Did not do detailed analysis')
        return any(tbox.is_corrupt for tbox in self._pageinfo['textboxes'])

    @property
    def has_vector(self):
        return self._pageinfo['has_vector']

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

    def get_textareas(self, visible=None, corrupt=None):
        def predicate(obj, want_visible, want_corrupt):
            result = True
            if want_visible is not None:
                if obj.is_visible != want_visible:
                    result = False
            if want_corrupt is not None:
                if obj.is_corrupt != want_corrupt:
                    result = False
            return result

        if 'textboxes' not in self._pageinfo:
            if visible is not None and corrupt is not None:
                raise NotImplementedError('Ghostscript textboxes cannot be classified')
            return self._pageinfo['bboxes']

        return (
            obj.bbox
            for obj in self._pageinfo['textboxes']
            if predicate(obj, visible, corrupt)
        )

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

    def __repr__(self):
        return (
            '<PageInfo ' 'pageno={} {}"x{}" rotation={} res={}x{} has_text={}>'
        ).format(
            self.pageno,
            self.width_inches,
            self.height_inches,
            self.rotation,
            self.xres,
            self.yres,
            self.has_text,
        )


class PdfInfo:
    """Get summary information about a PDF"""

    def __init__(self, infile, detailed_page_analysis=False, log=None):
        self._infile = infile
        self._pages, pdf = _pdf_get_all_pageinfo(
            infile, detailed_page_analysis, log=log
        )
        self._needs_rendering = pdf.root.get('/NeedsRendering', False)
        self._has_acroform = False
        if '/AcroForm' in pdf.root:
            if len(pdf.root.AcroForm.get('/Fields', [])) > 0:
                self._has_acroform = True
            elif '/XFA' in pdf.root.AcroForm:
                self._has_acroform = True
        pdf.close()

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

    @property
    def has_acroform(self):
        return self._has_acroform

    @property
    def filename(self):
        if not isinstance(self._infile, (str, Path)):
            raise NotImplementedError("can't get filename from stream")
        return self._infile

    @property
    def needs_rendering(self):
        return self._needs_rendering

    def __getitem__(self, item):
        return self._pages[item]

    def __len__(self):
        return len(self._pages)

    def __repr__(self):
        return f"<PdfInfo('...'), page count={len(self)}>"


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
