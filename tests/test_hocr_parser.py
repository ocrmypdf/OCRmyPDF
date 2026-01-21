# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for HocrParser class."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from ocrmypdf.hocrtransform import (
    HocrParseError,
    HocrParser,
    OcrClass,
)


@pytest.fixture
def simple_hocr(tmp_path) -> Path:
    """Create a simple valid hOCR file."""
    content = dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
            "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head>
            <title>Test</title>
        </head>
        <body>
            <div class='ocr_page' title='bbox 0 0 1000 500; ppageno 0'>
                <p class='ocr_par' lang='eng' dir='ltr'>
                    <span class='ocr_line' title='bbox 100 100 900 150; baseline 0.01 -5'>
                        <span class='ocrx_word' title='bbox 100 100 200 150; x_wconf 95'>Hello</span>
                        <span class='ocrx_word' title='bbox 250 100 350 150; x_wconf 90'>World</span>
                    </span>
                </p>
            </div>
        </body>
        </html>
    """)
    hocr_file = tmp_path / "simple.hocr"
    hocr_file.write_text(content, encoding='utf-8')
    return hocr_file


@pytest.fixture
def multiline_hocr(tmp_path) -> Path:
    """Create an hOCR file with multiple lines and paragraphs."""
    content = dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <html>
        <body>
            <div class='ocr_page' title='bbox 0 0 1000 1000'>
                <p class='ocr_par' lang='eng'>
                    <span class='ocr_line' title='bbox 100 100 900 150'>
                        <span class='ocrx_word' title='bbox 100 100 200 150'>Line</span>
                        <span class='ocrx_word' title='bbox 210 100 280 150'>one</span>
                    </span>
                    <span class='ocr_line' title='bbox 100 200 900 250'>
                        <span class='ocrx_word' title='bbox 100 200 200 250'>Line</span>
                        <span class='ocrx_word' title='bbox 210 200 280 250'>two</span>
                    </span>
                </p>
                <p class='ocr_par' lang='deu'>
                    <span class='ocr_line' title='bbox 100 400 900 450'>
                        <span class='ocrx_word' title='bbox 100 400 200 450'>German</span>
                        <span class='ocrx_word' title='bbox 210 400 280 450'>text</span>
                    </span>
                </p>
            </div>
        </body>
        </html>
    """)
    hocr_file = tmp_path / "multiline.hocr"
    hocr_file.write_text(content, encoding='utf-8')
    return hocr_file


@pytest.fixture
def rtl_hocr(tmp_path) -> Path:
    """Create an hOCR file with RTL text."""
    content = dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <html>
        <body>
            <div class='ocr_page' title='bbox 0 0 1000 500'>
                <p class='ocr_par' lang='ara' dir='rtl'>
                    <span class='ocr_line' title='bbox 100 100 900 150'>
                        <span class='ocrx_word' title='bbox 100 100 200 150'>مرحبا</span>
                    </span>
                </p>
            </div>
        </body>
        </html>
    """)
    hocr_file = tmp_path / "rtl.hocr"
    hocr_file.write_text(content, encoding='utf-8')
    return hocr_file


@pytest.fixture
def rotated_hocr(tmp_path) -> Path:
    """Create an hOCR file with rotated text (textangle)."""
    content = dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <html>
        <body>
            <div class='ocr_page' title='bbox 0 0 1000 500'>
                <p class='ocr_par' lang='eng'>
                    <span class='ocr_line' title='bbox 100 100 900 150; textangle 5.5'>
                        <span class='ocrx_word' title='bbox 100 100 200 150'>Rotated</span>
                    </span>
                </p>
            </div>
        </body>
        </html>
    """)
    hocr_file = tmp_path / "rotated.hocr"
    hocr_file.write_text(content, encoding='utf-8')
    return hocr_file


