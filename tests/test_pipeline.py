# © 2021 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittest.mock import Mock

import pytest
from PIL import Image
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from ocrmypdf import _pipeline, pdfinfo
from ocrmypdf.helpers import Resolution


@pytest.fixture(scope='session')
def rgb_image():
    im = Image.new('RGB', (8, 8))
    im.putpixel((4, 4), (255, 0, 0))
    im.putpixel((5, 5), (0, 255, 0))
    im.putpixel((6, 6), (0, 0, 255))
    return ImageReader(im)


DUMMY_OVERSAMPLE_RESOLUTION = Resolution(42.0, 42.0)
VECTOR_RESOLUTION = Resolution(_pipeline.VECTOR_PAGE_DPI, _pipeline.VECTOR_PAGE_DPI)


@pytest.mark.parametrize(
    'image, text, vector, result',
    [
        (False, False, False, VECTOR_RESOLUTION),
        (False, True, False, VECTOR_RESOLUTION),
        (True, False, False, DUMMY_OVERSAMPLE_RESOLUTION),
        (True, True, False, VECTOR_RESOLUTION),
        (False, False, True, VECTOR_RESOLUTION),
        (False, True, True, VECTOR_RESOLUTION),
        (True, False, True, VECTOR_RESOLUTION),
        (True, True, True, VECTOR_RESOLUTION),
    ],
)
def test_dpi_needed(image, text, vector, result, rgb_image, outdir):

    c = Canvas(str(outdir / 'dpi.pdf'), pagesize=(5 * inch, 5 * inch))
    if image:
        c.drawImage(rgb_image, 1 * inch, 1 * inch, width=1 * inch, height=1 * inch)
    if text:
        c.drawString(1 * inch, 4 * inch, "Actual text")
    if vector:
        c.ellipse(3 * inch, 3 * inch, 4 * inch, 4 * inch)
    c.showPage()
    c.save()

    mock = Mock()
    mock.oversample = DUMMY_OVERSAMPLE_RESOLUTION[0]

    pi = pdfinfo.PdfInfo(outdir / 'dpi.pdf')

    assert _pipeline.get_canvas_square_dpi(pi[0], mock) == result
    assert _pipeline.get_page_square_dpi(pi[0], mock) == result
