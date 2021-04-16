#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import atexit
import logging
import re
from collections import defaultdict, namedtuple
from contextlib import ExitStack
from decimal import Decimal
from enum import Enum
from functools import partial
from math import hypot, inf, isclose
from os import PathLike
from pathlib import Path
from typing import Container, Iterator, Optional, Tuple, Union
from warnings import warn

import pikepdf
from pikepdf import Object, Pdf, PdfMatrix

from ocrmypdf._concurrent import Executor, SerialExecutor
from ocrmypdf.exceptions import EncryptedPdfError, InputFileError
from ocrmypdf.helpers import Resolution, available_cpu_count, pikepdf_enable_mmap
from ocrmypdf.pdfinfo.layout import get_page_analysis, get_text_boxes

logger = logging.getLogger()

Colorspace = Enum('Colorspace', 'gray rgb cmyk lab icc index sep devn pattern jpeg2000')

Encoding = Enum(
    'Encoding', 'ccitt jpeg jpeg2000 jbig2 asciihex ascii85 lzw flate runlength'
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
    return all(isclose(a, b, rel_tol=1e-3) for a, b in pairwise)


XobjectSettings = namedtuple('XobjectSettings', ['name', 'shorthand', 'stack_depth'])

InlineSettings = namedtuple('InlineSettings', ['iimage', 'shorthand', 'stack_depth'])

ContentsInfo = namedtuple(
    'ContentsInfo',
    ['xobject_settings', 'inline_images', 'found_vector', 'found_text', 'name_index'],
)

TextboxInfo = namedtuple('TextboxInfo', ['bbox', 'is_visible', 'is_corrupt'])


class VectorMarker:
    pass


class TextMarker:
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


def _interpret_contents(contentstream: Object, initial_shorthand=UNIT_SQUARE):
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
    name_index = defaultdict(lambda: [])
    found_vector = False
    found_text = False
    vector_ops = set('S s f F f* B B* b b*'.split())
    text_showing_ops = set("""TJ Tj " '""".split())
    image_ops = set('BI ID EI q Q Do cm'.split())
    operator_whitelist = ' '.join(vector_ops | text_showing_ops | image_ops)

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
            name_index[image_name].append(settings)
        elif operator == 'INLINE IMAGE':  # BI/ID/EI are grouped into this
            iimage = operands[0]
            inline = InlineSettings(
                iimage=iimage, shorthand=ctm.shorthand, stack_depth=len(stack)
            )
            inline_images.append(inline)
        elif operator in vector_ops:
            found_vector = True
        elif operator in text_showing_ops:
            found_text = True

    return ContentsInfo(
        xobject_settings=xobject_settings,
        inline_images=inline_images,
        found_vector=found_vector,
        found_text=found_text,
        name_index=name_index,
    )


def _get_dpi(ctm_shorthand, image_size) -> Resolution:
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
    row vector * matrix_transposed unlike the traditional
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
    image_drawn = hypot(a, b), hypot(c, d)

    def calc(drawn, pixels, inches_per_pt=72.0):
        # The scale of the image is pixels per unit of default user space (1/72")
        scale = pixels / drawn if drawn != 0 else inf
        dpi = scale * inches_per_pt
        return dpi

    dpi_w, dpi_h = (calc(image_drawn[n], image_size[n]) for n in range(2))
    return Resolution(dpi_w, dpi_h)


class ImageInfo:
    DPI_PREC = Decimal('1.000')

    def __init__(
        self,
        *,
        name='',
        pdfimage: Optional[Object] = None,
        inline: Optional[Object] = None,
        shorthand=None,
    ):
        self._name = str(name)
        self._shorthand = shorthand

        if inline is not None:
            self._origin = 'inline'
            pim = inline.iimage
        elif pdfimage is not None:
            self._origin = 'xobject'
            pim = pikepdf.PdfImage(pdfimage)
        else:
            raise ValueError("Either pdfimage or inline must be set")
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

        if self._color == Colorspace.icc:
            # Check the ICC profile to determine actual colorspace
            pim_icc = pim.icc
            if pim_icc.profile.xcolor_space == 'GRAY':
                self._comp = 1
            elif pim_icc.profile.xcolor_space == 'CMYK':
                self._comp = 4
            else:
                self._comp = 3
        else:
            self._comp = FRIENDLY_COMP.get(self._color, '?')

            # Bit of a hack... infer grayscale if component count is uncertain
            # but encoding only supports monochrome.
            if self._comp == '?' and self._enc in (Encoding.ccitt, Encoding.jbig2):
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
    def renderable(self):
        return self.dpi.is_finite and self.width >= 0 and self.height >= 0

    @property
    def dpi(self):
        return _get_dpi(self._shorthand, (self._width, self._height))

    def __repr__(self):
        class_locals = {
            attr: getattr(self, attr, None)
            for attr in dir(self)
            if not attr.startswith('_')
        }
        return (
            "<ImageInfo '{name}' {type_} {width}x{height} {color} "
            "{comp} {bpc} {enc} {dpi}>"
        ).format(**class_locals)


def _find_inline_images(contentsinfo: ContentsInfo) -> Iterator[ImageInfo]:
    "Find inline images in the contentstream"

    for n, inline in enumerate(contentsinfo.inline_images):
        yield ImageInfo(
            name='inline-%02d' % n, shorthand=inline.shorthand, inline=inline
        )


def _image_xobjects(container) -> Iterator[Tuple[Object, str]]:
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
        candidate: Object = xobjs[xobj]
        if not '/Subtype' in candidate:
            continue
        if candidate['/Subtype'] == '/Image':
            pdfimage = candidate
            yield (pdfimage, xobj)


def _find_regular_images(
    container: Object, contentsinfo: ContentsInfo
) -> Iterator[ImageInfo]:
    """Find images stored in the container's /Resources /XObject

    Usually the container is a page, but it could also be a Form XObject
    that contains images.

    Generates images with their DPI at time of drawing.
    """

    for pdfimage, xobj in _image_xobjects(container):
        if xobj not in contentsinfo.name_index:
            continue
        for draw in contentsinfo.name_index[xobj]:
            if draw.stack_depth == 0 and _is_unit_square(draw.shorthand):
                # At least one PDF in the wild (and test suite) draws an image
                # when the graphics stack depth is 0, meaning that the image
                # gets drawn into a square of 1x1 PDF units (or 1/72",
                # or 0.35 mm).  The equivalent DPI will be >100,000.  Exclude
                # these from our DPI calculation for the page.
                continue

            yield ImageInfo(name=draw.name, pdfimage=pdfimage, shorthand=draw.shorthand)


def _find_form_xobject_images(pdf: Pdf, container: Object, contentsinfo: ContentsInfo):
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


def _process_content_streams(
    *, pdf: Pdf, container: Object, shorthand=None
) -> Iterator[Union[VectorMarker, TextMarker, ImageInfo]]:
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
        yield VectorMarker()
    if contentsinfo.found_text:
        yield TextMarker()
    yield from _find_inline_images(contentsinfo)
    yield from _find_regular_images(container, contentsinfo)
    yield from _find_form_xobject_images(pdf, container, contentsinfo)


def _page_has_text(text_blocks, page_width, page_height) -> bool:
    """Smarter text detection that ignores text in margins"""

    pw, ph = float(page_width), float(page_height)

    margin_ratio = 0.125
    interior_bbox = (
        margin_ratio * pw,  # left
        (1 - margin_ratio) * ph,  # top
        (1 - margin_ratio) * pw,  # right
        margin_ratio * ph,  # bottom  (first quadrant: bottom < top)
    )

    def rects_intersect(a, b) -> bool:
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


def simplify_textboxes(miner, textbox_getter) -> Iterator[TextboxInfo]:
    """Extract only limited content from text boxes

    We do this to save memory and ensure that our objects are pickleable.
    """
    for box in textbox_getter(miner):
        first_line = box._objs[0]
        first_char = first_line._objs[0]

        visible = first_char.rendermode != 3
        corrupt = first_char.get_text() == '\ufffd'
        yield TextboxInfo(box.bbox, visible, corrupt)


worker_pdf = None


def _pdf_pageinfo_sync_init(pdf: Pdf, infile: Path, pdfminer_loglevel):
    global worker_pdf  # pylint: disable=global-statement
    pikepdf_enable_mmap()

    logging.getLogger('pdfminer').setLevel(pdfminer_loglevel)

    # If the pdf is not opened, open a copy for our worker process to use
    if pdf is None:
        worker_pdf = pikepdf.open(infile)

        def on_process_close():
            worker_pdf.close()

        # Close when this process exits
        atexit.register(on_process_close)


def _pdf_pageinfo_sync(args):
    pageno, thread_pdf, infile, check_pages, detailed_analysis = args
    pdf = thread_pdf if thread_pdf is not None else worker_pdf
    with ExitStack() as stack:
        if not pdf:  # When called with SerialExecutor
            pdf = stack.enter_context(pikepdf.open(infile))
        page = PageInfo(pdf, pageno, infile, check_pages, detailed_analysis)
        return page


def _pdf_pageinfo_concurrent(
    pdf,
    executor: Executor,
    infile,
    progbar,
    max_workers,
    check_pages,
    detailed_analysis=False,
):
    pages = [None] * len(pdf.pages)

    def update_pageinfo(result, pbar):
        page = result
        if not page:
            raise InputFileError("Could read a page in the PDF")
        pages[page.pageno] = page
        pbar.update()

    if max_workers is None:
        max_workers = available_cpu_count()

    total = len(pdf.pages)

    use_threads = False  # No performance gain if threaded due to GIL
    n_workers = min(1 + len(pages) // 4, max_workers)
    if n_workers == 1:
        # But if we decided on only one worker, there is no point in using
        # a separate process.
        use_threads = True

    # If we use a thread, we can pass the already-open Pdf for them to use
    # If we use processes, we pass a None which tells the init function to open its
    # own
    initial_pdf = pdf if use_threads else None

    contexts = (
        (n, initial_pdf, infile, check_pages, detailed_analysis) for n in range(total)
    )
    assert n_workers == 1 if use_threads else n_workers >= 1, "Not multithreadable"
    executor(
        use_threads=use_threads,
        max_workers=n_workers,
        tqdm_kwargs=dict(
            total=total, desc="Scanning contents", unit='page', disable=not progbar
        ),
        worker_initializer=partial(
            _pdf_pageinfo_sync_init,
            initial_pdf,
            infile,
            logging.getLogger('pdfminer').level,
        ),
        task=_pdf_pageinfo_sync,
        task_arguments=contexts,
        task_finished=update_pageinfo,
    )
    return pages


class PageInfo:
    def __init__(
        self,
        pdf: Pdf,
        pageno: int,
        infile: PathLike,
        check_pages: Container[int],
        detailed_analysis: bool = False,
    ):
        self._pageno = pageno
        self._infile = infile
        self._detailed_analysis = detailed_analysis
        self._gather_pageinfo(pdf, pageno, infile, check_pages, detailed_analysis)

    def _gather_pageinfo(
        self,
        pdf: Pdf,
        pageno: int,
        infile: PathLike,
        check_pages: Container[int],
        detailed_analysis: bool,
    ):
        page = pdf.pages[pageno]
        mediabox = [Decimal(d) for d in page.MediaBox.as_list()]
        width_pt = mediabox[2] - mediabox[0]
        height_pt = mediabox[3] - mediabox[1]

        check_this_page = pageno in check_pages

        if check_this_page and detailed_analysis:
            pscript5_mode = str(pdf.docinfo.get('/Creator')).startswith('PScript5')
            miner = get_page_analysis(infile, pageno, pscript5_mode)
            self._textboxes = list(simplify_textboxes(miner, get_text_boxes))
            bboxes = (box.bbox for box in self._textboxes)

            self._has_text = _page_has_text(bboxes, width_pt, height_pt)
        else:
            self._textboxes = []
            self._has_text = None  # i.e. "no information"

        userunit = page.get('/UserUnit', Decimal(1.0))
        if not isinstance(userunit, Decimal):
            userunit = Decimal(userunit)
        self._userunit = userunit
        self._width_inches = width_pt * userunit / Decimal(72.0)
        self._height_inches = height_pt * userunit / Decimal(72.0)

        try:
            self._rotate = int(page['/Rotate'])
        except KeyError:
            self._rotate = 0

        userunit_shorthand = (userunit, 0, 0, userunit, 0, 0)

        if check_this_page:
            self._has_vector = False
            self._has_text = False
            self._images = []
            for ci in _process_content_streams(
                pdf=pdf, container=page, shorthand=userunit_shorthand
            ):
                if isinstance(ci, VectorMarker):
                    self._has_vector = True
                elif isinstance(ci, TextMarker):
                    self._has_text = True
                elif isinstance(ci, ImageInfo):
                    self._images.append(ci)
                else:
                    raise NotImplementedError()
        else:
            self._has_vector = None  # i.e. "no information"
            self._has_text = None
            self._images = None

        self._dpi = None
        if self._images:
            dpi = Resolution(0.0, 0.0).take_max(
                image.dpi for image in self._images if image.renderable
            )
            self._dpi = dpi
            self._width_pixels = int(round(dpi.x * float(self._width_inches)))
            self._height_pixels = int(round(dpi.y * float(self._height_inches)))

    @property
    def pageno(self) -> int:
        return self._pageno

    @property
    def has_text(self) -> bool:
        return self._has_text

    @property
    def has_corrupt_text(self) -> bool:
        if not self._detailed_analysis:
            raise NotImplementedError('Did not do detailed analysis')
        return any(tbox.is_corrupt for tbox in self._textboxes)

    @property
    def has_vector(self) -> bool:
        return self._has_vector

    @property
    def width_inches(self) -> Decimal:
        return self._width_inches

    @property
    def height_inches(self) -> Decimal:
        return self._height_inches

    @property
    def width_pixels(self) -> int:
        return int(round(float(self.width_inches) * self.dpi.x))

    @property
    def height_pixels(self) -> int:
        return int(round(float(self.height_inches) * self.dpi.y))

    @property
    def rotation(self) -> int:
        return self._rotate

    @rotation.setter
    def rotation(self, value):
        if value in (0, 90, 180, 270, 360, -90, -180, -270):
            self._rotate = value
        else:
            raise ValueError("rotation must be a cardinal angle")

    @property
    def images(self):
        return self._images

    def get_textareas(
        self, visible: Optional[bool] = None, corrupt: Optional[bool] = None
    ):
        def predicate(obj, want_visible, want_corrupt):
            result = True
            if want_visible is not None:
                if obj.is_visible != want_visible:
                    result = False
            if want_corrupt is not None:
                if obj.is_corrupt != want_corrupt:
                    result = False
            return result

        if not self._textboxes:
            if visible is not None and corrupt is not None:
                raise NotImplementedError('Incomplete information on textboxes')
            return self._textboxes

        return (obj.bbox for obj in self._textboxes if predicate(obj, visible, corrupt))

    @property
    def dpi(self) -> Resolution:
        if self._dpi is None:
            return Resolution(0.0, 0.0)
        return self._dpi

    @property
    def userunit(self) -> Decimal:
        return self._userunit

    @property
    def min_version(self) -> str:
        if self.userunit is not None:
            return '1.6'
        else:
            return '1.5'

    def __repr__(self):
        return (
            f'<PageInfo '
            f'pageno={self.pageno} {self.width_inches}"x{self.height_inches}" '
            f'rotation={self.rotation} dpi={self.dpi} has_text={self.has_text}>'
        )


class PdfInfo:
    """Get summary information about a PDF"""

    def __init__(
        self,
        infile,
        *,
        detailed_analysis: bool = False,
        progbar: bool = False,
        max_workers: int = None,
        check_pages=None,
        executor: Executor = SerialExecutor(),
    ):
        self._infile = infile
        if check_pages is None:
            check_pages = range(0, 1_000_000_000)

        with pikepdf.open(infile) as pdf:
            if pdf.is_encrypted:
                raise EncryptedPdfError()  # Triggered by encryption with empty passwd
            self._pages = _pdf_pageinfo_concurrent(
                pdf,
                executor,
                infile,
                progbar,
                max_workers,
                check_pages=check_pages,
                detailed_analysis=detailed_analysis,
            )
            self._needs_rendering = pdf.Root.get('/NeedsRendering', False)
            self._has_acroform = False
            if '/AcroForm' in pdf.Root:
                if len(pdf.Root.AcroForm.get('/Fields', [])) > 0:
                    self._has_acroform = True
                elif '/XFA' in pdf.Root.AcroForm:
                    self._has_acroform = True

    @property
    def pages(self):
        return self._pages

    @property
    def min_version(self) -> str:
        # The minimum PDF is the maximum version that any particular page needs
        return max(page.min_version for page in self.pages)

    @property
    def has_userunit(self) -> bool:
        return any(page.userunit != 1.0 for page in self.pages)

    @property
    def has_acroform(self) -> bool:
        return self._has_acroform

    @property
    def filename(self) -> Union[str, Path]:
        if not isinstance(self._infile, (str, Path)):
            raise NotImplementedError("can't get filename from stream")
        return self._infile

    @property
    def needs_rendering(self) -> bool:
        return self._needs_rendering

    def __getitem__(self, item) -> PageInfo:
        return self._pages[item]

    def __len__(self):
        return len(self._pages)

    def __repr__(self):
        return f"<PdfInfo('...'), page count={len(self)}>"


def main():
    import argparse  # pylint: disable=import-outside-toplevel
    from pprint import pprint  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    args = parser.parse_args()
    pdfinfo = PdfInfo(args.infile)

    pprint(pdfinfo)
    for page in pdfinfo.pages:
        pprint(page)
        for im in page.images:
            pprint(im)


if __name__ == '__main__':
    main()