@pytest.fixture
def header_hocr(tmp_path) -> Path:
    """Create an hOCR file with different line types."""
    content = dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <html>
        <body>
            <div class='ocr_page' title='bbox 0 0 1000 500'>
                <p class='ocr_par' lang='eng'>
                    <span class='ocr_header' title='bbox 100 50 900 100'>
                        <span class='ocrx_word' title='bbox 100 50 300 100'>Chapter</span>
                        <span class='ocrx_word' title='bbox 310 50 400 100'>One</span>
                    </span>
                    <span class='ocr_line' title='bbox 100 150 900 200'>
                        <span class='ocrx_word' title='bbox 100 150 200 200'>Body</span>
                        <span class='ocrx_word' title='bbox 210 150 280 200'>text</span>
                    </span>
                    <span class='ocr_caption' title='bbox 100 300 900 350'>
                        <span class='ocrx_word' title='bbox 100 300 200 350'>Figure</span>
                        <span class='ocrx_word' title='bbox 210 300 250 350'>1</span>
                    </span>
                </p>
            </div>
        </body>
        </html>
    """)
    hocr_file = tmp_path / "header.hocr"
    hocr_file.write_text(content, encoding='utf-8')
    return hocr_file


@pytest.fixture
def font_info_hocr(tmp_path) -> Path:
    """Create an hOCR file with font information."""
    content = dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <html>
        <body>
            <div class='ocr_page' title='bbox 0 0 1000 500'>
                <p class='ocr_par' lang='eng'>
                    <span class='ocr_line' title='bbox 100 100 900 150'>
                        <span class='ocrx_word' title='bbox 100 100 200 150; x_font Arial; x_fsize 12.5'>Styled</span>
                    </span>
                </p>
            </div>
        </body>
        </html>
    """)
    hocr_file = tmp_path / "font_info.hocr"
    hocr_file.write_text(content, encoding='utf-8')
    return hocr_file


class TestHocrParserBasic:
    """Basic HocrParser functionality tests."""

    def test_parse_simple_hocr(self, simple_hocr):
        parser = HocrParser(simple_hocr)
        page = parser.parse()

        assert page.ocr_class == OcrClass.PAGE
        assert page.bbox is not None
        assert page.bbox.width == 1000
        assert page.bbox.height == 500

    def test_parse_page_number(self, simple_hocr):
        parser = HocrParser(simple_hocr)
        page = parser.parse()

        assert page.page_number == 0

    def test_parse_paragraphs(self, simple_hocr):
        parser = HocrParser(simple_hocr)
        page = parser.parse()

        assert len(page.paragraphs) == 1
        paragraph = page.paragraphs[0]
        assert paragraph.ocr_class == OcrClass.PARAGRAPH
        assert paragraph.language == "eng"
        assert paragraph.direction == "ltr"

    def test_parse_lines(self, simple_hocr):
        parser = HocrParser(simple_hocr)
        page = parser.parse()

        lines = page.lines
        assert len(lines) == 1
        line = lines[0]
        assert line.ocr_class == OcrClass.LINE
        assert line.bbox is not None
        assert line.baseline is not None
        assert line.baseline.slope == pytest.approx(0.01)
        assert line.baseline.intercept == -5

    def test_parse_words(self, simple_hocr):
        parser = HocrParser(simple_hocr)
        page = parser.parse()

        words = page.words
        assert len(words) == 2
        assert words[0].text == "Hello"
        assert words[1].text == "World"

    def test_parse_word_confidence(self, simple_hocr):
        parser = HocrParser(simple_hocr)
        page = parser.parse()

        words = page.words
        assert words[0].confidence == pytest.approx(0.95)
        assert words[1].confidence == pytest.approx(0.90)

    def test_parse_word_bbox(self, simple_hocr):
        parser = HocrParser(simple_hocr)
        page = parser.parse()

        word = page.words[0]
        assert word.bbox is not None
        assert word.bbox.left == 100
        assert word.bbox.top == 100
        assert word.bbox.right == 200
        assert word.bbox.bottom == 150


class TestHocrParserMultiline:
    """Test parsing of multi-line/multi-paragraph hOCR."""

    def test_multiple_lines(self, multiline_hocr):
        parser = HocrParser(multiline_hocr)
        page = parser.parse()

        assert len(page.paragraphs) == 2
        assert len(page.lines) == 3  # 2 in first par, 1 in second

    def test_multiple_paragraphs_languages(self, multiline_hocr):
        parser = HocrParser(multiline_hocr)
        page = parser.parse()

        paragraphs = page.paragraphs
        assert paragraphs[0].language == "eng"
        assert paragraphs[1].language == "deu"

    def test_word_count(self, multiline_hocr):
        parser = HocrParser(multiline_hocr)
        page = parser.parse()

        assert len(page.words) == 6  # 2 + 2 + 2


