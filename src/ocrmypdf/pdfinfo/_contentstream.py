# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""PDF content stream interpretation."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping
from math import hypot, inf, isclose
from typing import NamedTuple
from warnings import warn

from pikepdf import (
    Dictionary,
    Matrix,
    Name,
    Object,
    PdfInlineImage,
    parse_content_stream,
)

from ocrmypdf.helpers import Resolution
from ocrmypdf.pdfinfo._types import UNIT_SQUARE, Ink


class XobjectSettings(NamedTuple):
    """Info about an XObject found in a PDF."""

    name: str
    shorthand: tuple[float, float, float, float, float, float]
    stack_depth: int
    fill_ink: Ink
    text_render_mode: int = 0
    glyphless_font: bool = False


class InlineSettings(NamedTuple):
    """Info about an inline image found in a PDF."""

    iimage: PdfInlineImage
    shorthand: tuple[float, float, float, float, float, float]
    stack_depth: int
    fill_ink: Ink


class ContentsInfo(NamedTuple):
    """Info about various objects found in a PDF."""

    xobject_settings: list[XobjectSettings]
    inline_images: list[InlineSettings]
    found_vector: bool
    found_text: bool
    name_index: Mapping[str, list[XobjectSettings]]
    found_visible_text: bool = False


class TextboxInfo(NamedTuple):
    """Info about a text box found in a PDF."""

    bbox: tuple[float, float, float, float]
    is_visible: bool
    is_corrupt: bool


class VectorMarker:
    """Sentinel indicating vector drawing operations were found on a page."""


class TextMarker:
    """Sentinel indicating text drawing operations were found on a page."""


class VisibleTextMarker(TextMarker):
    """Sentinel indicating text that is drawn visibly was found on a page.

    Text is invisible when drawn with text render mode 3 (neither fill nor
    stroke) or 7 (clip only), or with a glyphless font such as those used by
    OCR engines to place an invisible text layer over a scanned image.
    """


def _is_unit_square(shorthand):
    """Check if the shorthand represents a unit square transformation."""
    values = map(float, shorthand)
    pairwise = zip(values, UNIT_SQUARE, strict=False)
    return all(isclose(a, b, rel_tol=1e-3) for a, b in pairwise)


_INK_EPSILON = 1e-3

# Maps a fill-colorspace name (set by the `cs` operator) to a device color
# family we can classify. Names not present here (Separation, ICCBased,
# Indexed, DeviceN, Pattern, resource names like /CS0) are treated as color.
_DEVICE_FILL_SPACE = {
    '/DeviceGray': 'gray',
    '/CalGray': 'gray',
    '/G': 'gray',
    '/DeviceRGB': 'rgb',
    '/CalRGB': 'rgb',
    '/RGB': 'rgb',
    '/DeviceCMYK': 'cmyk',
    '/CMYK': 'cmyk',
}


def _ink_from_components(space: str, comps: list[float]) -> Ink:
    """Classify a device-color fill into mono/gray/color.

    ``space`` is one of 'gray', 'rgb', 'cmyk'. Any other value is treated
    conservatively as color, since we cannot prove it is achromatic.
    """
    eps = _INK_EPSILON
    if space == 'gray' and len(comps) == 1:
        return Ink.mono if comps[0] <= eps else Ink.gray
    if space == 'rgb' and len(comps) == 3:
        r, g, b = comps
        if max(r, g, b) <= eps:
            return Ink.mono
        if abs(r - g) <= eps and abs(g - b) <= eps:
            return Ink.gray
        return Ink.color
    if space == 'cmyk' and len(comps) == 4:
        c, m, y, k = comps
        if c <= eps and m <= eps and y <= eps:
            return Ink.mono if k <= eps else Ink.gray
        return Ink.color
    return Ink.color  # conservative-to-color


def _operand_floats(operands) -> list[float] | None:
    """Convert color operands to floats, or None if any is non-numeric.

    Color operators in a malformed content stream may carry the wrong number
    of operands or a non-numeric operand (e.g. a Name). Returning None lets
    the caller keep the prior fill state instead of raising.
    """
    try:
        return [float(o) for o in operands]
    except (TypeError, ValueError):
        return None


_INVISIBLE_TEXT_RENDER_MODES = frozenset({3, 7})

# Fonts with no visible glyphs, used by OCR engines (including Tesseract and
# OCRmyPDF itself) to draw an invisible text layer
_GLYPHLESS_FONT_NAMES = frozenset({'glyphlessfont', 'occulta', 'occulta-regular'})

