from __future__ import annotations

import importlib
import re
from io import BufferedReader, BufferedWriter, BytesIO
from pathlib import Path

import pikepdf
from bs4 import BeautifulSoup
from pikepdf import (
    ContentStreamInstruction,
    Dictionary,
    Name,
    Operator,
    Pdf,
    unparse_content_stream,
)

GLYPHLESS_FONT = importlib.resources.read_binary("ocrmypdf", "pdf.ttf")
CHAR_ASPECT = 2


def parse_bbox(title):
    # Match for bbox pattern
    bbox_pattern = re.compile(r'bbox (\d+) (\d+) (\d+) (\d+)')
    match = bbox_pattern.search(title)
    if match:
        return tuple(map(int, match.groups()))
    else:
        return None


def register_glyphlessfont(pdf: Pdf):
    """Register the glyphless font.

    Create several data structures in the Pdf to describe the font. While it create
    the data, a reference should be set in at least one page's /Resources dictionary
    to retain the font in the output PDF and ensure it is usable on that page.
    """
    PLACEHOLDER = Name.Placeholder

    basefont = pdf.make_indirect(
        Dictionary(
            BaseFont=Name.GlyphLessFont,
            DescendantFonts=[PLACEHOLDER],
            Encoding=Name("/Identity-H"),
            Subtype=Name.Type0,
            ToUnicode=PLACEHOLDER,
            Type=Name.Font,
        )
    )
    cid_font_type2 = pdf.make_indirect(
        Dictionary(
            BaseFont=Name.GlyphLessFont,
            CIDToGIDMap=PLACEHOLDER,
            CIDSystemInfo=Dictionary(
                Ordering="Identity",
                Registry="Adobe",
                Supplement=0,
            ),
            FontDescriptor=PLACEHOLDER,
            Subtype=Name.CIDFontType2,
            Type=Name.Font,
            DW=1000 // CHAR_ASPECT,
        )
    )
    basefont.DescendantFonts = [cid_font_type2]
    cid_font_type2.CIDToGIDMap = pdf.make_stream(b"\x00\x01" * 65536)
    basefont.ToUnicode = pdf.make_stream(
        b"/CIDInit /ProcSet findresource begin\n"
        b"12 dict begin\n"
        b"begincmap\n"
        b"/CIDSystemInfo\n"
        b"<<\n"
        b"  /Registry (Adobe)\n"
        b"  /Ordering (UCS)\n"
        b"  /Supplement 0\n"
        b">> def\n"
        b"/CMapName /Adobe-Identify-UCS def\n"
        b"/CMapType 2 def\n"
        b"1 begincodespacerange\n"
        b"<0000> <FFFF>\n"
        b"endcodespacerange\n"
        b"1 beginbfrange\n"
        b"<0000> <FFFF> <0000>\n"
        b"endbfrange\n"
        b"endcmap\n"
        b"CMapName currentdict /CMap defineresource pop\n"
        b"end\n"
        b"end\n"
    )
    font_descriptor = pdf.make_indirect(
        Dictionary(
            Ascent=1000,
            CapHeight=1000,
            Descent=-1,
            Flags=5,  # Fixed pitch and symbolic
            FontBBox=[0, 0, 1000 // CHAR_ASPECT, 1000],
            FontFile2=PLACEHOLDER,
            FontName=Name.GlyphLessFont,
            ItalicAngle=0,
            StemV=80,
            Type=Name.FontDescriptor,
        )
    )
    font_descriptor.FontFile2 = pdf.make_stream(GLYPHLESS_FONT)
    cid_font_type2.FontDescriptor = font_descriptor
    return basefont


class ContentStreamSequence:
    def __init__(self, instructions=None):
        self._instructions: list[ContentStreamInstruction] = instructions or []

    def push(self):
        """Save the graphics state."""
        inst = [ContentStreamInstruction([], Operator("q"))]
        return ContentStreamSequence(self._instructions + inst)

    def pop(self):
        """Restore the graphics state."""
        inst = [ContentStreamInstruction([], Operator("Q"))]
        return ContentStreamSequence(self._instructions + inst)

    def cm(self, a: float, b: float, c: float, d: float, e: float, f: float):
        """Concatenate matrix."""
        inst = [ContentStreamInstruction([a, b, c, d, e, f], Operator("cm"))]
        return ContentStreamSequence(self._instructions + inst)

    def begin_text(self):
        """Begin text object."""
        inst = [ContentStreamInstruction([], Operator("BT"))]
        return ContentStreamSequence(self._instructions + inst)

    def end_text(self):
        """End text object."""
        inst = [ContentStreamInstruction([], Operator("ET"))]
        return ContentStreamSequence(self._instructions + inst)

    def begin_marked_content(self, mctype: Name, mcid: int):
        """Begin marked content sequence."""
        inst = [
            ContentStreamInstruction([mctype, Dictionary(MCID=mcid)], Operator("BDC"))
        ]
        return ContentStreamSequence(self._instructions + inst)

    def end_marked_content(self):
        """End marked content sequence."""
        inst = [ContentStreamInstruction([], Operator("EMC"))]
        return ContentStreamSequence(self._instructions + inst)

    def set_text_font(self, font: Name, size: int):
        """Set text font and size."""
        inst = [ContentStreamInstruction([font, size], Operator("Tf"))]
        return ContentStreamSequence(self._instructions + inst)

    def set_text_matrix(
        self, a: float, b: float, c: float, d: float, e: float, f: float
    ):
        """Set text matrix."""
        inst = [ContentStreamInstruction([a, b, c, d, e, f], Operator("Tm"))]
        return ContentStreamSequence(self._instructions + inst)

    def set_text_rendering(self, mode: int):
        """Set text rendering mode."""
        inst = [ContentStreamInstruction([mode], Operator("Tr"))]
        return ContentStreamSequence(self._instructions + inst)

    def set_text_horizontal_scaling(self, scale: float):
        """Set text horizontal scaling."""
        inst = [ContentStreamInstruction([scale], Operator("Tz"))]
        return ContentStreamSequence(self._instructions + inst)

    def show_text(self, text: str):
        """Show text."""
        inst = [ContentStreamInstruction([[text.encode("utf-16be")]], Operator("TJ"))]
        return ContentStreamSequence(self._instructions + inst)

    def stroke_and_close(self):
        """Stroke and close path."""
        inst = [ContentStreamInstruction([], Operator("s"))]
        return ContentStreamSequence(self._instructions + inst)

    def append_rectangle(self, x: float, y: float, w: float, h: float):
        """Append rectangle to path."""
        inst = [ContentStreamInstruction([x, y, w, h], Operator("re"))]
        return ContentStreamSequence(self._instructions + inst)

    def set_stroke_color(self, r: float, g: float, b: float):
        """Set RGB stroke color."""
        inst = [ContentStreamInstruction([r, g, b], Operator("RG"))]
        return ContentStreamSequence(self._instructions + inst)


class ContentStreamBuilder:
    def __init__(self):
        self._instructions = []

    def build(self):
        return self._instructions

    def add(self, other: ContentStreamSequence):
        self._instructions.extend(other._instructions)


def hocr_to_pdf(hocr_stream: BufferedReader, output_stream: BufferedWriter):
    # Parse the hOCR data
    soup = BeautifulSoup(hocr_stream, 'lxml')

    # Find the page size from the hOCR input
    ocr_page = soup.find('div', class_='ocr_page')
    if not ocr_page or 'title' not in ocr_page.attrs:
        raise ValueError("hOCR input does not contain page information")
    page_bbox = parse_bbox(ocr_page['title'])
    if page_bbox is None:
        raise ValueError("Could not parse page bounding box from hOCR input")
    _, _, page_width, page_height = page_bbox

    # Create a new PDF with pikepdf
    pdf = pikepdf.new()
    page = pdf.add_blank_page(page_size=(page_width, page_height))

    font_name = Name("/f-0-0")

    page.Resources = Dictionary(
        Font=Dictionary({font_name: register_glyphlessfont(pdf)})
    )

    cs = ContentStreamBuilder()
    cs.add(ContentStreamSequence().push().cm(1, 0, 0, -1, 0, page_height))

    # Add content using these fonts
    for span in soup.find_all('span', class_='ocrx_word'):
        if 'title' not in span.attrs:
            continue
        word_bbox = parse_bbox(span['title'])
        if not word_bbox:
            continue
        x0, y0, x1, y1 = word_bbox
        text = span.get_text() if span.get_text() else ''

        cos_a, sin_a = 1, 0
        font_size = y1 - y0
        space_width = 0
        box_width = x1 - x0 + space_width

        h_stretch = 100.0 * box_width / len(text) / font_size * CHAR_ASPECT

        cs.add(
            ContentStreamSequence()
            .begin_text()
            .set_text_rendering(3)
            .set_text_matrix(cos_a, -sin_a, sin_a, cos_a, x0, y1)
            .set_text_font(font_name, font_size)
            .set_text_horizontal_scaling(h_stretch)
            .show_text(text)
            .end_text()
        )

    cs.add(ContentStreamSequence().pop())

    page.Contents = pdf.make_stream(unparse_content_stream(cs.build()))

    # Save the PDF to a file or return as a byte string
    pdf.save(output_stream)
    pdf.close()
