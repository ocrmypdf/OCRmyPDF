# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Structural tests for the bundled glyphless font, Occulta."""

from __future__ import annotations

from pathlib import Path

import pytest
from fontTools.pens.areaPen import AreaPen  # type: ignore[import-untyped]
from fontTools.ttLib import TTFont  # type: ignore[import-untyped]
from fpdf import FPDF

OCCULTA = Path(__file__).parent.parent / "src" / "ocrmypdf" / "data" / "Occulta.ttf"

# Glyphs that stay empty, as in ordinary fonts
EMPTY_GLYPHS = {'space', 'nbspace'}


@pytest.fixture(scope='module')
def font():
    with TTFont(OCCULTA) as font:
        # Force every table to decompile so malformed data fails here
        for tag in font.keys():
            font[tag]
        yield font


def _glyph(font, name):
    glyph = font['glyf'][name]
    glyph.recalcBounds(font['glyf'])
    return glyph


def test_font_metrics_consistent(font):
    hhea = font['hhea']
    os2 = font['OS/2']
    assert (hhea.ascent, hhea.descent) == (800, -200)
    assert (os2.sTypoAscender, os2.sTypoDescender) == (hhea.ascent, hhea.descent)
    assert font['head'].unitsPerEm == 1000


def test_version_consistent(font):
    revision = font['head'].fontRevision
    version_string = font['name'].getDebugName(5)
    assert version_string == f"Version {revision:.3f}"


def test_not_installable(font):
    # Preview & Print embedding only, to discourage installing a font that
    # draws nothing as a system font
    assert font['OS/2'].fsType == 4


def test_no_hinting(font):
    for tag in ('fpgm', 'prep', 'cvt '):
        assert tag not in font
    for name in font.getGlyphOrder():
        glyph = _glyph(font, name)
        assert not getattr(glyph, 'program', None) or not glyph.program.getBytecode()


@pytest.mark.parametrize(
    'char, width',
    [
        ('A', 500),
        ('א', 500),  # HEBREW LETTER ALEF
        ('क', 500),  # DEVANAGARI LETTER KA
        ('男', 1000),  # CJK ideograph
        ('あ', 1000),  # HIRAGANA LETTER A
        ('Ａ', 1000),  # FULLWIDTH LATIN CAPITAL LETTER A
        ('́', 0),  # COMBINING ACUTE ACCENT
        ('゙', 0),  # COMBINING KATAKANA-HIRAGANA VOICED SOUND MARK
        ('​', 0),  # ZERO WIDTH SPACE
        ('﻿', 0),  # ZERO WIDTH NO-BREAK SPACE
        (' ', 500),
        (' ', 500),
    ],
)
def test_character_class_widths(font, char, width):
    cmap = font.getBestCmap()
    glyph_name = cmap[ord(char)]
    assert font['hmtx'][glyph_name][0] == width


def test_whole_bmp_mapped(font):
    cmap = font.getBestCmap()
    assert all(cp in cmap for cp in range(0x10000))


def test_glyphs_have_zero_area_extent(font):
    """Each glyph spans its advance and the font's ascent to descent.

    PDF viewers such as pdfium derive character boxes from glyph outlines and
    drop characters without one, so every glyph carries an outline. The
    outline is two isolated points at opposite corners of the glyph cell,
    which has no edges to fill, stroke or trigger dropout control.
    """
    hhea = font['hhea']
    glyph_set = font.getGlyphSet()
    checked = 0
    for name in font.getGlyphOrder():
        advance, lsb = font['hmtx'][name]
        glyph = _glyph(font, name)
        if name in EMPTY_GLYPHS:
            assert glyph.numberOfContours == 0
            continue
        coords, end_pts, flags = glyph.getCoordinates(font['glyf'])
        assert list(end_pts) == [0, 1], name  # two single-point contours
        assert all(flag & 1 for flag in flags), name  # on-curve points only
        assert (glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax) == (
            0,
            hhea.descent,
            advance,
            hhea.ascent,
        ), name
        assert lsb == glyph.xMin
        pen = AreaPen(glyph_set)
        glyph_set[name].draw(pen)
        assert pen.value == 0, name
        checked += 1
    assert checked == len(font.getGlyphOrder()) - len(EMPTY_GLYPHS)


@pytest.mark.parametrize('scale', [1, 3])
@pytest.mark.parametrize('smooth', [True, False], ids=['smooth', 'aliased'])
def test_fill_mode_text_is_blank(scale, smooth, tmp_path):
    """Occulta paints nothing even when its text is not invisible.

    Monochrome rasterizers apply dropout control to zero-width features, so a
    degenerate line segment would still be drawn as a hairline.
    """
    pdfium = pytest.importorskip('pypdfium2')
    text = "男その hello \u0915\u093f \u304b\u3099 x\u200by"
    pdf = FPDF(unit='pt', format=(400, 200))
    pdf.add_page()
    pdf.add_font('Occulta', fname=OCCULTA)
    for y, size in [(40, 6), (80, 9), (140, 40)]:
        pdf.set_font('Occulta', size=size)
        pdf.text(10, y, text)
    output = tmp_path / 'fill.pdf'
    pdf.output(output)

    image = pdfium.PdfDocument(output)[0].render(
        scale=scale, no_smoothtext=not smooth, no_smoothpath=not smooth
    )
    assert image.to_pil().convert('L').getextrema() == (255, 255)