class TestHocrParserRTL:
    """Test parsing of RTL text."""

    def test_rtl_direction(self, rtl_hocr):
        parser = HocrParser(rtl_hocr)
        page = parser.parse()

        paragraph = page.paragraphs[0]
        assert paragraph.direction == "rtl"
        assert paragraph.language == "ara"

    def test_rtl_line_inherits_direction(self, rtl_hocr):
        parser = HocrParser(rtl_hocr)
        page = parser.parse()

        line = page.lines[0]
        assert line.direction == "rtl"


class TestHocrParserRotation:
    """Test parsing of rotated text."""

    def test_textangle(self, rotated_hocr):
        parser = HocrParser(rotated_hocr)
        page = parser.parse()

        line = page.lines[0]
        assert line.textangle == pytest.approx(5.5)


class TestHocrParserLineTypes:
    """Test parsing of different line types."""

    def test_header_line(self, header_hocr):
        parser = HocrParser(header_hocr)
        page = parser.parse()

        lines = page.lines
        assert len(lines) == 3

        # Check line types
        line_classes = [line.ocr_class for line in lines]
        assert OcrClass.HEADER in line_classes
        assert OcrClass.LINE in line_classes
        assert OcrClass.CAPTION in line_classes

    def test_all_line_types_have_words(self, header_hocr):
        parser = HocrParser(header_hocr)
        page = parser.parse()

        for line in page.lines:
            assert len(line.children) > 0


class TestHocrParserFontInfo:
    """Test parsing of font information."""

    def test_font_name_and_size(self, font_info_hocr):
        parser = HocrParser(font_info_hocr)
        page = parser.parse()

        word = page.words[0]
        assert word.font is not None
        assert word.font.name == "Arial"
        assert word.font.size == pytest.approx(12.5)


class TestHocrParserErrors:
    """Test error handling in HocrParser."""

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            HocrParser(tmp_path / "nonexistent.hocr")

    def test_invalid_xml(self, tmp_path):
        hocr_file = tmp_path / "invalid.hocr"
        hocr_file.write_text("<html><body>not closed", encoding='utf-8')

        with pytest.raises(HocrParseError):
            HocrParser(hocr_file)

    def test_missing_ocr_page(self, tmp_path):
        hocr_file = tmp_path / "no_page.hocr"
        hocr_file.write_text(
            "<html><body><p>No ocr_page</p></body></html>", encoding='utf-8'
        )

        parser = HocrParser(hocr_file)
        with pytest.raises(HocrParseError, match="No ocr_page"):
            parser.parse()

    def test_missing_page_bbox(self, tmp_path):
        hocr_file = tmp_path / "no_bbox.hocr"
        hocr_file.write_text(
            "<html><body><div class='ocr_page'>No bbox</div></body></html>",
            encoding='utf-8',
        )

        parser = HocrParser(hocr_file)
        with pytest.raises(HocrParseError, match="bbox"):
            parser.parse()


