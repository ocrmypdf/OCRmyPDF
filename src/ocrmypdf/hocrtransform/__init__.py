# SPDX-FileCopyrightText: 2023-2025 James R. Barlow
# SPDX-License-Identifier: MIT

"""Transform OCR output to text-only PDFs.

This package provides tools for:
1. Parsing OCR output (hOCR format) into generic OcrElement structures
2. Rendering OcrElement structures to searchable PDF text layers

The architecture separates parsing from rendering, allowing:
- Support for multiple OCR input formats (hOCR, ALTO, custom engines)
- Independent improvements to text rendering
- Reuse of the OcrElement data model for other purposes

Main components:
- OcrElement: Generic dataclass representing OCR output structure
- HocrParser: Parses hOCR files into OcrElement trees
- Fpdf2PdfRenderer: Renders OcrElement trees to PDF text layers (via fpdf2)

For PDF rendering, use the fpdf2_renderer module:
    from ocrmypdf.fpdf_renderer import Fpdf2PdfRenderer, DebugRenderOptions
"""

from __future__ import annotations

from ocrmypdf.hocrtransform.hocr_parser import (
    HocrParseError,
    HocrParser,
)
from ocrmypdf.models.ocr_element import (
    Baseline,
    BoundingBox,
    FontInfo,
    OcrClass,
    OcrElement,
)

__all__ = (
    # hOCR parsing
    'HocrParser',
    'HocrParseError',
    # OCR element data model
    'OcrElement',
    'OcrClass',
    'BoundingBox',
    'Baseline',
    'FontInfo',
)
