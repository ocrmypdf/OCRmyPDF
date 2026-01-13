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

from pikepdf import Matrix, Object, PdfInlineImage, parse_content_stream

from ocrmypdf.exceptions import InputFileError
from ocrmypdf.helpers import Resolution
from ocrmypdf.pdfinfo._types import UNIT_SQUARE


class XobjectSettings(NamedTuple):
    """Info about an XObject found in a PDF."""

    name: str
    shorthand: tuple[float, float, float, float, float, float]
    stack_depth: int


class InlineSettings(NamedTuple):
    """Info about an inline image found in a PDF."""

    iimage: PdfInlineImage
    shorthand: tuple[float, float, float, float, float, float]
    stack_depth: int


class ContentsInfo(NamedTuple):
    """Info about various objects found in a PDF."""

    xobject_settings: list[XobjectSettings]
    inline_images: list[InlineSettings]
    found_vector: bool
    found_text: bool
    name_index: Mapping[str, list[XobjectSettings]]


class TextboxInfo(NamedTuple):
    """Info about a text box found in a PDF."""

    bbox: tuple[float, float, float, float]
    is_visible: bool
    is_corrupt: bool


class VectorMarker:
    """Sentinel indicating vector drawing operations were found on a page."""


class TextMarker:
    """Sentinel indicating text drawing operations were found on a page."""


def _is_unit_square(shorthand):
    """Check if the shorthand represents a unit square transformation."""
    values = map(float, shorthand)
    pairwise = zip(values, UNIT_SQUARE, strict=False)
    return all(isclose(a, b, rel_tol=1e-3) for a, b in pairwise)


def _normalize_stack(graphobjs):
    """Convert runs of qQ's in the stack into single graphobjs."""
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
    ctm = Matrix(initial_shorthand)
    xobject_settings: list[XobjectSettings] = []
    inline_images: list[InlineSettings] = []
    name_index = defaultdict(lambda: [])
    found_vector = False
    found_text = False
    vector_ops = set('S s f F f* B B* b b*'.split())
    text_showing_ops = set("""TJ Tj " '""".split())
    image_ops = set('BI ID EI q Q Do cm'.split())
    operator_whitelist = ' '.join(vector_ops | text_showing_ops | image_ops)

    for n, graphobj in enumerate(
        _normalize_stack(parse_content_stream(contentstream, operator_whitelist))
    ):
        operands, operator = graphobj
        if operator == 'q':
            stack.append(ctm)
            if len(stack) > 32:  # See docstring
                if len(stack) > 128:
                    raise RuntimeError(
                        f"PDF graphics stack overflowed hard limit at operator {n}"
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
            try:
                ctm = Matrix(operands) @ ctm
            except ValueError as e:
                raise InputFileError(
                    "PDF content stream is corrupt - this PDF is malformed. "
                    "Use a PDF editor that is capable of visually inspecting the PDF."
                ) from e
        elif operator == 'Do':
            image_name = operands[0]
            settings = XobjectSettings(
                name=image_name, shorthand=ctm.shorthand, stack_depth=len(stack)
            )
            xobject_settings.append(settings)
            name_index[str(image_name)].append(settings)
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
