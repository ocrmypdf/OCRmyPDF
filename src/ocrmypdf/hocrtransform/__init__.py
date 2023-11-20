#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2010 Jonathan Brinley
# SPDX-FileCopyrightText: 2013-2014 Julien Pfefferkorn
# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT

"""Transform .hocr and page image to text PDF."""

from __future__ import annotations

import argparse
import os
import re
import unicodedata
from dataclasses import dataclass
from itertools import pairwise
from math import atan, cos, pi, sin
from pathlib import Path
from typing import Any, NamedTuple
from xml.etree import ElementTree

from pikepdf import PdfMatrix

from ocrmypdf.hocrtransform.backends import (
    Canvas,
)
from ocrmypdf.hocrtransform.backends.pikepdf import PikepdfCanvas
from ocrmypdf.hocrtransform.backends.reportlab import (
    ReportlabCanvas,
    black,
    blue,
    cyan,
    green,
    inch,
    magenta,
    red,
)

# According to Wikipedia these languages are supported in the ISO-8859-1 character
# set, meaning reportlab can generate them and they are compatible with hocr,
# assuming Tesseract has the necessary languages installed. Note that there may
# not be language packs for them.
HOCR_OK_LANGS = frozenset(
    [
        # Languages fully covered by Latin-1:
        'afr',  # Afrikaans
        'alb',  # Albanian
        'ast',  # Leonese
        'baq',  # Basque
        'bre',  # Breton
        'cos',  # Corsican
        'eng',  # English
        'eus',  # Basque
        'fao',  # Faoese
        'gla',  # Scottish Gaelic
        'glg',  # Galician
        'glv',  # Manx
        'ice',  # Icelandic
        'ind',  # Indonesian
        'isl',  # Icelandic
        'ita',  # Italian
        'ltz',  # Luxembourgish
        'mal',  # Malay Rumi
        'mga',  # Irish
        'nor',  # Norwegian
        'oci',  # Occitan
        'por',  # Portugeuse
        'roh',  # Romansh
        'sco',  # Scots
        'sma',  # Sami
        'spa',  # Spanish
        'sqi',  # Albanian
        'swa',  # Swahili
        'swe',  # Swedish
        'tgl',  # Tagalog
        'wln',  # Walloon
        # Languages supported by Latin-1 except for a few rare characters that OCR
        # is probably not trained to recognize anyway:
        'cat',  # Catalan
        'cym',  # Welsh
        'dan',  # Danish
        'deu',  # German
        'dut',  # Dutch
        'est',  # Estonian
        'fin',  # Finnish
        'fra',  # French
        'hun',  # Hungarian
        'kur',  # Kurdish
        'nld',  # Dutch
        'wel',  # Welsh
    ]
)


Element = ElementTree.Element


class Rect(NamedTuple):
    """A rectangle for managing PDF coordinates."""

    x1: Any
    y1: Any
    x2: Any
    y2: Any

    def transform(self, matrix, inverse=True):
        """Transform the rectangle by the given matrix."""
        if inverse:
            matrix = matrix.inverse()
        return Rect._make(
            [
                matrix.a * self.x1 + matrix.c * self.y1 + matrix.e,
                matrix.b * self.x1 + matrix.d * self.y1 + matrix.f,
                matrix.a * self.x2 + matrix.c * self.y2 + matrix.e,
                matrix.b * self.x2 + matrix.d * self.y2 + matrix.f,
            ]
        )


@dataclass
class DebugRenderOptions:
    """A class for managing rendering options."""

    render_paragraph_bbox: bool
    render_baseline: bool
    render_triangle: bool
    render_line_bbox: bool
    render_word_bbox: bool
    render_space_bbox: bool


class HocrTransformError(Exception):
    """Error while applying hOCR transform."""


