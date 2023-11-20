# SPDX-FileCopyrightText: 2010 Jonathan Brinley
# SPDX-FileCopyrightText: 2013-2014 Julien Pfefferkorn
# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MIT

"""hOCR transform implementation."""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from itertools import pairwise
from math import atan, cos, pi
from pathlib import Path
from xml.etree import ElementTree

from pikepdf import Matrix, Rectangle

from ocrmypdf.hocrtransform._canvas import PikepdfCanvas as Canvas
from ocrmypdf.hocrtransform._canvas import PikepdfText
from ocrmypdf.hocrtransform.color import (
    BLACK,
    BLUE,
    CYAN,
    DARKGREEN,
    GREEN,
    MAGENTA,
    RED,
)

log = logging.getLogger(__name__)

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
            render_baseline=False,
            render_triangle=False,
            render_line_bbox=False,
            render_word_bbox=True,
            render_paragraph_bbox=False,
            render_space_bbox=True,
        )

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
    def normalize_text(cls, s: str) -> str:
        """Normalize the given text using the NFKC normalization form."""
        return unicodedata.normalize("NFKC", s)

    def to_pdf(
        self,
        *,
        out_filename: Path,
        image_filename: Path | None = None,
        fontname: str = "Helvetica",
        invisible_text: bool = False,
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
            fontname: Name of font to use.
            invisible_text: If True, text is rendered invisible so that is
                selectable but never drawn. If False, text is visible and may
                be seen if the image is skipped or deleted in Acrobat.
        """
        # create the PDF file
        # page size in points (1/72 in.)
        canvas = Canvas(page_size=(self.width, self.height))
        with canvas.do.enter_context():
            page_matrix = (
                Matrix()
                .translated(0, self.height)
                .scaled(1, -1)
                .scaled(INCH / self.dpi, INCH / self.dpi)
            )
            canvas.do.cm(page_matrix)
            log.debug(page_matrix)

            self._debug_draw_paragraph_boxes(canvas)

            found_lines = False
            for line in (
                element
                for element in self.hocr.iterfind(self._child_xpath('span'))
                if 'class' in element.attrib
                and element.attrib['class']
                in {'ocr_header', 'ocr_line', 'ocr_textfloat'}
            ):
                found_lines = True
                self._do_line(
                    canvas,
                    line,
                    "ocrx_word",
                    fontname,
                    invisible_text,
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
                )
        # put the image on the page, scaled to fill the page
        if image_filename is not None:
            canvas.do.draw_image(
                image_filename, 0, 0, width=self.width, height=self.height
            )

        # finish up the page and save it
        canvas.save(out_filename)

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
    ):
        """Render the text for a given line.

        The canvas's coordinate system must be configured so that hOCR pixel
        coordinates are mapped to PDF coordinates.
        """
        if line is None:
            return
        line_box = self.element_coordinates(line)
        assert line_box.ury > line_box.lly  # lly is top, ury is bottom

        self._debug_draw_line_bbox(canvas, line_box)

        # Baseline is a polynomial (usually straight line) that describes the
        # text baseline relative to the bottom left corner of the line bounding
        # box.
        bottom_left_corner = line_box.llx, line_box.ury
        slope, intercept = self.baseline(line)
        if abs(slope) < 0.005:
            slope = 0.0
        angle = atan(slope)

        # Setup a new coordinate system on the line box's intercept and rotated by
        # its slope.
        with canvas.do.enter_context():
            line_matrix = (
                Matrix()
                .translated(*bottom_left_corner)
                .translated(0, intercept)
                .rotated(angle / pi * 180)
            )
            canvas.do.cm(line_matrix)
            log.debug(line_matrix)
            text = PikepdfText()

            # Don't allow the font to break out of the bounding box. Division by
            # cos_a accounts for extra clearance between the glyph's vertical axis
            # on a sloped baseline and the edge of the bounding box.
            line_box_height = abs(line_box.height) / cos(angle)
            fontsize = line_box_height + intercept
            text.set_font(fontname, fontsize)
            if invisible_text or True:
                text.set_render_mode(3)  # Invisible (indicates OCR text)

            self._debug_draw_baseline(
                canvas, line_matrix.inverse().transform(line_box), 0
            )

            canvas.do.fill_color(BLACK)  # text in black
            elements = line.findall(self._child_xpath('span', elemclass))
            for elem, next_elem in pairwise(elements + [None]):
                self._do_line_word(
                    canvas,
                    fontname,
                    line_matrix,
                    text,
                    fontsize,
                    elem,
                    next_elem,
                )
            canvas.do.draw_text(text)

    def _do_line_word(
        self,
        canvas: Canvas,
        fontname,
        line_matrix: Matrix,
        text: PikepdfText,
        fontsize: float,
        elem: Element,
        next_elem: Element | None,
    ):
        """Render the text for a single word."""
        elemtxt = self.normalize_text(self._get_element_text(elem).strip())
        if elemtxt == '':
            return

        hocr_box = self.element_coordinates(elem)
        if hocr_box is None:
            return
        box = line_matrix.inverse().transform(hocr_box)
        font_width = canvas.string_width(elemtxt, fontname, fontsize)

        # Debug sketches
        self._debug_draw_word_triangle(canvas, box)
        self._debug_draw_word_bbox(canvas, box)

        # If this word is 0 units wide, our best bet seems to be to suppress this text
        if font_width > 0:
            text.set_text_transform(Matrix(1, 0, 0, 1, box.llx, 0))
            text.set_horiz_scale(100 * box.width / font_width)
            text.show(elemtxt)

        # Get coordinates of the next word (if there is one)
        hocr_next_box = (
            self.element_coordinates(next_elem) if next_elem is not None else None
        )
        if hocr_next_box is not None:
            # Render a space this word and the next word. The explicit space helps
            # PDF viewers identify the word break, and horizontally scaling it to
            # occupy the space the between the words helps the PDF viewer
            # avoid combiningthewordstogether.
            next_box = line_matrix.inverse().transform(hocr_next_box)
            space_box = Rectangle(box.urx, box.lly, next_box.llx, next_box.ury)
            self._debug_draw_space_bbox(canvas, space_box)
            text.set_text_transform(Matrix(1, 0, 0, 1, space_box.llx, 0))
            space_width = canvas.string_width(' ', fontname, fontsize)
            space_box_width = space_box.urx - space_box.llx
            text.set_horiz_scale(100 * space_box_width / space_width)
            text.show(' ')

    def _debug_draw_paragraph_boxes(self, canvas: Canvas, color=CYAN):
        """Draw boxes around paragraphs in the document."""
        if not self.render_options.render_paragraph_bbox:  # pragma: no cover
            return
        with canvas.do.enter_context():
            # draw box around paragraph
            canvas.do.stroke_color(color).line_width(0.1)
            for elem in self.hocr.iterfind(self._child_xpath('p', 'ocr_par')):
                elemtxt = self._get_element_text(elem).strip()
                if len(elemtxt) == 0:
                    continue
                ocr_par = self.element_coordinates(elem)
                canvas.do.rect(
                    ocr_par.llx, ocr_par.lly, ocr_par.width, ocr_par.height, fill=0
                )

    def _debug_draw_line_bbox(self, canvas: Canvas, line_box: Rectangle, color=BLUE):
        """Render the bounding box of a text line."""
        if not self.render_options.render_line_bbox:  # pragma: no cover
            return
        with canvas.do.enter_context():
            canvas.do.stroke_color(color).line_width(0.15).rect(
                line_box.llx, line_box.lly, line_box.width, line_box.height, fill=0
            )

    def _debug_draw_word_triangle(
        self, canvas: Canvas, box: Rectangle, color=RED, line_width=0.1
    ):
        """Render a triangle that conveys word height and drawing direction."""
        if not self.render_options.render_triangle:  # pragma: no cover
            return
        with canvas.do.enter_context():
            canvas.do.stroke_color(color).line_width(line_width).line(
                box.llx, box.lly, box.urx, box.lly
            ).line(box.urx, box.lly, box.llx, box.ury).line(
                box.llx, box.lly, box.llx, box.ury
            )

    def _debug_draw_word_bbox(
        self, canvas: Canvas, box: Rectangle, color=GREEN, line_width=0.1
    ):
        """Render a box depicting the word."""
        if not self.render_options.render_word_bbox:  # pragma: no cover
            return
        with canvas.do.enter_context():
            canvas.do.stroke_color(color).line_width(line_width).rect(
                box.llx, box.lly, box.width, box.height, fill=0
            )

    def _debug_draw_space_bbox(
        self, canvas: Canvas, box: Rectangle, color=DARKGREEN, line_width=0.1
    ):
        """Render a box depicting the space between two words."""
        if not self.render_options.render_space_bbox:  # pragma: no cover
            return
        with canvas.do.enter_context():
            canvas.do.fill_color(color).line_width(line_width).rect(
                box.llx, box.lly, box.width, box.height, fill=1
            )

    def _debug_draw_baseline(
        self,
        canvas: Canvas,
        line_box: Rectangle,
        baseline_lly,
        color=MAGENTA,
        line_width=0.25,
    ):
        """Render the text baseline."""
        if not self.render_options.render_baseline:
            return
        with canvas.do.enter_context():
            canvas.do.stroke_color(color).line_width(line_width).line(
                line_box.llx,
                baseline_lly,
                line_box.urx,
                baseline_lly,
            )
