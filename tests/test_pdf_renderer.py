# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for Fpdf2PdfRenderer class."""

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path

import pikepdf
import pytest
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from ocrmypdf.font import MultiFontManager
from ocrmypdf.fpdf_renderer import DebugRenderOptions, Fpdf2PdfRenderer
from ocrmypdf.helpers import check_pdf
from ocrmypdf.hocrtransform import (
    Baseline,
    BoundingBox,
    OcrClass,
    OcrElement,
)


def text_from_pdf(filename: Path) -> str:
    """Extract text from a PDF file using pdfminer."""
    output_string = StringIO()
    with open(filename, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    return output_string.getvalue()


@pytest.fixture
def font_dir():
    """Get the font directory."""
    return Path(__file__).parent.parent / "src" / "ocrmypdf" / "data"


@pytest.fixture
def multi_font_manager(font_dir):
    """Create a MultiFontManager for tests."""
    return MultiFontManager(font_dir)


def create_simple_page(
    width: float = 1000,
    height: float = 500,
    words: list[tuple[str, tuple[float, float, float, float]]] | None = None,
) -> OcrElement:
    """Create a simple OcrElement page for testing.

    Args:
        width: Page width in pixels
        height: Page height in pixels
        words: List of (text, (left, top, right, bottom)) tuples

    Returns:
        OcrElement representing the page
    """
    if words is None:
        words = [("Hello", (100, 100, 200, 150)), ("World", (250, 100, 350, 150))]

    word_elements = [
        OcrElement(
            ocr_class=OcrClass.WORD,
            text=text,
            bbox=BoundingBox(left=bbox[0], top=bbox[1], right=bbox[2], bottom=bbox[3]),
        )
        for text, bbox in words
    ]

    line = OcrElement(
        ocr_class=OcrClass.LINE,
        bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
        baseline=Baseline(slope=0.0, intercept=0),
        children=word_elements,
    )

    paragraph = OcrElement(
        ocr_class=OcrClass.PARAGRAPH,
        bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
        direction="ltr",
        language="eng",
        children=[line],
    )

    page = OcrElement(
        ocr_class=OcrClass.PAGE,
        bbox=BoundingBox(left=0, top=0, right=width, bottom=height),
        children=[paragraph],
    )

    return page


class TestFpdf2PdfRendererBasic:
    """Basic Fpdf2PdfRenderer functionality tests."""

    def test_render_simple_page(self, tmp_path, multi_font_manager):
        """Test rendering a simple page with two words."""
        page = create_simple_page()
        output_pdf = tmp_path / "simple.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()
        check_pdf(str(output_pdf))

    def test_rendered_text_extractable(self, tmp_path, multi_font_manager):
        """Test that rendered text can be extracted from the PDF."""
        page = create_simple_page()
        output_pdf = tmp_path / "extractable.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text
        assert "World" in extracted_text

    def test_invisible_text_mode(self, tmp_path, multi_font_manager):
        """Test that invisible_text=True creates a valid PDF."""
        page = create_simple_page()
        output_pdf = tmp_path / "invisible.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=True,
        )
        renderer.render(output_pdf)

        # Text should still be extractable even when invisible
        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text

    def test_visible_text_mode(self, tmp_path, multi_font_manager):
        """Test that invisible_text=False creates a valid PDF with visible text."""
        page = create_simple_page()
        output_pdf = tmp_path / "visible.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )
        renderer.render(output_pdf)

        # Text should be extractable
        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text


