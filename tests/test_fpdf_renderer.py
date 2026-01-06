# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for fpdf2-based PDF renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from ocrmypdf.font import MultiFontManager
from ocrmypdf.fpdf_renderer import DebugRenderOptions, Fpdf2MultiPageRenderer, Fpdf2PdfRenderer
from ocrmypdf.hocrtransform.hocr_parser import HocrParser
from ocrmypdf.hocrtransform.ocr_element import OcrClass


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
        from ocrmypdf.hocrtransform.ocr_element import BoundingBox, OcrElement

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
        from ocrmypdf.hocrtransform.ocr_element import OcrElement

        page = OcrElement(ocr_class=OcrClass.PAGE)

        with pytest.raises(ValueError, match="Page must have bounding box"):
            Fpdf2PdfRenderer(
                page=page,
                dpi=300,
                multi_font_manager=multi_font_manager,
            )

    def test_render_simple_page(self, multi_font_manager, tmp_path):
        """Test rendering a simple page with one word."""
        from ocrmypdf.hocrtransform.ocr_element import BoundingBox, OcrElement

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
        from ocrmypdf.hocrtransform.ocr_element import BoundingBox, OcrElement

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
        from ocrmypdf.hocrtransform.ocr_element import BoundingBox, OcrElement

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

    def test_render_hello_world_scripts_hocr(self, resources, multi_font_manager, tmp_path):
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
