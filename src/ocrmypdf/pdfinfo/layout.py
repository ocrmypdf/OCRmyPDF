# © 2018 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import pdfminer.encodingdb
import pdfminer.pdfinterp
import pdfminer.pdfdevice

from pdfminer.converter import PDFLayoutAnalyzer
from pdfminer.glyphlist import glyphname2unicode
from pdfminer.layout import (
    LTChar, LTContainer, LTLayoutContainer, LTPage, LTTextLine, LAParams,
    LTTextBox
)
from pdfminer.pdffont import PDFUnicodeNotDefined, PDFType3Font
from pdfminer.pdfpage import PDFPage
from pdfminer.utils import matrix2str, bbox2str, fsplit


def PDFType3Font_to_unichr(self, cid):
    """Patch Type3 fonts to fix misinterpretation of gids as Unicode mapping

    In a Type3 font the /Encoding /Differences [ ] array describes the mapping
    of character codes to glyph numbers like /g178 where 178 is an index into
    Type3 font's /CharProcs data structure.

    See PDF RM 1.7: 9.6.6.3 Encodings for Type 3 Fonts

    There is no correspondence between glyph numbers and Unicode, however,
    except by coincidence. So, if there is no ToUnicode table, then Unicode
    mapping is impossible.

    """
    try:
        if self.unicode_map:
            return self.unicode_map.get_unichr(cid)
    except KeyError:
        pass
    raise PDFUnicodeNotDefined(None, cid)

PDFType3Font.to_unichr = PDFType3Font_to_unichr


class LTStateAwareChar(LTChar):
    """A subclass of LTChar that tracks text render mode at time of drawing"""

    __slots__ = (
        'rendermode', '_text', 'matrix', 'fontname', 'adv', 'upright', 'size',
        'width', 'height', 'bbox', 'x0', 'x1', 'y0', 'y1'
    )

    def __init__(self, matrix, font, fontsize, scaling, rise, text, textwidth,                textdisp, textstate, *args):
        super().__init__(matrix, font, fontsize, scaling, rise, text, textwidth,                  textdisp, *args)
        self.rendermode = textstate.render

    def is_compatible(self, obj):
        """Check if characters can be combined into a textline

        We consider characters compatible if:
            - the Unicode mapping is known, and both have the same render mode
            - the Unicode mapping is unknown but both are part of the same font
        """
        both_unicode_mapped = (isinstance(self._text, str) and
                               isinstance(obj._text, str))
        try:
            if both_unicode_mapped:
                return self.rendermode == obj.rendermode
            font0, _ = self._text
            font1, _ = obj._text
            return font0 == font1 and self.rendermode == obj.rendermode
        except (ValueError, AttributeError):
            return False

    def get_text(self):
        if isinstance(self._text, tuple):
            return '�'
        return self._text

    def __repr__(self):
        return ('<%s %s matrix=%s rendermode=%r font=%r adv=%s text=%r>' %
                (self.__class__.__name__, bbox2str(self.bbox),
                 matrix2str(self.matrix), self.rendermode, self.fontname, self.adv,
                 self.get_text()))


class TextPositionTracker(PDFLayoutAnalyzer):
    """A page layout analyzer that pays attention to text visibility"""

    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        super().__init__(rsrcmgr, pageno, laparams)
        self.textstate = None
        self.result = None

    def begin_page(self, page, ctm):
        super().begin_page(page, ctm)
        self.cur_item = LTPage(self.pageno, page.mediabox)

    def end_page(self, page):
        assert not self._stack, str(len(self._stack))
        assert isinstance(self.cur_item, LTPage), str(type(self.cur_item))
        if self.laparams is not None:
            self.cur_item.analyze(self.laparams)
        self.pageno += 1
        self.receive_layout(self.cur_item)

    def render_string(self, textstate, seq, *args):
        self.textstate = textstate.copy()
        super().render_string(self.textstate, seq, *args)

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, *args):
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, str), str(type(text))
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTStateAwareChar(
                matrix, font, fontsize, scaling, rise, text,
                textwidth, textdisp, self.textstate, *args)
        self.cur_item.add(item)
        return item.adv

    def handle_undefined_char(self, font, cid):
        #log.info('undefined: %r, %r', font, cid)
        return (font, cid)

    def receive_layout(self, ltpage):
        self.result = ltpage

    def get_result(self):
        return self.result


def get_textblocks(infile, pageno):
    rman = pdfminer.pdfinterp.PDFResourceManager(caching=True)
    dev = TextPositionTracker(rman, laparams=LAParams())
    interp = pdfminer.pdfinterp.PDFPageInterpreter(rman, dev)

    page = PDFPage.get_pages(infile, pagenos=[pageno], maxpages=0)

    interp.process_page(next(page))

    return dev.get_result()


def textbox_predicate(*, visible, corrupt):
    def real_predicate(textbox, want_visible=visible, want_corrupt=corrupt):
        textline = textbox._objs[0]
        first_char = textline._objs[0]

        result = True

        is_visible = (first_char.rendermode != 3)
        if want_visible is not None:
            if is_visible != want_visible:
                result = False
        is_corrupt = (first_char.get_text() == '\ufffd')
        if want_corrupt is not None:
            if is_corrupt != want_corrupt:
                result = False

        return result
    return real_predicate


def filter_textboxes(obj, predicate):
    for child in obj:
        if isinstance(child, (LTTextBox)):
            if predicate(child):
                yield child
        else:
            try:
                yield from filter_textboxes(child, predicate)
            except TypeError:
                continue
