# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""fpdf2-based PDF renderer for OCR text layers.

This module provides PDF rendering using fpdf2 for creating searchable
OCR text layers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from itertools import pairwise
from math import atan, degrees
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import TextMode
from pikepdf import Matrix, Rectangle

from ocrmypdf.font import FontManager, MultiFontManager
from ocrmypdf.models.ocr_element import OcrClass, OcrElement

log = logging.getLogger(__name__)


def transform_point(matrix: Matrix, x: float, y: float) -> tuple[float, float]:
    """Transform a point (x, y) by a matrix.

    Args:
        matrix: pikepdf Matrix to apply
        x: X coordinate
        y: Y coordinate

    Returns:
        Tuple of (transformed_x, transformed_y)
    """
    # Use a degenerate rectangle to transform a single point
    rect = Rectangle(x, y, x, y)
    transformed = matrix.transform(rect)
    return (transformed.llx, transformed.lly)


def transform_box(
    matrix: Matrix, left: float, top: float, right: float, bottom: float
) -> tuple[float, float, float, float]:
    """Transform a bounding box by a matrix.

    Args:
        matrix: pikepdf Matrix to apply
        left: Left edge of box
        top: Top edge of box
        right: Right edge of box
        bottom: Bottom edge of box

    Returns:
        Tuple of (llx, lly, width, height) of the transformed box
    """
    rect = Rectangle(left, top, right, bottom)
    transformed = matrix.transform(rect)
    return (
        transformed.llx,
        transformed.lly,
        transformed.width,
        transformed.height,
    )


@dataclass
class DebugRenderOptions:
    """Options for debug visualization during rendering.

    When enabled, draws colored lines/shapes to visualize OCR structure.
    """

    render_baseline: bool = False  # Magenta lines along baselines
    render_line_bbox: bool = False  # Blue rectangles around lines
    render_word_bbox: bool = False  # Green rectangles around words


class CoordinateTransform:
    """Manages coordinate transformations for fpdf2 rendering.

    Handles conversion from OCR pixel coordinates (top-left origin) to
    PDF points. fpdf2 uses top-left origin like hOCR, so no Y-flip needed.
    """

    def __init__(self, dpi: float, page_width_px: float, page_height_px: float):
        """Initialize coordinate transform."""
        self.dpi = dpi
        self.page_width_px = page_width_px
        self.page_height_px = page_height_px

    @property
    def page_width_pt(self) -> float:
        """Page width in PDF points."""
        return self.page_width_px * 72.0 / self.dpi

    @property
    def page_height_pt(self) -> float:
        """Page height in PDF points."""
        return self.page_height_px * 72.0 / self.dpi

    def px_to_pt(self, value: float) -> float:
        """Convert pixels to PDF points."""
        return value * 72.0 / self.dpi

    def bbox_to_pt(self, bbox) -> tuple[float, float, float, float]:
        """Convert BoundingBox from pixels to points."""
        return (
            self.px_to_pt(bbox.left),
            self.px_to_pt(bbox.top),
            self.px_to_pt(bbox.right),
            self.px_to_pt(bbox.bottom),
        )


