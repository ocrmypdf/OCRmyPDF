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
from math import atan, cos, pi
from pathlib import Path
from typing import Any, NamedTuple
from xml.etree import ElementTree

from pikepdf import Matrix, Rectangle

from ocrmypdf.hocrtransform._canvas import PikepdfCanvas, PikepdfText
from ocrmypdf.hocrtransform.color import (
    BLACK,
    BLUE,
    CYAN,
    GREEN,
    MAGENTA,
    RED,
)

INCH = 72.0

Element = ElementTree.Element


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

    box_pattern = re.compile(r'bbox (\d+) (\d+) (\d+) (\d+)')
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

        self.width, self.height = None, None
        for div in self.hocr.findall(self._child_xpath('div', 'ocr_page')):
            coords = self.element_coordinates(div)
            self.width = (coords.urx - coords.llx) / (self.dpi / INCH)
            self.height = (coords.ury - coords.lly) / (self.dpi / INCH)
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
            render_space_bbox=False,
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
    def element_coordinates(cls, element: Element) -> Rectangle | None:
        """Get coordinates of the bounding box around an element."""
        if 'title' in element.attrib:
            matches = cls.box_pattern.search(element.attrib['title'])
            if matches:
                return Rectangle(
                    float(matches.group(1)),  # llx = left
                    float(matches.group(2)),  # lly = top
                    float(matches.group(3)),  # urx = right
                    float(matches.group(4)),  # ury = bottom
                )
        return None

    @classmethod
    def baseline(cls, element: Element) -> tuple[float, float]:
        """Get baseline's slope and intercept."""
        if 'title' in element.attrib:
            matches = cls.baseline_pattern.search(element.attrib['title'])
            if matches:
                return float(matches.group(1)), int(matches.group(2))
        return (0.0, 0.0)

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
        canvas = PikepdfCanvas(
            out_filename,
            page_size=(self.width, self.height),
        )
        canvas.push()
        page_matrix = (
            Matrix()
            .translated(0, self.height)
            .scaled(1, -1)
            .scaled(INCH / self.dpi, INCH / self.dpi)
        )
        canvas.cm(page_matrix)
        print(page_matrix)

        for elem in self.hocr.iterfind(self._child_xpath('p', 'ocr_par')):
            elemtxt = self._get_element_text(elem).rstrip()
            if len(elemtxt) == 0:
                continue

            ocr_par = self.element_coordinates(elem)
            # draw cyan box around paragraph
            if self.render_options.render_paragraph_bbox:
                # pragma: no cover
                canvas.set_stroke_color(CYAN)
                canvas.set_line_width(0.1)  # no line for bounding box
                canvas.rect(
                    ocr_par.llx, ocr_par.lly, ocr_par.width, ocr_par.height, fill=0
                )

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
        canvas.pop()
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
        canvas: PikepdfCanvas,
        line: Element | None,
        elemclass: str,
        fontname: str,
        invisible_text: bool,
        interword_spaces: bool,
    ):
        if line is None:
            return
        line_box = self.element_coordinates(line)
        assert line_box.ury > line_box.lly  # lly is top, ury is bottom

        self._do_debug_line_bbox(canvas, line_box)

        # Baseline is a polynomial (usually straight line) in the coordinate system
        # of the line
        slope, intercept = self.baseline(line)
        if abs(slope) < 0.005:
            slope = 0.0
        angle = atan(slope)

        # Setup a new coordinate system on the line box's intercept and rotated by
        # its slope
        canvas.push()
        line_matrix = (
            Matrix()
            .translated(line_box.llx, line_box.ury)
            .translated(0, intercept)
            .rotated(angle / pi * 180)
        )
        canvas.cm(line_matrix)
        print(line_matrix)
        text = canvas.begin_text()

        # Don't allow the font to break out of the bounding box. Division by
        # cos_a accounts for extra clearance between the glyph's vertical axis
        # on a sloped baseline and the edge of the bounding box.
        line_box_height = abs(line_box.height) / cos(angle)
        fontsize = line_box_height + intercept
        text.set_font(fontname, fontsize)
        if invisible_text or True:
            text.set_render_mode(3)  # Invisible (indicates OCR text)

        self._do_debug_baseline(canvas, line_matrix.inverse().transform(line_box), 0)
        canvas.set_fill_color(BLACK)  # text in black

        elements = line.findall(self._child_xpath('span', elemclass))
        for elem, next_elem in pairwise(elements + [None]):
            self._do_line_word(
                canvas,
                fontname,
                line_matrix,
                line_box_height,
                line_box,
                text,
                fontsize,
                elem,
                next_elem,
            )
        canvas.draw_text(text)
        canvas.pop()

    def _do_line_word(
        self,
        canvas: PikepdfCanvas,
        fontname,
        line_matrix: Matrix,
        line_height: float,
        line_box: Rectangle,
        text: PikepdfText,
        fontsize: float,
        elem: Element,
        next_elem: Element | None,
    ):
        elemtxt = self._get_element_text(elem).strip()
        elemtxt = self.normalize_text(elemtxt)
        if elemtxt == '':
            return

        box = self.element_coordinates(elem)
        if box is None:
            return
        box = line_matrix.inverse().transform(box)
        font_width = canvas.string_width(elemtxt, fontname, fontsize)

        # Debug sketches
        self._do_debug_word_triangle(canvas, box)
        self._do_debug_word_bbox(
            canvas,
            box.height,
            line_matrix.inverse().transform(line_box),
            box,
            box.width,
        )

        # If this word is 0 units wide, our best bet seems to be to suppress this text
        if font_width > 0:
            text.set_text_transform(Matrix(1, 0, 0, 1, box.llx, 0))
            text.set_horiz_scale(100 * box.width / font_width)
            text.show(elemtxt)

        if next_elem is not None:
            next_box = self.element_coordinates(next_elem)
            space_box = Rectangle(box.urx, line_box.lly, next_box.llx, line_box.ury)
            self._do_debug_space_bbox(canvas, space_box)
            text.set_text_transform(Matrix(1, 0, 0, 1, space_box.llx, 0))
            space_width = canvas.string_width(' ', fontname, fontsize)
            space_box_width = space_box.urx - space_box.llx
            text.set_horiz_scale(100 * space_box_width / space_width)
            text.show(' ')

    def _do_debug_line_bbox(self, canvas, line_box):
        if not self.render_options.render_line_bbox:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_stroke_color(BLUE)
        canvas.set_line_width(0.15)
        canvas.rect(
            line_box.llx,
            line_box.lly,
            line_box.width,
            line_box.height,
            fill=0,
        )
        canvas.pop()

    def _do_debug_word_triangle(
        self,
        canvas: PikepdfCanvas,
        box,
    ):
        if not self.render_options.render_triangle:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_stroke_color(RED)
        canvas.set_line_width(0.1)
        # Draw a triangle that conveys word height and drawing direction
        canvas.line(box.llx, box.lly, box.urx, box.lly)  # across bottom
        canvas.line(box.urx, box.lly, box.llx, box.ury)  # diagonal
        canvas.line(box.llx, box.lly, box.llx, box.ury)  # rise
        canvas.pop()

    def _do_debug_word_bbox(
        self, canvas: PikepdfCanvas, line_height, line_box, box, box_width
    ):
        if not self.render_options.render_word_bbox:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_stroke_color(GREEN)
        canvas.set_line_width(0.1)
        canvas.rect(box.llx, box.lly, box_width, line_height, fill=0)
        canvas.pop()

    def _do_debug_space_bbox(self, canvas: PikepdfCanvas, box):
        if not self.render_options.render_space_bbox:  # pragma: no cover
            return
        canvas.push()
        canvas.set_dashes()
        canvas.set_fill_color(GREEN)
        canvas.set_line_width(0.1)
        canvas.rect(box.llx, box.lly, box.width, box.height, fill=1)
        canvas.pop()

    def _do_debug_baseline(self, canvas, line_box, baseline_lly):
        if not self.render_options.render_baseline:
            return
        # draw the baseline in magenta, dashed
        canvas.set_dashes()
        canvas.set_stroke_color(MAGENTA)
        canvas.set_line_width(0.25)
        # negate slope because it is defined as a rise/run in pixel
        # coordinates and page coordinates have the y axis flipped
        canvas.line(
            line_box.llx,
            baseline_lly,
            line_box.urx,
            baseline_lly,
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