_SUBSET_PREFIX = re.compile(r'^[A-Z]{6}\+')


def _is_glyphless_font(font: Object | None) -> bool:
    """Check if a font dictionary is a known glyphless font, by its name."""
    if not isinstance(font, Dictionary):
        return False
    basefont = font.get(Name.BaseFont)
    if not isinstance(basefont, Name):
        return False
    # PDF names are byte sequences in no particular encoding, so str() may
    # raise on non-UTF-8 names; unparse() gives the escaped PDF syntax form.
    name = basefont.unparse().decode('ascii', 'replace').removeprefix('/')
    name = _SUBSET_PREFIX.sub('', name, count=1)
    return name.lower() in _GLYPHLESS_FONT_NAMES


def _font_resources(container: Object) -> Dictionary | None:
    """Get the /Font resource dictionary of a page or Form XObject.

    A page may inherit its resources from its ancestors in the page tree.
    """
    node = container
    for _ in range(64):  # Guard against cycles in the page tree
        try:
            resources = node.get(Name.Resources)
        except (AttributeError, TypeError, ValueError):
            return None
        if isinstance(resources, Dictionary):
            fonts = resources.get(Name.Font)
            return fonts if isinstance(fonts, Dictionary) else None
        if node.get(Name.Type) != Name.Page and node.get(Name.Type) != Name.Pages:
            return None
        parent = node.get(Name.Parent)
        if not isinstance(parent, Dictionary):
            return None
        node = parent
    return None


def _text_render_mode(operands) -> int | None:
    """Get the text render mode from the operands of Tr, or None if invalid."""
    if len(operands) != 1:
        return None
    try:
        mode = float(operands[0])
    except (TypeError, ValueError):
        return None
    if not mode.is_integer() or not 0 <= mode <= 7:
        return None
    return int(mode)


def _normalize_stack(graphobjs):
    """Convert runs of qQ's in the stack into single graphobjs."""
    for operands, operator in graphobjs:
        operator = str(operator)
        if re.match(r'Q*q+$', operator):  # Zero or more Q, one or more q
            for char in operator:  # Split into individual
                yield ([], char)  # Yield individual
        else:
            yield (operands, operator)


