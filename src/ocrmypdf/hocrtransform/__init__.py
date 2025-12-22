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
- PdfTextRenderer: Renders OcrElement trees to PDF text layers
- HocrTransform: Backward-compatible wrapper combining parser and renderer
"""

from __future__ import annotations

from ocrmypdf.hocrtransform._hocr import (
    HocrTransform,
    HocrTransformError,
)
from ocrmypdf.hocrtransform.hocr_parser import (
    HocrParseError,
    HocrParser,
)
from ocrmypdf.hocrtransform.ocr_element import (
    Baseline,
    BoundingBox,
    FontInfo,
    OcrClass,
    OcrElement,
)
from ocrmypdf.hocrtransform.pdf_renderer import (
    DebugRenderOptions,
    PdfTextRenderer,
)

__all__ = (
    # Backward-compatible API
    'HocrTransform',
    'HocrTransformError',
    'DebugRenderOptions',
    # New separated components
    'HocrParser',
    'HocrParseError',
    'PdfTextRenderer',
    # OCR element data model
    'OcrElement',
    'OcrClass',
    'BoundingBox',
    'Baseline',
    'FontInfo',
)
