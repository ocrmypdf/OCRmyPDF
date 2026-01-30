# SPDX-FileCopyrightText: 2010 Jonathan Brinley
# SPDX-FileCopyrightText: 2013-2014 Julien Pfefferkorn
# SPDX-FileCopyrightText: 2023-2025 James R. Barlow
# SPDX-License-Identifier: MIT

"""Parser for hOCR format files.

This module provides functionality to parse hOCR files (HTML-based OCR format)
and convert them to the engine-agnostic OcrElement tree structure.

For details of the hOCR format, see:
http://kba.github.io/hocr-spec/1.2/
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Literal, cast
from xml.etree import ElementTree as ET

from ocrmypdf.models.ocr_element import (
    Baseline,
    BoundingBox,
    FontInfo,
    OcrClass,
    OcrElement,
)

TextDirection = Literal["ltr", "rtl"]

log = logging.getLogger(__name__)

Element = ET.Element


class HocrParseError(Exception):
    """Error while parsing hOCR file."""


class HocrParser:
    """Parser for hOCR format files.

    Converts hOCR XML/HTML files into OcrElement trees.

    The hOCR format uses HTML with special class attributes (ocr_page, ocr_line,
    ocrx_word, etc.) and a title attribute containing properties like bbox,
    baseline, and confidence scores.
    """

    # Regex patterns for parsing hOCR title attributes
    _bbox_pattern = re.compile(
        r'''
        bbox \s+
        (\d+) \s+   # left: uint
        (\d+) \s+   # top: uint
        (\d+) \s+   # right: uint
        (\d+)       # bottom: uint
        ''',
        re.VERBOSE,
    )

    _baseline_pattern = re.compile(
        r'''
        baseline \s+
        ([\-\+]?\d*\.?\d*) \s+  # slope: +/- decimal float
        ([\-\+]?\d+)            # intercept: +/- int
        ''',
        re.VERBOSE,
    )

    _textangle_pattern = re.compile(
        r'''
        textangle \s+
        ([\-\+]?\d*\.?\d*)  # angle: +/- decimal float
        ''',
        re.VERBOSE,
    )

    _x_wconf_pattern = re.compile(
        r'''
        x_wconf \s+
        (\d+)  # confidence: uint (0-100)
        ''',
        re.VERBOSE,
    )

    _x_fsize_pattern = re.compile(
        r'''
        x_fsize \s+
        (\d*\.?\d+)  # font size: float
        ''',
        re.VERBOSE,
    )

    _x_font_pattern = re.compile(
        r'''
        x_font \s+
        ([^\s;]+)  # font name: non-whitespace, non-semicolon string
        ''',
        re.VERBOSE,
    )

    _ppageno_pattern = re.compile(
        r'''
        ppageno \s+
        (\d+)  # page number: uint
        ''',
        re.VERBOSE,
    )

    _scan_res_pattern = re.compile(
        r'''
        scan_res \s+
        (\d+) \s+  # x resolution
        (\d+)      # y resolution
        ''',
        re.VERBOSE,
    )

    def __init__(self, hocr_file: str | Path):
        """Initialize the parser with an hOCR file.

        Args:
            hocr_file: Path to the hOCR file to parse

        Raises:
            HocrParseError: If the file cannot be parsed
        """
        self._hocr_path = Path(hocr_file)
        try:
            self._tree = ET.parse(os.fspath(hocr_file))
        except ET.ParseError as e:
            raise HocrParseError(f"Failed to parse hOCR file: {e}") from e

        # Detect XML namespace
        root_tag = self._tree.getroot().tag
        matches = re.match(r'({.*})html', root_tag)
        self._xmlns = matches.group(1) if matches else ''

    def parse(self) -> OcrElement:
        """Parse the hOCR file and return an OcrElement tree.

        Returns:
            The root OcrElement (ocr_page) containing the document structure

        Raises:
            HocrParseError: If no ocr_page element is found
        """
        # Find the first ocr_page element
        page_div = self._tree.find(self._xpath('div', 'ocr_page'))
        if page_div is None:
            raise HocrParseError("No ocr_page element found in hOCR file")

        return self._parse_page(page_div)

    def _xpath(self, html_tag: str, html_class: str | None = None) -> str:
        """Build an XPath expression for finding elements.

        Args:
            html_tag: HTML tag name (e.g., 'div', 'span', 'p')
            html_class: Optional class attribute to match

        Returns:
            XPath expression string
        """
        xpath = f".//{self._xmlns}{html_tag}"
        if html_class:
            xpath += f"[@class='{html_class}']"
        return xpath

    def _parse_page(self, page_elem: Element) -> OcrElement:
        """Parse an ocr_page element.

        Args:
            page_elem: The XML element with class="ocr_page"

        Returns:
            OcrElement representing the page
        """
        title = page_elem.attrib.get('title', '')

        bbox = self._parse_bbox(title)
        if bbox is None:
            raise HocrParseError("ocr_page missing bbox")

        # Parse page-level properties
        page_number = self._parse_ppageno(title)
        dpi = self._parse_scan_res(title)

        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=bbox,
            page_number=page_number,
            dpi=dpi,
        )

        # Parse child paragraphs
        for par_elem in page_elem.iterfind(self._xpath('p', 'ocr_par')):
            paragraph = self._parse_paragraph(par_elem)
            if paragraph is not None:
                page.children.append(paragraph)

        # If no paragraphs found, check for words directly under page
        # (some Tesseract output structures)
        if not page.children:
            for word_elem in page_elem.iterfind(self._xpath('span', 'ocrx_word')):
                word = self._parse_word(word_elem)
                if word is not None:
                    page.children.append(word)

        return page

    def _parse_paragraph(self, par_elem: Element) -> OcrElement | None:
        """Parse an ocr_par element.

        Args:
            par_elem: The XML element with class="ocr_par"

        Returns:
            OcrElement representing the paragraph, or None if empty
        """
        title = par_elem.attrib.get('title', '')
        bbox = self._parse_bbox(title)

        # Get direction and language from attributes
        dir_attr = par_elem.attrib.get('dir')
        direction: TextDirection | None = (
            cast(TextDirection, dir_attr) if dir_attr in ('ltr', 'rtl') else None
        )

        language = par_elem.attrib.get('lang')

        paragraph = OcrElement(
            ocr_class=OcrClass.PARAGRAPH,
            bbox=bbox,
            direction=direction,
            language=language,
        )

        # Parse child lines
        line_classes = {
            'ocr_line',
            'ocr_header',
            'ocr_footer',
            'ocr_caption',
            'ocr_textfloat',
        }
        for span_elem in par_elem.iterfind(self._xpath('span')):
            elem_class = span_elem.attrib.get('class', '')
            if elem_class in line_classes:
                line = self._parse_line(span_elem, elem_class, direction, language)
                if line is not None:
                    paragraph.children.append(line)

        # Return None if paragraph is empty
        if not paragraph.children:
            return None

        return paragraph

    def _parse_line(
        self,
        line_elem: Element,
        ocr_class: str,
        parent_direction: TextDirection | None,
        parent_language: str | None,
    ) -> OcrElement | None:
        """Parse a line element (ocr_line, ocr_header, etc.).

        Args:
            line_elem: The XML element representing the line
            ocr_class: The hOCR class of the line
            parent_direction: Text direction inherited from parent
            parent_language: Language inherited from parent

        Returns:
            OcrElement representing the line, or None if empty
        """
        title = line_elem.attrib.get('title', '')
        bbox = self._parse_bbox(title)

        if bbox is None:
            return None

        baseline = self._parse_baseline(title)
        textangle = self._parse_textangle(title)

        # Inherit direction and language from parent if not specified
        dir_attr = line_elem.attrib.get('dir')
        if dir_attr in ('ltr', 'rtl'):
            direction: TextDirection | None = cast(TextDirection, dir_attr)
        else:
            direction = parent_direction

        language = line_elem.attrib.get('lang') or parent_language

        line = OcrElement(
            ocr_class=ocr_class,
            bbox=bbox,
            baseline=baseline,
            textangle=textangle,
            direction=direction,
            language=language,
        )

        # Parse child words
        for word_elem in line_elem.iterfind(self._xpath('span', 'ocrx_word')):
            word = self._parse_word(word_elem)
            if word is not None:
                line.children.append(word)

        # Return None if line has no words
        if not line.children:
            return None

        return line

    def _parse_word(self, word_elem: Element) -> OcrElement | None:
        """Parse an ocrx_word element.

        Args:
            word_elem: The XML element with class="ocrx_word"

        Returns:
            OcrElement representing the word, or None if empty
        """
        title = word_elem.attrib.get('title', '')
        bbox = self._parse_bbox(title)

        # Get the text content
        text = self._get_element_text(word_elem)
        text = self._normalize_text(text)

        if not text:
            return None

        # Parse confidence (x_wconf is 0-100, convert to 0.0-1.0)
        confidence = self._parse_x_wconf(title)
        if confidence is not None:
            confidence = confidence / 100.0

        # Parse font info
        font = self._parse_font_info(title)

        return OcrElement(
            ocr_class=OcrClass.WORD,
            bbox=bbox,
            text=text,
            confidence=confidence,
            font=font,
        )

    def _get_element_text(self, element: Element) -> str:
        """Get the full text content of an element including children.

        Args:
            element: XML element

        Returns:
            Combined text content
        """
        text = element.text if element.text is not None else ''
        for child in element:
            text += self._get_element_text(child)
        text += element.tail if element.tail is not None else ''
        return text

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text using NFKC normalization.

        This splits ligatures and combines diacritics.

        Args:
            text: Raw text

        Returns:
            Normalized text, stripped of leading/trailing whitespace
        """
        return unicodedata.normalize("NFKC", text).strip()

    def _parse_bbox(self, title: str) -> BoundingBox | None:
        """Parse a bbox from an hOCR title attribute.

        Args:
            title: The title attribute value

        Returns:
            BoundingBox or None if not found
        """
        match = self._bbox_pattern.search(title)
        if not match:
            return None

        try:
            return BoundingBox(
                left=float(match.group(1)),
                top=float(match.group(2)),
                right=float(match.group(3)),
                bottom=float(match.group(4)),
            )
        except ValueError:
            return None

    def _parse_baseline(self, title: str) -> Baseline | None:
        """Parse baseline from an hOCR title attribute.

        Args:
            title: The title attribute value

        Returns:
            Baseline or None if not found
        """
        match = self._baseline_pattern.search(title)
        if not match:
            return None

        try:
            return Baseline(
                slope=float(match.group(1)) if match.group(1) else 0.0,
                intercept=float(match.group(2)),
            )
        except ValueError:
            return None

    def _parse_textangle(self, title: str) -> float | None:
        """Parse textangle from an hOCR title attribute.

        Args:
            title: The title attribute value

        Returns:
            Angle in degrees or None if not found
        """
        match = self._textangle_pattern.search(title)
        if not match:
            return None

        try:
            return float(match.group(1))
        except ValueError:
            return None

    def _parse_x_wconf(self, title: str) -> float | None:
        """Parse word confidence from an hOCR title attribute.

        Args:
            title: The title attribute value

        Returns:
            Confidence (0-100) or None if not found
        """
        match = self._x_wconf_pattern.search(title)
        if not match:
            return None

        try:
            return float(match.group(1))
        except ValueError:
            return None

    def _parse_ppageno(self, title: str) -> int | None:
        """Parse physical page number from an hOCR title attribute.

        Args:
            title: The title attribute value

        Returns:
            Page number or None if not found
        """
        match = self._ppageno_pattern.search(title)
        if not match:
            return None

        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _parse_scan_res(self, title: str) -> float | None:
        """Parse scan resolution (DPI) from an hOCR title attribute.

        Args:
            title: The title attribute value

        Returns:
            DPI (using first value if x and y differ) or None if not found
        """
        match = self._scan_res_pattern.search(title)
        if not match:
            return None

        try:
            # Use the first (x) resolution value
            return float(match.group(1))
        except ValueError:
            return None

    def _parse_font_info(self, title: str) -> FontInfo | None:
        """Parse font information from an hOCR title attribute.

        Args:
            title: The title attribute value

        Returns:
            FontInfo or None if no font info found
        """
        font_match = self._x_font_pattern.search(title)
        size_match = self._x_fsize_pattern.search(title)

        if not font_match and not size_match:
            return None

        return FontInfo(
            name=font_match.group(1) if font_match else None,
            size=float(size_match.group(1)) if size_match else None,
        )
