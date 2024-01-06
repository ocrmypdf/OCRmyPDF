# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import unicodedata
import zlib
from importlib.resources import files as package_files

from pikepdf import (
    Dictionary,
    Name,
    Pdf,
)
from pikepdf.canvas import Font

log = logging.getLogger(__name__)


class EncodableFont(Font):
    def text_encode(self, text: str) -> bytes:
        raise NotImplementedError()


class GlyphlessFont(EncodableFont):
    CID_TO_GID_DATA = zlib.compress(b"\x00\x01" * 65536)
    GLYPHLESS_FONT_NAME = 'pdf.ttf'
    GLYPHLESS_FONT = (package_files('ocrmypdf.data') / GLYPHLESS_FONT_NAME).read_bytes()
    CHAR_ASPECT = 2

    def __init__(self):
        pass

    def text_width(self, text: str, fontsize: float) -> float:
        """Estimate the width of a text string when rendered with the given font."""
        # NFKC: split ligatures, combine diacritics
        return len(unicodedata.normalize("NFKC", text)) * (fontsize / self.CHAR_ASPECT)

    def text_encode(self, text: str) -> bytes:
        return text.encode('utf-16be')

    def register(self, pdf: Pdf):
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
                DW=1000 // self.CHAR_ASPECT,
            )
        )
        basefont.DescendantFonts = [cid_font_type2]
        cid_font_type2.CIDToGIDMap = pdf.make_stream(
            self.CID_TO_GID_DATA, Filter=Name.FlateDecode
        )
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
                FontBBox=[0, 0, 1000 // self.CHAR_ASPECT, 1000],
                FontFile2=PLACEHOLDER,
                FontName=Name.GlyphLessFont,
                ItalicAngle=0,
                StemV=80,
                Type=Name.FontDescriptor,
            )
        )
        font_descriptor.FontFile2 = pdf.make_stream(self.GLYPHLESS_FONT)
        cid_font_type2.FontDescriptor = font_descriptor
        return basefont


class Courier(EncodableFont):
    """Courier font."""

    def text_width(self, text: str, fontsize: float) -> float:
        """Estimate the width of a text string when rendered with the given font."""
        return len(text) * fontsize

    def text_encode(self, text: str) -> bytes:
        return text.encode('pdfdoc', errors='ignore')

    def register(self, pdf: Pdf) -> Dictionary:
        """Register the font."""
        return pdf.make_indirect(
            Dictionary(
                BaseFont=Name.Courier,
                Type=Name.Font,
                Subtype=Name.Type1,
            )
        )
