#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Generate the Occulta glyphless font for OCRmyPDF.

Occulta (Latin for "hidden") is a glyphless font designed for invisible text layers
in searchable PDFs. It has proper Unicode cmap coverage using format 13 (many-to-one)
for efficient mapping of all BMP codepoints to a small set of width-specific glyphs.

Features:
- Full BMP coverage (U+0000 to U+FFFF)
- Width-aware glyphs for proper text selection:
  - Zero-width for combining marks and invisible characters
  - Regular width (500 units) for Latin, Greek, Cyrillic, Arabic, Hebrew, etc.
  - Double width (1000 units) for CJK and fullwidth characters
- Uses cmap format 13 (many-to-one) for ~12KB size vs ~780KB with format 12
- Compatible with fpdf2 and other modern PDF libraries

Usage:
    python scripts/generate_glyphless_font.py

Output:
    src/ocrmypdf/data/Occulta.ttf
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib.tables._g_l_y_f import Glyph

# Output path relative to this script
OUTPUT_PATH = Path(__file__).parent.parent / "src" / "ocrmypdf" / "data" / "Occulta.ttf"

# Font metrics (units per em = 1000)
UNITS_PER_EM = 1000
ASCENT = 800
DESCENT = -200

# Glyph definitions: (name, advance_width, left_side_bearing)
GLYPHS = [
    (".notdef", 500, 0),  # Required, used for unmapped characters
    ("space", 500, 0),  # U+0020 SPACE
    ("nbspace", 500, 0),  # U+00A0 NO-BREAK SPACE
    ("blank0", 0, 0),  # Zero-width (combining marks, ZWNJ, ZWJ, BOM)
    ("blank1", 500, 0),  # Regular width (most scripts)
    ("blank2", 1000, 0),  # Double width (CJK, fullwidth)
]

# Explicit zero-width character codepoints
ZERO_WIDTH_CHARS = frozenset(
    [
        0x200B,  # ZERO WIDTH SPACE
        0x200C,  # ZERO WIDTH NON-JOINER
        0x200D,  # ZERO WIDTH JOINER
        0xFEFF,  # ZERO WIDTH NO-BREAK SPACE (BOM)
        0x200E,  # LEFT-TO-RIGHT MARK
        0x200F,  # RIGHT-TO-LEFT MARK
        0x202A,  # LEFT-TO-RIGHT EMBEDDING
        0x202B,  # RIGHT-TO-LEFT EMBEDDING
        0x202C,  # POP DIRECTIONAL FORMATTING
        0x202D,  # LEFT-TO-RIGHT OVERRIDE
        0x202E,  # RIGHT-TO-LEFT OVERRIDE
        0x2060,  # WORD JOINER
        0x2061,  # FUNCTION APPLICATION
        0x2062,  # INVISIBLE TIMES
        0x2063,  # INVISIBLE SEPARATOR
        0x2064,  # INVISIBLE PLUS
    ]
)


def classify_codepoint(codepoint: int) -> str:
    """Classify a Unicode codepoint into one of our glyph categories.

    Args:
        codepoint: Unicode codepoint (0x0000 to 0xFFFF)

    Returns:
        Glyph name to map this codepoint to
    """
    # Special cases first
    if codepoint == 0x0020:
        return "space"
    if codepoint == 0x00A0:
        return "nbspace"
    if codepoint in ZERO_WIDTH_CHARS:
        return "blank0"

    # Use Unicode properties for the rest
    char = chr(codepoint)
    try:
        category = unicodedata.category(char)
        east_asian_width = unicodedata.east_asian_width(char)

        # Combining marks are zero-width
        if category.startswith("M"):
            return "blank0"

        # Wide and Fullwidth characters are double-width
        if east_asian_width in ("W", "F"):
            return "blank2"

        # Everything else is regular width
        return "blank1"

    except (ValueError, TypeError):
        # Fallback for any edge cases
        return "blank1"


def build_cmap() -> dict[int, str]:
    """Build the Unicode to glyph name mapping for the entire BMP.

    Returns:
        Dictionary mapping codepoints to glyph names
    """
    return {cp: classify_codepoint(cp) for cp in range(0x10000)}


def create_font() -> TTFont:
    """Create the Occulta glyphless font.

    Returns:
        TTFont object ready to be saved
    """
    glyph_names = [g[0] for g in GLYPHS]

    # Start building the font
    fb = FontBuilder(UNITS_PER_EM, isTTF=True)
    fb.setupGlyphOrder(glyph_names)

    # Create empty (invisible) glyphs
    glyphs = {}
    for name, _, _ in GLYPHS:
        glyph = Glyph()
        glyph.numberOfContours = 0
        glyphs[name] = glyph
    fb.setupGlyf(glyphs)

    # Set up horizontal metrics
    metrics = {name: (width, lsb) for name, width, lsb in GLYPHS}
    fb.setupHorizontalMetrics(metrics)

    # Minimal cmap to satisfy FontBuilder (we'll replace it later)
    fb.setupCharacterMap({0x0020: "space", 0x00A0: "nbspace"})

    # Set up other required tables
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=DESCENT,
        sTypoLineGap=0,
        usWinAscent=UNITS_PER_EM,
        usWinDescent=abs(DESCENT),
        sxHeight=500,
        sCapHeight=700,
    )
    import time

    # Use current time for font timestamps
    now = int(time.time())
    fb.setupHead(unitsPerEm=UNITS_PER_EM, created=now, modified=now)
    fb.setupPost()
    fb.setupNameTable(
        {
            "familyName": "Occulta",
            "styleName": "Regular",
            "uniqueFontIdentifier": "OCRmyPDF;Occulta-Regular;2026",
            "fullName": "Occulta Regular",
            "version": "Version 2.0",
            "psName": "Occulta-Regular",
        }
    )

    # Build the font
    font = fb.font

    # Now replace the cmap with format 13 for efficient many-to-one mapping
    char_to_glyph = build_cmap()

    cmap13 = CmapSubtable.newSubtable(13)
    cmap13.platformID = 3  # Windows
    cmap13.platEncID = 10  # Unicode full repertoire
    cmap13.language = 0
    cmap13.cmap = char_to_glyph

    font["cmap"].tables = [cmap13]

    return font


def main() -> None:
    """Generate the Occulta font and save it."""
    print("Generating Occulta glyphless font...")

    font = create_font()

    # Create output directory if needed
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save the font
    font.save(str(OUTPUT_PATH))
    font.close()

    # Report statistics
    size = OUTPUT_PATH.stat().st_size
    print(f"Saved to: {OUTPUT_PATH}")
    print(f"Size: {size:,} bytes")

    # Verify cmap
    font = TTFont(str(OUTPUT_PATH))
    for table in font["cmap"].tables:
        print(
            f"cmap: Platform {table.platformID}, "
            f"Encoding {table.platEncID}, "
            f"Format {table.format}, "
            f"{len(table.cmap)} mappings"
        )
    font.close()

    print("Done!")


if __name__ == "__main__":
    main()
