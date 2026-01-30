# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Built-in plugin implementing a null OCR engine (no OCR).

This plugin provides an OCR engine that produces no text output. It is useful
when users want OCRmyPDF's image processing, PDF/A conversion, or optimization
features without performing actual OCR.

Usage:
    ocrmypdf --ocr-engine none input.pdf output.pdf
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from ocrmypdf import hookimpl
from ocrmypdf.hocrtransform import BoundingBox, OcrClass, OcrElement
from ocrmypdf.pluginspec import OcrEngine, OrientationConfidence

if TYPE_CHECKING:
    from ocrmypdf._options import OcrOptions


class NullOcrEngine(OcrEngine):
    """A no-op OCR engine that produces no text output.

    Use this when you want OCRmyPDF's image processing, PDF/A conversion,
    or optimization features without performing actual OCR.
    """

    @staticmethod
    def version() -> str:
        """Return version string."""
        return "none"

    @staticmethod
    def creator_tag(options: OcrOptions) -> str:
        """Return creator tag for PDF metadata."""
        return "OCRmyPDF (no OCR)"

    def __str__(self) -> str:
        """Return human-readable engine name."""
        return "No OCR engine"

    @staticmethod
    def languages(options: OcrOptions) -> set[str]:
        """Return supported languages (empty set for null engine)."""
        return set()

    @staticmethod
    def get_orientation(input_file: Path, options: OcrOptions) -> OrientationConfidence:
        """Return neutral orientation (no rotation detected)."""
        return OrientationConfidence(angle=0, confidence=0.0)

    @staticmethod
    def get_deskew(input_file: Path, options: OcrOptions) -> float:
        """Return zero deskew angle."""
        return 0.0

    @staticmethod
    def supports_generate_ocr() -> bool:
        """Return True - this engine supports the generate_ocr() API."""
        return True

    @staticmethod
    def generate_ocr(
        input_file: Path,
        options: OcrOptions,
        page_number: int = 0,
    ) -> tuple[OcrElement, str]:
        """Generate empty OCR results.

        Args:
            input_file: The image file (used to get dimensions).
            options: OCR options (ignored).
            page_number: Page number (stored in result).

        Returns:
            A tuple of (empty OcrElement page, empty string).
        """
        # Get image dimensions
        with Image.open(input_file) as img:
            width, height = img.size
            dpi_info = img.info.get('dpi', (72, 72))
            dpi = dpi_info[0] if isinstance(dpi_info, tuple) else dpi_info

        # Create empty page element with correct dimensions
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=width, bottom=height),
            dpi=float(dpi),
            page_number=page_number,
        )

        return page, ""

    @staticmethod
    def generate_hocr(
        input_file: Path,
        output_hocr: Path,
        output_text: Path,
        options: OcrOptions,
    ) -> None:
        """Generate empty hOCR file.

        Creates minimal valid hOCR output with no text content.
        """
        # Get image dimensions for hOCR bbox
        with Image.open(input_file) as img:
            width, height = img.size

        hocr_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <title>OCRmyPDF - No OCR</title>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
    <meta name='ocr-system' content='OCRmyPDF null engine'/>
</head>
<body>
    <div class='ocr_page' title='bbox 0 0 {width} {height}'>
    </div>
</body>
</html>
'''
        output_hocr.write_text(hocr_content, encoding='utf-8')
        output_text.write_text('', encoding='utf-8')

    @staticmethod
    def generate_pdf(
        input_file: Path,
        output_pdf: Path,
        output_text: Path,
        options: OcrOptions,
    ) -> None:
        """NullOcrEngine cannot generate PDFs directly.

        Use pdf_renderer='fpdf2' instead of 'sandwich'.
        """
        raise NotImplementedError(
            "NullOcrEngine cannot generate PDFs directly. "
            "Use --pdf-renderer fpdf2 instead of sandwich mode."
        )


@hookimpl
def get_ocr_engine(options):
    """Return NullOcrEngine when --ocr-engine none is selected."""
    if options is not None:
        ocr_engine = getattr(options, 'ocr_engine', 'auto')
        if ocr_engine != 'none':
            return None
    return NullOcrEngine()
