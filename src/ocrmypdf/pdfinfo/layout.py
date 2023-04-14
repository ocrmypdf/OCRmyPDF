# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Detailed text position and layout analysis, building on pdfminer.six."""

from __future__ import annotations

import re
from math import copysign
from pathlib import Path
from unittest.mock import patch

import pdfminer
import pdfminer.encodingdb
import pdfminer.pdfdevice
import pdfminer.pdfinterp
from pdfminer.converter import PDFLayoutAnalyzer
from pdfminer.layout import LAParams, LTChar, LTPage, LTTextBox
from pdfminer.pdfdocument import PDFTextExtractionNotAllowed
from pdfminer.pdffont import PDFSimpleFont, PDFUnicodeNotDefined
from pdfminer.pdfpage import PDFPage
from pdfminer.utils import bbox2str, matrix2str

from ocrmypdf.exceptions import EncryptedPdfError, InputFileError

STRIP_NAME = re.compile(r'[0-9]+')


original_pdfsimplefont_init = PDFSimpleFont.__init__


def pdfsimplefont__init__(self, descriptor, widths, spec):
    """Monkeypatch pdfminer.six PDFSimpleFont.__init__.

    If there is no ToUnicode and no Encoding, pdfminer.six assumes that Unicode
    conversion is possible. This is incorrect, according to PDF Reference Manual
    9.10.2. This patch fixes that.
    """
    # Font encoding is specified either by a name of
    # built-in encoding or a dictionary that describes
    # the differences.
    original_pdfsimplefont_init(self, descriptor, widths, spec)
    if not self.unicode_map and 'Encoding' not in spec:
        self.cid2unicode = {}
    return


PDFSimpleFont.__init__ = pdfsimplefont__init__

#
# pdfminer patches when creator is PScript5.dll
#


def pdftype3font__pscript5_get_height(self):
    """Monkeypatch for PScript5.dll PDFs.

    The height of Type3 fonts is known to be incorrect in PScript5.dll
    generated PDFs. This patch attempts to correct the height by
    using the bbox height if it is available, otherwise using the
    ascent and descent.
    """
    h = self.bbox[3] - self.bbox[1]
    if h == 0:
        h = self.ascent - self.descent
    return h * copysign(1.0, self.vscale)


def pdftype3font__pscript5_get_descent(self):
    """Monkeypatch for PScript5.dll PDFs.

    The descent of Type3 fonts is known to be incorrect in PScript5.dll
    generated PDFs. This patch attempts to correct the descent by
    using the vscale.
    """
    return self.descent * copysign(1.0, self.vscale)


def pdftype3font__pscript5_get_ascent(self):
    """Monkeypatch for PScript5.dll PDFs.

    The ascent of Type3 fonts is known to be incorrect in PScript5.dll
    generated PDFs. This patch attempts to correct the ascent by
    using the vscale.
    """
    return self.ascent * copysign(1.0, self.vscale)


class LTStateAwareChar(LTChar):
    """A subclass of LTChar that tracks text render mode at time of drawing."""

    __slots__ = (
        'rendermode',
        '_text',
        'matrix',
        'fontname',
        'adv',
        'upright',
        'size',
        'width',
        'height',
        'bbox',
        'x0',
        'x1',
        'y0',
        'y1',
    )

    def __init__(
        self,
        matrix,
        font,
        fontsize,
        scaling,
        rise,
        text,
        textwidth,
        textdisp,
        ncs,
        graphicstate,
        textstate,
    ):
        """Initialize."""
        super().__init__(
            matrix,
            font,
            fontsize,
            scaling,
            rise,
            text,
            textwidth,
            textdisp,
            ncs,
            graphicstate,
        )
        self.rendermode = textstate.render

    def is_compatible(self, obj):
        """Check if characters can be combined into a textline.

        We consider characters compatible if:
            - the Unicode mapping is known, and both have the same render mode
            - the Unicode mapping is unknown but both are part of the same font
        """
        # pylint: disable=protected-access
        both_unicode_mapped = isinstance(self._text, str) and isinstance(obj._text, str)
        try:
            if both_unicode_mapped:
                return self.rendermode == obj.rendermode
            font0, _ = self._text
            font1, _ = obj._text
            return font0 == font1 and self.rendermode == obj.rendermode
        except (ValueError, AttributeError):
            return False

    def get_text(self):
        """Get text from this character."""
        if isinstance(self._text, tuple):
            return '\ufffd'  # standard 'Unknown symbol'
        return self._text

    def __repr__(self):
        """Return a string representation of this object."""
        return (
            f"<{self.__class__.__name__} "
            f"{bbox2str(self.bbox)} "
            f"matrix={matrix2str(self.matrix)} "
            f"rendermode={self.rendermode!r} "
            f"font={self.fontname!r} "
            f"adv={self.adv} "
            f"text={self.get_text()!r}>"
        )


