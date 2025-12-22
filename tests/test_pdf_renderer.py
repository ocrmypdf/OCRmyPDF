# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for PdfTextRenderer class."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from PIL import Image

from ocrmypdf.helpers import check_pdf
from ocrmypdf.hocrtransform import (
    Baseline,
    BoundingBox,
    OcrClass,
    OcrElement,
    PdfTextRenderer,
)
from ocrmypdf.hocrtransform.pdf_renderer import DebugRenderOptions


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


class TestPdfTextRendererBasic:
    """Basic PdfTextRenderer functionality tests."""

    def test_render_simple_page(self, tmp_path):
        """Test rendering a simple page with two words."""
        page = create_simple_page()
        output_pdf = tmp_path / "simple.pdf"

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        assert output_pdf.exists()
        check_pdf(str(output_pdf))

    def test_rendered_text_extractable(self, tmp_path):
        """Test that rendered text can be extracted from the PDF."""
        page = create_simple_page()
        output_pdf = tmp_path / "extractable.pdf"

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text
        assert "World" in extracted_text

    def test_invisible_text_mode(self, tmp_path):
        """Test that invisible_text=True creates a valid PDF."""
        page = create_simple_page()
        output_pdf = tmp_path / "invisible.pdf"

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf, invisible_text=True)

        # Text should still be extractable even when invisible
        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text

    def test_visible_text_mode(self, tmp_path):
        """Test that invisible_text=False creates a valid PDF with visible text."""
        page = create_simple_page()
        output_pdf = tmp_path / "visible.pdf"

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf, invisible_text=False)

        # Text should be extractable
        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text


class TestPdfTextRendererPageSize:
    """Test page size calculations."""

    def test_page_dimensions(self, tmp_path):
        """Test that page dimensions are calculated correctly."""
        # 1000x500 pixels at 72 dpi = 1000x500 points
        page = create_simple_page(width=1000, height=500)
        output_pdf = tmp_path / "dimensions.pdf"

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        assert renderer.width == pytest.approx(1000.0)
        assert renderer.height == pytest.approx(500.0)

        renderer.render(out_filename=output_pdf)

    def test_high_dpi_page(self, tmp_path):
        """Test page dimensions at higher DPI."""
        # 720x360 pixels at 144 dpi = 360x180 points
        page = create_simple_page(width=720, height=360)
        output_pdf = tmp_path / "high_dpi.pdf"

        renderer = PdfTextRenderer(page=page, dpi=144.0)
        assert renderer.width == pytest.approx(360.0)
        assert renderer.height == pytest.approx(180.0)

        renderer.render(out_filename=output_pdf)
        check_pdf(str(output_pdf))


class TestPdfTextRendererMultiLine:
    """Test rendering of multi-line content."""

    def test_multiple_lines(self, tmp_path):
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
        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        extracted_text = text_from_pdf(output_pdf)
        assert "Line" in extracted_text
        assert "one" in extracted_text
        assert "two" in extracted_text


class TestPdfTextRendererTextDirection:
    """Test rendering of different text directions."""

    def test_ltr_text(self, tmp_path):
        """Test rendering LTR text."""
        page = create_simple_page()
        output_pdf = tmp_path / "ltr.pdf"

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        check_pdf(str(output_pdf))

    def test_rtl_text(self, tmp_path):
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
        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        check_pdf(str(output_pdf))


class TestPdfTextRendererBaseline:
    """Test baseline handling in rendering."""

    def test_sloped_baseline(self, tmp_path):
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
        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Sloped" in extracted_text


class TestPdfTextRendererTextangle:
    """Test textangle (rotation) handling in rendering."""

    def test_rotated_text(self, tmp_path):
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
        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Rotated" in extracted_text


class TestPdfTextRendererWordBreaks:
    """Test word break injection."""

    def test_word_breaks_english(self, tmp_path):
        """Test that word breaks are injected for English text."""
        page = create_simple_page()
        output_pdf = tmp_path / "english.pdf"

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        extracted_text = text_from_pdf(output_pdf)
        # Words should be separated
        assert "Hello" in extracted_text
        assert "World" in extracted_text

    def test_no_word_breaks_cjk(self, tmp_path):
        """Test that word breaks are not injected for CJK text."""
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
        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        check_pdf(str(output_pdf))


class TestPdfTextRendererDebugOptions:
    """Test debug rendering options."""

    def test_debug_render_options_default(self):
        """Test that debug options are disabled by default."""
        page = create_simple_page()
        renderer = PdfTextRenderer(page=page, dpi=72.0)

        assert renderer.render_options.render_paragraph_bbox is False
        assert renderer.render_options.render_baseline is False
        assert renderer.render_options.render_word_bbox is False

    def test_debug_render_options_enabled(self, tmp_path):
        """Test rendering with debug options enabled."""
        page = create_simple_page()
        output_pdf = tmp_path / "debug.pdf"

        debug_opts = DebugRenderOptions(
            render_paragraph_bbox=True,
            render_baseline=True,
            render_word_bbox=True,
            render_triangle=True,
        )

        renderer = PdfTextRenderer(
            page=page, dpi=72.0, debug_render_options=debug_opts
        )
        renderer.render(out_filename=output_pdf, invisible_text=False)

        check_pdf(str(output_pdf))
        # Text should still be extractable
        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text


class TestPdfTextRendererWithImage:
    """Test rendering with image overlay."""

    def test_render_with_image(self, tmp_path):
        """Test rendering with an image overlaid on text."""
        page = create_simple_page()
        output_pdf = tmp_path / "with_image.pdf"

        # Create a simple test image
        image_path = tmp_path / "test.png"
        img = Image.new('RGB', (1000, 500), color='white')
        img.save(image_path)

        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(
            out_filename=output_pdf, image_filename=image_path, invisible_text=True
        )

        check_pdf(str(output_pdf))
        # Text should still be extractable under the image
        extracted_text = text_from_pdf(output_pdf)
        assert "Hello" in extracted_text


class TestPdfTextRendererErrors:
    """Test error handling in PdfTextRenderer."""

    def test_invalid_ocr_class(self):
        """Test that non-page elements are rejected."""
        line = OcrElement(
            ocr_class=OcrClass.LINE, bbox=BoundingBox(left=0, top=0, right=100, bottom=50)
        )

        with pytest.raises(ValueError, match="ocr_page"):
            PdfTextRenderer(page=line, dpi=72.0)

    def test_page_without_bbox(self):
        """Test that pages without bbox are rejected."""
        page = OcrElement(ocr_class=OcrClass.PAGE)

        with pytest.raises(ValueError, match="bounding box"):
            PdfTextRenderer(page=page, dpi=72.0)


class TestPdfTextRendererLineTypes:
    """Test rendering of different line types."""

    def test_header_line(self, tmp_path):
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
        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Header" in extracted_text

    def test_caption_line(self, tmp_path):
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
        renderer = PdfTextRenderer(page=page, dpi=72.0)
        renderer.render(out_filename=output_pdf)

        check_pdf(str(output_pdf))
        extracted_text = text_from_pdf(output_pdf)
        assert "Caption" in extracted_text
