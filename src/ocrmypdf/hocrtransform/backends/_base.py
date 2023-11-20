from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Canvas(ABC):
    def __init__(self, path: Path, *, page_size):
        self.path = path
        self.page_size = page_size

    @abstractmethod
    def set_stroke_color(color):
        pass

    @abstractmethod
    def set_fill_color(color):
        pass

    @abstractmethod
    def set_line_width(width):
        pass

    @abstractmethod
    def line(x1, y1, x2, y2):
        pass

    @abstractmethod
    def begin_text(self) -> Text:
        pass

    @abstractmethod
    def draw_text(self, text: Text):
        pass

    @abstractmethod
    def draw_image(self, image: Path, x, y, width, height):
        pass

    @abstractmethod
    def string_width(self, text, fontname, fontsize):
        pass

    @abstractmethod
    def set_dashes(self, array, phase):
        pass

    @abstractmethod
    def save(self):
        pass


class Text(ABC):
    # @abstractmethod
    # def begin_marked_content(self, mctype, mcid):
    #     pass

    # @abstractmethod
    # def end_marked_content(self):
    #     pass

    @abstractmethod
    def set_render_mode(self, mode):
        pass

    @abstractmethod
    def set_font(self, font, size):
        pass

    @abstractmethod
    def set_text_transform(self, a, b, c, d, e, f):
        pass

    @abstractmethod
    def show(self, text):
        pass

    @abstractmethod
    def set_horiz_scale(self, scale):
        pass

    @abstractmethod
    def get_start_of_line(self):
        pass

    @abstractmethod
    def move_cursor(self, x, y):
        pass
