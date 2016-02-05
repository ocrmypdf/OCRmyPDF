#!/usr/bin/env python3
##############################################################################
# Copyright (c) 2013-14: fritz-hh from Github
#   (https://github.com/fritz-hh)
#
# Copyright (c) 2010: Jonathan Brinley from Github
#   (https://github.com/jbrinley/HocrConverter)
#   Initial version by Jonathan Brinley, jonathanbrinley@gmail.com
##############################################################################
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from xml.etree import ElementTree
from PIL import Image
from collections import namedtuple
import re
import argparse


Rect = namedtuple('Rect', ['x1', 'y1', 'x2', 'y2'])


class HocrTransformError(Exception):
    pass


class HocrTransform():

    """
    A class for converting documents from the hOCR format.
    For details of the hOCR format, see:
    http://docs.google.com/View?docid=dfxcv4vc_67g844kf
    """

    def __init__(self, hocrFileName, dpi):
        self.dpi = dpi
        self.boxPattern = re.compile(r'bbox((\s+\d+){4})')

        self.hocr = ElementTree.parse(hocrFileName)

        # if the hOCR file has a namespace, ElementTree requires its use to
        # find elements
        matches = re.match(r'({.*})html', self.hocr.getroot().tag)
        self.xmlns = ''
        if matches:
            self.xmlns = matches.group(1)

        # get dimension in pt (not pixel!!!!) of the OCRed image
        self.width, self.height = None, None
        for div in self.hocr.findall(
                ".//%sdiv[@class='ocr_page']" % (self.xmlns)):
            coords = self.element_coordinates(div)
            pt_coords = self.pt_from_pixel(coords)
            self.width = pt_coords.x2 - pt_coords.x1
            self.height = pt_coords.y2 - pt_coords.y1
            # there shouldn't be more than one, and if there is, we don't want
            # it
            break
        if self.width is None or self.height is None:
            raise HocrTransformError("hocr file is missing page dimensions")

    def __str__(self):
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

    def element_coordinates(self, element):
        """
        Returns a tuple containing the coordinates of the bounding box around
        an element
        """
        out = (0, 0, 0, 0)
        if 'title' in element.attrib:
            matches = self.boxPattern.search(element.attrib['title'])
            if matches:
                coords = matches.group(1).split()
                out = Rect._make(int(coords[n]) for n in range(4))
        return out

    def pt_from_pixel(self, pxl):
        """
        Returns the quantity in PDF units (pt) given quantity in pixels
        """
        return Rect._make(
            (c / self.dpi * inch) for c in pxl)

    def replace_unsupported_chars(self, s):
        """
        Given an input string, returns the corresponding string that:
        - is available in the helvetica facetype
        - does not contain any ligature (to allow easy search in the PDF file)
        """
        # The 'u' before the character to replace indicates that it is a
        # unicode character
        s = s.replace(u"ﬂ", "fl")
        s = s.replace(u"ﬁ", "fi")
        return s

    def to_pdf(self, outFileName, imageFileName=None, showBoundingboxes=False,
               fontname="Helvetica", invisibleText=False):
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
            outFileName, pagesize=(self.width, self.height), pageCompression=1)

        # draw bounding box for each paragraph
        # light blue for bounding box of paragraph
        pdf.setStrokeColorRGB(0, 1, 1)
        # light blue for bounding box of paragraph
        pdf.setFillColorRGB(0, 1, 1)
        pdf.setLineWidth(0)		# no line for bounding box
        for elem in self.hocr.findall(
                ".//%sp[@class='%s']" % (self.xmlns, "ocr_par")):

            elemtxt = self._get_element_text(elem).rstrip()
            if len(elemtxt) == 0:
                continue

            pxl_coords = self.element_coordinates(elem)
            pt = self.pt_from_pixel(pxl_coords)

            # draw the bbox border
            if showBoundingboxes:
                pdf.rect(
                    pt.x1, self.height - pt.y2, pt.x2 - pt.x1, pt.y2 - pt.y1,
                    fill=1)

        # check if element with class 'ocrx_word' are available
        # otherwise use 'ocr_line' as fallback
        elemclass = "ocr_line"
        if self.hocr.find(
                ".//%sspan[@class='ocrx_word']" % (self.xmlns)) is not None:
            elemclass = "ocrx_word"

        # itterate all text elements
        # light green for bounding box of word/line
        pdf.setStrokeColorRGB(1, 0, 0)
        pdf.setLineWidth(0.5)		# bounding box line width
        pdf.setDash(6, 3)		# bounding box is dashed
        pdf.setFillColorRGB(0, 0, 0)  # text in black
        for elem in self.hocr.findall(
                ".//%sspan[@class='%s']" % (self.xmlns, elemclass)):

            elemtxt = self._get_element_text(elem).rstrip()

            elemtxt = self.replace_unsupported_chars(elemtxt)

            if len(elemtxt) == 0:
                continue

            pxl_coords = self.element_coordinates(elem)
            pt = self.pt_from_pixel(pxl_coords)

            # draw the bbox border
            if showBoundingboxes:
                pdf.rect(
                    pt.x1, self.height - pt.y2, pt.x2 - pt.x1, pt.y2 - pt.y1,
                    fill=0)

            text = pdf.beginText()
            fontsize = pt.y2 - pt.y1
            text.setFont(fontname, fontsize)
            if invisibleText:
                text.setTextRenderMode(3)  # Invisible (indicates OCR text)

            # set cursor to bottom left corner of bbox (adjust for dpi)
            text.setTextOrigin(pt.x1, self.height - pt.y2)

            # scale the width of the text to fill the width of the bbox
            text.setHorizScale(
                100 * (pt.x2 - pt.x1) / pdf.stringWidth(
                    elemtxt, fontname, fontsize))

            # write the text to the page
            text.textLine(elemtxt)
            pdf.drawText(text)

        # put the image on the page, scaled to fill the page
        if imageFileName is not None:
            pdf.drawImage(imageFileName, 0, 0,
                          width=self.width, height=self.height)

        # finish up the page and save it
        pdf.showPage()
        pdf.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert hocr file to PDF')
    parser.add_argument('-b', '--boundingboxes', action="store_true",
                        default=False, help='Show bounding boxes borders')
    parser.add_argument('-r', '--resolution', type=int,
                        default=300,
                        help='Resolution of the image that was OCRed')
    parser.add_argument('-i', '--image', default=None,
                        help='Path to the image to be placed above the text')
    parser.add_argument('hocrfile', help='Path to the hocr file to be parsed')
    parser.add_argument(
        'outputfile', help='Path to the PDF file to be generated')
    args = parser.parse_args()

    hocr = HocrTransform(args.hocrfile, args.resolution)
    hocr.to_pdf(args.outputfile, args.image, args.boundingboxes)
