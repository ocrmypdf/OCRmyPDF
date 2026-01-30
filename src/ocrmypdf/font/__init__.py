# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Font management for OCRmyPDF PDF rendering.

This module provides font infrastructure for the fpdf2 PDF renderer. It includes:

- FontManager: Base class for font loading and glyph checking
- FontProvider: Protocol and implementations for font discovery
- MultiFontManager: Automatic font selection for multilingual documents
- SystemFontProvider: System font discovery
"""
from __future__ import annotations

from ocrmypdf.font.font_manager import FontManager
from ocrmypdf.font.font_provider import (
    BuiltinFontProvider,
    ChainedFontProvider,
    FontProvider,
)
from ocrmypdf.font.multi_font_manager import MultiFontManager
from ocrmypdf.font.system_font_provider import SystemFontProvider

__all__ = [
    "FontManager",
    "FontProvider",
    "BuiltinFontProvider",
    "ChainedFontProvider",
    "MultiFontManager",
    "SystemFontProvider",
]
