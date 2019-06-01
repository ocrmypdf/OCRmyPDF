# © 2019 James R. Barlow: github.com/jbarlow83
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

import logging
from decimal import Decimal

import pikepdf
import pytest
from PIL import Image

from ocrmypdf.exec.ghostscript import rasterize_pdf


@pytest.fixture
def linn(resources):
    path = resources / 'linn.pdf'
    return path, pikepdf.open(path)


def test_rasterize_size(linn, outdir, caplog):
    path, pdf = linn
    page_size_pts = (pdf.pages[0].MediaBox[2], pdf.pages[0].MediaBox[3])
    assert pdf.pages[0].MediaBox[0] == pdf.pages[0].MediaBox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('200.0'), Decimal('150.0')
    target_dpi = 42.0, 4242.0

    log = logging.getLogger()
    rasterize_pdf(
        path,
        outdir / 'out.png',
        target_size[0] / page_size[0],
        target_size[1] / page_size[1],
        raster_device='pngmono',
        log=log,
        page_dpi=target_dpi,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == target_size
        assert im.info['dpi'] == target_dpi


def test_rasterize_rotated(linn, outdir, caplog):
    path, pdf = linn
    page_size_pts = (pdf.pages[0].MediaBox[2], pdf.pages[0].MediaBox[3])
    assert pdf.pages[0].MediaBox[0] == pdf.pages[0].MediaBox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('200.0'), Decimal('150.0')
    target_dpi = 42.0, 4242.0

    log = logging.getLogger()
    caplog.set_level(logging.DEBUG)
    rasterize_pdf(
        path,
        outdir / 'out.png',
        target_size[0] / page_size[0],
        target_size[1] / page_size[1],
        raster_device='pngmono',
        log=log,
        page_dpi=target_dpi,
        rotation=90,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == (target_size[1], target_size[0])
        assert im.info['dpi'] == (target_dpi[1], target_dpi[0])
