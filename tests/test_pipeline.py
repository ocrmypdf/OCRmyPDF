# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import warnings
from unittest.mock import Mock

import pytest
from PIL import Image
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from ocrmypdf import _pipeline, pdfinfo
from ocrmypdf.helpers import Resolution

warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="reportlab.lib.rl_safe_eval"
)


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

    pi = pdfinfo.PdfInfo(outdir / 'dpi.pdf')
    pageinfo = pi[0]
    ctx = Mock()
    ctx.options.oversample = DUMMY_OVERSAMPLE_RESOLUTION[0]
    ctx.pageinfo = pageinfo

    assert _pipeline.get_canvas_square_dpi(ctx) == result
    assert _pipeline.get_page_square_dpi(ctx) == result


@pytest.mark.parametrize(
    # Name for nicer -v output
    'name,input,output',
    (
        (
            'empty_input',
            # Input:
            (),
            # Output:
            (),
        ),
        (
            'no_values',
            # Input:
            ('', '', '', '', ''),
            # Output:
            (((1, 5), None),),
        ),
        (
            'no_empty_values',
            # Input:
            ('v', 'w', 'x', 'y', 'z'),
            # Output:
            (
                ((1, 1), 'v'),
                ((2, 2), 'w'),
                ((3, 3), 'x'),
                ((4, 4), 'y'),
                ((5, 5), 'z'),
            ),
        ),
        (
            'skip_head',
            # Input:
            ('', '', 'x', 'y', 'z'),
            # Output:
            (
                ((1, 2), None),
                ((3, 3), 'x'),
                ((4, 4), 'y'),
                ((5, 5), 'z'),
            ),
        ),
        (
            'skip_tail',
            # Input:
            ('x', 'y', 'z', '', ''),
            # Output:
            (
                ((1, 1), 'x'),
                ((2, 2), 'y'),
                ((3, 3), 'z'),
                ((4, 5), None),
            ),
        ),
        (
            'range_in_middle',
            # Input:
            ('x', '', '', '', 'y'),
            # Output:
            (
                ((1, 1), 'x'),
                ((2, 4), None),
                ((5, 5), 'y'),
            ),
        ),
        (
            'range_in_middle_2',
            # Input:
            ('x', '', '', 'y', '', '', '', 'z'),
            # Output:
            (
                ((1, 1), 'x'),
                ((2, 3), None),
                ((4, 4), 'y'),
                ((5, 7), None),
                ((8, 8), 'z'),
            ),
        ),
    ),
)
def test_enumerate_compress_ranges(name, input, output):
    assert output == tuple(_pipeline.enumerate_compress_ranges(input))