class HocrTransform:
    """A class for converting documents from the hOCR format.

    For details of the hOCR format, see:
    http://kba.cloud/hocr-spec/.
    """

    box_pattern = re.compile(r'bbox((\s+\d+){4})')
    baseline_pattern = re.compile(
        r'''
        baseline \s+
        ([\-\+]?\d*\.?\d*) \s+  # +/- decimal float
        ([\-\+]?\d+)            # +/- int''',
        re.VERBOSE,
    )
    ligatures = str.maketrans(
        {'ﬀ': 'ff', 'ﬃ': 'f‌f‌i', 'ﬄ': 'f‌f‌l', 'ﬁ': 'fi', 'ﬂ': 'fl'}
    )

    def __init__(self, *, hocr_filename: str | Path, dpi: float):
        """Initialize the HocrTransform object."""
        self.dpi = dpi
        self.hocr = ElementTree.parse(os.fspath(hocr_filename))

        # if the hOCR file has a namespace, ElementTree requires its use to
        # find elements
        matches = re.match(r'({.*})html', self.hocr.getroot().tag)
        self.xmlns = ''
        if matches:
            self.xmlns = matches.group(1)

        # get dimension in pt (not pixel!!!!) of the OCRed image
        self.width, self.height = None, None
        for div in self.hocr.findall(self._child_xpath('div', 'ocr_page')):
            coords = self.element_coordinates(div)
            pt_coords = self.pt_from_pixel(coords)
            self.width = pt_coords.x2 - pt_coords.x1
            self.height = pt_coords.y2 - pt_coords.y1
            # there shouldn't be more than one, and if there is, we don't want
            # it
            break
        if self.width is None or self.height is None:
            raise HocrTransformError("hocr file is missing page dimensions")
        self.render_options = DebugRenderOptions(
            render_baseline=True,
            render_triangle=False,
            render_line_bbox=False,
            render_word_bbox=True,
            render_paragraph_bbox=False,
            render_space_bbox=True,
        )

    def __str__(self):  # pragma: no cover
        """Return the textual content of the HTML body."""
        if self.hocr is None:
            return ''
        body = self.hocr.find(self._child_xpath('body'))
        if body:
            return self._get_element_text(body)
        else:
            return ''

    def _get_element_text(self, element: Element):
        """Return the textual content of the element and its children."""
        text = ''
        if element.text is not None:
            text += element.text
        for child in element:
            text += self._get_element_text(child)
        if element.tail is not None:
            text += element.tail
        return text

    @classmethod
    def element_coordinates(cls, element: Element) -> Rect:
        """Get coordinates of the bounding box around an element."""
        out = Rect._make(0 for _ in range(4))
        if 'title' in element.attrib:
            matches = cls.box_pattern.search(element.attrib['title'])
            if matches:
                coords = matches.group(1).split()
                out = Rect._make(int(coords[n]) for n in range(4))
        return out

    @classmethod
    def baseline(cls, element: Element) -> tuple[float, float]:
        """Get baseline's slope and intercept."""
        if 'title' in element.attrib:
            matches = cls.baseline_pattern.search(element.attrib['title'])
            if matches:
                return float(matches.group(1)), int(matches.group(2))
        return (0.0, 0.0)

    def pt_from_pixel(self, pxl: Rect, bottomup=False) -> Rect:
        """Returns the quantity in PDF units (pt) given quantity in pixels."""
        if bottomup:
            return Rect._make(
                [
                    (pxl.x1 / self.dpi * inch),
                    self.height - (pxl.y2 / self.dpi * inch),  # swap y1/y2
                    (pxl.x2 / self.dpi * inch),
                    self.height - (pxl.y1 / self.dpi * inch),
                ]
            )
        else:
            return Rect._make(
                (c / self.dpi * inch) for c in (pxl.x1, pxl.y1, pxl.x2, pxl.y2)
            )

    def _child_xpath(self, html_tag: str, html_class: str | None = None) -> str:
        xpath = f".//{self.xmlns}{html_tag}"
        if html_class:
            xpath += f"[@class='{html_class}']"
        return xpath

    @classmethod
    def replace_unsupported_chars(cls, s: str) -> str:
        """Replaces characters with those available in the Helvetica typeface."""
        return s.translate(cls.ligatures)

    @classmethod
    def normalize_text(cls, s: str) -> str:
        """Normalize the given text using the NFKC normalization form."""
        return unicodedata.normalize("NFKC", s)

    def to_pdf(
        self,
        *,
        out_filename: Path,
        image_filename: Path | None = None,
        show_bounding_boxes: bool = False,
        fontname: str = "Helvetica",
        invisible_text: bool = False,
        interword_spaces: bool = False,
    ) -> None:
        """Creates a PDF file with an image superimposed on top of the text.

        Text is positioned according to the bounding box of the lines in
        the hOCR file.
        The image need not be identical to the image used to create the hOCR
        file.
        It can have a lower resolution, different color mode, etc.

        Arguments:
            out_filename: Path of PDF to write.
            image_filename: Image to use for this file. If omitted, the OCR text
                is shown.
            show_bounding_boxes: Show bounding boxes around various text regions,
                for debugging.
            fontname: Name of font to use.
            invisible_text: If True, text is rendered invisible so that is
                selectable but never drawn. If False, text is visible and may
                be seen if the image is skipped or deleted in Acrobat.
            interword_spaces: If True, insert spaces between words rather than
                drawing each word without spaces. Generally this improves text
                extraction.
        """
        # create the PDF file
        # page size in points (1/72 in.)
        canvas = PikepdfCanvas(  # ReportlabCanvas(
            out_filename,
            page_size=(self.width, self.height),
        )

        for elem in self.hocr.iterfind(self._child_xpath('p', 'ocr_par')):
            elemtxt = self._get_element_text(elem).rstrip()
            if len(elemtxt) == 0:
                continue

            pxl_coords = self.element_coordinates(elem)
            pt = self.pt_from_pixel(pxl_coords, bottomup=True)
            # draw cyan box around paragraph
            if self.render_options.render_paragraph_bbox:
                # pragma: no cover
                canvas.set_stroke_color(cyan)
                canvas.set_line_width(0.1)  # no line for bounding box
                canvas.rect(pt.x1, pt.y2, pt.x2 - pt.x1, pt.y2 - pt.y1, fill=0)

        found_lines = False
        for line in (
            element
            for element in self.hocr.iterfind(self._child_xpath('span'))
            if 'class' in element.attrib
            and element.attrib['class'] in {'ocr_header', 'ocr_line', 'ocr_textfloat'}
        ):
            found_lines = True
            self._do_line(
                canvas,
                line,
                "ocrx_word",
                fontname,
                invisible_text,
                interword_spaces,
            )

        if not found_lines:
            # Tesseract did not report any lines (just words)
            root = self.hocr.find(self._child_xpath('div', 'ocr_page'))
            self._do_line(
                canvas,
                root,
                "ocrx_word",
                fontname,
                invisible_text,
                interword_spaces,
            )
        # put the image on the page, scaled to fill the page
        if image_filename is not None:
            canvas.draw_image(
                image_filename, 0, 0, width=self.width, height=self.height
            )

        # finish up the page and save it
        canvas.save()

    @classmethod
    def polyval(cls, poly, x):  # pragma: no cover
        """Calculate the value of a polynomial at a point."""
        return x * poly[0] + poly[1]

    def _do_line(
        self,
        canvas: Canvas,
        line: Element | None,
        elemclass: str,
        fontname: str,
        invisible_text: bool,
        interword_spaces: bool,
    ):
        if line is None:
            return
        pxl_line_coords = self.element_coordinates(line)
        line_box = self.pt_from_pixel(pxl_line_coords, bottomup=True)

        assert line_box.y2 > line_box.y1

        # Baseline is a polynomial (usually straight line) in the coordinate system
        # of the line
        slope, pxl_intercept = self.baseline(line)
        if abs(slope) < 0.005:
            slope = 0.0
        angle = atan(slope)
        intercept = pxl_intercept / self.dpi * inch

        # Enter a new coordinate system with the linebox at the origin
        canvas.push()
        line_matrix = (
            PdfMatrix().translated(line_box.x1, line_box.y1).rotated(-angle / pi * 180)
        )
        canvas.cm(*line_matrix.shorthand)

        cm_line_box = line_box.transform(line_matrix, inverse=True)
        cm_line_height = cm_line_box.y2 - cm_line_box.y1

        text = canvas.begin_text()

        # Don't allow the font to break out of the bounding box. Division by
        # cos_a accounts for extra clearance between the glyph's vertical axis
        # on a sloped baseline and the edge of the bounding box.
        fontsize = cm_line_height - abs(intercept)
        text.set_font(fontname, fontsize)
        if invisible_text or True:
            text.set_render_mode(3)  # Invisible (indicates OCR text)

        # Intercept is normally negative. Subtracting it will raise the baseline
        # above the bottom of the bounding box (y1).
        baseline_y1 = cm_line_box.y1 - intercept

        self._do_debug_line_bbox(canvas, cm_line_box)
        self._do_debug_baseline(canvas, 0, cm_line_box, baseline_y1)
        text.set_text_transform(1, 0, 0, 1, line_box.x1, baseline_y1)
        canvas.set_fill_color(black)  # text in black

        elements = line.findall(self._child_xpath('span', elemclass))
        for elem, next_elem in pairwise(elements + [None]):
            self._do_line_word(
                canvas,
                fontname,
                interword_spaces,
                cm_line_height,
                line_matrix,
                cm_line_box,
                text,
                fontsize,
                elem,
                next_elem,
            )
        canvas.draw_text(text)
        canvas.pop()

    def _do_line_word(
        self,
        canvas,
        fontname,
        interword_spaces,
        line_height,
        line_matrix,
        cm_line_box,
        text,
        fontsize,
        elem,
        next_elem,
    ):
        elemtxt = self._get_element_text(elem).strip()
        elemtxt = self.normalize_text(elemtxt)
        if elemtxt == '':
            return

        pxl_coords = self.element_coordinates(elem)
        box = self.pt_from_pixel(pxl_coords, bottomup=True)
        cm_box = box.transform(line_matrix, inverse=True)

        box_width = cm_box.x2 - cm_box.x1
        font_width = canvas.string_width(elemtxt, fontname, fontsize)

        # Debug sketches
        self._do_debug_word_triangle(canvas, cm_box)
        self._do_debug_word_bbox(canvas, line_height, cm_line_box, cm_box, box_width)

        # If this word is 0 units wide, our best bet seems to be to suppress this text
        if font_width > 0:
            text.set_text_transform(1, 0, 0, 1, cm_box.x1, cm_line_box.y1)
            text.set_horiz_scale(100 * box_width / font_width)
            text.show(elemtxt)

        if interword_spaces and next_elem is not None:
            next_box = self.pt_from_pixel(
                self.element_coordinates(next_elem), bottomup=True
            )
            next_cm_box = next_box.transform(line_matrix, inverse=True)
            space_box = Rect(cm_box.x2, cm_line_box.y1, next_cm_box.x1, cm_line_box.y2)
            self._do_debug_space_bbox(canvas, space_box)
            text.set_text_transform(1, 0, 0, 1, space_box.x1, cm_line_box.y1)
            space_width = canvas.string_width(' ', fontname, fontsize)
            box_width = space_box.x2 - space_box.x1
            text.set_horiz_scale(100 * box_width / space_width)
            text.show(' ')

    def _do_debug_line_bbox(self, canvas, line_box):
        if not self.render_options.render_line_bbox:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_stroke_color(blue)
        canvas.set_line_width(0.15)
        canvas.rect(
            line_box.x1,
            line_box.y1,
            line_box.x2 - line_box.x1,
            line_box.y2 - line_box.y1,
            fill=0,
        )
        canvas.pop()

    def _do_debug_word_triangle(
        self,
        canvas,
        cm_box,
    ):
        if not self.render_options.render_triangle:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_stroke_color(red)
        canvas.set_line_width(0.1)
        # Draw a triangle that conveys word height and drawing direction
        canvas.line(cm_box.x1, cm_box.y1, cm_box.x2, cm_box.y1)  # across bottom
        canvas.line(cm_box.x2, cm_box.y1, cm_box.x1, cm_box.y2)  # diagonal
        canvas.line(cm_box.x1, cm_box.y1, cm_box.x1, cm_box.y2)  # rise
        canvas.pop()

    def _do_debug_word_bbox(self, canvas, line_height, cm_line_box, cm_box, box_width):
        if not self.render_options.render_word_bbox:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_stroke_color(green)
        canvas.set_line_width(0.1)
        canvas.rect(cm_box.x1, cm_line_box.y1, box_width, line_height, fill=0)
        canvas.pop()

    def _do_debug_space_bbox(self, canvas, box):
        if not self.render_options.render_space_bbox:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_fill_color(green)
        canvas.set_line_width(0.1)
        canvas.rect(box.x1, box.y1, box.x2 - box.x1, box.y2 - box.y1, fill=1)
        canvas.pop()

    def _do_debug_baseline(self, canvas, slope, line_box, baseline_y1):
        if not self.render_options.render_baseline:
            return
        # draw the baseline in magenta, dashed
        canvas.set_dashes()
        canvas.set_stroke_color(magenta)
        canvas.set_line_width(0.25)
        # negate slope because it is defined as a rise/run in pixel
        # coordinates and page coordinates have the y axis flipped
        canvas.line(
            line_box.x1,
            baseline_y1,
            line_box.x2,
            baseline_y1,
            # self.polyval((-slope, baseline_y1), line_box.x2 - line_box.x1),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert hocr file to PDF')
    parser.add_argument(
        '-b',
        '--boundingboxes',
        action="store_true",
        default=False,
        help='Show bounding boxes borders',
    )
    parser.add_argument(
        '-r',
        '--resolution',
        type=int,
        default=300,
        help='Resolution of the image that was OCRed',
    )
    parser.add_argument(
        '-i',
        '--image',
        default=None,
        help='Path to the image to be placed above the text',
    )
    parser.add_argument(
        '--interword-spaces',
        action='store_true',
        default=False,
        help='Add spaces between words',
    )
    parser.add_argument('hocrfile', help='Path to the hocr file to be parsed')
    parser.add_argument('outputfile', help='Path to the PDF file to be generated')
    args = parser.parse_args()

    hocr = HocrTransform(hocr_filename=args.hocrfile, dpi=args.resolution)
    hocr.to_pdf(
        out_filename=args.outputfile,
        image_filename=args.image,
        show_bounding_boxes=args.boundingboxes,
        interword_spaces=args.interword_spaces,
    )