class TestFpdf2PdfRendererPageSize:
    """Test page size calculations."""

    def test_page_dimensions(self, tmp_path, multi_font_manager):
        """Test that page dimensions are calculated correctly."""
        # 1000x500 pixels at 72 dpi = 1000x500 points
        page = create_simple_page(width=1000, height=500)
        output_pdf = tmp_path / "dimensions.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        assert renderer.coord_transform.page_width_pt == pytest.approx(1000.0)
        assert renderer.coord_transform.page_height_pt == pytest.approx(500.0)

        renderer.render(output_pdf)

    def test_high_dpi_page(self, tmp_path, multi_font_manager):
        """Test page dimensions at higher DPI."""
        # 720x360 pixels at 144 dpi = 360x180 points
        page = create_simple_page(width=720, height=360)
        output_pdf = tmp_path / "high_dpi.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page, dpi=144.0, multi_font_manager=multi_font_manager
        )
        assert renderer.coord_transform.page_width_pt == pytest.approx(360.0)
        assert renderer.coord_transform.page_height_pt == pytest.approx(180.0)

        renderer.render(output_pdf)
        check_pdf(str(output_pdf))


class TestFpdf2PdfRendererMultiLine:
    """Test rendering of multi-line content."""

    def test_multiple_lines(self, tmp_path, multi_font_manager):
        """Test rendering multiple lines of text."""
        line1_words = [
            OcrElement(
                ocr_class=OcrClass.WORD,
                text="Line",
                bbox=BoundingBox(left=100, top=100, right=180, bottom=150),
            ),
            OcrElement(
                ocr_class=OcrClass.WORD,
                text="one",
                bbox=BoundingBox(left=190, top=100, right=250, bottom=150),
            ),
        ]
        line1 = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            baseline=Baseline(slope=0.0, intercept=0),
            children=line1_words,
        )

        line2_words = [
            OcrElement(
                ocr_class=OcrClass.WORD,
                text="Line",
                bbox=BoundingBox(left=100, top=200, right=180, bottom=250),
            ),
            OcrElement(
                ocr_class=OcrClass.WORD,
                text="two",
                bbox=BoundingBox(left=190, top=200, right=250, bottom=250),
            ),
        ]
        line2 = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=200, right=900, bottom=250),
            baseline=Baseline(slope=0.0, intercept=0),
            children=line2_words,
        )

        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=250),
            direction="ltr",
            language="eng",
            children=[line1, line2],
        )

        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=1000, bottom=500),
            children=[paragraph],
        )

        output_pdf = tmp_path / "multiline.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        extracted_text = text_from_pdf(output_pdf)
        assert "Line" in extracted_text
        assert "one" in extracted_text
        assert "two" in extracted_text


class TestFpdf2PdfRendererTextDirection:
    """Test rendering of different text directions."""

    def test_ltr_text(self, tmp_path, multi_font_manager):
        """Test rendering LTR text."""
        page = create_simple_page()
        output_pdf = tmp_path / "ltr.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))

    def test_rtl_text(self, tmp_path, multi_font_manager):
        """Test rendering RTL text."""
        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="مرحبا",
            bbox=BoundingBox(left=100, top=100, right=200, bottom=150),
        )
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            baseline=Baseline(slope=0.0, intercept=0),
            direction="rtl",
            children=[word],
        )
        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            direction="rtl",
            language="ara",
            children=[line],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=1000, bottom=500),
            children=[paragraph],
        )

        output_pdf = tmp_path / "rtl.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))


class TestFpdf2PdfRendererBaseline:
    """Test baseline handling in rendering."""

    def test_sloped_baseline(self, tmp_path, multi_font_manager):
        """Test rendering with a sloped baseline."""
        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Sloped",
            bbox=BoundingBox(left=100, top=100, right=200, bottom=150),
        )
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            baseline=Baseline(slope=0.02, intercept=-5),
            children=[word],
        )
        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            direction="ltr",
            language="eng",
            children=[line],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=1000, bottom=500),
            children=[paragraph],
        )

        output_pdf = tmp_path / "sloped.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Sloped" in extracted_text


