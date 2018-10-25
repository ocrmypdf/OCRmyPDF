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

import pdfminer.pdfinterp
import pdfminer.pdfdevice

from pdfminer.pdfpage import PDFPage

from pdfminer.utils import matrix2str, bbox2str, fsplit
from pdfminer.pdffont import PDFUnicodeNotDefined
from pdfminer.layout import (
    LTChar, LTContainer, LTLayoutContainer, LTPage, LTTextLine, LAParams
)

from pdfminer.converter import PDFLayoutAnalyzer

class LTStateAwareChar(LTChar):
    """A subclass of LTChar that tracks text render mode at time of drawing"""

    def __init__(self, matrix, font, fontsize, scaling, rise, text, textwidth,                textdisp, textstate, *args):
        super().__init__(matrix, font, fontsize, scaling, rise, text, textwidth,                  textdisp, *args)
        self.rendermode = textstate.render

    def is_compatible(self, obj):
        """We are only compatible with same rendering mode"""
        if not hasattr(obj, 'rendermode'):
            return False
        return self.rendermode == obj.rendermode

    def __repr__(self):
        return ('<%s %s matrix=%s rendermode=%r font=%r adv=%s text=%r>' %
                (self.__class__.__name__, bbox2str(self.bbox),
                 matrix2str(self.matrix), self.rendermode, self.fontname, self.adv,
                 self.get_text()))


class LTStateAwarePage(LTPage):
    """A page container that exploits character type information"""

    def __init__(self, pageid, bbox, rotate=0):
        LTPage.__init__(self, pageid, bbox, rotate)

    def analyze(self, laparams):
        """Analysis taking rendering mode into account

        Looks at visible and invisible characters separately.
        Depends on some superclass implementation details...
        """

        objs = self._objs[:]

        # Split into invisible text objects and all others
        (invisible_textobjs, other_objs) = fsplit(
                lambda obj: getattr(obj, 'rendermode', 0) == 3, self)

        # Analyze all invisible text objects and group them into text lines and
        # text boxes
        self._objs = invisible_textobjs
        LTPage.analyze(self, laparams)
        invisible_analyzed = self._objs[:]

        # Analyze all other objects
        self._objs = other_objs
        LTPage.analyze(self, laparams)
        other_analyzed = self._objs[:]

        self._objs = invisible_analyzed + other_analyzed
        self.visible = other_analyzed
        self.invisible = invisible_analyzed


class TextPositionTracker(PDFLayoutAnalyzer):
    """A page layout analyzer that pays attention to text visibility"""

    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        super().__init__(rsrcmgr, pageno, laparams)
        self.textstate = None
        self.result = None

    def begin_page(self, page, ctm):
        super().begin_page(page, ctm)
        self.cur_item = LTStateAwarePage(self.pageno, page.mediabox)

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
                matrix, font, fontsize, scaling, rise, text,            textwidth, textdisp, self.textstate, *args)
        self.cur_item.add(item)
        return item.adv

    def handle_undefined_char(self, font, cid):
        log.info('undefined: %r, %r', font, cid)
        return '(cid:%d)' % cid

    def receive_layout(self, ltpage):
        self.result = (ltpage.visible, ltpage.invisible)

    def get_result(self):
        return self.result


def get_textblocks(infile, pageno):
    rman = pdfminer.pdfinterp.PDFResourceManager(caching=True)
    dev = TextPositionTracker(rman, laparams=LAParams())
    interp = pdfminer.pdfinterp.PDFPageInterpreter(rman, dev)

    page = PDFPage.get_pages(infile, pagenos=[pageno], maxpages=0)

    interp.process_page(next(page))

    return dev.get_result()
