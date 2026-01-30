# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""PDF image analysis."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from decimal import Decimal

from pikepdf import (
    Dictionary,
    Matrix,
    Name,
    Object,
    Pdf,
    PdfImage,
    PdfInlineImage,
    Stream,
    UnsupportedImageTypeError,
)

from ocrmypdf.helpers import Resolution
from ocrmypdf.pdfinfo._contentstream import (
    ContentsInfo,
    TextMarker,
    VectorMarker,
    _get_dpi,
    _interpret_contents,
    _is_unit_square,
)
from ocrmypdf.pdfinfo._types import (
    FRIENDLY_COLORSPACE,
    FRIENDLY_COMP,
    FRIENDLY_ENCODING,
    UNIT_SQUARE,
    Colorspace,
    Encoding,
)

logger = logging.getLogger()


class ImageInfo:
    """Information about an image found in a PDF.

    This gathers information from pikepdf and pdfminer.six, and is pickle-able
    so that it can be passed to a worker process, unlike objects from those
    libraries.
    """

    DPI_PREC = Decimal('1.000')

    _comp: int | None
    _name: str

    def __init__(
        self,
        *,
        name='',
        pdfimage: Object | None = None,
        inline: PdfInlineImage | None = None,
        shorthand=None,
    ):
        """Initialize an ImageInfo."""
        self._name = str(name)
        self._shorthand = shorthand

        pim: PdfInlineImage | PdfImage

        if inline is not None:
            self._origin = 'inline'
            pim = inline
        elif pdfimage is not None and isinstance(pdfimage, Stream):
            self._origin = 'xobject'
            pim = PdfImage(pdfimage)
        else:
            raise ValueError("Either pdfimage or inline must be set")

        self._width = pim.width
        self._height = pim.height
        if (smask := pim.obj.get(Name.SMask, None)) is not None and isinstance(
            smask, Stream | Dictionary
        ):
            # SMask is pretty much an alpha channel, but in PDF it's possible
            # for channel to have different dimensions than the image
            # itself. Some PDF writers use this to create a grayscale stencil
            # mask. For our purposes, the effective size is the size of the
            # larger component (image or smask).
            self._width = max(smask.get(Name.Width, 0), self._width)
            self._height = max(smask.get(Name.Height, 0), self._height)
        if (mask := pim.obj.get(Name.Mask, None)) is not None and isinstance(
            mask, Stream | Dictionary
        ):
            # If the image has a /Mask entry, it has an explicit mask.
            # /Mask can be a Stream or an Array. If it's a Stream,
            # use its /Width and /Height if they are larger than the main
            # image's.
            self._width = max(mask.get(Name.Width, 0), self._width)
            self._height = max(mask.get(Name.Height, 0), self._height)

        # If /ImageMask is true, then this image is a stencil mask
        # (Images that draw with this stencil mask will have a reference to
        # it in their /Mask, but we don't actually need that information)
        if pim.image_mask:
            self._type = 'stencil'
        else:
            self._type = 'image'

        self._bpc = int(pim.bits_per_component)
        if (
            len(pim.filters) == 2
            and pim.filters[0] == '/FlateDecode'
            and pim.filters[1] == '/DCTDecode'
        ):
            # Special case: FlateDecode followed by DCTDecode
            self._enc = Encoding.flate_jpeg
        else:
            try:
                self._enc = FRIENDLY_ENCODING.get(pim.filters[0])
            except IndexError:
                self._enc = None

        try:
            self._color = FRIENDLY_COLORSPACE.get(pim.colorspace or '')
        except NotImplementedError:
            self._color = None
        if self._enc == Encoding.jpeg2000:
            self._color = Colorspace.jpeg2000

        self._comp = None
        if self._color == Colorspace.icc and isinstance(pim, PdfImage):
            self._comp = self._init_icc(pim)
        else:
            if isinstance(self._color, Colorspace):
                self._comp = FRIENDLY_COMP.get(self._color)
            # Bit of a hack... infer grayscale if component count is uncertain
            # but encoding only supports monochrome.
            if self._comp is None and self._enc in (Encoding.ccitt, Encoding.jbig2):
                self._comp = FRIENDLY_COMP[Colorspace.gray]

    def _init_icc(self, pim: PdfImage):
        try:
            icc = pim.icc
        except UnsupportedImageTypeError as e:
            logger.warning(
                f"An image with a corrupt or unreadable ICC profile was found. "
                f"Output PDF may not match the input PDF visually: {e}. {self}"
            )
            return None
        # Check the ICC profile to determine actual colorspace
        if icc is None or not hasattr(icc, 'profile'):
            logger.warning(
                f"An image with an ICC profile but no ICC profile data was found. "
                f"The output PDF may not match the input PDF visually. {self}"
            )
            return None
        try:
            if icc.profile.xcolor_space == 'GRAY':
                return 1
            elif icc.profile.xcolor_space == 'CMYK':
                return 4
            else:
                return 3
        except AttributeError:
            return None

    @property
    def name(self):
        """Name of the image as it appears in the PDF."""
        return self._name

    @property
    def type_(self):
        """Type of image, either 'image' or 'stencil'."""
        return self._type

    @property
    def width(self) -> int:
        """Width of the image in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Height of the image in pixels."""
        return self._height

    @property
    def bpc(self):
        """Bits per component."""
        return self._bpc

    @property
    def color(self):
        """Colorspace of the image."""
        return self._color if self._color is not None else '?'

    @property
    def comp(self):
        """Number of components/channels in the image."""
        return self._comp if self._comp is not None else '?'

    @property
    def enc(self):
        """Encoding of the image."""
        return self._enc if self._enc is not None else 'image'

    @property
    def renderable(self) -> bool:
        """Whether the image is renderable.

        Some PDFs in the wild have invalid images that are not renderable,
        due to unusual dimensions.

        Stencil masks are not also not renderable, since they are not
        drawn, but rather they control how rendering happens.
        """
        return (
            self.dpi.is_finite
            and self.width >= 0
            and self.height >= 0
            and self.type_ != 'stencil'
        )

    @property
    def dpi(self) -> Resolution:
        """Dots per inch of the image.

        Calculated based on where and how the image is drawn in the PDF.
        """
        return _get_dpi(self._shorthand, (self._width, self._height))

    @property
    def printed_area(self) -> float:
        """Physical area of the image in square inches."""
        if not self.renderable:
            return 0.0
        return float((self.width / self.dpi.x) * (self.height / self.dpi.y))

    def __repr__(self):
        """Return a string representation of the image."""
        return (
            f"<ImageInfo '{self.name}' {self.type_} {self.width}×{self.height} "
            f"{self.color} {self.comp} {self.bpc} {self.enc} {self.dpi}>"
        )


