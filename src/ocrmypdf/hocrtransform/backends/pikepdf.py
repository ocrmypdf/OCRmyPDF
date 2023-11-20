from __future__ import annotations

import unicodedata
from importlib.resources import files as package_files
from pathlib import Path

from pikepdf import (
    ContentStreamInstruction,
    Dictionary,
    Name,
    Operator,
    Pdf,
    unparse_content_stream,
)

from ocrmypdf.hocrtransform.backends._base import Canvas as BaseCanvas
from ocrmypdf.hocrtransform.backends._base import Text as BaseText

GLYPHLESS_FONT_NAME = 'pdf.ttf'

GLYPHLESS_FONT = (package_files('ocrmypdf.data') / GLYPHLESS_FONT_NAME).read_bytes()
CHAR_ASPECT = 2


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


class ContentStreamBuilder:
    def __init__(self, instructions=None):
        self._instructions: list[ContentStreamInstruction] = instructions or []

    def push(self):
        """Save the graphics state."""
        inst = ContentStreamInstruction([], Operator("q"))
        self._instructions.append(inst)
        return self

    def pop(self):
        """Restore the graphics state."""
        inst = ContentStreamInstruction([], Operator("Q"))
        self._instructions.append(inst)
        return self

    def cm(self, a: float, b: float, c: float, d: float, e: float, f: float):
        """Concatenate matrix."""
        inst = ContentStreamInstruction([a, b, c, d, e, f], Operator("cm"))
        self._instructions.append(inst)
        return self

    def begin_text(self):
        """Begin text object."""
        inst = ContentStreamInstruction([], Operator("BT"))
        self._instructions.append(inst)
        return self

    def end_text(self):
        """End text object."""
        inst = ContentStreamInstruction([], Operator("ET"))
        self._instructions.append(inst)
        return self

    def begin_marked_content(self, mctype: Name, mcid: int):
        """Begin marked content sequence."""
        inst = ContentStreamInstruction(
            [mctype, Dictionary(MCID=mcid)], Operator("BDC")
        )
        self._instructions.append(inst)
        return self

    def end_marked_content(self):
        """End marked content sequence."""
        inst = ContentStreamInstruction([], Operator("EMC"))
        self._instructions.append(inst)
        return self

    def set_text_font(self, font: Name, size: int):
        """Set text font and size."""
        inst = ContentStreamInstruction([font, size], Operator("Tf"))
        self._instructions.append(inst)
        return self

    def set_text_matrix(
        self, a: float, b: float, c: float, d: float, e: float, f: float
    ):
        """Set text matrix."""
        inst = ContentStreamInstruction([a, b, c, d, e, f], Operator("Tm"))
        self._instructions.append(inst)
        return self

    def set_text_rendering(self, mode: int):
        """Set text rendering mode."""
        inst = ContentStreamInstruction([mode], Operator("Tr"))
        self._instructions.append(inst)
        return self

    def set_text_horizontal_scaling(self, scale: float):
        """Set text horizontal scaling."""
        inst = ContentStreamInstruction([scale], Operator("Tz"))
        self._instructions.append(inst)
        return self

    def show_text(self, text: str):
        """Show text."""
        inst = ContentStreamInstruction([[text.encode("utf-16be")]], Operator("TJ"))
        self._instructions.append(inst)
        return self

    def move_cursor(self, dx, dy):
        """Move cursor."""
        inst = ContentStreamInstruction([dx, dy], Operator("Td"))
        self._instructions.append(inst)
        return self

    def stroke_and_close(self):
        """Stroke and close path."""
        inst = ContentStreamInstruction([], Operator("s"))
        self._instructions.append(inst)
        return self

    def append_rectangle(self, x: float, y: float, w: float, h: float):
        """Append rectangle to path."""
        inst = ContentStreamInstruction([x, y, w, h], Operator("re"))
        self._instructions.append(inst)
        return self

    def set_stroke_color(self, r: float, g: float, b: float):
        """Set RGB stroke color."""
        inst = ContentStreamInstruction([r, g, b], Operator("RG"))
        self._instructions.append(inst)
        return self

    def set_fill_color(self, r: float, g: float, b: float):
        """Set RGB fill color."""
        inst = ContentStreamInstruction([r, g, b], Operator("rg"))
        self._instructions.append(inst)
        return self

    def set_line_width(self, width):
        """Set line width."""
        inst = ContentStreamInstruction([width], Operator("w"))
        self._instructions.append(inst)
        return self

    def line(self, x1: float, y1: float, x2: float, y2: float):
        """Draw line."""
        insts = [
            ContentStreamInstruction([x1, y1], Operator("m")),
            ContentStreamInstruction([x2, y2], Operator("l")),
        ]
        self._instructions.extend(insts)
        return self

    def set_dashes(self, array=None, phase=0):
        """Set dashes."""
        if array is None:
            array = []
        if isinstance(array, (int, float)):
            array = (array, phase)
            phase = 0
        inst = ContentStreamInstruction([array, phase], Operator("d"))
        self._instructions.append(inst)
        return self

    def build(self):
        return self._instructions


