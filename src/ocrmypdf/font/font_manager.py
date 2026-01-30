# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Base font management for PDF rendering.

This module provides the base FontManager class that handles font loading
and glyph checking using uharfbuzz.
"""

from __future__ import annotations

from pathlib import Path

import uharfbuzz as hb


class FontManager:
    """Manages font loading and glyph checking for PDF rendering.

    This base class handles loading fonts with uharfbuzz for glyph checking
    and text shaping. Renderer-specific subclasses should extend this to
    add their own font objects.

    Attributes:
        font_path: Path to the font file
        font_data: Raw font file bytes
        font_index: Index within TTC collection (0 for single-font files)
        hb_face: uharfbuzz Face object
        hb_font: uharfbuzz Font object
    """

    def __init__(self, font_path: Path, font_index: int = 0):
        """Initialize font manager.

        Args:
            font_path: Path to TrueType/OpenType font file
            font_index: Index of font within a TTC collection (default 0).
                        For single-font files (.ttf, .otf), use 0.
        """
        self.font_path = font_path
        self.font_index = font_index

        # Load font data
        self.font_data = font_path.read_bytes()

        # Load font with uharfbuzz for glyph checking and text measurement
        # Note: uharfbuzz Face also supports font_index for TTC files
        self.hb_face = hb.Face(self.font_data, font_index)
        self.hb_font = hb.Font(self.hb_face)

    def get_hb_font(self) -> hb.Font:
        """Get uharfbuzz Font object for text measurement.

        Returns:
            UHarfBuzz Font instance
        """
        return self.hb_font

    def has_glyph(self, codepoint: int) -> bool:
        """Check if font has a glyph for given codepoint.

        Args:
            codepoint: Unicode codepoint

        Returns:
            True if font has a real glyph (not .notdef)
        """
        glyph_id = self.hb_font.get_nominal_glyph(codepoint)
        return glyph_id is not None and glyph_id != 0

    def get_font_metrics(self) -> tuple[float, float, float]:
        """Get normalized font metrics (ascent, descent, units_per_em).

        Returns:
            Tuple of (ascent, descent, units_per_em) where ascent and descent
            are in font units. Ascent is positive (above baseline), descent
            is typically negative (below baseline).
        """
        extents = self.hb_font.get_font_extents('ltr')
        units_per_em = self.hb_face.upem
        return (extents.ascender, extents.descender, units_per_em)

    def get_left_side_bearing(self, char: str, font_size: float) -> float:
        """Get the left side bearing of a character at a given font size.

        The left side bearing (lsb) is the horizontal distance from the glyph
        origin (x=0) to the leftmost pixel of the glyph. A positive lsb means
        there's whitespace before the glyph starts.

        Args:
            char: Single character to get lsb for
            font_size: Font size in points

        Returns:
            Left side bearing in points. Returns 0 if character not found.
        """
        if not char:
            return 0.0

        codepoint = ord(char)
        glyph_id = self.hb_font.get_nominal_glyph(codepoint)
        if glyph_id is None or glyph_id == 0:
            return 0.0

        # Get glyph extents which include left/right bearing info
        extents = self.hb_font.get_glyph_extents(glyph_id)
        if extents is None:
            return 0.0

        # x_bearing is the left side bearing in font units
        units_per_em = self.hb_face.upem
        lsb_units = extents.x_bearing
        lsb_pt = lsb_units * font_size / units_per_em

        return lsb_pt