class TestFpdf2PdfRendererTextangle:
    """Test textangle (rotation) handling in rendering."""

    def test_rotated_text(self, tmp_path, multi_font_manager):
        """Test rendering rotated text."""
        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Rotated",
            bbox=BoundingBox(left=100, top=100, right=200, bottom=150),
        )
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            baseline=Baseline(slope=0.0, intercept=0),
            textangle=5.0,
            children=[word],
        )
        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            direction="ltr",
            language="eng",
            children=[line],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=1000, bottom=500),
            children=[paragraph],
        )

        output_pdf = tmp_path / "rotated.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Rotated" in extracted_text


class TestFpdf2PdfRendererWordBreaks:
    """Test word rendering."""

    def test_word_breaks_english(self, tmp_path, multi_font_manager):
        """Test that words are rendered for English text."""
        page = create_simple_page()
        output_pdf = tmp_path / "english.pdf"

        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        extracted_text = text_from_pdf(output_pdf)
        # Words should be present
        assert "Hello" in extracted_text
        assert "World" in extracted_text

    def test_cjk_text(self, tmp_path, multi_font_manager):
        """Test rendering CJK text."""
        words = [
            OcrElement(
                ocr_class=OcrClass.WORD,
                text="你好",
                bbox=BoundingBox(left=100, top=100, right=150, bottom=150),
            ),
            OcrElement(
                ocr_class=OcrClass.WORD,
                text="世界",
                bbox=BoundingBox(left=160, top=100, right=210, bottom=150),
            ),
        ]
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            baseline=Baseline(slope=0.0, intercept=0),
            children=words,
        )
        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=BoundingBox(left=100, top=100, right=900, bottom=150),
            direction="ltr",
            language="chi_sim",  # Simplified Chinese
            children=[line],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=1000, bottom=500),
            children=[paragraph],
        )

        output_pdf = tmp_path / "chinese.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))


class TestFpdf2PdfRendererDebugOptions:
    """Test debug rendering options."""

    def test_debug_render_options_default(self, multi_font_manager):
        """Test that debug options are disabled by default."""
        page = create_simple_page()
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )

        assert renderer.debug_options.render_baseline is False
        assert renderer.debug_options.render_word_bbox is False
        assert renderer.debug_options.render_line_bbox is False

    def test_debug_render_options_enabled(self, tmp_path, multi_font_manager):
        """Test rendering with debug options enabled."""
        page = create_simple_page()
        output_pdf = tmp_path / "debug.pdf"

        debug_opts = DebugRenderOptions(
            render_baseline=True,
            render_word_bbox=True,
            render_line_bbox=True,
        )

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
            debug_render_options=debug_opts,
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))
        # Text should still be extractable
        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text


class TestFpdf2PdfRendererErrors:
    """Test error handling in Fpdf2PdfRenderer."""

    def test_invalid_ocr_class(self, multi_font_manager):
        """Test that non-page elements are rejected."""
        line = OcrElement(
            ocr_class=OcrClass.LINE, bbox=BoundingBox(left=0, top=0, right=100, bottom=50)
        )

        with pytest.raises(ValueError, match="ocr_page"):
            Fpdf2PdfRenderer(page=line, dpi=72.0, multi_font_manager=multi_font_manager)

    def test_page_without_bbox(self, multi_font_manager):
        """Test that pages without bbox are rejected."""
        page = OcrElement(ocr_class=OcrClass.PAGE)

        with pytest.raises(ValueError, match="bounding box"):
            Fpdf2PdfRenderer(page=page, dpi=72.0, multi_font_manager=multi_font_manager)


