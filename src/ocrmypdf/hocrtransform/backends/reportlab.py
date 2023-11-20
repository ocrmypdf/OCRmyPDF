from __future__ import annotations

import os
import warnings
from pathlib import Path

with warnings.catch_warnings():
    # reportlab uses deprecated load_module
    # shim can be removed when we require reportlab >= 3.7
    warnings.filterwarnings(
        'ignore', category=DeprecationWarning, message=r".*load_module.*"
    )
    from reportlab.lib.colors import black, cyan, magenta, red
    from reportlab.lib.units import inch
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfgen.textobject import PDFTextObject

from ocrmypdf.hocrtransform.backends._base import Canvas as BaseCanvas
from ocrmypdf.hocrtransform.backends._base import Text as BaseText


class ReportlabCanvas(BaseCanvas):
    def __init__(self, path, *, page_size):
        super().__init__(path, page_size=page_size)
        self._canvas = Canvas(os.fspath(path), pagesize=page_size, pageCompression=1)

    def set_stroke_color(self, color):
        self._canvas.setStrokeColor(color)

    def set_fill_color(self, color):
        self._canvas.setFillColor(color)

    def set_line_width(self, width):
        self._canvas.setLineWidth(width)

    def line(self, x1, y1, x2, y2):
        self._canvas.line(x1, y1, x2, y2)

    def begin_text(self, x=0, y=0, direction=None):
        return ReportlabText(self._canvas.beginText(x, y, direction))

    def draw_text(self, text):
        self._canvas.drawText(text._text)

    def draw_image(self, image: Path, x, y, width, height):
        self._canvas.drawImage(os.fspath(image), x, y, width, height)

    def string_width(self, text, fontname, fontsize):
        return self._canvas.stringWidth(text, fontname, fontsize)

    def set_dashes(self, dashes):
        self._canvas.setDash(*dashes)

    def save(self):
        self._canvas.showPage()
        self._canvas.save()


class ReportlabText(BaseText):
    def __init__(self, text: PDFTextObject):
        self._text = text

    def set_font(self, font, size):
        self._text.setFont(font, size)

    def set_render_mode(self, mode):
        self._text.setTextRenderMode(mode)

    def set_text_transform(self, a, b, c, d, e, f):
        return self._text.setTextTransform(a, b, c, d, e, f)

    def show(self, text):
        return self._text.textOut(text)

    def set_horiz_scale(self, scale):
        return self._text.setHorizScale(scale)

    def get_start_of_line(self):
        return self._text.getStartOfLine()

    def move_cursor(self, x, y):
        return self._text.moveCursor(x, y)