def _find_inline_images(contentsinfo: ContentsInfo) -> Iterator[ImageInfo]:
    """Find inline images in the contentstream."""
    for n, inline in enumerate(contentsinfo.inline_images):
        yield ImageInfo(
            name=f'inline-{n:02d}', shorthand=inline.shorthand, inline=inline.iimage
        )


def _image_xobjects(container) -> Iterator[tuple[Object, str]]:
    """Search for all XObject-based images in the container.

    Usually the container is a page, but it could also be a Form XObject
    that contains images. Filter out the Form XObjects which are dealt with
    elsewhere.

    Generate a sequence of tuples (image, xobj container), where container,
    where xobj is the name of the object and image is the object itself,
    since the object does not know its own name.

    """
    if Name.Resources not in container:
        return
    resources = container[Name.Resources]
    if Name.XObject not in resources:
        return
    for key, candidate in resources[Name.XObject].items():
        if candidate is None or Name.Subtype not in candidate:
            continue
        if candidate[Name.Subtype] == Name.Image:
            pdfimage = candidate
            yield (pdfimage, key)


def _find_regular_images(
    container: Object, contentsinfo: ContentsInfo
) -> Iterator[ImageInfo]:
    """Find images stored in the container's /Resources /XObject.

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
    """Find any images that are in Form XObjects in the container.

    The container may be a page, or a parent Form XObject.

    """
    if Name.Resources not in container:
        return
    resources = container[Name.Resources]
    if Name.XObject not in resources:
        return
    xobjs = resources[Name.XObject].as_dict()
    for xobj in xobjs:
        candidate = xobjs[xobj]
        if candidate is None or candidate.get(Name.Subtype) != Name.Form:
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
) -> Iterator[VectorMarker | TextMarker | ImageInfo]:
    """Find all individual instances of images drawn in the container.

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
    if container.get(Name.Type) == Name.Page and Name.Contents in container:
        initial_shorthand = shorthand or UNIT_SQUARE
    elif (
        container.get(Name.Type) == Name.XObject
        and container[Name.Subtype] == Name.Form
    ):
        # Set the CTM to the state it was when the "Do" operator was
        # encountered that is drawing this instance of the Form XObject
        ctm = Matrix(shorthand) if shorthand else Matrix()

        # A Form XObject may provide its own matrix to map form space into
        # user space. Get this if one exists
        form_shorthand = container.get(Name.Matrix, Matrix())
        form_matrix = Matrix(form_shorthand)

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