class TestFpdf2PdfRendererLineTypes:
    """Test rendering of different line types."""

    def test_header_line(self, tmp_path, multi_font_manager):
        """Test rendering header lines."""
        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Header",
            bbox=BoundingBox(left=100, top=50, right=200, bottom=100),
        )
        header = OcrElement(
            ocr_class=OcrClass.HEADER,
            bbox=BoundingBox(left=100, top=50, right=900, bottom=100),
            baseline=Baseline(slope=0.0, intercept=0),
            children=[word],
        )
        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=BoundingBox(left=100, top=50, right=900, bottom=100),
            direction="ltr",
            language="eng",
            children=[header],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=1000, bottom=500),
            children=[paragraph],
        )

        output_pdf = tmp_path / "header.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Header" in extracted_text

    def test_caption_line(self, tmp_path, multi_font_manager):
        """Test rendering caption lines."""
        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Caption",
            bbox=BoundingBox(left=100, top=300, right=200, bottom=350),
        )
        caption = OcrElement(
            ocr_class=OcrClass.CAPTION,
            bbox=BoundingBox(left=100, top=300, right=900, bottom=350),
            baseline=Baseline(slope=0.0, intercept=0),
            children=[word],
        )
        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=BoundingBox(left=100, top=300, right=900, bottom=350),
            direction="ltr",
            language="eng",
            children=[caption],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=1000, bottom=500),
            children=[paragraph],
        )

        output_pdf = tmp_path / "caption.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page, dpi=72.0, multi_font_manager=multi_font_manager
        )
        renderer.render(output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Caption" in extracted_text


def create_rtl_page(
    words: list[tuple[str, tuple[float, float, float, float]]],
    language: str = "ara",
    width: float = 1000,
    height: float = 500,
) -> OcrElement:
    """Create an OcrElement page with a single RTL paragraph/line.

    Args:
        words: List of (text, (left, top, right, bottom)) tuples.
        language: Language code for the paragraph.
        width: Page width in pixels.
        height: Page height in pixels.

    Returns:
        OcrElement page.
    """
    word_elements = [
        OcrElement(
            ocr_class=OcrClass.WORD,
            text=text,
            bbox=BoundingBox(
                left=bbox[0], top=bbox[1], right=bbox[2], bottom=bbox[3]
            ),
        )
        for text, bbox in words
    ]
    line = OcrElement(
        ocr_class=OcrClass.LINE,
        bbox=BoundingBox(left=50, top=100, right=950, bottom=200),
        baseline=Baseline(slope=0.0, intercept=0),
        direction="rtl",
        children=word_elements,
    )
    paragraph = OcrElement(
        ocr_class=OcrClass.PARAGRAPH,
        bbox=BoundingBox(left=50, top=100, right=950, bottom=200),
        direction="rtl",
        language=language,
        children=[line],
    )
    return OcrElement(
        ocr_class=OcrClass.PAGE,
        bbox=BoundingBox(left=0, top=0, right=width, bottom=height),
        children=[paragraph],
    )


def _tounicode_map(pdf_path: Path) -> dict[int, str]:
    """Extract all ToUnicode CMap entries from the first page's OCR overlay.

    Returns a dict mapping subset glyph index -> unicode string.
    """
    pdf = pikepdf.open(pdf_path)
    page = pdf.pages[0]
    resources = page.get('/Resources', {})

    # Collect fonts from the page and from any Form XObjects (OCR overlay)
    fonts: dict[str, pikepdf.Object] = {}
    if '/Font' in resources:
        for name, obj in resources['/Font'].items():
            fonts[str(name)] = obj
    for xobj in resources.get('/XObject', {}).values():
        if xobj.get('/Subtype') == '/Form':
            for name, obj in xobj.get('/Resources', {}).get('/Font', {}).items():
                fonts[str(name)] = obj

    result: dict[int, str] = {}
    for fobj in fonts.values():
        tounicode = fobj.get('/ToUnicode')
        if tounicode is None:
            continue
        cmap = bytes(tounicode.read_bytes()).decode('latin-1', errors='replace')
        for m in re.finditer(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', cmap):
            src_int = int(m.group(1), 16)
            dst_hex = m.group(2)
            chars = ''.join(
                chr(int(dst_hex[i : i + 4], 16))
                for i in range(0, len(dst_hex), 4)
                if int(dst_hex[i : i + 4], 16) > 0
            )
            if src_int > 0 and chars:
                result[src_int] = chars
    return result


def _decode_tounicode_stream(
    pdf_path: Path,
) -> tuple[dict[int, str], list[int]]:
    """Extract ToUnicode CMap and Tj glyph stream from a test PDF.

    Searches the page content stream and any Form XObjects for fonts
    and Tj operations.

    Returns:
        (cmap, glyph_ids) where *cmap* maps subset index -> Unicode string
        and *glyph_ids* is the flat list of 2-byte glyph indices found in
        the first Tj string.
    """
    pdf = pikepdf.open(pdf_path)
    page = pdf.pages[0]
    resources = page.get('/Resources', {})

    # Collect fonts from page and from Form XObjects
    cmap: dict[int, str] = {}
    for font_dict in [resources.get('/Font', {})]:
        for fobj in font_dict.values():
            tounicode = fobj.get('/ToUnicode')
            if tounicode is None:
                continue
            raw = bytes(tounicode.read_bytes()).decode('latin-1', errors='replace')
            for m in re.finditer(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', raw):
                src = int(m.group(1), 16)
                dst_hex = m.group(2)
                chars = ''.join(
                    chr(int(dst_hex[i : i + 4], 16))
                    for i in range(0, len(dst_hex), 4)
                    if int(dst_hex[i : i + 4], 16) > 0
                )
                if src > 0 and chars:
                    cmap[src] = chars
    for xobj in resources.get('/XObject', {}).values():
        if xobj.get('/Subtype') != '/Form':
            continue
        for fobj in xobj.get('/Resources', {}).get('/Font', {}).values():
            tounicode = fobj.get('/ToUnicode')
            if tounicode is None:
                continue
            raw = bytes(tounicode.read_bytes()).decode('latin-1', errors='replace')
            for m in re.finditer(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', raw):
                src = int(m.group(1), 16)
                dst_hex = m.group(2)
                chars = ''.join(
                    chr(int(dst_hex[i : i + 4], 16))
                    for i in range(0, len(dst_hex), 4)
                    if int(dst_hex[i : i + 4], 16) > 0
                )
                if src > 0 and chars:
                    cmap[src] = chars

    # Find first Tj glyph IDs from page content or XObject streams
    glyph_ids: list[int] = []
    streams: list[bytes] = []
    contents = page.get('/Contents')
    if contents:
        streams.append(bytes(contents.read_bytes()))
    for xobj in resources.get('/XObject', {}).values():
        if xobj.get('/Subtype') == '/Form':
            streams.append(bytes(xobj.read_bytes()))
    for data in streams:
        if glyph_ids:
            break
        tj = re.search(rb'\(([^\)]+)\)\s*Tj', data)
        if tj:
            raw_bytes = tj.group(1)
            for j in range(0, len(raw_bytes) - 1, 2):
                glyph_ids.append((raw_bytes[j] << 8) | raw_bytes[j + 1])
    return cmap, glyph_ids


class TestRtlTextExtraction:
    """Verify that RTL text is extracted in correct logical order.

    The fpdf2 renderer must produce PDF text layers where text extractors
    (pdftotext, pdfminer) return characters in correct logical (reading)
    order for Arabic, Hebrew, and Farsi scripts.

    These tests exercise invisible_text=True (the production path) to
    catch issues like the lam-alef ligature CMap ordering bug (issue #1655).
    """

    def test_arabic_lam_alef_extraction_order(self, tmp_path, multi_font_manager):
        """Arabic words with lam-alef ligature extract in correct order.

        The lam-alef (لا) ligature was the primary trigger for issue #1655:
        fpdf2's shape_text() produced a multi-char CMap entry whose
        character order was reversed by the bidi algorithm during
        extraction, giving "سالم" instead of "سلام".
        """
        # سلام contains lam-alef: sin(س) lam(ل) alef(ا) meem(م)
        page = create_rtl_page(
            [("سلام", (600, 100, 900, 200))],
            language="fas",
        )
        output_pdf = tmp_path / "rtl_lam_alef.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=True,
        )
        renderer.render(output_pdf)

        cmap, glyph_ids = _decode_tounicode_stream(output_pdf)
        # Decode the glyph stream via the CMap
        decoded = ''.join(cmap.get(g, '') for g in glyph_ids)
        # The stream is pre-reversed for RTL, so reversing it back
        # must yield the original logical text
        logical = decoded[::-1]
        assert logical == 'سلام', (
            f"Expected logical text 'سلام', got {logical!r} "
            f"(stream: {decoded!r}, glyph_ids: {glyph_ids})"
        )

    def test_arabic_multiple_words_extraction(self, tmp_path, multi_font_manager):
        """Multiple Arabic words produce correct Unicode mappings."""
        page = create_rtl_page(
            [
                ("مرحبا", (600, 100, 900, 200)),
                ("بالعالم", (100, 100, 500, 200)),
            ],
            language="ara",
        )
        output_pdf = tmp_path / "rtl_arabic_words.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=True,
        )
        renderer.render(output_pdf)

        cmap, _ = _decode_tounicode_stream(output_pdf)
        # Every CMap value should contain valid Arabic characters
        arabic_chars = {c for chars in cmap.values() for c in chars}
        expected = set('مرحبابالعالم')
        assert expected.issubset(arabic_chars | {' '}), (
            f"CMap missing Arabic characters; got {arabic_chars}"
        )

    def test_hebrew_extraction_order(self, tmp_path, multi_font_manager):
        """Hebrew text produces correct stream order for extraction."""
        page = create_rtl_page(
            [("שלום", (600, 100, 900, 200))],
            language="heb",
        )
        output_pdf = tmp_path / "rtl_hebrew.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=True,
        )
        renderer.render(output_pdf)

        cmap, glyph_ids = _decode_tounicode_stream(output_pdf)
        decoded = ''.join(cmap.get(g, '') for g in glyph_ids)
        logical = decoded[::-1]
        assert logical == 'שלום', (
            f"Expected logical text 'שלום', got {logical!r} "
            f"(stream: {decoded!r})"
        )

    def test_rtl_tounicode_one_to_one(self, tmp_path, multi_font_manager):
        """RTL invisible text produces 1:1 glyph-to-Unicode CMap entries.

        When using encode_text() for RTL words, each glyph maps to exactly
        one Unicode character. Multi-char ligature CMap entries (produced by
        shape_text()) are the root cause of the extraction order bug, so
        their absence confirms the fix.
        """
        page = create_rtl_page(
            [("سلام", (600, 100, 900, 200))],
            language="ara",
        )
        output_pdf = tmp_path / "rtl_tounicode.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=True,
        )
        renderer.render(output_pdf)

        cmap, _ = _decode_tounicode_stream(output_pdf)
        # Every CMap entry should map to exactly one Unicode character
        for glyph_id, chars in cmap.items():
            assert len(chars) == 1, (
                f"Glyph {glyph_id} maps to {len(chars)} chars {chars!r}; "
                f"expected 1:1 mapping for RTL invisible text"
            )

    def test_visible_rtl_still_uses_shaping(self, tmp_path, multi_font_manager):
        """Visible RTL text (debug mode) still uses text shaping.

        The encode_text() bypass is only for invisible text. When
        invisible_text=False, shaping must remain active for correct
        glyph rendering (joining forms, ligatures).
        """
        page = create_rtl_page(
            [("سلام", (600, 100, 900, 200))],
            language="ara",
        )
        output_pdf = tmp_path / "rtl_visible.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72.0,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )
        renderer.render(output_pdf)

        # Shaped text may have multi-char CMap entries (ligatures);
        # just verify the PDF is valid and non-empty
        check_pdf(str(output_pdf))
        text = text_from_pdf(output_pdf)
        assert len(text.strip()) > 0, "Visible RTL should produce extractable text"
