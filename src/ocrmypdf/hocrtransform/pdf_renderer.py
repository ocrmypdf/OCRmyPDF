# SPDX-FileCopyrightText: 2010 Jonathan Brinley
# SPDX-FileCopyrightText: 2013-2014 Julien Pfefferkorn
# SPDX-FileCopyrightText: 2023-2025 James R. Barlow
# SPDX-FileCopyrightText: 2025 Odin Dahlstr\u00f6m
# SPDX-License-Identifier: MIT

"""PDF text renderer for OcrElement structures.

This module provides functionality to render OcrElement trees to PDF files,
creating text layers that can be overlaid on scanned document images.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from itertools import pairwise
from math import atan, pi
from pathlib import Path

from pikepdf import Matrix, Name, Rectangle
from pikepdf.canvas import (
    BLACK,
    BLUE,
    CYAN,
    DARKGREEN,
    GREEN,
    MAGENTA,
    RED,
    Canvas,
    Text,
    TextDirection,
)

from ocrmypdf.hocrtransform._font import EncodableFont as Font
from ocrmypdf.hocrtransform._font import GlyphlessFont
from ocrmypdf.hocrtransform.ocr_element import OcrClass, OcrElement

log = logging.getLogger(__name__)

INCH = 72.0

# CJK languages where word breaks should not be injected
CJK_LANGUAGES = frozenset({'chi_sim', 'chi_tra', 'jpn', 'kor'})


@dataclass
class DebugRenderOptions:
    """Options for debug visualization during rendering.

    When enabled, these options draw colored boxes and lines to visualize
    the OCR structure, which is helpful for debugging layout issues.

    Attributes:
        render_paragraph_bbox: Draw boxes around paragraphs (cyan)
        render_baseline: Draw text baselines (magenta)
        render_triangle: Draw direction triangles at word positions (red)
        render_line_bbox: Draw boxes around lines (blue)
        render_word_bbox: Draw boxes around words (green)
        render_space_bbox: Draw boxes for inter-word spaces (dark green)
    """

    render_paragraph_bbox: bool = False
    render_baseline: bool = False
    render_triangle: bool = False
    render_line_bbox: bool = False
    render_word_bbox: bool = False
    render_space_bbox: bool = False


class PdfTextRenderer:
    """Renders OcrElement trees to PDF text layers.

    This class takes an OcrElement tree (typically parsed from hOCR or
    another OCR format) and renders it to a PDF file. The text is positioned
    according to the bounding boxes in the OcrElement structure, allowing
    it to be overlaid on scanned document images.

    The renderer supports:
        - Invisible text mode for selectable but hidden text
        - Text direction (LTR and RTL)
        - Baseline-aware positioning
        - Text rotation (textangle)
        - Word break injection for better PDF viewer segmentation
        - Debug visualization options
    """

    def __init__(
        self,
        *,
        page: OcrElement,
        dpi: float,
        fontname: Name = Name("/f-0-0"),
        font: Font | None = None,
        debug_render_options: DebugRenderOptions | None = None,
    ):
        """Initialize the PDF text renderer.

        Args:
            page: The root OcrElement (should be ocr_page)
            dpi: Resolution of the source image in dots per inch
            fontname: PDF font name to use
            font: Font implementation for encoding and metrics
            debug_render_options: Options for debug visualization
        """
        if page.ocr_class != OcrClass.PAGE:
            raise ValueError(f"Expected ocr_page element, got {page.ocr_class}")

        if page.bbox is None:
            raise ValueError("Page element must have a bounding box")

        self.page = page
        self.dpi = dpi
        self._fontname = fontname
        self._font = font or GlyphlessFont()
        self.render_options = debug_render_options or DebugRenderOptions()

        # Calculate page size in PDF points (1/72 inch)
        self.width = page.bbox.width / (self.dpi / INCH)
        self.height = page.bbox.height / (self.dpi / INCH)

    def render(
        self,
        *,
        out_filename: Path,
        image_filename: Path | None = None,
        invisible_text: bool = True,
    ) -> None:
        """Render the OCR elements to a PDF file.

        Creates a PDF file with text positioned according to the OcrElement
        bounding boxes. Optionally overlays an image on top of the text.

        Args:
            out_filename: Path to write the PDF file
            image_filename: Optional image to composite on top of text
            invisible_text: If True, text is selectable but not visible.
                If False, text is visible (useful for debugging).
        """
        canvas = Canvas(page_size=(self.width, self.height))
        canvas.add_font(self._fontname, self._font)

        # Transform from hOCR pixel coordinates (top-left origin) to
        # PDF coordinates (bottom-left origin)
        page_matrix = (
            Matrix()
            .translated(0, self.height)
            .scaled(1, -1)
            .scaled(INCH / self.dpi, INCH / self.dpi)
        )

        log.debug("Page matrix: %s", page_matrix)

        with canvas.do.save_state(cm=page_matrix):
            self._render_debug_paragraph_boxes(canvas)
            self._render_page_content(canvas, invisible_text)

        # Overlay image if provided
        if image_filename is not None:
            canvas.do.draw_image(
                image_filename, 0, 0, width=self.width, height=self.height
            )

        canvas.to_pdf().save(out_filename)

    def _render_page_content(self, canvas: Canvas, invisible_text: bool) -> None:
        """Render all text content from the page.

        Args:
            canvas: The PDF canvas to render to
            invisible_text: Whether text should be invisible
        """
        found_lines = False

        # Iterate through paragraphs and their lines
        for paragraph in self.page.paragraphs:
            direction = self._get_text_direction(paragraph)
            inject_word_breaks = self._should_inject_word_breaks(paragraph)

            for line in paragraph.lines:
                found_lines = True
                self._render_line(
                    canvas,
                    line,
                    invisible_text,
                    direction,
                    inject_word_breaks,
                )

        # Fallback: if no lines found in paragraphs, check for lines/words
        # directly under page (some OCR output structures)
        if not found_lines:
            direction = self._get_text_direction(self.page)
            inject_word_breaks = True

            # Try to find lines directly under page
            for line in self.page.lines:
                found_lines = True
                self._render_line(
                    canvas,
                    line,
                    invisible_text,
                    direction,
                    inject_word_breaks,
                )

            # If still no lines, render words directly
            if not found_lines:
                for word in self.page.words:
                    self._render_standalone_word(canvas, word, invisible_text)

    def _get_text_direction(self, element: OcrElement) -> TextDirection:
        """Get the text direction for an element.

        Args:
            element: OcrElement to check

        Returns:
            TextDirection.LTR or TextDirection.RTL
        """
        if element.direction == "rtl":
            return TextDirection.RTL
        return TextDirection.LTR

    def _should_inject_word_breaks(self, element: OcrElement) -> bool:
        """Determine whether word breaks should be injected.

        Word breaks are not injected for CJK languages where words are
        typically one or two characters and separators are explicit.

        Args:
            element: OcrElement to check (typically a paragraph)

        Returns:
            True if word breaks should be injected
        """
        language = element.language or ''
        return language not in CJK_LANGUAGES

    def _render_line(
        self,
        canvas: Canvas,
        line: OcrElement,
        invisible_text: bool,
        text_direction: TextDirection,
        inject_word_breaks: bool,
    ) -> None:
        """Render a line of text.

        Args:
            canvas: The PDF canvas (with page coordinate transform active)
            line: The line element to render
            invisible_text: Whether text should be invisible
            text_direction: LTR or RTL text direction
            inject_word_breaks: Whether to add spaces between words
        """
        if line.bbox is None:
            return

        # Validate line bbox
        if line.bbox.height <= 0:
            log.error(
                "line box is invalid so we cannot render it: box=%s text=%s",
                line.bbox,
                line.get_text_recursive(),
            )
            return

        # Convert BoundingBox to Rectangle for pikepdf operations
        line_min_aabb = Rectangle(
            line.bbox.left,
            line.bbox.top,
            line.bbox.right,
            line.bbox.bottom,
        )

        self._render_debug_line_bbox(canvas, line_min_aabb)

        # Calculate the line's oriented bounding box transform
        # The bbox from hOCR is the minimum AABB enclosing the rotated text
        textangle = line.textangle or 0.0

        top_left_corner = (line_min_aabb.llx, line_min_aabb.lly)
        line_size_aabb_matrix = (
            Matrix()
            .translated(*top_left_corner)
            # Note: negative sign (textangle is counter-clockwise, see hOCR spec)
            .rotated(-textangle)
        )
        line_size_aabb = line_size_aabb_matrix.inverse().transform(line_min_aabb)

        # Get baseline information
        slope = 0.0
        intercept = 0.0
        if line.baseline is not None:
            slope = line.baseline.slope
            intercept = line.baseline.intercept

        if abs(slope) < 0.005:
            slope = 0.0
        slope_angle = atan(slope)

        # Create the baseline transform matrix
        # Translate from hOCR perspective (top-left) to PDF perspective (bottom-left)
        baseline_matrix = (
            line_size_aabb_matrix.translated(0, line_size_aabb.height)
            .translated(0, intercept)
            .rotated(slope_angle / pi * 180)
        )

        with canvas.do.save_state(cm=baseline_matrix):
            text = Text(direction=text_direction)
            fontsize = line_size_aabb.height + intercept
            text.font(self._fontname, fontsize)
            text.render_mode(3 if invisible_text else 0)

            self._render_debug_baseline(
                canvas, baseline_matrix.inverse().transform(line_min_aabb), 0
            )

            canvas.do.fill_color(BLACK)

            # Get words and render with inter-word spaces
            words = line.children
            for word, next_word in pairwise(words + [None]):
                if word is not None:
                    self._render_word(
                        canvas,
                        baseline_matrix,
                        text,
                        fontsize,
                        word,
                        next_word,
                        text_direction,
                        inject_word_breaks,
                    )

            canvas.do.draw_text(text)

    def _render_word(
        self,
        canvas: Canvas,
        line_matrix: Matrix,
        text: Text,
        fontsize: float,
        word: OcrElement,
        next_word: OcrElement | None,
        text_direction: TextDirection,
        inject_word_breaks: bool,
    ) -> None:
        """Render a single word.

        Args:
            canvas: The PDF canvas
            line_matrix: Transform matrix for the line
            text: Text object to add glyphs to
            fontsize: Font size in points
            word: The word element to render
            next_word: The next word (for space calculation) or None
            text_direction: LTR or RTL text direction
            inject_word_breaks: Whether to add space after this word
        """
        if word.bbox is None or not word.text:
            return

        # Convert to Rectangle for transform
        hocr_box = Rectangle(
            word.bbox.left, word.bbox.top, word.bbox.right, word.bbox.bottom
        )
        box = line_matrix.inverse().transform(hocr_box)
        font_width = float(self._font.text_width(word.text, fontsize))

        # Debug rendering
        self._render_debug_word_triangle(canvas, box)
        self._render_debug_word_bbox(canvas, box)

        # Skip zero-width words
        if font_width <= 0:
            return

        if text_direction == TextDirection.RTL:
            log.info("RTL: %s", word.text)

        # Position and scale the word
        if text_direction == TextDirection.LTR:
            text.text_transform(Matrix(1, 0, 0, -1, box.llx, 0))
        elif text_direction == TextDirection.RTL:
            text.text_transform(Matrix(-1, 0, 0, -1, box.llx + box.width, 0))

        text.horiz_scale(100 * box.width / font_width)
        text.show(self._font.text_encode(word.text))

        # Render space to next word
        if not inject_word_breaks or next_word is None or next_word.bbox is None:
            return

        next_hocr_box = Rectangle(
            next_word.bbox.left,
            next_word.bbox.top,
            next_word.bbox.right,
            next_word.bbox.bottom,
        )
        next_box = line_matrix.inverse().transform(next_hocr_box)

        if text_direction == TextDirection.LTR:
            space_box = Rectangle(box.urx, box.lly, next_box.llx, next_box.ury)
        elif text_direction == TextDirection.RTL:
            space_box = Rectangle(next_box.urx, box.lly, box.llx, next_box.ury)

        self._render_debug_space_bbox(canvas, space_box)

        space_width = float(self._font.text_width(' ', fontsize))
        if space_width > 0 and space_box.width > 0:
            if text_direction == TextDirection.LTR:
                text.text_transform(Matrix(1, 0, 0, -1, space_box.llx, 0))
            elif text_direction == TextDirection.RTL:
                text.text_transform(
                    Matrix(-1, 0, 0, -1, space_box.llx + space_box.width, 0)
                )
            text.horiz_scale(100 * space_box.width / space_width)
            text.show(self._font.text_encode(' '))

    def _render_standalone_word(
        self, canvas: Canvas, word: OcrElement, invisible_text: bool
    ) -> None:
        """Render a word that is not part of a line structure.

        This is a fallback for OCR output that doesn't have line structure.

        Args:
            canvas: The PDF canvas
            word: The word element to render
            invisible_text: Whether text should be invisible
        """
        if word.bbox is None or not word.text:
            return

        # Simple rendering without baseline adjustment
        box = Rectangle(
            word.bbox.left, word.bbox.top, word.bbox.right, word.bbox.bottom
        )

        fontsize = box.height
        font_width = float(self._font.text_width(word.text, fontsize))

        if font_width <= 0:
            return

        text = Text()
        text.font(self._fontname, fontsize)
        text.render_mode(3 if invisible_text else 0)
        text.text_transform(Matrix(1, 0, 0, -1, box.llx, box.ury))
        text.horiz_scale(100 * box.width / font_width)
        text.show(self._font.text_encode(word.text))

        canvas.do.fill_color(BLACK)
        canvas.do.draw_text(text)

    # Debug rendering methods

    def _render_debug_paragraph_boxes(self, canvas: Canvas, color=CYAN) -> None:
        """Draw boxes around paragraphs."""
        if not self.render_options.render_paragraph_bbox:
            return

        with canvas.do.save_state():
            canvas.do.stroke_color(color).line_width(0.1)
            for paragraph in self.page.paragraphs:
                if paragraph.bbox is None:
                    continue
                if not paragraph.get_text_recursive():
                    continue
                canvas.do.rect(
                    paragraph.bbox.left,
                    paragraph.bbox.top,
                    paragraph.bbox.width,
                    paragraph.bbox.height,
                    fill=False,
                )

    def _render_debug_line_bbox(
        self, canvas: Canvas, line_box: Rectangle, color=BLUE
    ) -> None:
        """Render the bounding box of a text line."""
        if not self.render_options.render_line_bbox:
            return
        with canvas.do.save_state():
            canvas.do.stroke_color(color).line_width(0.15).rect(
                line_box.llx, line_box.lly, line_box.width, line_box.height, fill=False
            )

    def _render_debug_word_triangle(
        self, canvas: Canvas, box: Rectangle, color=RED, line_width=0.1
    ) -> None:
        """Render a triangle that conveys word height and direction."""
        if not self.render_options.render_triangle:
            return
        with canvas.do.save_state():
            canvas.do.stroke_color(color).line_width(line_width).line(
                box.llx, box.lly, box.urx, box.lly
            ).line(box.urx, box.lly, box.llx, box.ury).line(
                box.llx, box.lly, box.llx, box.ury
            )

    def _render_debug_word_bbox(
        self, canvas: Canvas, box: Rectangle, color=GREEN, line_width=0.1
    ) -> None:
        """Render a box depicting the word."""
        if not self.render_options.render_word_bbox:
            return
        with canvas.do.save_state():
            canvas.do.stroke_color(color).line_width(line_width).rect(
                box.llx, box.lly, box.width, box.height, fill=False
            )

    def _render_debug_space_bbox(
        self, canvas: Canvas, box: Rectangle, color=DARKGREEN, line_width=0.1
    ) -> None:
        """Render a box depicting the space between words."""
        if not self.render_options.render_space_bbox:
            return
        with canvas.do.save_state():
            canvas.do.fill_color(color).line_width(line_width).rect(
                box.llx, box.lly, box.width, box.height, fill=True
            )

    def _render_debug_baseline(
        self,
        canvas: Canvas,
        line_box: Rectangle,
        baseline_lly: float,
        color=MAGENTA,
        line_width=0.25,
    ) -> None:
        """Render the text baseline."""
        if not self.render_options.render_baseline:
            return
        with canvas.do.save_state():
            canvas.do.stroke_color(color).line_width(line_width).line(
                line_box.llx,
                baseline_lly,
                line_box.urx,
                baseline_lly,
            )
