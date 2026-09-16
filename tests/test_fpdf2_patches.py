# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for the runtime patches OCRmyPDF applies to fpdf2."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pikepdf
import pytest
from fpdf import FPDF

from ocrmypdf.font import MultiFontManager
from ocrmypdf.fpdf_renderer import Fpdf2PdfRenderer
from ocrmypdf.fpdf_renderer.fpdf2_patches import (
    CMAP_BLOCK_LIMIT,
    install_fpdf2_patches,
    split_cmap_blocks,
)
from ocrmypdf.models.ocr_element import BoundingBox, OcrClass, OcrElement

FONT_DIR = Path(__file__).parent.parent / "src" / "ocrmypdf" / "data"
NOTO_SANS = FONT_DIR / "NotoSans-Regular.ttf"
# CFF CID-keyed OpenType font: fpdf2 writes its Encoding CMap as cidchar blocks
NOTO_CJK = Path(__file__).parent / "resources" / "NotoSansCJKjp-Medium-subset.otf"

# Enough distinct printable glyphs, all in NotoSans, to exceed the 100-entry
# limit on a bfchar block.
MANY_CHARS = "".join(chr(c) for c in range(0x21, 0x7F)) + "".join(
    chr(c) for c in range(0xA1, 0xFF)
)
MANY_CJK_CHARS = "".join(chr(c) for c in range(0x4E00, 0x4E00 + 180))

CMAP_HEADER = (
    "/CIDInit /ProcSet findresource begin\n"
    "12 dict begin\n"
    "begincmap\n"
    "/CIDSystemInfo\n"
    "<</Registry (Adobe)\n"
    "/Ordering (UCS)\n"
    "/Supplement 0\n"
    ">> def\n"
    "/CMapName /Adobe-Identity-UCS def\n"
    "/CMapType 2 def\n"
    "1 begincodespacerange\n"
    "<0000> <FFFF>\n"
    "endcodespacerange\n"
)
CMAP_FOOTER = "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend"


def _cmap_with_bfchar_entries(n: int) -> bytes:
    entries = "".join(f"<{i:04X}> <{0x21 + i:04X}>\n" for i in range(n))
    return (f"{CMAP_HEADER}{n} beginbfchar\n{entries}endbfchar\n{CMAP_FOOTER}").encode(
        "latin-1"
    )


def _bfchar_block_sizes(cmap: bytes) -> list[int]:
    """Return the declared entry count of every bfchar block in a CMap."""
    return [int(n) for n in re.findall(rb"(\d+) beginbfchar\n", cmap)]


def _bfchar_entries(cmap: bytes) -> list[bytes]:
    """Return every mapping line inside any bfchar block, in order."""
    bodies = re.findall(rb"\d+ beginbfchar\n(.*?)endbfchar\n", cmap, flags=re.DOTALL)
    return [line for body in bodies for line in body.split(b"\n") if line]


def _mapping_entries(cmap: bytes) -> list[bytes]:
    """Return every mapping line inside any bfchar or bfrange block."""
    bodies = re.findall(
        rb"\d+ begin(bfchar|bfrange)\n(.*?)end\1\n", cmap, flags=re.DOTALL
    )
    return [line for _kind, body in bodies for line in body.split(b"\n") if line]


def _block_sizes(cmap: bytes, kind: str) -> list[int]:
    return [int(n) for n in re.findall(rb"(\d+) begin" + kind.encode(), cmap)]


def _encoding_cmaps(pdf_path: Path) -> list[bytes]:
    with pikepdf.open(pdf_path) as pdf:
        return [
            obj.Encoding.read_bytes()
            for obj in pdf.objects
            if isinstance(obj, pikepdf.Dictionary)
            and obj.get('/Type') == '/Font'
            and isinstance(obj.get('/Encoding'), pikepdf.Stream)
        ]


