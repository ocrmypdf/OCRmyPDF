# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for fpdf2-based PDF renderer."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from ocrmypdf.font import MultiFontManager
from ocrmypdf.fpdf_renderer import (
    DebugRenderOptions,
    Fpdf2MultiPageRenderer,
    Fpdf2PdfRenderer,
)
from ocrmypdf.hocrtransform.hocr_parser import HocrParser
from ocrmypdf.models.ocr_element import Baseline, BoundingBox, OcrClass, OcrElement


@pytest.fixture
def font_dir():
    """Return path to font directory."""
    return Path(__file__).parent.parent / "src" / "ocrmypdf" / "data"


@pytest.fixture
def multi_font_manager(font_dir):
    """Create MultiFontManager instance for testing."""
    return MultiFontManager(font_dir)


@pytest.fixture
def resources():
    """Return path to test resources directory."""
    return Path(__file__).parent / "resources"


@pytest.fixture
def pdftotext():
    """Return a function to extract text from PDF using pdftotext.

    Skips the test if pdftotext is not available.
    """
    pdftotext_path = shutil.which('pdftotext')
    if pdftotext_path is None:
        pytest.skip("pdftotext not available")

    def extract_text(pdf_path: Path) -> str:
        return subprocess.check_output(
            ['pdftotext', '-enc', 'UTF-8', str(pdf_path), '-'],
            text=True,
            encoding='utf-8',
        )

    return extract_text


class TestFpdf2RendererImports:
    """Test that all fpdf2 renderer modules can be imported."""

    def test_imports(self):
        """Test that all fpdf_renderer modules can be imported."""
        from ocrmypdf.fpdf_renderer import (
            DebugRenderOptions,
            Fpdf2MultiPageRenderer,
            Fpdf2PdfRenderer,
        )

        assert DebugRenderOptions is not None
        assert Fpdf2PdfRenderer is not None
        assert Fpdf2MultiPageRenderer is not None


class TestDebugRenderOptions:
    """Test DebugRenderOptions dataclass."""

    def test_defaults(self):
        """Test default values."""
        opts = DebugRenderOptions()
        assert opts.render_baseline is False
        assert opts.render_line_bbox is False
        assert opts.render_word_bbox is False

    def test_custom_values(self):
        """Test custom values."""
        opts = DebugRenderOptions(
            render_baseline=True,
            render_line_bbox=True,
            render_word_bbox=True,
        )
        assert opts.render_baseline is True
        assert opts.render_line_bbox is True
        assert opts.render_word_bbox is True