class Fpdf2PdfRenderer:
    """Renders OcrElement trees to PDF using fpdf2.

    This class provides the core rendering logic for converting OCR output
    into PDF text layers using fpdf2's text drawing capabilities.
    """

    def __init__(
        self,
        page: OcrElement,
        dpi: float,
        multi_font_manager: MultiFontManager,
        invisible_text: bool = True,
        debug_render_options: DebugRenderOptions | None = None,
    ):
        """Initialize renderer.

        Args:
            page: Root OcrElement (must be ocr_page)
            dpi: Source image DPI
            multi_font_manager: MultiFontManager instance
            invisible_text: If True, render text as invisible (text mode 3)
            debug_render_options: Options for debug visualization

        Raises:
            ValueError: If page is not an ocr_page or lacks a bounding box
        """
        if page.ocr_class != OcrClass.PAGE:
            raise ValueError("Root element must be ocr_page")
        if page.bbox is None:
            raise ValueError("Page must have bounding box")

        self.page = page
        self.dpi = dpi
        self.multi_font_manager = multi_font_manager
        self.invisible_text = invisible_text
        self.debug_options = debug_render_options or DebugRenderOptions()

        # Setup coordinate transform
        self.coord_transform = CoordinateTransform(
            dpi=dpi,
            page_width_px=page.bbox.width,
            page_height_px=page.bbox.height,
        )

        # Registered fonts: font_path -> fpdf_family_name
        self._registered_fonts: dict[str, str] = {}

    def render(self, output_path: Path) -> None:
        """Render page to PDF file.

        Args:
            output_path: Output PDF file path
        """
        # Create PDF with custom page size
        pdf = FPDF(
            unit="pt",
            format=(
                self.coord_transform.page_width_pt,
                self.coord_transform.page_height_pt,
            ),
        )
        pdf.set_auto_page_break(auto=False)

        # Enable text shaping for complex scripts
        pdf.set_text_shaping(True)

        # Disable cell margin to ensure precise text positioning
        # fpdf2's cell() adds c_margin padding by default, which shifts text
        pdf.c_margin = 0

        # Set text mode for invisible text
        if self.invisible_text:
            pdf.text_rendering_mode = TextMode.INVISIBLE
        else:
            pdf.text_rendering_mode = TextMode.FILL

        # Render content to PDF
        self.render_to_pdf(pdf)

        # Write PDF
        pdf.output(str(output_path))

    def render_to_pdf(self, pdf: FPDF) -> None:
        """Render page content to an existing FPDF instance.

        This method adds a page and renders all content. Used by both
        single-page rendering and multi-page rendering.

        Args:
            pdf: FPDF instance to render into
        """
        # Add page with correct dimensions
        pdf.add_page(
            format=(
                self.coord_transform.page_width_pt,
                self.coord_transform.page_height_pt,
            )
        )

        # Render all paragraphs
        for para in self.page.paragraphs:
            self._render_paragraph(pdf, para)

        # If no paragraphs, render lines directly
        if not self.page.paragraphs:
            for line in self.page.lines:
                self._render_line(pdf, line)

    def _register_font(self, pdf: FPDF, font_manager: FontManager) -> str:
        """Register font with fpdf2 if not already registered.

        Args:
            pdf: FPDF instance
            font_manager: FontManager containing the font

        Returns:
            Font family name to use with pdf.set_font()
        """
        font_path_str = str(font_manager.font_path)

        if font_path_str not in self._registered_fonts:
            # Use the font filename stem as the family name
            family_name = font_manager.font_path.stem
            pdf.add_font(family=family_name, fname=font_path_str)
            self._registered_fonts[font_path_str] = family_name

        return self._registered_fonts[font_path_str]

    def _render_paragraph(self, pdf: FPDF, para: OcrElement) -> None:
        """Render a paragraph element.

        Args:
            pdf: FPDF instance
            para: Paragraph OCR element
        """
        for line in para.children:
            if line.ocr_class in OcrClass.LINE_TYPES:
                self._render_line(pdf, line)

    def _render_line(self, pdf: FPDF, line: OcrElement) -> None:
        """Render a line element with baseline support.

        Strategy (following pikepdf reference implementation):
        1. Create a baseline_matrix that transforms from hOCR coordinates to
           a coordinate system aligned with the text baseline
        2. For each word, transform its hOCR bbox using baseline_matrix.inverse()
           to get its position in the baseline coordinate system
        3. Render words along the baseline with horizontal scaling

        Args:
            pdf: FPDF instance
            line: Line OCR element
        """
        if line.bbox is None:
            return

        # Validate line bbox
        if line.bbox.height <= 0:
            log.error(
                "line box is invalid so we cannot render it: box=%s text=%s",
                line.bbox,
                line.text if hasattr(line, 'text') else '',
            )
            return

        # Convert line bbox to PDF points
        line_left_pt = self.coord_transform.px_to_pt(line.bbox.left)
        line_top_pt = self.coord_transform.px_to_pt(line.bbox.top)
        line_right_pt = self.coord_transform.px_to_pt(line.bbox.right)
        line_bottom_pt = self.coord_transform.px_to_pt(line.bbox.bottom)
        # Note: line_width_pt and line_height_pt not needed since we compute
        # dimensions in the un-rotated coordinate system via matrix transform

        # Debug rendering: draw line bbox (in page coordinates)
        if self.debug_options.render_line_bbox:
            self._render_debug_line_bbox(
                pdf, line_left_pt, line_top_pt, line_right_pt, line_bottom_pt
            )

        # Get textangle (rotation of the entire line)
        textangle = line.textangle or 0.0

        # Build line_size_aabb_matrix: transforms from page coords to un-rotated
        # line coords. The hOCR bbox is the minimum axis-aligned bounding box
        # enclosing the rotated text.
        # Start at top-left corner of line bbox, then rotate by -textangle
        line_size_aabb_matrix = (
            Matrix()
            .translated(line_left_pt, line_top_pt)
            .rotated(-textangle)  # textangle is counter-clockwise per hOCR spec
        )

        # Get the line dimensions in the un-rotated coordinate system
        # Transform line bbox corners to get the un-rotated dimensions
        inv_line_matrix = line_size_aabb_matrix.inverse()
        # Transform bottom-right corner to get line dimensions in rotated space
        _, _, line_size_width, line_size_height = transform_box(
            inv_line_matrix, line_left_pt, line_top_pt, line_right_pt, line_bottom_pt
        )

        # Get baseline information (slope and intercept)
        slope = 0.0
        intercept_pt = 0.0
        if line.baseline is not None:
            slope = line.baseline.slope
            intercept_pt = self.coord_transform.px_to_pt(line.baseline.intercept)
            if abs(slope) < 0.005:
                slope = 0.0
        else:
            # No baseline provided: calculate from font metrics
            default_font_manager = self.multi_font_manager.fonts['NotoSans-Regular']
            ascent, descent, units_per_em = default_font_manager.get_font_metrics()
            ascent_norm = ascent / units_per_em
            descent_norm = descent / units_per_em
            # Baseline intercept based on font metrics
            intercept_pt = (
                -abs(descent_norm)
                * line_size_height
                / (ascent_norm + abs(descent_norm))
            )

        slope_angle_deg = degrees(atan(slope)) if slope != 0.0 else 0.0

        # Build baseline_matrix: transforms from page coords to baseline coords
        # 1. Start with line_size_aabb_matrix (translates to line corner, rotates)
        # 2. Translate down to bottom of un-rotated line (line_size_height)
        # 3. Apply baseline intercept offset
        # 4. Rotate by baseline slope
        baseline_matrix = (
            line_size_aabb_matrix.translated(
                0, line_size_height
            )  # Move to bottom of line
            .translated(0, intercept_pt)  # Apply baseline intercept
            .rotated(slope_angle_deg)  # Rotate by baseline slope
        )

        # Calculate font size: height from baseline to top of line
        font_size = line_size_height + intercept_pt
        if font_size < 1.0:
            font_size = line_size_height * 0.8

        # Total rotation for rendering (textangle + slope)
        total_rotation_deg = -textangle + slope_angle_deg

        # Debug rendering: draw baseline
        if self.debug_options.render_baseline:
            # Baseline starts at origin in baseline coords, extends line width
            baseline_start = transform_point(baseline_matrix, 0, 0)
            baseline_end = transform_point(baseline_matrix, line_size_width, 0)
            pdf.set_draw_color(255, 0, 255)  # Magenta
            pdf.set_line_width(0.75)
            pdf.line(
                baseline_start[0], baseline_start[1], baseline_end[0], baseline_end[1]
            )

        # Extract line language for font selection
        line_language = line.language

        # Get inverse of baseline_matrix for transforming word bboxes
        inv_baseline_matrix = baseline_matrix.inverse()

        # Collect words to render
        words: list[OcrElement | None] = [
            w for w in line.children if w.ocr_class == OcrClass.WORD and w.text
        ]

        # Render each word followed by space (except last)
        # Use pairwise to iterate over consecutive word pairs, pairing the last
        # word with a None to signal the end of the line.
        for current_word, next_word in pairwise(words + [None]):
            if current_word:  # Don't render EOL sentinel
                # Render the current word
                self._render_word(
                    pdf,
                    current_word,
                    baseline_matrix,
                    inv_baseline_matrix,
                    font_size,
                    total_rotation_deg,
                    line_language,
                )
            if next_word:  # Don't render EOL sentinel
                self._maybe_render_space(
                    pdf,
                    current_word,
                    next_word,
                    baseline_matrix,
                    inv_baseline_matrix,
                    font_size,
                    total_rotation_deg,
                    line_language,
                    line.direction,
                )

    def _render_word(
        self,
        pdf: FPDF,
        word: OcrElement,
        baseline_matrix: Matrix,
        inv_baseline_matrix: Matrix,
        font_size: float,
        rotation_deg: float,
        line_language: str | None,
    ) -> None:
        """Render a word using word bbox positioning.

        Position text so its visual bounding box matches the hOCR word bbox.
        This provides more accurate placement than baseline-relative positioning
        because we match the actual glyph bounds rather than relying on font
        metrics which may not exactly match the OCR'd text appearance.

        Args:
            pdf: FPDF instance
            word: Word OCR element
            baseline_matrix: Transform from baseline coords to page coords
            inv_baseline_matrix: Transform from page coords to baseline coords
            font_size: Font size in points (from line calculation)
            rotation_deg: Total rotation angle for text
            line_language: Language code from line for font selection
        """
        if not word.text or word.bbox is None:
            return

        # Select appropriate font for this word
        font_manager = self.multi_font_manager.select_font_for_word(
            word.text, line_language
        )

        # Register font with fpdf2
        font_family = self._register_font(pdf, font_manager)

        # Convert word bbox to PDF points
        word_left_pt = self.coord_transform.px_to_pt(word.bbox.left)
        word_top_pt = self.coord_transform.px_to_pt(word.bbox.top)
        word_right_pt = self.coord_transform.px_to_pt(word.bbox.right)
        word_bottom_pt = self.coord_transform.px_to_pt(word.bbox.bottom)
        word_width_pt = word_right_pt - word_left_pt

        # Transform word bbox into baseline coordinate system to get x position
        box_llx, _, _, _ = transform_box(
            inv_baseline_matrix,
            word_left_pt,
            word_top_pt,
            word_right_pt,
            word_bottom_pt,
        )

        # Debug rendering: draw word bbox (in page coordinates)
        if self.debug_options.render_word_bbox:
            self._render_debug_word_bbox(
                pdf, word_left_pt, word_top_pt, word_right_pt, word_bottom_pt
            )

        # Use line-based font_size for consistent vertical sizing
        word_font_size = font_size

        # Set font
        pdf.set_font(font_family, size=word_font_size)

        # Calculate natural text width at this font size
        natural_width = pdf.get_string_width(word.text)

        # Calculate horizontal scale to fit word bbox width
        if natural_width > 0 and word_width_pt > 0:
            scale_x = (word_width_pt / natural_width) * 100
        else:
            scale_x = 100

        # Apply horizontal stretching
        pdf.set_stretching(scale_x)

        # Get left side bearing of first character to compensate for glyph offset
        lsb_pt = font_manager.get_left_side_bearing(word.text[0], word_font_size)

        # Transform the baseline-relative x position back to page coordinates
        # The word sits at (box_llx, 0) in baseline coords (on the baseline)
        page_x, page_y = transform_point(baseline_matrix, box_llx, 0)

        # Adjust x position to account for lsb (scaled by horizontal stretch)
        adjusted_x = page_x - lsb_pt * (scale_x / 100)

        # Calculate y position based on baseline
        # In fpdf2, set_xy(x, y) positions text such that the baseline is at:
        #   baseline_y = set_y + font_size * (ascent / (ascent + |descent|))
        # We want baseline at page_y, so:
        #   page_y = set_y + font_size * (ascent / (ascent + |descent|))
        #   set_y = page_y - font_size * (ascent / (ascent + |descent|))
        ascent, descent, _ = font_manager.get_font_metrics()
        total_height = ascent + abs(descent)
        baseline_offset_ratio = ascent / total_height
        adjusted_y = page_y - word_font_size * baseline_offset_ratio

        # Position and draw text with rotation
        if abs(rotation_deg) > 0.1:
            with pdf.rotation(-rotation_deg, x=page_x, y=page_y):
                pdf.set_xy(adjusted_x, adjusted_y)
                pdf.cell(text=word.text)
        else:
            pdf.set_xy(adjusted_x, adjusted_y)
            pdf.cell(text=word.text)

        # Reset stretching
        pdf.set_stretching(100)

    def _is_cjk_only(self, text: str) -> bool:
        """Check if text contains only CJK characters.

        CJK scripts don't use spaces between words, so we should not insert
        spaces between adjacent CJK words.

        Args:
            text: Text to check

        Returns:
            True if text contains only CJK characters
        """
        for char in text:
            cp = ord(char)
            # Check if character is in CJK ranges
            if not (
                0x4E00 <= cp <= 0x9FFF  # CJK Unified Ideographs
                or 0x3400 <= cp <= 0x4DBF  # CJK Extension A
                or 0x20000 <= cp <= 0x2A6DF  # CJK Extension B
                or 0x2A700 <= cp <= 0x2B73F  # CJK Extension C
                or 0x2B740 <= cp <= 0x2B81F  # CJK Extension D
                or 0x2B820 <= cp <= 0x2CEAF  # CJK Extension E
                or 0x2CEB0 <= cp <= 0x2EBEF  # CJK Extension F
                or 0x30000 <= cp <= 0x3134F  # CJK Extension G
                or 0x3040 <= cp <= 0x309F  # Hiragana
                or 0x30A0 <= cp <= 0x30FF  # Katakana
                or 0x31F0 <= cp <= 0x31FF  # Katakana Phonetic Extensions
                or 0xAC00 <= cp <= 0xD7AF  # Hangul Syllables
                or 0x1100 <= cp <= 0x11FF  # Hangul Jamo
                or 0x3130 <= cp <= 0x318F  # Hangul Compatibility Jamo
                or 0xA960 <= cp <= 0xA97F  # Hangul Jamo Extended-A
                or 0xD7B0 <= cp <= 0xD7FF  # Hangul Jamo Extended-B
                or 0x3000 <= cp <= 0x303F  # CJK Symbols and Punctuation
                or 0xFF00 <= cp <= 0xFFEF  # Halfwidth and Fullwidth Forms
            ):
                return False
        return True

    def _maybe_render_space(
        self,
        pdf: FPDF,
        current_word: OcrElement,
        next_word: OcrElement,
        baseline_matrix: Matrix,
        inv_baseline_matrix: Matrix,
        font_size: float,
        rotation_deg: float,
        line_language: str | None,
        direction: str | None,
    ) -> None:
        """Render a space character between two words if a gap exists.

        This ensures that PDF readers like pdfminer.six can properly segment
        words during text extraction. Some PDF readers rely on explicit space
        characters rather than inferring word boundaries from positioning.

        Args:
            pdf: FPDF instance
            current_word: The word that was just rendered
            next_word: The next word to be rendered
            baseline_matrix: Transform from baseline coords to page coords
            inv_baseline_matrix: Transform from page coords to baseline coords
            font_size: Font size in points
            rotation_deg: Total rotation angle for text
            line_language: Language code from line for font selection
            direction: Text direction ("ltr" or "rtl")
        """
        if current_word.bbox is None or next_word.bbox is None:
            return

        # Skip if both words are CJK-only (no spaces in CJK text)
        if self._is_cjk_only(current_word.text) and self._is_cjk_only(next_word.text):
            return

        # Calculate gap between words
        if direction == "rtl":
            gap_left = next_word.bbox.right
            gap_right = current_word.bbox.left
        else:
            gap_left = current_word.bbox.right
            gap_right = next_word.bbox.left

        gap_width_px = gap_right - gap_left

        # Use word height as proxy for line height
        line_height_px = current_word.bbox.height

        # Skip if gap is too small (noise) or words are overlapping
        if gap_width_px <= line_height_px * 0.05:
            return

        # Render space in the gap
        self._render_space(
            pdf,
            gap_left,
            gap_right,
            current_word.bbox.top,
            current_word.bbox.bottom,
            baseline_matrix,
            inv_baseline_matrix,
            font_size,
            rotation_deg,
            line_language,
        )

    def _render_space(
        self,
        pdf: FPDF,
        gap_left_px: float,
        gap_right_px: float,
        gap_top_px: float,
        gap_bottom_px: float,
        baseline_matrix: Matrix,
        inv_baseline_matrix: Matrix,
        font_size: float,
        rotation_deg: float,
        line_language: str | None,
    ) -> None:
        """Render a space character in a gap between words.

        Uses the same baseline transformation logic as word rendering to ensure
        proper alignment on rotated or sloped baselines.

        Args:
            pdf: FPDF instance
            gap_left_px: Left edge of gap in pixels
            gap_right_px: Right edge of gap in pixels
            gap_top_px: Top edge of gap in pixels
            gap_bottom_px: Bottom edge of gap in pixels
            baseline_matrix: Transform from baseline coords to page coords
            inv_baseline_matrix: Transform from page coords to baseline coords
            font_size: Font size in points
            rotation_deg: Total rotation angle for text
            line_language: Language code from line for font selection
        """
        # Convert gap to PDF points
        gap_left_pt = self.coord_transform.px_to_pt(gap_left_px)
        gap_top_pt = self.coord_transform.px_to_pt(gap_top_px)
        gap_right_pt = self.coord_transform.px_to_pt(gap_right_px)
        gap_bottom_pt = self.coord_transform.px_to_pt(gap_bottom_px)
        gap_width_pt = gap_right_pt - gap_left_pt

        # Transform gap bbox into baseline coordinate system to get x position
        box_llx, _, _, _ = transform_box(
            inv_baseline_matrix,
            gap_left_pt,
            gap_top_pt,
            gap_right_pt,
            gap_bottom_pt,
        )

        # Select font (use default font for space)
        font_manager = self.multi_font_manager.select_font_for_word(" ", line_language)
        font_family = self._register_font(pdf, font_manager)

        # Set font
        pdf.set_font(font_family, size=font_size)

        # Calculate natural space width and scaling
        natural_width = pdf.get_string_width(" ")
        if natural_width > 0 and gap_width_pt > 0:
            scale_x = (gap_width_pt / natural_width) * 100
        else:
            scale_x = 100

        # Apply horizontal stretching
        pdf.set_stretching(scale_x)

        # Transform the baseline-relative x position back to page coordinates
        page_x, page_y = transform_point(baseline_matrix, box_llx, 0)

        # Calculate y position based on baseline (same as _render_word)
        ascent, descent, _ = font_manager.get_font_metrics()
        total_height = ascent + abs(descent)
        baseline_offset_ratio = ascent / total_height
        adjusted_y = page_y - font_size * baseline_offset_ratio

        # Position and draw space with rotation
        if abs(rotation_deg) > 0.1:
            with pdf.rotation(-rotation_deg, x=page_x, y=page_y):
                pdf.set_xy(page_x, adjusted_y)
                pdf.cell(text=" ")
        else:
            pdf.set_xy(page_x, adjusted_y)
            pdf.cell(text=" ")

        # Reset stretching
        pdf.set_stretching(100)

    def _render_debug_line_bbox(
        self,
        pdf: FPDF,
        left: float,
        top: float,
        right: float,
        bottom: float,
    ) -> None:
        """Draw a blue box around the line bbox."""
        pdf.set_draw_color(0, 0, 255)  # Blue
        pdf.set_line_width(0.5)
        pdf.rect(left, top, right - left, bottom - top)

    def _render_debug_baseline(
        self,
        pdf: FPDF,
        x: float,
        y: float,
        width: float,
        rotation_deg: float,
    ) -> None:
        """Draw a magenta line along the baseline."""
        pdf.set_draw_color(255, 0, 255)  # Magenta
        pdf.set_line_width(0.75)

        if abs(rotation_deg) > 0.1:
            with pdf.rotation(rotation_deg, x=x, y=y):
                pdf.line(x, y, x + width, y)
        else:
            pdf.line(x, y, x + width, y)

    def _render_debug_word_bbox(
        self,
        pdf: FPDF,
        left: float,
        top: float,
        right: float,
        bottom: float,
    ) -> None:
        """Draw a green box around the word bbox."""
        pdf.set_draw_color(0, 255, 0)  # Green
        pdf.set_line_width(0.3)
        pdf.rect(left, top, right - left, bottom - top)