def _tounicode_cmaps(pdf_path: Path) -> list[bytes]:
    with pikepdf.open(pdf_path) as pdf:
        return [
            obj.ToUnicode.read_bytes()
            for obj in pdf.objects
            if isinstance(obj, pikepdf.Dictionary)
            and obj.get('/Type') == '/Font'
            and '/ToUnicode' in obj
        ]


class TestSplitCmapBlocks:
    def test_over_limit_is_chunked(self):
        original = _cmap_with_bfchar_entries(117)
        result = split_cmap_blocks(original)

        assert _bfchar_block_sizes(result) == [CMAP_BLOCK_LIMIT, 17]
        assert _bfchar_entries(result) == _bfchar_entries(original)
        assert result.startswith(CMAP_HEADER.encode("latin-1"))
        assert result.endswith(CMAP_FOOTER.encode("latin-1"))
        # Each declared count must match the entries physically in the block
        for count, body in re.findall(
            rb"(\d+) beginbfchar\n(.*?)endbfchar\n", result, flags=re.DOTALL
        ):
            assert int(count) == len(body.strip(b"\n").split(b"\n"))

    def test_exact_multiple_of_limit(self):
        result = split_cmap_blocks(_cmap_with_bfchar_entries(200))
        assert _bfchar_block_sizes(result) == [100, 100]

    def test_within_limit_is_unchanged(self):
        original = _cmap_with_bfchar_entries(92)
        assert split_cmap_blocks(original) == original

    def test_empty_block_is_unchanged(self):
        original = _cmap_with_bfchar_entries(0)
        assert split_cmap_blocks(original) == original

    def test_bfrange_is_also_chunked(self):
        entries = "".join(f"<{i:04X}> <{i:04X}> <{0x21 + i:04X}>\n" for i in range(150))
        original = (
            f"{CMAP_HEADER}150 beginbfrange\n{entries}endbfrange\n{CMAP_FOOTER}"
        ).encode("latin-1")
        result = split_cmap_blocks(original)
        assert re.findall(rb"(\d+) beginbfrange\n", result) == [b"100", b"50"]

    def test_cidchar_is_also_chunked(self):
        entries = "".join(f"<{i:04X}> {i + 1}\n" for i in range(182))
        original = (
            f"{CMAP_HEADER}182 begincidchar\n{entries}endcidchar\n{CMAP_FOOTER}"
        ).encode("latin-1")
        result = split_cmap_blocks(original)
        assert _block_sizes(result, "cidchar") == [100, 82]
        assert result.count(b"endcidchar\n") == 2

    def test_non_cmap_content_is_unchanged(self):
        content = b"BT /F1 12 Tf (Hello) Tj ET"
        assert split_cmap_blocks(content) == content