def _interpret_contents(
    contentstream: Object,
    initial_shorthand=UNIT_SQUARE,
    initial_fill_ink=Ink.mono,
    initial_text_render_mode: int = 0,
    initial_glyphless_font: bool = False,
):
    """Interpret the PDF content stream.

    The stack represents the state of the PDF graphics stack.  We track the
    current transformation matrix (CTM) and the current fill color (so that
    image masks, which are painted with the fill color, can be classified)
    and enough of the text state to decide whether text is visible (the text
    render mode, and whether the current font is a known glyphless font);
    a full implementation would need to track many other items.

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
    graphics state unchanged.
    """
    stack = []
    ctm = Matrix(initial_shorthand)
    fill_ink = initial_fill_ink  # PDF default fill color is black
    fill_space = '/DeviceGray'  # current fill colorspace name (for sc/scn)
    text_render_mode = initial_text_render_mode
    glyphless_font = initial_glyphless_font
    font_resources = _font_resources(contentstream)
    glyphless_cache: dict[str, bool] = {}
    xobject_settings: list[XobjectSettings] = []
    inline_images: list[InlineSettings] = []
    name_index = defaultdict(lambda: [])
    found_vector = False
    found_text = False
    found_visible_text = False
    vector_ops = set(['S', 's', 'f', 'F', 'f*', 'B', 'B*', 'b', 'b*'])
    text_showing_ops = set(["TJ", "Tj", '"', "'"])
    image_ops = set(['BI', 'ID', 'EI', 'q', 'Q', 'Do', 'cm'])
    color_ops = set(['g', 'rg', 'k', 'cs', 'sc', 'scn'])
    text_state_ops = set(['Tr', 'Tf'])
    operator_whitelist = ' '.join(
        vector_ops | text_showing_ops | image_ops | color_ops | text_state_ops
    )

    for n, graphobj in enumerate(
        _normalize_stack(parse_content_stream(contentstream, operator_whitelist))
    ):
        operands, operator = graphobj
        if operator == 'q':
            stack.append((ctm, fill_ink, fill_space, text_render_mode, glyphless_font))
            if len(stack) > 32:  # See docstring
                if len(stack) > 128:
                    raise RuntimeError(
                        f"PDF graphics stack overflowed hard limit at operator {n}"
                    )
                warn("PDF graphics stack overflowed spec limit")
        elif operator == 'Q':
            try:
                (
                    ctm,
                    fill_ink,
                    fill_space,
                    text_render_mode,
                    glyphless_font,
                ) = stack.pop()
            except IndexError:
                # Keeping the state the same seems to be the only sensible thing
                # to do. Just pretend nothing happened, keep calm and carry on.
                warn("PDF graphics stack underflowed - PDF may be malformed")
        elif operator == 'cm':
            try:
                ctm = Matrix(operands) @ ctm
            except (ValueError, TypeError):
                # A 'cm' with the wrong number of operands (ValueError) or a
                # non-numeric one (TypeError) means the content stream is
                # malformed - typically a producer emitted a broken real number
                # such as '0.000-50131235', which the parser reads as an
                # operator that swallows the operands that precede it.
                # Viewers tolerate this, so ignore the operator and carry on
                # with the transformation matrix we have.
                warn("PDF content stream has a malformed 'cm' - PDF may be malformed")
        elif operator == 'g':
            if vals := _operand_floats(operands):
                fill_ink = _ink_from_components('gray', vals)
                fill_space = '/DeviceGray'
        elif operator == 'rg':
            if vals := _operand_floats(operands):
                fill_ink = _ink_from_components('rgb', vals)
                fill_space = '/DeviceRGB'
        elif operator == 'k':
            if vals := _operand_floats(operands):
                fill_ink = _ink_from_components('cmyk', vals)
                fill_space = '/DeviceCMYK'
        elif operator == 'cs':
            # Selecting a colorspace resets the fill color to that space's
            # initial value, which is black for all device colorspaces.
            fill_ink = Ink.mono
            if operands:
                fill_space = str(operands[0])
        elif operator in ('sc', 'scn'):
            if any(isinstance(o, Name) for o in operands):
                fill_ink = Ink.color  # pattern fill
            else:
                space = _DEVICE_FILL_SPACE.get(fill_space)
                vals = _operand_floats(operands)
                if space is None or vals is None:
                    fill_ink = Ink.color  # conservative for non-device space
                else:
                    fill_ink = _ink_from_components(space, vals)
        elif operator == 'Do':
            if not operands:
                warn("PDF content stream has a malformed 'Do' - PDF may be malformed")
                continue
            image_name = operands[0]
            settings = XobjectSettings(
                name=image_name,
                shorthand=ctm.shorthand,
                stack_depth=len(stack),
                fill_ink=fill_ink,
                text_render_mode=text_render_mode,
                glyphless_font=glyphless_font,
            )
            xobject_settings.append(settings)
            name_index[str(image_name)].append(settings)
        elif operator == 'INLINE IMAGE':  # BI/ID/EI are grouped into this
            iimage = operands[0]
            inline = InlineSettings(
                iimage=iimage,
                shorthand=ctm.shorthand,
                stack_depth=len(stack),
                fill_ink=fill_ink,
            )
            inline_images.append(inline)
        elif operator in vector_ops:
            found_vector = True
        elif operator == 'Tr':
            if (mode := _text_render_mode(operands)) is not None:
                text_render_mode = mode
        elif operator == 'Tf':
            if operands and isinstance(operands[0], Name):
                font_key = operands[0].unparse().decode('ascii', 'replace')
                if font_key not in glyphless_cache:
                    font = (
                        font_resources.get(operands[0])
                        if font_resources is not None
                        else None
                    )
                    glyphless_cache[font_key] = _is_glyphless_font(font)
                glyphless_font = glyphless_cache[font_key]
        elif operator in text_showing_ops:
            found_text = True
            if (
                text_render_mode not in _INVISIBLE_TEXT_RENDER_MODES
                and not glyphless_font
            ):
                found_visible_text = True

    return ContentsInfo(
        xobject_settings=xobject_settings,
        inline_images=inline_images,
        found_vector=found_vector,
        found_text=found_text,
        name_index=name_index,
        found_visible_text=found_visible_text,
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
    a, b, c, d, _, _ = ctm_shorthand  # pylint: disable=invalid-name

    # Calculate the width and height of the image in PDF units
    image_drawn = hypot(a, b), hypot(c, d)

    def calc(drawn, pixels, inches_per_pt=72.0):
        # The scale of the image is pixels per unit of default user space (1/72")
        scale = pixels / drawn if drawn != 0 else inf
        dpi = scale * inches_per_pt
        return dpi

    dpi_w, dpi_h = (calc(image_drawn[n], image_size[n]) for n in range(2))
    return Resolution(dpi_w, dpi_h)