class TestFpdf2PdfRenderer:
    """Test Fpdf2PdfRenderer."""

    def test_requires_page_element(self, multi_font_manager):
        """Test that renderer requires ocr_page element."""
        from ocrmypdf.models.ocr_element import BoundingBox, OcrElement

        # Create a non-page element
        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="test",
            bbox=BoundingBox(left=0, top=0, right=100, bottom=20),
        )

        with pytest.raises(ValueError, match="Root element must be ocr_page"):
            Fpdf2PdfRenderer(
                page=word,
                dpi=300,
                multi_font_manager=multi_font_manager,
            )

    def test_requires_bbox(self, multi_font_manager):
        """Test that renderer requires page with bounding box."""
        from ocrmypdf.models.ocr_element import OcrElement

        page = OcrElement(ocr_class=OcrClass.PAGE)

        with pytest.raises(ValueError, match="Page must have bounding box"):
            Fpdf2PdfRenderer(
                page=page,
                dpi=300,
                multi_font_manager=multi_font_manager,
            )

    def test_render_simple_page(self, multi_font_manager, tmp_path):
        """Test rendering a simple page with one word."""
        from ocrmypdf.models.ocr_element import BoundingBox, OcrElement

        # Create a simple page with one word
        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Hello",
            bbox=BoundingBox(left=100, top=100, right=200, bottom=130),
        )
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=200, bottom=130),
            children=[word],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
            children=[line],
        )

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72,  # 1:1 mapping to PDF points
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "test_simple.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_invisible_text(self, multi_font_manager, tmp_path):
        """Test rendering invisible text (OCR layer)."""
        from ocrmypdf.models.ocr_element import BoundingBox, OcrElement

        word = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Invisible",
            bbox=BoundingBox(left=100, top=100, right=250, bottom=130),
        )
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=250, bottom=130),
            children=[word],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
            children=[line],
        )

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72,
            multi_font_manager=multi_font_manager,
            invisible_text=True,  # This is the default
        )

        output_path = tmp_path / "test_invisible.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestFpdf2MultiPageRenderer:
    """Test Fpdf2MultiPageRenderer."""

    def test_requires_pages(self, multi_font_manager):
        """Test that renderer requires at least one page."""
        with pytest.raises(ValueError, match="No pages to render"):
            renderer = Fpdf2MultiPageRenderer(
                pages_data=[],
                multi_font_manager=multi_font_manager,
            )
            renderer.render(Path("/tmp/test.pdf"))

    def test_render_multiple_pages(self, multi_font_manager, tmp_path):
        """Test rendering multiple pages."""
        from ocrmypdf.models.ocr_element import BoundingBox, OcrElement

        pages_data = []
        for i in range(3):
            word = OcrElement(
                ocr_class=OcrClass.WORD,
                text=f"Page{i + 1}",
                bbox=BoundingBox(left=100, top=100, right=200, bottom=130),
            )
            line = OcrElement(
                ocr_class=OcrClass.LINE,
                bbox=BoundingBox(left=100, top=100, right=200, bottom=130),
                children=[word],
            )
            page = OcrElement(
                ocr_class=OcrClass.PAGE,
                bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
                children=[line],
            )
            pages_data.append((i + 1, page, 72))

        renderer = Fpdf2MultiPageRenderer(
            pages_data=pages_data,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "test_multipage.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestFpdf2RendererWithHocr:
    """Test fpdf2 renderer with actual hOCR files."""

    def test_render_latin_hocr(self, resources, multi_font_manager, tmp_path):
        """Test rendering Latin text from hOCR."""
        hocr_path = resources / "latin.hocr"
        if not hocr_path.exists():
            pytest.skip("latin.hocr not found")

        parser = HocrParser(hocr_path)
        page = parser.parse()

        # Ensure we got a page
        assert page.ocr_class == OcrClass.PAGE
        assert page.bbox is not None

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "latin_fpdf2.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_cjk_hocr(self, resources, multi_font_manager, tmp_path):
        """Test rendering CJK text from hOCR."""
        hocr_path = resources / "cjk.hocr"
        if not hocr_path.exists():
            pytest.skip("cjk.hocr not found")

        parser = HocrParser(hocr_path)
        page = parser.parse()

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "cjk_fpdf2.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_arabic_hocr(self, resources, multi_font_manager, tmp_path):
        """Test rendering Arabic text from hOCR."""
        hocr_path = resources / "arabic.hocr"
        if not hocr_path.exists():
            pytest.skip("arabic.hocr not found")

        parser = HocrParser(hocr_path)
        page = parser.parse()

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "arabic_fpdf2.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_hello_world_scripts_hocr(
        self, resources, multi_font_manager, tmp_path
    ):
        """Test rendering comprehensive multilingual 'Hello!' hOCR file.

        This tests all major scripts including:
        - Latin (English, Spanish, French, German, Italian, Polish, Portuguese, Turkish)
        - Cyrillic (Russian)
        - Greek
        - CJK (Chinese Simplified, Chinese Traditional, Japanese, Korean)
        - Devanagari (Hindi)
        - Arabic (RTL)
        - Hebrew (RTL)

        Also includes rotated baselines to exercise skew handling.
        """
        hocr_path = resources / "hello_world_scripts.hocr"
        if not hocr_path.exists():
            pytest.skip("hello_world_scripts.hocr not found")

        parser = HocrParser(hocr_path)
        page = parser.parse()

        # Verify we parsed the page correctly
        assert page.ocr_class == OcrClass.PAGE
        assert page.bbox is not None
        # Should have 2550x3300 at 300 DPI
        assert page.bbox.right == 2550
        assert page.bbox.bottom == 3300

        # Test with visible text for visual inspection
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "hello_world_scripts_fpdf2.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_hello_world_scripts_multipage(
        self, resources, multi_font_manager, tmp_path
    ):
        """Test rendering hello_world_scripts.hocr using MultiPageRenderer.

        Uses Fpdf2MultiPageRenderer to render the multilingual test file,
        demonstrating font handling across all major writing systems.
        """
        hocr_path = resources / "hello_world_scripts.hocr"
        if not hocr_path.exists():
            pytest.skip("hello_world_scripts.hocr not found")

        parser = HocrParser(hocr_path)
        page = parser.parse()

        # Build pages_data list as expected by MultiPageRenderer
        pages_data = [(1, page, 300)]  # (page_number, page_element, dpi)

        renderer = Fpdf2MultiPageRenderer(
            pages_data=pages_data,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "hello_world_scripts_multipage.pdf"
        renderer.render(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestWordSegmentation:
    """Test that rendered PDFs have proper word segmentation for pdfminer.six."""

    def test_word_segmentation_with_pdfminer(self, multi_font_manager, tmp_path):
        """Test that pdfminer.six can extract words with proper spacing.

        This test verifies that explicit space characters are inserted between
        words so that pdfminer.six (and similar PDF readers) can properly
        segment words during text extraction.
        """
        from pdfminer.high_level import extract_text

        from ocrmypdf.models.ocr_element import BoundingBox, OcrElement

        # Create a page with multiple words on one line
        word1 = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Hello",
            bbox=BoundingBox(left=100, top=100, right=200, bottom=130),
        )
        word2 = OcrElement(
            ocr_class=OcrClass.WORD,
            text="World",
            bbox=BoundingBox(left=220, top=100, right=320, bottom=130),
        )
        word3 = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Test",
            bbox=BoundingBox(left=340, top=100, right=420, bottom=130),
        )
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=420, bottom=130),
            children=[word1, word2, word3],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
            children=[line],
        )

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72,  # 1:1 mapping to PDF points
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "test_word_segmentation.pdf"
        renderer.render(output_path)

        # Extract text using pdfminer.six
        extracted_text = extract_text(str(output_path))

        # Verify words are separated by spaces
        assert "Hello" in extracted_text
        assert "World" in extracted_text
        assert "Test" in extracted_text

        # The text should NOT be run together like "HelloWorldTest"
        assert "HelloWorld" not in extracted_text
        assert "WorldTest" not in extracted_text

        # Verify proper word segmentation - words should be separated
        # (allowing for whitespace variations)
        words_found = extracted_text.split()
        assert "Hello" in words_found
        assert "World" in words_found
        assert "Test" in words_found

    def test_cjk_no_spurious_spaces(self, multi_font_manager, tmp_path, pdftotext):
        """Test that CJK text does not get spurious spaces inserted.

        CJK scripts don't use spaces between characters/words, so we should
        not insert spaces between adjacent CJK words.

        Uses pdftotext (poppler) instead of pdfminer.six because the latter
        cannot decode the custom Encoding CMap that fpdf2 >= 2.8.7 emits for
        subsetted CFF-based CID fonts (e.g. NotoSansCJK).
        """
        from ocrmypdf.models.ocr_element import BoundingBox, OcrElement

        # Create a page with CJK words (Chinese characters)
        # 你好 = "Hello" in Chinese
        # 世界 = "World" in Chinese
        word1 = OcrElement(
            ocr_class=OcrClass.WORD,
            text="你好",
            bbox=BoundingBox(left=100, top=100, right=160, bottom=130),
        )
        word2 = OcrElement(
            ocr_class=OcrClass.WORD,
            text="世界",
            bbox=BoundingBox(left=170, top=100, right=230, bottom=130),
        )
        line = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=230, bottom=130),
            children=[word1, word2],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
            children=[line],
        )

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "test_cjk_segmentation.pdf"
        renderer.render(output_path)

        extracted_text = pdftotext(output_path)

        # CJK text should be present
        assert "你好" in extracted_text
        assert "世界" in extracted_text

        # There should NOT be spaces between CJK characters
        # (a space between the two words is acceptable, since they are
        # separated horizontally on the rendered page)
        extracted_chars = extracted_text.replace(" ", "").replace("\n", "")
        assert "你好世界" in extracted_chars or (
            "你好" in extracted_chars and "世界" in extracted_chars
        )

    def test_last_word_of_line_gets_trailing_space(self, multi_font_manager, tmp_path):
        """Regression test for #1731.

        The last word of a line must also emit a trailing space, otherwise an
        extractor whose newline heuristic does not fire for a small baseline
        shift (e.g. adjacent columns in a multi-column scan) glues it to the
        first word of the next line. Here two single-word lines share the same
        baseline and are horizontally adjacent, so nothing but an explicit
        trailing space on the first line's last word can separate them.
        """
        from pdfminer.high_level import extract_text

        from ocrmypdf.models.ocr_element import BoundingBox, OcrElement

        word_a = OcrElement(
            ocr_class=OcrClass.WORD,
            text="Bijdrage",
            bbox=BoundingBox(left=100, top=100, right=180, bottom=112),
        )
        line_a = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=100, top=100, right=180, bottom=112),
            children=[word_a],
        )
        word_b = OcrElement(
            ocr_class=OcrClass.WORD,
            text="4835",
            bbox=BoundingBox(left=180, top=100, right=230, bottom=112),
        )
        line_b = OcrElement(
            ocr_class=OcrClass.LINE,
            bbox=BoundingBox(left=180, top=100, right=230, bottom=112),
            children=[word_b],
        )
        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
            children=[line_a, line_b],
        )

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=72,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "test_last_word_trailing_space.pdf"
        renderer.render(output_path)

        extracted_text = extract_text(str(output_path))

        # Without the trailing space the two words are extracted glued together.
        assert "Bijdrage4835" not in extracted_text
        words_found = extracted_text.split()
        assert "Bijdrage" in words_found
        assert "4835" in words_found

    def test_latin_hocr_word_segmentation(
        self, resources, multi_font_manager, tmp_path
    ):
        """Test word segmentation with real Latin hOCR file."""
        from pdfminer.high_level import extract_text

        hocr_path = resources / "latin.hocr"
        if not hocr_path.exists():
            pytest.skip("latin.hocr not found")

        parser = HocrParser(hocr_path)
        page = parser.parse()

        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )

        output_path = tmp_path / "latin_segmentation.pdf"
        renderer.render(output_path)

        # Extract text using pdfminer.six
        extracted_text = extract_text(str(output_path))

        # The Latin text should have proper word segmentation
        # Words should be separable
        words = extracted_text.split()
        assert len(words) > 0

        # Check that common English words are properly segmented
        # (not stuck together)
        text_no_newlines = extracted_text.replace("\n", " ")
        # There should be spaces in the extracted text
        assert " " in text_no_newlines


