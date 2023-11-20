from __future__ import annotations

from collections import namedtuple

Color = namedtuple('Color', ['red', 'green', 'blue', 'alpha'])

BLACK = Color(0, 0, 0, 1)
WHITE = Color(1, 1, 1, 1)
BLUE = Color(0, 0, 1, 1)
CYAN = Color(0, 1, 1, 1)
GREEN = Color(0, 1, 0, 1)
DARKGREEN = Color(0, 0.5, 0, 1)
MAGENTA = Color(1, 0, 1, 1)
RED = Color(1, 0, 0, 1)
