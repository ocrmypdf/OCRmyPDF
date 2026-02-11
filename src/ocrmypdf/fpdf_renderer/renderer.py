# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""fpdf2-based PDF renderer for OCR text layers.

This module provides PDF rendering using fpdf2 for creating searchable
OCR text layers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from math import atan, cos, degrees, radians, sin, sqrt
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import PDFResourceType, TextMode
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
        # Track whether we've already logged the info-level suppression message
        self._logged_aspect_ratio_suppression = False

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
            pdf.text_mode = TextMode.INVISIBLE
        else:
            pdf.text_mode = TextMode.FILL

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

        # Read baseline early so we can detect rotation from steep slopes.
        # When Tesseract doesn't report textangle for rotated text, the
        # rotation gets encoded as a very steep baseline slope instead.
        slope = 0.0
        intercept_pt = 0.0
        has_meaningful_baseline = False
        if line.baseline is not None:
            slope = line.baseline.slope
            intercept_pt = self.coord_transform.px_to_pt(line.baseline.intercept)
            if abs(slope) < 0.005:
                slope = 0.0
            has_meaningful_baseline = True

        # Detect text rotation from steep baseline slope.
        # A slope magnitude > 1.0 corresponds to > 45° from horizontal,
        # which indicates the line is rotated, not merely skewed.
        if textangle == 0.0 and abs(slope) > 1.0:
            textangle = degrees(atan(slope))
            # The original baseline slope and intercept are not meaningful
            # after extracting rotation; recalculate intercept from font
            # metrics below.
            slope = 0.0
            has_meaningful_baseline = False

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

        # Get baseline intercept
        if not has_meaningful_baseline:
            # No baseline provided or baseline was used for rotation detection:
            # calculate intercept from font metrics
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

        # Suppress lines where the text aspect ratio is implausible.
        # This catches cases where Tesseract failed to detect rotation
        # entirely (slope=0, no textangle) and produced garbage text in a
        # bounding box whose shape doesn't match the text content at all.
        if not self._check_aspect_ratio_plausible(
            pdf, words, font_size, slope_angle_deg,
            line_size_width, line_size_height, line_language,
        ):
            return

        # Collect word rendering data: (text, x_baseline, font_family, word_tz)
        word_render_data: list[tuple[str, float, str, float]] = []
        for word in words:
            if word is None or not word.text or word.bbox is None:
                continue

            word_left_pt = self.coord_transform.px_to_pt(word.bbox.left)
            word_top_pt = self.coord_transform.px_to_pt(word.bbox.top)
            word_right_pt = self.coord_transform.px_to_pt(word.bbox.right)
            word_bottom_pt = self.coord_transform.px_to_pt(word.bbox.bottom)
            word_width_pt = word_right_pt - word_left_pt

            # Debug rendering: draw word bbox (in page coordinates)
            if self.debug_options.render_word_bbox:
                self._render_debug_word_bbox(
                    pdf, word_left_pt, word_top_pt, word_right_pt, word_bottom_pt
                )

            # Get x position in baseline coordinate system
            box_llx, _, _, _ = transform_box(
                inv_baseline_matrix,
                word_left_pt,
                word_top_pt,
                word_right_pt,
                word_bottom_pt,
            )

            # Select font and compute word-only Tz
            font_manager = self.multi_font_manager.select_font_for_word(
                word.text, line_language
            )
            font_family = self._register_font(pdf, font_manager)
            pdf.set_font(font_family, size=font_size)
            natural_width = pdf.get_string_width(word.text)
            if natural_width > 0 and word_width_pt > 0:
                word_tz = (word_width_pt / natural_width) * 100
            else:
                word_tz = 100.0

            word_render_data.append((word.text, box_llx, font_family, word_tz))

        if not word_render_data:
            return

        # Emit single BT block for the entire line using raw PDF operators.
        # This avoids a poppler bug where Tz (horizontal scaling) is not
        # carried across BT/ET boundaries, affecting all poppler-based tools
        # and viewers (Evince, pdftotext, etc.). By keeping all words in a
        # single BT block with relative Td positioning and per-word Tz, we
        # ensure correct inter-word spacing.
        self._emit_line_bt_block(
            pdf,
            word_render_data,
            baseline_matrix,
            font_size,
            total_rotation_deg,
        )

    def _check_aspect_ratio_plausible(
        self,
        pdf: FPDF,
        words: list[OcrElement | None],
        font_size: float,
        slope_angle_deg: float,
        line_size_width: float,
        line_size_height: float,
        line_language: str | None,
    ) -> bool:
        """Check whether the line's aspect ratio is plausible for its text.

        Compares the aspect ratio of the OCR bounding box to the aspect ratio
        the text would have if rendered normally (accounting for baseline
        slope). A large mismatch indicates Tesseract misread rotated text
        without detecting the rotation.

        Returns:
            True if plausible (rendering should proceed), False to suppress.
        """
        if line_size_width <= 0 or line_size_height <= 0 or font_size <= 0:
            return True

        # Fast path: most lines are wider than they are tall, which is
        # the normal shape for horizontal text. Only tall-narrow boxes
        # (height > width) need the expensive font measurement check.
        if line_size_width >= line_size_height:
            return True

        line_text = ' '.join(
            w.text for w in words if w is not None and w.text
        )
        if not line_text:
            return True

        # Measure the natural rendered width of the line text
        font_manager = self.multi_font_manager.select_font_for_word(
            line_text, line_language
        )
        font_family = self._register_font(pdf, font_manager)
        pdf.set_font(font_family, size=round(font_size))
        natural_width = pdf.get_string_width(line_text)

        if natural_width <= 0:
            return True

        # Compute the AABB the text would occupy considering baseline slope
        theta = radians(abs(slope_angle_deg))
        expected_w = natural_width * cos(theta) + font_size * sin(theta)
        expected_h = natural_width * sin(theta) + font_size * cos(theta)

        if expected_h <= 0:
            return True

        actual_aspect = line_size_width / line_size_height
        expected_aspect = expected_w / expected_h
        ratio = actual_aspect / expected_aspect

        if ratio >= 0.1:
            return True

        # Implausible aspect ratio — suppress this line
        log.debug(
            "Suppressing text with improbable aspect ratio: "
            "actual=%.3f expected=%.3f ratio=%.4f text=%r",
            actual_aspect,
            expected_aspect,
            ratio,
            line_text[:80],
        )
        if not self._logged_aspect_ratio_suppression:
            log.info(
                "Suppressing OCR output text with improbable aspect ratio"
            )
            self._logged_aspect_ratio_suppression = True
        return False

    def _emit_line_bt_block(
        self,
        pdf: FPDF,
        word_render_data: list[tuple[str, float, str, float]],
        baseline_matrix: Matrix,
        font_size: float,
        total_rotation_deg: float,
    ) -> None:
        """Emit a single BT block for the entire line using raw PDF operators.

        Writes all words in a single BT..ET block with relative Td positioning
        and per-word Tz. Each non-last word gets a trailing space appended, with
        Tz calculated so the rendered width of "word " spans from the current
        word's start to the next word's start. This works around a poppler bug
        where Tz is not carried across BT/ET boundaries, which affects all
        poppler-based viewers and tools (Evince, pdftotext, etc.).

        Args:
            pdf: FPDF instance
            word_render_data: List of (text, x_baseline, font_family, word_tz)
                tuples, one per word on this line
            baseline_matrix: Transform from baseline coords to page coords
            font_size: Font size in points
            total_rotation_deg: Total rotation angle (textangle + slope)
        """
        page_height = self.coord_transform.page_height_pt

        # Compute baseline direction in PDF coordinates for rotation
        has_rotation = abs(total_rotation_deg) > 0.01
        bx0, by0_fpdf = transform_point(baseline_matrix, 0, 0)
        by0_pdf = page_height - by0_fpdf

        ops: list[str] = []

        if has_rotation:
            # Compute direction vector along the baseline in PDF coordinates
            bx1, by1_fpdf = transform_point(baseline_matrix, 100, 0)
            by1_pdf = page_height - by1_fpdf
            dx = bx1 - bx0
            dy = by1_pdf - by0_pdf
            length = sqrt(dx * dx + dy * dy)
            if length > 0:
                cos_a = dx / length
                sin_a = dy / length
            else:
                cos_a = 1.0
                sin_a = 0.0

            # Save graphics state, apply rotation+translation via cm.
            # The cm maps local coordinates (baseline-aligned, x along text)
            # to PDF page coordinates.
            ops.append('q')
            ops.append(
                f'{cos_a:.6f} {sin_a:.6f} {-sin_a:.6f} {cos_a:.6f} '
                f'{bx0:.2f} {by0_pdf:.2f} cm'
            )

        # Begin text object
        ops.append('BT')

        # Text render mode: 3 = invisible, 0 = fill
        tr = 3 if self.invisible_text else 0
        ops.append(f'{tr} Tr')

        # Initial text position
        first_x_baseline = word_render_data[0][1]
        if has_rotation:
            # In the cm-transformed space, origin is at the baseline start
            ops.append(f'{first_x_baseline:.2f} 0 Td')
        else:
            # Direct PDF coordinates
            page_x, page_y_fpdf = transform_point(
                baseline_matrix, first_x_baseline, 0
            )
            page_y_pdf = page_height - page_y_fpdf
            ops.append(f'{page_x:.2f} {page_y_pdf:.2f} Td')

        prev_font_family: str | None = None
        prev_x_baseline = first_x_baseline

        for i, (text, x_baseline, font_family, word_tz) in enumerate(
            word_render_data
        ):
            is_last = i == len(word_render_data) - 1

            # Set font if changed
            if font_family != prev_font_family:
                pdf.set_font(font_family, size=font_size)
                # Register font resource on this page
                pdf._resource_catalog.add(
                    PDFResourceType.FONT, pdf.current_font.i, pdf.page
                )
                ops.append(
                    f'/F{pdf.current_font.i} {pdf.font_size_pt:.2f} Tf'
                )
                prev_font_family = font_family

            # Relative positioning (for words after the first)
            if i > 0:
                if has_rotation:
                    # In rotated space, advance is purely along x-axis
                    dx_baseline = x_baseline - prev_x_baseline
                    ops.append(f'{dx_baseline:.2f} 0 Td')
                else:
                    # Non-rotated: compute delta in PDF coordinates
                    px_prev, py_prev_f = transform_point(
                        baseline_matrix, prev_x_baseline, 0
                    )
                    px_curr, py_curr_f = transform_point(
                        baseline_matrix, x_baseline, 0
                    )
                    dx_pdf = px_curr - px_prev
                    # Flip y delta for PDF coordinates (y-up)
                    dy_pdf = -(py_curr_f - py_prev_f)
                    ops.append(f'{dx_pdf:.2f} {dy_pdf:.2f} Td')

            # Determine text to render and compute Tz
            if not is_last:
                next_text, next_x_baseline, _, _ = word_render_data[i + 1]
                advance = next_x_baseline - x_baseline

                # Add trailing space unless both words are CJK-only
                if (
                    advance > 0
                    and not (
                        self._is_cjk_only(text)
                        and self._is_cjk_only(next_text)
                    )
                ):
                    text_to_render = text + ' '
                    natural_w = pdf.get_string_width(text_to_render)
                    render_tz = (
                        (advance / natural_w) * 100
                        if natural_w > 0
                        else word_tz
                    )
                else:
                    text_to_render = text
                    render_tz = word_tz
            else:
                text_to_render = text
                render_tz = word_tz

            ops.append(f'{render_tz:.2f} Tz')
            ops.append(self._encode_shaped_text(pdf, text_to_render))

            prev_x_baseline = x_baseline

        # End text object
        ops.append('ET')

        if has_rotation:
            ops.append('Q')

        pdf._out('\n'.join(ops))

        # Reset fpdf2's internal stretching tracking so subsequent API calls
        # don't think Tz is still set from our raw operators
        pdf.font_stretching = 100

    def _encode_shaped_text(self, pdf: FPDF, text: str) -> str:
        """Encode text using HarfBuzz text shaping for complex script support.

        Unlike font.encode_text() which maps unicode characters one-by-one to
        glyph IDs, this uses HarfBuzz to handle BiDi reordering, Arabic joining
        forms, Devanagari conjuncts, and other complex script shaping. Falls
        back to encode_text() when text shaping is not enabled.
        """
        font = pdf.current_font
        if pdf.text_shaping and pdf.text_shaping.get("use_shaping_engine"):
            shaped = font.shape_text(text, pdf.font_size_pt, pdf.text_shaping)
            if shaped:
                mapped = "".join(
                    chr(ti["mapped_char"])
                    for ti in shaped
                    if ti["mapped_char"] is not None
                )
                if mapped:
                    return f"({font.escape_text(mapped)}) Tj"
        return font.encode_text(text)

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
            pdf.text_mode = TextMode.INVISIBLE
        else:
            pdf.text_mode = TextMode.FILL

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