class TestFpdf2Output:
    def test_install_is_idempotent(self):
        from fpdf.output import OutputProducer

        install_fpdf2_patches()
        first = OutputProducer._add_pdf_obj
        install_fpdf2_patches()
        assert OutputProducer._add_pdf_obj is first

    def test_composite_font_tounicode_blocks_limited(self, tmp_path):
        pdf = FPDF()
        pdf.add_font("noto", "", NOTO_SANS)
        pdf.set_font("noto", "", 8)
        pdf.add_page()
        pdf.multi_cell(0, 4, MANY_CHARS)
        out = tmp_path / "many.pdf"
        pdf.output(out)

        cmaps = _tounicode_cmaps(out)
        assert cmaps
        for cmap in cmaps:
            sizes = _bfchar_block_sizes(cmap)
            assert sizes, "ToUnicode has no bfchar block"
            assert max(sizes) <= CMAP_BLOCK_LIMIT
            assert sum(sizes) == len(_bfchar_entries(cmap)) > CMAP_BLOCK_LIMIT

    def test_cff_cid_font_encoding_blocks_limited(self, tmp_path):
        """The Encoding CMap of a CFF CID-keyed font is split too.

        fpdf2 2.8.9 splits ToUnicode blocks but not this one.
        """
        pdf = FPDF()
        pdf.add_font("cjk", "", NOTO_CJK)
        pdf.set_font("cjk", "", 10)
        pdf.add_page()
        pdf.multi_cell(0, 6, MANY_CJK_CHARS)
        out = tmp_path / "cjk.pdf"
        pdf.output(out)

        encodings = _encoding_cmaps(out)
        assert encodings, "expected a CMap stream as /Encoding for a CFF CID font"
        for cmap in encodings:
            sizes = _block_sizes(cmap, "cidchar")
            assert max(sizes) <= CMAP_BLOCK_LIMIT
            assert sum(sizes) > CMAP_BLOCK_LIMIT
        for cmap in _tounicode_cmaps(out):
            assert max(_bfchar_block_sizes(cmap)) <= CMAP_BLOCK_LIMIT

    def test_renderer_tounicode_blocks_limited(self, tmp_path):
        words = [
            OcrElement(
                ocr_class=OcrClass.WORD,
                text=MANY_CHARS[i : i + 10],
                bbox=BoundingBox(
                    left=50, top=50 + 20 * n, right=250, bottom=65 + 20 * n
                ),
            )
            for n, i in enumerate(range(0, len(MANY_CHARS), 10))
        ]
        lines = [
            OcrElement(ocr_class=OcrClass.LINE, bbox=w.bbox, children=[w])
            for w in words
        ]
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
            children=lines,
        )
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72, multi_font_manager=MultiFontManager(FONT_DIR)
        )
        out = tmp_path / "renderer.pdf"
        renderer.render(out)

        cmaps = _tounicode_cmaps(out)
        assert cmaps
        for cmap in cmaps:
            assert max(_bfchar_block_sizes(cmap)) <= CMAP_BLOCK_LIMIT
        assert any(len(_bfchar_entries(c)) > CMAP_BLOCK_LIMIT for c in cmaps)


def _run_gs_pdfa(src: Path, out: Path) -> None:
    subprocess.run(
        [
            'gs',
            '-dBATCH',
            '-dNOPAUSE',
            '-dSAFER',
            '-sDEVICE=pdfwrite',
            '-dPDFA=2',
            '-dPDFACompatibilityPolicy=1',
            f'-sOutputFile={out}',
            str(src),
        ],
        check=True,
        capture_output=True,
    )


@pytest.mark.skipif(shutil.which('gs') is None, reason="Ghostscript not installed")
@pytest.mark.parametrize(
    'font_path, text, expected',
    [
        (NOTO_SANS, MANY_CHARS, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        (NOTO_CJK, MANY_CJK_CHARS, MANY_CJK_CHARS[:20]),
    ],
    ids=['truetype', 'cff_cid'],
)
def test_ghostscript_pdfwrite_keeps_text(tmp_path, font_path, text, expected):
    """Ghostscript pdfwrite keeps CMaps with more than 100 entries.

    Ghostscript 9.56 through 10.04 discard a CMap with an oversized block. For
    a ToUnicode CMap the text layer becomes unextractable; for the Encoding
    CMap of a CFF CID-keyed font the wrong glyphs are drawn as well.
    """
    pdf = FPDF()
    pdf.add_font("f", "", font_path)
    pdf.set_font("f", "", 8)
    pdf.add_page()
    pdf.multi_cell(0, 4, text)
    src = tmp_path / "many.pdf"
    pdf.output(src)

    out = tmp_path / "gs.pdf"
    _run_gs_pdfa(src, out)

    cmaps = _tounicode_cmaps(out)
    assert cmaps, "Ghostscript dropped the ToUnicode CMap"
    assert sum(len(_mapping_entries(c)) for c in cmaps) > CMAP_BLOCK_LIMIT

    if shutil.which('pdftotext'):
        extracted = subprocess.check_output(
            ['pdftotext', '-enc', 'UTF-8', str(out), '-'], text=True
        )
        assert expected in extracted.replace("\n", "")