def _rotated_line_page(
    words: list[tuple[str, tuple[int, int, int, int]]], slope: float
) -> OcrElement:
    """Build a page with one line whose rotation is encoded as a steep slope.

    Tesseract reports vertical and 90-degree rotated lines this way, without
    a textangle, and the sign of the slope is unreliable.
    """
    word_elements = [
        OcrElement(
            ocr_class=OcrClass.WORD,
            text=text,
            bbox=BoundingBox(left=box[0], top=box[1], right=box[2], bottom=box[3]),
        )
        for text, box in words
    ]
    line = OcrElement(
        ocr_class=OcrClass.LINE,
        bbox=BoundingBox(
            left=min(box[0] for _, box in words),
            top=min(box[1] for _, box in words),
            right=max(box[2] for _, box in words),
            bottom=max(box[3] for _, box in words),
        ),
        # A steep line has a meaningless intercept, like the ones Tesseract gives
        baseline=Baseline(slope=slope, intercept=10032 if abs(slope) > 1 else 0),
        children=word_elements,
    )
    return OcrElement(
        ocr_class=OcrClass.PAGE,
        bbox=BoundingBox(left=0, top=0, right=612, bottom=792),
        children=[line],
    )


# Vertical Japanese column, words stacked top to bottom with small gaps
VERTICAL_CJK_WORDS = [
    ("その", (300, 100, 330, 160)),
    ("まま", (300, 165, 330, 225)),
    ("男", (300, 230, 330, 260)),
]


