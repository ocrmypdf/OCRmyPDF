#!/usr/bin/env python3
#
# Copyright (c) 2010, Jonathan Brinley
#   Original version from: https://github.com/jbrinley/HocrConverter
#
# Copyright (c) 2013-14, Julien Pfefferkorn
#   Modifications
#
# Copyright (c) 2015-16, James R. Barlow
#   Set text to transparent
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
import os
import re
from collections import namedtuple
from math import atan, cos, sin
from pathlib import Path
from xml.etree import ElementTree

from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

Rect = namedtuple('Rect', ['x1', 'y1', 'x2', 'y2'])


class HocrTransformError(Exception):
    pass


class HocrTransform:

    """
    A class for converting documents from the hOCR format.
    For details of the hOCR format, see:
    http://kba.cloud/hocr-spec/
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

    def __init__(self, hocr_filename: str, dpi: float):
        self.dpi = dpi
        self.hocr = ElementTree.parse(hocr_filename)

        # if the hOCR file has a namespace, ElementTree requires its use to
        # find elements
        matches = re.match(r'({.*})html', self.hocr.getroot().tag)
        self.xmlns = ''
        if matches:
            self.xmlns = matches.group(1)

        # get dimension in pt (not pixel!!!!) of the OCRed image
        self.width, self.height = None, None
        for div in self.hocr.findall(".//%sdiv[@class='ocr_page']" % (self.xmlns)):
            coords = self.element_coordinates(div)
            pt_coords = self.pt_from_pixel(coords)
            self.width = pt_coords.x2 - pt_coords.x1
            self.height = pt_coords.y2 - pt_coords.y1
            # there shouldn't be more than one, and if there is, we don't want
            # it
            break
        if self.width is None or self.height is None:
            raise HocrTransformError("hocr file is missing page dimensions")

    def __str__(self):  # pragma: no cover
        """
        Return the textual content of the HTML body
        """
        if self.hocr is None:
            return ''
        body = self.hocr.find(".//%sbody" % (self.xmlns))
        if body:
            return self._get_element_text(body)
        else:
            return ''

    def _get_element_text(self, element):
        """
        Return the textual content of the element and its children
        """
        text = ''
        if element.text is not None:
            text += element.text
        for child in element.getchildren():
            text += self._get_element_text(child)
        if element.tail is not None:
            text += element.tail
        return text

    @classmethod
    def element_coordinates(cls, element) -> Rect:
        """
        Returns a tuple containing the coordinates of the bounding box around
        an element
        """
        out = Rect._make(0 for _ in range(4))
        if 'title' in element.attrib:
            matches = cls.box_pattern.search(element.attrib['title'])
            if matches:
                coords = matches.group(1).split()
                out = Rect._make(int(coords[n]) for n in range(4))
        return out

    @classmethod
    def baseline(cls, element):
        """
        Returns a tuple containing the baseline slope and intercept.
        """
        if 'title' in element.attrib:
            matches = cls.baseline_pattern.search(element.attrib['title'])
            if matches:
                return float(matches.group(1)), int(matches.group(2))
        return (0.0, 0.0)

    def pt_from_pixel(self, pxl):
        """
        Returns the quantity in PDF units (pt) given quantity in pixels
        """
        return Rect._make((c / self.dpi * inch) for c in pxl)

    @classmethod
    def replace_unsupported_chars(cls, s: str):
        """
        Given an input string, returns the corresponding string that:
        - is available in the helvetica facetype
        - does not contain any ligature (to allow easy search in the PDF file)
        """
        return s.translate(cls.ligatures)

    def to_pdf(
        self,
        out_filename: Path,
        image_filename: Path = None,
        show_bounding_boxes: bool = False,
        fontname: str = "Helvetica",
        invisible_text: bool = False,
        interword_spaces: bool = False,
    ):
        """
        Creates a PDF file with an image superimposed on top of the text.
        Text is positioned according to the bounding box of the lines in
        the hOCR file.
        The image need not be identical to the image used to create the hOCR
        file.
        It can have a lower resolution, different color mode, etc.
        """
        # create the PDF file
        # page size in points (1/72 in.)
        pdf = Canvas(
            os.fspath(out_filename),
            pagesize=(self.width, self.height),
            pageCompression=1,
        )

        # draw bounding box for each paragraph
        # light blue for bounding box of paragraph
        pdf.setStrokeColorRGB(0, 1, 1)
        # light blue for bounding box of paragraph
        pdf.setFillColorRGB(0, 1, 1)
        pdf.setLineWidth(0)  # no line for bounding box
        for elem in self.hocr.findall(".//%sp[@class='%s']" % (self.xmlns, "ocr_par")):

            elemtxt = self._get_element_text(elem).rstrip()
            if len(elemtxt) == 0:
                continue

            pxl_coords = self.element_coordinates(elem)
            pt = self.pt_from_pixel(pxl_coords)

            # draw the bbox border
            if show_bounding_boxes:  # pragma: no cover
                pdf.rect(
                    pt.x1, self.height - pt.y2, pt.x2 - pt.x1, pt.y2 - pt.y1, fill=1
                )

        found_lines = False
        for line in self.hocr.findall(
            ".//%sspan[@class='%s']" % (self.xmlns, "ocr_line")
        ):
            found_lines = True
            self._do_line(
                pdf,
                line,
                "ocrx_word",
                fontname,
                invisible_text,
                interword_spaces,
                show_bounding_boxes,
            )

        if not found_lines:
            # Tesseract did not report any lines (just words)
            root = self.hocr.find(".//%sdiv[@class='%s']" % (self.xmlns, "ocr_page"))
            self._do_line(
                pdf,
                root,
                "ocrx_word",
                fontname,
                invisible_text,
                interword_spaces,
                show_bounding_boxes,
            )
        # put the image on the page, scaled to fill the page
        if image_filename is not None:
            pdf.drawImage(
                os.fspath(image_filename), 0, 0, width=self.width, height=self.height
            )

        # finish up the page and save it
        pdf.showPage()
        pdf.save()

    @classmethod
    def polyval(cls, poly, x):  # pragma: no cover
        return x * poly[0] + poly[1]

    def _do_line(
        self,
        pdf: Canvas,
        line,
        elemclass: str,
        fontname: str,
        invisible_text: bool,
        interword_spaces: bool,
        show_bounding_boxes: bool,
    ):
        pxl_line_coords = self.element_coordinates(line)
        line_box = self.pt_from_pixel(pxl_line_coords)
        line_height = line_box.y2 - line_box.y1

        slope, pxl_intercept = self.baseline(line)
        if abs(slope) < 0.005:
            slope = 0.0
        angle = atan(slope)
        cos_a, sin_a = cos(angle), sin(angle)

        text = pdf.beginText()
        intercept = pxl_intercept / self.dpi * inch

        # Don't allow the font to break out of the bounding box. Division by
        # cos_a accounts for extra clearance between the glyph's vertical axis
        # on a sloped baseline and the edge of the bounding box.
        fontsize = (line_height - abs(intercept)) / cos_a
        text.setFont(fontname, fontsize)
        if invisible_text:
            text.setTextRenderMode(3)  # Invisible (indicates OCR text)

        # Intercept is normally negative, so this places it above the bottom
        # of the line box
        baseline_y2 = self.height - (line_box.y2 + intercept)

        if show_bounding_boxes:  # pragma: no cover
            # draw the baseline in magenta, dashed
            pdf.setDash()
            pdf.setStrokeColorRGB(0.95, 0.65, 0.95)
            pdf.setLineWidth(0.5)
            # negate slope because it is defined as a rise/run in pixel
            # coordinates and page coordinates have the y axis flipped
            pdf.line(
                line_box.x1,
                baseline_y2,
                line_box.x2,
                self.polyval((-slope, baseline_y2), line_box.x2 - line_box.x1),
            )
            # light green for bounding box of word/line
            pdf.setDash(6, 3)
            pdf.setStrokeColorRGB(1, 0, 0)

        text.setTextTransform(cos_a, -sin_a, sin_a, cos_a, line_box.x1, baseline_y2)
        pdf.setFillColorRGB(0, 0, 0)  # text in black

        elements = line.findall(".//%sspan[@class='%s']" % (self.xmlns, elemclass))
        for elem in elements:
            elemtxt = self._get_element_text(elem).strip()
            elemtxt = self.replace_unsupported_chars(elemtxt)
            if elemtxt == '':
                continue

            pxl_coords = self.element_coordinates(elem)
            box = self.pt_from_pixel(pxl_coords)
            if interword_spaces:
                # if  `--interword-spaces` is true, append a space
                # to the end of each text element to allow simpler PDF viewers
                # such as PDF.js to better recognize words in search and copy
                # and paste. Do not remove space from last word in line, even
                # though it would look better, because it will interfere with
                # naive text extraction. \n does not work either.
                elemtxt += ' '
                box = Rect._make(
                    (
                        box.x1,
                        line_box.y1,
                        box.x2 + pdf.stringWidth(' ', fontname, line_height),
                        line_box.y2,
                    )
                )
            box_width = box.x2 - box.x1
            font_width = pdf.stringWidth(elemtxt, fontname, fontsize)

            # draw the bbox border
            if show_bounding_boxes:  # pragma: no cover
                pdf.rect(
                    box.x1, self.height - line_box.y2, box_width, line_height, fill=0
                )

            # Adjust relative position of cursor
            # This is equivalent to:
            #   text.setTextOrigin(pt.x1, self.height - line_box.y2)
            # but the former generates a full text reposition matrix (Tm) in the
            # content stream while this issues a "offset" (Td) command.
            # .moveCursor() is relative to start of the text line, where the
            # "text line" means whatever reportlab defines it as. Do not use
            # use .getCursor(), since moveCursor() rather unintuitively plans
            # its moves relative to .getStartOfLine().
            # For skewed lines, in the text transform we set up a rotated
            # coordinate system, so we don't have to account for the
            # incremental offset. Surprisingly most PDF viewers can handle this.
            cursor = text.getStartOfLine()
            dx = box.x1 - cursor[0]
            dy = baseline_y2 - cursor[1]
            text.moveCursor(dx, dy)

            # If reportlab tells us this word is 0 units wide, our best seems
            # to be to suppress this text
            if font_width > 0:
                text.setHorizScale(100 * box_width / font_width)
                text.textOut(elemtxt)
        pdf.drawText(text)


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

    hocr = HocrTransform(args.hocrfile, args.resolution)
    hocr.to_pdf(
        args.outputfile,
        args.image,
        args.boundingboxes,
        interword_spaces=args.interword_spaces,
    )
