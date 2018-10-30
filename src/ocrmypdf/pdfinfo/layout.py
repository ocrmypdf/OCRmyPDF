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

import re

import pdfminer.encodingdb
import pdfminer.pdfinterp
import pdfminer.pdfdevice

from pdfminer.converter import PDFLayoutAnalyzer
from pdfminer.pdfdocument import PDFTextExtractionNotAllowed
from pdfminer.glyphlist import glyphname2unicode
from pdfminer.layout import (
    LTChar, LTContainer, LTLayoutContainer, LTPage, LTTextLine, LAParams,
    LTTextBox
)
from pdfminer.pdffont import PDFUnicodeNotDefined, PDFType3Font, PDFFont, PDFCIDFont
from pdfminer.pdfpage import PDFPage
from pdfminer.utils import matrix2str, bbox2str, fsplit

from ..exceptions import EncryptedPdfError



STRIP_NAME = re.compile(r'[0-9]+')

def name2unicode(name):
    """Fix pdfminer's regex in name2unicode function

    Font cids that are mapped to names of the form /g123 seem to be, by convention
    characters with no corresponding Unicode entry. These can be subsetted fonts
    or symbolic fonts. There seems to be no way to map /g123 fonts to Unicode,
    barring a ToUnicode data structure.
    """
    if name in glyphname2unicode:
        return glyphname2unicode[name]
    if name.startswith('g'):
        raise KeyError(name)
    m = STRIP_NAME.search(name)
    if not m:
        raise KeyError(name)
    return chr(int(m.group(0)))

pdfminer.encodingdb.name2unicode = name2unicode

from math import copysign
def PDFType3Font__get_height(self):
    h = self.bbox[3]-self.bbox[1]
    if h == 0:
        h = self.ascent - self.descent
    return h * copysign(1.0, self.vscale)

def PDFType3Font__get_descent(self):
    return self.descent * copysign(1.0, self.vscale)

def PDFType3Font__get_ascent(self):
    return self.ascent * copysign(1.0, self.vscale)

PDFType3Font.get_height = PDFType3Font__get_height
PDFType3Font.get_ascent = PDFType3Font__get_ascent
PDFType3Font.get_descent = PDFType3Font__get_descent


original_PDFFont_init = PDFFont.__init__
def PDFFont__init__(self, descriptor, widths, default_width=None):
    original_PDFFont_init(self, descriptor, widths, default_width)
    # PDF spec says descent should be negative
    # A font with a positive descent implies it floats entirely above the
    # baseline, i.e. it's not really a baseline anymore. I have fonts that
    # claim a positive descent, but treating descent as positive always seems
    # to misposition text.
    if self.descent > 0:
        self.descent = -self.descent

PDFFont.__init__ = PDFFont__init__



class LTStateAwareChar(LTChar):
    """A subclass of LTChar that tracks text render mode at time of drawing"""

    __slots__ = (
        'rendermode', '_text', 'matrix', 'fontname', 'adv', 'upright', 'size',
        'width', 'height', 'bbox', 'x0', 'x1', 'y0', 'y1'
    )

    def __init__(self, matrix, font, fontsize, scaling, rise, text, textwidth,
                 textdisp, textstate, *args):
        super().__init__(matrix, font, fontsize, scaling, rise, text, textwidth,
                         textdisp, *args)
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
        return (font.fontname, cid)

    def receive_layout(self, ltpage):
        self.result = ltpage

    def get_result(self):
        return self.result


def get_page_analysis(infile, pageno):
    rman = pdfminer.pdfinterp.PDFResourceManager(caching=True)
    dev = TextPositionTracker(rman, laparams=LAParams())
    interp = pdfminer.pdfinterp.PDFPageInterpreter(rman, dev)

    page = PDFPage.get_pages(infile, pagenos=[pageno], maxpages=0)

    try:
        interp.process_page(next(page))
    except PDFTextExtractionNotAllowed as e:
        raise EncryptedPdfError()

    return dev.get_result()


def get_text_boxes(obj):
    for child in obj:
        if isinstance(child, (LTTextBox)):
            yield child
        else:
            try:
                yield from get_text_boxes(child)
            except TypeError:
                continue
