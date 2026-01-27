# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""fpdf2-based PDF renderer for OCR text layers.

This module provides the PDF renderer using fpdf2 for creating
searchable OCR text layers.
"""
from __future__ import annotations

from ocrmypdf.fpdf_renderer.renderer import (
    DebugRenderOptions,
    Fpdf2MultiPageRenderer,
    Fpdf2PdfRenderer,
)

__all__ = [
    "DebugRenderOptions",
    "Fpdf2PdfRenderer",
    "Fpdf2MultiPageRenderer",
]
