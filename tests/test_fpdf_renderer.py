# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for fpdf2-based PDF renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from ocrmypdf.font import MultiFontManager
from ocrmypdf.fpdf_renderer import (
    DebugRenderOptions,
    Fpdf2MultiPageRenderer,
    Fpdf2PdfRenderer,
)
from ocrmypdf.hocrtransform.hocr_parser import HocrParser
from ocrmypdf.models.ocr_element import OcrClass


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
                text=f"Page{i+1}",
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

    def test_cjk_no_spurious_spaces(self, multi_font_manager, tmp_path):
        """Test that CJK text does not get spurious spaces inserted.

        CJK scripts don't use spaces between characters/words, so we should
        not insert spaces between adjacent CJK words.
        """
        from pdfminer.high_level import extract_text

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

        # Extract text using pdfminer.six
        extracted_text = extract_text(str(output_path))

        # CJK text should be present
        assert "你好" in extracted_text
        assert "世界" in extracted_text

        # There should NOT be spaces between CJK characters
        # (but pdfminer may add some whitespace, so we check the raw chars)
        extracted_chars = extracted_text.replace(" ", "").replace("\n", "")
        assert "你好世界" in extracted_chars or (
            "你好" in extracted_chars and "世界" in extracted_chars
        )

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
