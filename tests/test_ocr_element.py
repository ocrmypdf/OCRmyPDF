# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for OcrElement dataclass and related classes."""

from __future__ import annotations

import pytest

from ocrmypdf.hocrtransform import (
    Baseline,
    BoundingBox,
    FontInfo,
    OcrClass,
    OcrElement,
)


class TestBoundingBox:
    """Tests for BoundingBox dataclass."""

    def test_basic_creation(self):
        bbox = BoundingBox(left=10, top=20, right=100, bottom=50)
        assert bbox.left == 10
        assert bbox.top == 20
        assert bbox.right == 100
        assert bbox.bottom == 50

    def test_width_height(self):
        bbox = BoundingBox(left=10, top=20, right=110, bottom=70)
        assert bbox.width == 100
        assert bbox.height == 50

    def test_zero_size_box(self):
        bbox = BoundingBox(left=10, top=20, right=10, bottom=20)
        assert bbox.width == 0
        assert bbox.height == 0

    def test_invalid_left_right(self):
        with pytest.raises(ValueError, match="right.*left"):
            BoundingBox(left=100, top=20, right=10, bottom=50)

    def test_invalid_top_bottom(self):
        with pytest.raises(ValueError, match="bottom.*top"):
            BoundingBox(left=10, top=50, right=100, bottom=20)


class TestBaseline:
    """Tests for Baseline dataclass."""

    def test_defaults(self):
        baseline = Baseline()
        assert baseline.slope == 0.0
        assert baseline.intercept == 0.0

    def test_with_values(self):
        baseline = Baseline(slope=0.01, intercept=-5)
        assert baseline.slope == 0.01
        assert baseline.intercept == -5


class TestFontInfo:
    """Tests for FontInfo dataclass."""

    def test_defaults(self):
        font = FontInfo()
        assert font.name is None
        assert font.size is None
        assert font.bold is False
        assert font.italic is False

    def test_with_values(self):
        font = FontInfo(name="Arial", size=12.0, bold=True)
        assert font.name == "Arial"
        assert font.size == 12.0
        assert font.bold is True
        assert font.italic is False


