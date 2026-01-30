# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCR element dataclasses for representing OCR output structure.

This module provides a generic, engine-agnostic representation of OCR output.
The OcrElement dataclass can represent structural units from any OCR source
(hOCR, ALTO, custom engines, etc.) in a unified format suitable for rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class BoundingBox:
    """An axis-aligned bounding box in pixel coordinates.

    Coordinates use top-left origin (standard for images and hOCR).

    Attributes:
        left: Left edge x-coordinate
        top: Top edge y-coordinate
        right: Right edge x-coordinate
        bottom: Bottom edge y-coordinate
    """

    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.right - self.left

    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.bottom - self.top

    def __post_init__(self):
        """Validate bounding box coordinates."""
        if self.right < self.left:
            raise ValueError(
                f"Invalid bounding box: right ({self.right}) < left ({self.left})"
            )
        if self.bottom < self.top:
            raise ValueError(
                f"Invalid bounding box: bottom ({self.bottom}) < top ({self.top})"
            )


@dataclass
class Baseline:
    """Text baseline information.

    The baseline is represented as a linear equation: y = slope * x + intercept.
    This describes the line along which text characters sit, relative to the
    bottom-left corner of the line's bounding box.

    In hOCR, the baseline is specified relative to the bottom of the line's bbox,
    with the intercept being the vertical offset from the bottom and the slope
    representing rotation (positive = ascending left-to-right).

    Attributes:
        slope: Slope of the baseline (rise over run)
        intercept: Y-intercept of the baseline (vertical offset from bbox bottom)
    """

    slope: float = 0.0
    intercept: float = 0.0


@dataclass
class FontInfo:
    """Font information for text rendering.

    Attributes:
        name: Font family name (e.g., "Times New Roman")
        size: Font size in points
        bold: Whether the font is bold
        italic: Whether the font is italic
        monospace: Whether the font is monospace
        serif: Whether the font is serif (vs sans-serif)
        smallcaps: Whether the font uses small caps
        underline: Whether the text is underlined
    """

    name: str | None = None
    size: float | None = None
    bold: bool = False
    italic: bool = False
    monospace: bool = False
    serif: bool = False
    smallcaps: bool = False
    underline: bool = False


@dataclass
class OcrElement:
    """A generic OCR element representing any structural unit of OCR output.

    OcrElements form a tree structure where pages contain paragraphs, paragraphs
    contain lines, lines contain words, etc. The specific hierarchy depends on
    the OCR engine, but this dataclass can represent any of these levels.

    The ocr_class field uses hOCR naming conventions (ocr_page, ocr_par, ocr_line,
    ocrx_word, etc.) as a common vocabulary, but elements from other sources can
    map to these classes.

    Common hOCR classes:
        - ocr_page: The root element for a page
        - ocr_carea: A content/column area
        - ocr_par: A paragraph
        - ocr_line: A line of text
        - ocr_header: A header line
        - ocr_footer: A footer line
        - ocr_caption: A caption line
        - ocr_textfloat: A floating text element
        - ocrx_word: A single word

    Attributes:
        ocr_class: The element type (e.g., "ocr_page", "ocr_line", "ocrx_word")
        bbox: Axis-aligned bounding box in source pixel coordinates (top-left origin)
        poly: Polygon vertices for oriented/non-rectangular bounds
        text: Text content (primarily for leaf nodes like words)
        confidence: OCR confidence score (0.0-1.0)
        children: Child elements (hierarchical structure)
        direction: Text direction ("ltr" or "rtl")
        language: Language code (e.g., "eng", "deu", "chi_sim")
        baseline: Text baseline information (slope and intercept)
        textangle: Text rotation angle in degrees (counter-clockwise from horizontal)
        font: Font information (name, size, style)
        dpi: Image resolution in dots per inch (typically for page-level)
        page_number: Physical page number (0-indexed)
        logical_page_number: Logical page number (as printed on the page)
    """

    ocr_class: str

    # Bounding boxes
    bbox: BoundingBox | None = None
    poly: list[tuple[float, float]] | None = None

    # Text content
    text: str = ""

    # Confidence (0.0-1.0)
    confidence: float | None = None

    # Children (hierarchical structure)
    children: list[OcrElement] = field(default_factory=list)

    # Text direction and language
    direction: Literal["ltr", "rtl"] | None = None
    language: str | None = None

    # Baseline (for lines)
    baseline: Baseline | None = None

    # Rotation angle in degrees (counter-clockwise)
    textangle: float | None = None

    # Font information
    font: FontInfo | None = None

    # Page-level properties
    dpi: float | None = None
    page_number: int | None = None
    logical_page_number: int | None = None

    def iter_by_class(self, *ocr_classes: str) -> list[OcrElement]:
        """Iterate over all descendants matching the given class(es).

        Args:
            *ocr_classes: One or more ocr_class values to match

        Returns:
            List of all matching descendant elements (depth-first order)
        """
        result = []
        if self.ocr_class in ocr_classes:
            result.append(self)
        for child in self.children:
            result.extend(child.iter_by_class(*ocr_classes))
        return result

    def find_by_class(self, *ocr_classes: str) -> OcrElement | None:
        """Find the first descendant matching the given class(es).

        Args:
            *ocr_classes: One or more ocr_class values to match

        Returns:
            The first matching element, or None if not found
        """
        if self.ocr_class in ocr_classes:
            return self
        for child in self.children:
            result = child.find_by_class(*ocr_classes)
            if result is not None:
                return result
        return None

    def get_text_recursive(self) -> str:
        """Get the combined text of this element and all descendants.

        Returns:
            Combined text content, with words separated by spaces
        """
        if self.text:
            return self.text
        texts = [child.get_text_recursive() for child in self.children]
        return " ".join(t for t in texts if t)

    @property
    def words(self) -> list[OcrElement]:
        """Get all word elements (ocrx_word) in this element's subtree."""
        return self.iter_by_class("ocrx_word")

    @property
    def lines(self) -> list[OcrElement]:
        """Get all line elements in this element's subtree."""
        return self.iter_by_class(
            "ocr_line", "ocr_header", "ocr_footer", "ocr_caption", "ocr_textfloat"
        )

    @property
    def paragraphs(self) -> list[OcrElement]:
        """Get all paragraph elements (ocr_par) in this element's subtree."""
        return self.iter_by_class("ocr_par")


# Type alias for text direction
TextDirection = Literal["ltr", "rtl"]


# hOCR class constants for convenience
class OcrClass:
    """Constants for common OCR element classes."""

    # Page-level
    PAGE = "ocr_page"
    CAREA = "ocr_carea"

    # Block-level
    PARAGRAPH = "ocr_par"

    # Line-level
    LINE = "ocr_line"
    HEADER = "ocr_header"
    FOOTER = "ocr_footer"
    CAPTION = "ocr_caption"
    TEXTFLOAT = "ocr_textfloat"

    # Word-level
    WORD = "ocrx_word"

    # Character-level
    CHAR = "ocrx_cinfo"

    # Line types (for convenience)
    LINE_TYPES = frozenset({LINE, HEADER, FOOTER, CAPTION, TEXTFLOAT})