class TextPositionTracker(PDFLayoutAnalyzer):
    """A page layout analyzer that pays attention to text visibility."""

    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        """Initialize the layout analyzer."""
        super().__init__(rsrcmgr, pageno, laparams)
        self.textstate = None
        self.result = None
        self.cur_item = None  # not defined in pdfminer code as it should be

    def begin_page(self, page, ctm):
        """Begin processing of a page."""
        super().begin_page(page, ctm)
        self.cur_item = LTPage(self.pageno, page.mediabox)

    def end_page(self, page):
        """End processing of a page."""
        assert not self._stack, str(len(self._stack))
        assert isinstance(self.cur_item, LTPage), str(type(self.cur_item))
        if self.laparams is not None:
            self.cur_item.analyze(self.laparams)
        self.pageno += 1
        self.receive_layout(self.cur_item)

    def render_string(self, textstate, seq, ncs, graphicstate):
        """Respond to render string event by updating text state."""
        self.textstate = textstate.copy()
        super().render_string(self.textstate, seq, ncs, graphicstate)

    def render_char(
        self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate
    ):
        """Respond to render char event by updating text state."""
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, str), str(type(text))
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTStateAwareChar(
            matrix,
            font,
            fontsize,
            scaling,
            rise,
            text,
            textwidth,
            textdisp,
            ncs,
            graphicstate,
            self.textstate,
        )
        self.cur_item.add(item)
        return item.adv

    def handle_undefined_char(self, font, cid):
        """Handle undefined character."""
        # log.info('undefined: %r, %r', font, cid)
        return (font.fontname, cid)

    def receive_layout(self, ltpage):
        """Receive layout handler."""
        self.result = ltpage

    def get_result(self):
        """Get the result of the analysis."""
        return self.result


def get_page_analysis(infile, pageno, pscript5_mode):
    """Get the page analysis for a given page."""
    rman = pdfminer.pdfinterp.PDFResourceManager(caching=True)
    disable_boxes_flow = None
    dev = TextPositionTracker(
        rman,
        laparams=LAParams(
            all_texts=True, detect_vertical=True, boxes_flow=disable_boxes_flow
        ),
    )
    interp = pdfminer.pdfinterp.PDFPageInterpreter(rman, dev)

    patcher = None
    if pscript5_mode:
        patcher = patch.multiple(
            'pdfminer.pdffont.PDFType3Font',
            spec=True,
            get_ascent=pdftype3font__pscript5_get_ascent,
            get_descent=pdftype3font__pscript5_get_descent,
            get_height=pdftype3font__pscript5_get_height,
        )
        patcher.start()

    try:
        with Path(infile).open('rb') as f:
            page_iter = PDFPage.get_pages(f, pagenos=[pageno], maxpages=0)
            page = next(page_iter, None)
            if page is None:
                raise InputFileError(
                    f"pdfminer could not process page {pageno} (counting from 0)."
                )
            interp.process_page(page)
    except PDFTextExtractionNotAllowed as e:
        raise EncryptedPdfError() from e
    finally:
        if patcher is not None:
            patcher.stop()

    return dev.get_result()


def get_text_boxes(obj):
    """Get the text boxes attached to the current node."""
    for child in obj:
        if isinstance(child, (LTTextBox)):
            yield child
        else:
            try:
                yield from get_text_boxes(child)
            except TypeError:
                continue