class PikepdfCanvas(BaseCanvas):
    def __init__(self, path, *, page_size):
        super().__init__(path, page_size=page_size)
        self._pdf = Pdf.new()
        self._page = self._pdf.add_blank_page(page_size=page_size)
        self._cs = ContentStreamBuilder()
        self._cs.push()
        self._font_name = Name("/f-0-0")

    def set_stroke_color(self, color):
        r, g, b = color.red, color.green, color.blue
        self._cs.set_stroke_color(r, g, b)

    def set_fill_color(self, color):
        r, g, b = color.red, color.green, color.blue
        self._cs.set_fill_color(r, g, b)

    def set_line_width(self, width):
        self._cs.set_line_width(width)

    def line(self, x1, y1, x2, y2):
        self._cs.line(x1, y1, x2, y2)

    def rect(self, x, y, w, h, fill):
        self._cs.append_rectangle(x, y, w, h)
        self._cs.stroke_and_close()

    def begin_text(self, x=0, y=0, direction=None):
        return PikepdfText(x, y, direction)

    def draw_text(self, text: PikepdfText):
        self._cs._instructions.extend(text._cs._instructions)
        self._end_text()

    def _end_text(self):
        self._cs.end_text()

    def draw_image(self, image: Path, x, y, width, height):
        raise NotImplementedError()

    def string_width(self, text, fontname, fontsize):
        # NFKC: split ligatures, combine diacritics
        return len(unicodedata.normalize("NFKC", text)) * (fontsize / CHAR_ASPECT)

    def set_dashes(self, *args):
        self._cs.set_dashes(*args)

    def save(self):
        self._cs.pop()
        self._page.Contents = self._pdf.make_stream(
            unparse_content_stream(self._cs.build())
        )
        self._page.Resources = Dictionary(Font=Dictionary())
        self._page.Resources.Font[self._font_name] = register_glyphlessfont(self._pdf)
        self._pdf.save(self.path)


class PikepdfText(BaseText):
    def __init__(self, x=0, y=0, direction=None):
        self._cs = ContentStreamBuilder()
        self._cs.begin_text()
        self._p0 = (x, y)

    def set_font(self, font, size):
        self._cs.set_text_font(Name("/f-0-0"), size)

    def set_render_mode(self, mode):
        self._cs.set_text_rendering(mode)

    def set_text_transform(self, a, b, c, d, e, f):
        self._cs.set_text_matrix(a, b, c, d, e, f)
        self._p0 = (e, f)

    def show(self, text):
        self._cs.show_text(text)

    def set_horiz_scale(self, scale):
        self._cs.set_text_horizontal_scaling(scale)

    def get_start_of_line(self):
        return self._p0

    def move_cursor(self, x, y):
        self._cs.move_cursor(x, y)