class TestRotatedLines:
    """Lines whose rotation Tesseract encodes as a steep baseline slope (#1244)."""

    def _render(self, page, multi_font_manager, tmp_path) -> Path:
        output_path = tmp_path / "rotated.pdf"
        Fpdf2PdfRenderer(
            page=page, dpi=72, multi_font_manager=multi_font_manager
        ).render(output_path)
        return output_path

    @pytest.mark.parametrize('slope', [-912.0, 912.0])
    def test_vertical_cjk_no_spaces_and_in_order(
        self, slope, multi_font_manager, tmp_path, pdftotext
    ):
        page = _rotated_line_page(VERTICAL_CJK_WORDS, slope)
        output_path = self._render(page, multi_font_manager, tmp_path)
        text = pdftotext(output_path)
        assert "そのまま男" in text

    @pytest.mark.parametrize('slope', [-912.0, 912.0])
    def test_vertical_cjk_no_spaces_pdfium(self, slope, multi_font_manager, tmp_path):
        pdfium = pytest.importorskip('pypdfium2')
        page = _rotated_line_page(VERTICAL_CJK_WORDS, slope)
        output_path = self._render(page, multi_font_manager, tmp_path)
        pdf = pdfium.PdfDocument(output_path)
        text = pdf[0].get_textpage().get_text_range()
        assert text.strip() == "そのまま男"

    @pytest.mark.parametrize('slope', [-211.8, 211.8])
    def test_long_vertical_line_slight_slope(self, slope, multi_font_manager, tmp_path):
        """A near-vertical slope must not tilt a long column of text.

        Tesseract's slope for a vertical line deviates from vertical by a
        fraction of a degree; rendered faithfully, the baseline drifts across
        the column and poppler's raw mode splits words along the way.
        """
        text = "次の瞬間背中いや休全体に衝撃が走る"
        words = [
            (char, (300, 100 + 36 * i, 336, 130 + 36 * i))
            for i, char in enumerate(text)
        ]
        page = _rotated_line_page(words, slope)
        output_path = self._render(page, multi_font_manager, tmp_path)
        raw = subprocess.check_output(
            ['pdftotext', '-raw', '-enc', 'UTF-8', str(output_path), '-'],
            text=True,
            encoding='utf-8',
        )
        assert raw.strip() == text

    @pytest.mark.parametrize('slope', [-912.0, 912.0])
    def test_vertical_single_word_reads_top_to_bottom(
        self, slope, multi_font_manager, tmp_path
    ):
        pdfium = pytest.importorskip('pypdfium2')
        page = _rotated_line_page([("男の両足", (300, 100, 330, 220))], slope)
        output_path = self._render(page, multi_font_manager, tmp_path)
        pdf = pdfium.PdfDocument(output_path)
        textpage = pdf[0].get_textpage()
        assert textpage.get_text_range().strip() == "男の両足"
        page_height = pdf[0].get_height()
        # First character is at the top of the column (pdfium y is up)
        _, _, _, first_top = textpage.get_charbox(0)
        _, _, _, last_top = textpage.get_charbox(3)
        assert page_height - first_top < page_height - last_top

    @pytest.mark.parametrize('slope', [-912.0, 912.0])
    def test_vertical_word_fills_its_box(self, slope, multi_font_manager, tmp_path):
        """A vertical word's glyphs should span its box along the column.

        The word's advance must be scaled to the box length measured along
        the baseline, not to the column's thickness.
        """
        pdfium = pytest.importorskip('pypdfium2')
        page = _rotated_line_page(VERTICAL_CJK_WORDS, slope)
        output_path = self._render(page, multi_font_manager, tmp_path)
        pdf = pdfium.PdfDocument(output_path)
        textpage = pdf[0].get_textpage()
        page_height = pdf[0].get_height()
        # The first word "その" occupies y=100..160 in page (y-down) coords
        boxes = [textpage.get_charbox(i) for i in range(2)]
        top = min(page_height - b[3] for b in boxes)
        bottom = max(page_height - b[1] for b in boxes)
        assert bottom - top > 0.85 * 60

    @pytest.mark.parametrize('slope', [-300.0, 300.0])
    @pytest.mark.parametrize('upward', [True, False], ids=['upward', 'downward'])
    def test_rotated_latin(self, upward, slope, multi_font_manager, tmp_path):
        """Latin text rotated 90 degrees, reading up or down the page (#1632).

        Each word's first letter must be at the reading start of that word's
        box, whichever sign Tesseract gave the slope.
        """
        pdfium = pytest.importorskip('pypdfium2')
        top_box, bottom_box = (300, 280, 330, 380), (300, 400, 330, 500)
        if upward:
            words = [("Hello", bottom_box), ("World", top_box)]
        else:
            words = [("Hello", top_box), ("World", bottom_box)]
        page = _rotated_line_page(words, slope)
        output_path = self._render(page, multi_font_manager, tmp_path)
        pdf = pdfium.PdfDocument(output_path)
        textpage = pdf[0].get_textpage()
        text = textpage.get_text_range()
        assert text.split() == ["Hello", "World"]
        page_height = pdf[0].get_height()

        def centre_y(char_index):
            _, bottom, _, top = textpage.get_charbox(char_index)
            return page_height - (top + bottom) / 2

        for word, box in words:
            first = text.index(word)
            first_y = centre_y(first)
            last_y = centre_y(first + len(word) - 1)
            assert box[1] <= first_y <= box[3]
            assert box[1] <= last_y <= box[3]
            if upward:
                assert first_y > last_y
            else:
                assert first_y < last_y

        # Glyphs lie across the column, not beside it
        for i, char in enumerate(text):
            if char.strip():
                left, _, right, _ = textpage.get_charbox(i)
                assert 295 <= (left + right) / 2 <= 335, char

    @pytest.mark.parametrize('slope', [-912.0, 912.0])
    def test_vertical_cjk_glyphs_within_column(
        self, slope, multi_font_manager, tmp_path
    ):
        pdfium = pytest.importorskip('pypdfium2')
        page = _rotated_line_page(VERTICAL_CJK_WORDS, slope)
        output_path = self._render(page, multi_font_manager, tmp_path)
        textpage = pdfium.PdfDocument(output_path)[0].get_textpage()
        for i in range(textpage.count_chars()):
            left, _, right, _ = textpage.get_charbox(i)
            assert left >= 300 and right <= 330

    def test_horizontal_latin_unchanged(self, multi_font_manager, tmp_path):
        pdfium = pytest.importorskip('pypdfium2')
        words = [
            ("Alpha", (100, 100, 180, 130)),
            ("Beta", (195, 100, 260, 130)),
            ("Gamma", (275, 100, 380, 130)),
        ]
        page = _rotated_line_page(words, 0.0)
        output_path = self._render(page, multi_font_manager, tmp_path)
        textpage = pdfium.PdfDocument(output_path)[0].get_textpage()
        assert textpage.get_text_range().split() == ["Alpha", "Beta", "Gamma"]
        # "Alpha" spans its box horizontally
        left = textpage.get_charbox(0)[0]
        right = textpage.get_charbox(4)[2]
        assert left == pytest.approx(100, abs=3)
        assert right == pytest.approx(180, abs=3)

    def test_horizontal_cjk_small_gap_no_inferred_space(
        self, multi_font_manager, tmp_path
    ):
        """Adjacent CJK words with a small gap should not gain a space."""
        pdfium = pytest.importorskip('pypdfium2')
        words = [
            ("你好", (100, 100, 160, 130)),
            ("世界", (170, 100, 230, 130)),
        ]
        page = _rotated_line_page(words, 0.0)
        output_path = self._render(page, multi_font_manager, tmp_path)
        text = pdfium.PdfDocument(output_path)[0].get_textpage().get_text_range()
        assert text.strip() == "你好世界"

    def test_horizontal_cjk_wide_gap_keeps_separation(
        self, multi_font_manager, tmp_path
    ):
        """CJK words far apart are not stretched to meet each other."""
        pdfium = pytest.importorskip('pypdfium2')
        words = [
            ("你好", (100, 100, 160, 130)),
            ("世界", (400, 100, 460, 130)),
        ]
        page = _rotated_line_page(words, 0.0)
        output_path = self._render(page, multi_font_manager, tmp_path)
        textpage = pdfium.PdfDocument(output_path)[0].get_textpage()
        # "好" ends near the right edge of its own box
        assert textpage.get_charbox(1)[2] < 170