class Fpdf2MultiPageRenderer:
    """Renders multiple OcrElement pages into a single PDF.

    This class handles multi-page documents by delegating to Fpdf2PdfRenderer
    for each page while sharing a single FPDF instance and font registration.
    """

    def __init__(
        self,
        pages_data: list[tuple[int, OcrElement, float]],
        multi_font_manager: MultiFontManager,
        invisible_text: bool = True,
        debug_render_options: DebugRenderOptions | None = None,
    ):
        """Initialize multi-page renderer.

        Args:
            pages_data: List of (pageno, ocr_tree, dpi) tuples
            multi_font_manager: Shared multi-font manager for all pages
            invisible_text: Whether to render invisible text
            debug_render_options: Options for debug visualization
        """
        self.pages_data = pages_data
        self.multi_font_manager = multi_font_manager
        self.invisible_text = invisible_text
        self.debug_options = debug_render_options or DebugRenderOptions()

    def render(self, output_path: Path) -> None:
        """Render all pages to a single multi-page PDF.

        Args:
            output_path: Output PDF file path
        """
        if not self.pages_data:
            raise ValueError("No pages to render")

        # Create PDF (page size will be set per-page)
        pdf = FPDF(unit="pt")
        pdf.set_auto_page_break(auto=False)
        pdf.set_text_shaping(True)

        # Disable cell margin to ensure precise text positioning
        # fpdf2's cell() adds c_margin padding by default, which shifts text
        pdf.c_margin = 0

        # Set text mode for invisible text
        if self.invisible_text:
            pdf.text_rendering_mode = TextMode.INVISIBLE
        else:
            pdf.text_rendering_mode = TextMode.FILL

        # Shared font registration across all pages
        shared_registered_fonts: dict[str, str] = {}

        # Render each page using Fpdf2PdfRenderer
        for _pageno, page, dpi in self.pages_data:
            if page.bbox is None:
                continue

            # Create a renderer for this page
            page_renderer = Fpdf2PdfRenderer(
                page=page,
                dpi=dpi,
                multi_font_manager=self.multi_font_manager,
                invisible_text=self.invisible_text,
                debug_render_options=self.debug_options,
            )

            # Share font registration to avoid re-registering fonts
            page_renderer._registered_fonts = shared_registered_fonts

            # Render page content to the shared PDF
            page_renderer.render_to_pdf(pdf)

        # Write PDF
        pdf.output(str(output_path))