class TestHocrParserEdgeCases:
    """Test edge cases in HocrParser."""

    def test_empty_word_text(self, tmp_path):
        """Words with empty text should be skipped."""
        content = dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <html>
            <body>
                <div class='ocr_page' title='bbox 0 0 1000 500'>
                    <p class='ocr_par'>
                        <span class='ocr_line' title='bbox 100 100 900 150'>
                            <span class='ocrx_word' title='bbox 100 100 200 150'></span>
                            <span class='ocrx_word' title='bbox 210 100 300 150'>Valid</span>
                        </span>
                    </p>
                </div>
            </body>
            </html>
        """)
        hocr_file = tmp_path / "empty_word.hocr"
        hocr_file.write_text(content, encoding='utf-8')

        parser = HocrParser(hocr_file)
        page = parser.parse()

        # Only the non-empty word should be parsed
        assert len(page.words) == 1
        assert page.words[0].text == "Valid"

    def test_whitespace_only_word(self, tmp_path):
        """Words with only whitespace should be skipped."""
        content = dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <html>
            <body>
                <div class='ocr_page' title='bbox 0 0 1000 500'>
                    <p class='ocr_par'>
                        <span class='ocr_line' title='bbox 100 100 900 150'>
                            <span class='ocrx_word' title='bbox 100 100 200 150'>   </span>
                            <span class='ocrx_word' title='bbox 210 100 300 150'>Valid</span>
                        </span>
                    </p>
                </div>
            </body>
            </html>
        """)
        hocr_file = tmp_path / "whitespace_word.hocr"
        hocr_file.write_text(content, encoding='utf-8')

        parser = HocrParser(hocr_file)
        page = parser.parse()

        assert len(page.words) == 1
        assert page.words[0].text == "Valid"

    def test_line_without_bbox(self, tmp_path):
        """Lines without bbox should be skipped."""
        content = dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <html>
            <body>
                <div class='ocr_page' title='bbox 0 0 1000 500'>
                    <p class='ocr_par'>
                        <span class='ocr_line'>
                            <span class='ocrx_word' title='bbox 100 100 200 150'>Word</span>
                        </span>
                        <span class='ocr_line' title='bbox 100 200 900 250'>
                            <span class='ocrx_word' title='bbox 100 200 200 250'>Valid</span>
                        </span>
                    </p>
                </div>
            </body>
            </html>
        """)
        hocr_file = tmp_path / "no_line_bbox.hocr"
        hocr_file.write_text(content, encoding='utf-8')

        parser = HocrParser(hocr_file)
        page = parser.parse()

        # Only line with bbox should be parsed
        assert len(page.lines) == 1
        assert page.words[0].text == "Valid"

    def test_unicode_normalization(self, tmp_path):
        """Text should be NFKC normalized."""
        # Use a string with combining characters
        content = dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <html>
            <body>
                <div class='ocr_page' title='bbox 0 0 1000 500'>
                    <p class='ocr_par'>
                        <span class='ocr_line' title='bbox 100 100 900 150'>
                            <span class='ocrx_word' title='bbox 100 100 200 150'>ﬁ</span>
                        </span>
                    </p>
                </div>
            </body>
            </html>
        """)
        hocr_file = tmp_path / "unicode.hocr"
        hocr_file.write_text(content, encoding='utf-8')

        parser = HocrParser(hocr_file)
        page = parser.parse()

        # fi ligature should be normalized to "fi"
        assert page.words[0].text == "fi"

    def test_words_directly_under_page(self, tmp_path):
        """Test fallback for words directly under page (no paragraph structure)."""
        content = dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <html>
            <body>
                <div class='ocr_page' title='bbox 0 0 1000 500'>
                    <span class='ocrx_word' title='bbox 100 100 200 150'>Direct</span>
                    <span class='ocrx_word' title='bbox 210 100 300 150'>Word</span>
                </div>
            </body>
            </html>
        """)
        hocr_file = tmp_path / "direct_words.hocr"
        hocr_file.write_text(content, encoding='utf-8')

        parser = HocrParser(hocr_file)
        page = parser.parse()

        # Words should be parsed as direct children
        assert len(page.children) == 2
        assert page.children[0].text == "Direct"
        assert page.children[1].text == "Word"

    def test_no_namespace(self, tmp_path):
        """Test parsing hOCR without XHTML namespace."""
        content = dedent("""\
            <html>
            <body>
                <div class='ocr_page' title='bbox 0 0 1000 500'>
                    <p class='ocr_par'>
                        <span class='ocr_line' title='bbox 100 100 900 150'>
                            <span class='ocrx_word' title='bbox 100 100 200 150'>NoNS</span>
                        </span>
                    </p>
                </div>
            </body>
            </html>
        """)
        hocr_file = tmp_path / "no_namespace.hocr"
        hocr_file.write_text(content, encoding='utf-8')

        parser = HocrParser(hocr_file)
        page = parser.parse()

        assert len(page.words) == 1
        assert page.words[0].text == "NoNS"