class TestOcrElement:
    """Tests for OcrElement dataclass."""

    def test_minimal_element(self):
        elem = OcrElement(ocr_class=OcrClass.WORD, text="hello")
        assert elem.ocr_class == "ocrx_word"
        assert elem.text == "hello"
        assert elem.bbox is None
        assert elem.children == []

    def test_element_with_bbox(self):
        bbox = BoundingBox(left=0, top=0, right=100, bottom=50)
        elem = OcrElement(ocr_class=OcrClass.LINE, bbox=bbox)
        assert elem.bbox == bbox
        assert elem.bbox.width == 100

    def test_element_hierarchy(self):
        word1 = OcrElement(ocr_class=OcrClass.WORD, text="Hello")
        word2 = OcrElement(ocr_class=OcrClass.WORD, text="World")
        line = OcrElement(ocr_class=OcrClass.LINE, children=[word1, word2])
        paragraph = OcrElement(ocr_class=OcrClass.PARAGRAPH, children=[line])
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[paragraph])

        assert len(page.children) == 1
        assert len(page.children[0].children) == 1
        assert len(page.children[0].children[0].children) == 2

    def test_iter_by_class_single(self):
        word = OcrElement(ocr_class=OcrClass.WORD, text="test")
        line = OcrElement(ocr_class=OcrClass.LINE, children=[word])
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[line])

        words = page.iter_by_class(OcrClass.WORD)
        assert len(words) == 1
        assert words[0].text == "test"

    def test_iter_by_class_multiple(self):
        words = [
            OcrElement(ocr_class=OcrClass.WORD, text="one"),
            OcrElement(ocr_class=OcrClass.WORD, text="two"),
            OcrElement(ocr_class=OcrClass.WORD, text="three"),
        ]
        line = OcrElement(ocr_class=OcrClass.LINE, children=words)
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[line])

        result = page.iter_by_class(OcrClass.WORD)
        assert len(result) == 3
        assert [w.text for w in result] == ["one", "two", "three"]

    def test_iter_by_class_multiple_types(self):
        line = OcrElement(ocr_class=OcrClass.LINE)
        header = OcrElement(ocr_class=OcrClass.HEADER)
        caption = OcrElement(ocr_class=OcrClass.CAPTION)
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[line, header, caption])

        result = page.iter_by_class(OcrClass.LINE, OcrClass.HEADER)
        assert len(result) == 2

    def test_find_by_class(self):
        word = OcrElement(ocr_class=OcrClass.WORD, text="found")
        line = OcrElement(ocr_class=OcrClass.LINE, children=[word])
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[line])

        result = page.find_by_class(OcrClass.WORD)
        assert result is not None
        assert result.text == "found"

    def test_find_by_class_not_found(self):
        line = OcrElement(ocr_class=OcrClass.LINE)
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[line])

        result = page.find_by_class(OcrClass.WORD)
        assert result is None

    def test_get_text_recursive_leaf(self):
        word = OcrElement(ocr_class=OcrClass.WORD, text="hello")
        assert word.get_text_recursive() == "hello"

    def test_get_text_recursive_nested(self):
        word1 = OcrElement(ocr_class=OcrClass.WORD, text="Hello")
        word2 = OcrElement(ocr_class=OcrClass.WORD, text="World")
        line = OcrElement(ocr_class=OcrClass.LINE, children=[word1, word2])

        assert line.get_text_recursive() == "Hello World"

    def test_words_property(self):
        words = [
            OcrElement(ocr_class=OcrClass.WORD, text="a"),
            OcrElement(ocr_class=OcrClass.WORD, text="b"),
        ]
        line = OcrElement(ocr_class=OcrClass.LINE, children=words)
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[line])

        assert len(page.words) == 2
        assert page.words[0].text == "a"

    def test_lines_property(self):
        line1 = OcrElement(ocr_class=OcrClass.LINE)
        line2 = OcrElement(ocr_class=OcrClass.HEADER)  # Also a line type
        par = OcrElement(ocr_class=OcrClass.PARAGRAPH, children=[line1, line2])
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[par])

        assert len(page.lines) == 2

    def test_paragraphs_property(self):
        par1 = OcrElement(ocr_class=OcrClass.PARAGRAPH)
        par2 = OcrElement(ocr_class=OcrClass.PARAGRAPH)
        page = OcrElement(ocr_class=OcrClass.PAGE, children=[par1, par2])

        assert len(page.paragraphs) == 2

    def test_direction_ltr(self):
        elem = OcrElement(ocr_class=OcrClass.PARAGRAPH, direction="ltr")
        assert elem.direction == "ltr"

    def test_direction_rtl(self):
        elem = OcrElement(ocr_class=OcrClass.PARAGRAPH, direction="rtl")
        assert elem.direction == "rtl"

    def test_language(self):
        elem = OcrElement(ocr_class=OcrClass.PARAGRAPH, language="eng")
        assert elem.language == "eng"

    def test_baseline(self):
        baseline = Baseline(slope=0.01, intercept=-3)
        elem = OcrElement(ocr_class=OcrClass.LINE, baseline=baseline)
        assert elem.baseline.slope == 0.01
        assert elem.baseline.intercept == -3

    def test_textangle(self):
        elem = OcrElement(ocr_class=OcrClass.LINE, textangle=5.0)
        assert elem.textangle == 5.0

    def test_confidence(self):
        elem = OcrElement(ocr_class=OcrClass.WORD, confidence=0.95)
        assert elem.confidence == 0.95

    def test_page_properties(self):
        elem = OcrElement(
            ocr_class=OcrClass.PAGE,
            dpi=300.0,
            page_number=0,
            logical_page_number=1,
        )
        assert elem.dpi == 300.0
        assert elem.page_number == 0
        assert elem.logical_page_number == 1


class TestOcrClass:
    """Tests for OcrClass constants."""

    def test_class_values(self):
        assert OcrClass.PAGE == "ocr_page"
        assert OcrClass.PARAGRAPH == "ocr_par"
        assert OcrClass.LINE == "ocr_line"
        assert OcrClass.WORD == "ocrx_word"
        assert OcrClass.HEADER == "ocr_header"
        assert OcrClass.CAPTION == "ocr_caption"

    def test_line_types_frozenset(self):
        assert OcrClass.LINE in OcrClass.LINE_TYPES
        assert OcrClass.HEADER in OcrClass.LINE_TYPES
        assert OcrClass.CAPTION in OcrClass.LINE_TYPES
        assert OcrClass.WORD not in OcrClass.LINE_TYPES
