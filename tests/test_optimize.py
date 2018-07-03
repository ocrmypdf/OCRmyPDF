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

from pathlib import Path

import pytest
import logging

from PIL import Image

from ocrmypdf import optimize as opt
from ocrmypdf.exec.ghostscript import rasterize_pdf
from ocrmypdf.exec import jbig2enc
from ocrmypdf.helpers import fspath


check_ocrmypdf = pytest.helpers.check_ocrmypdf


@pytest.mark.parametrize('pdf', ['multipage.pdf', 'palette.pdf'])
def test_basic(resources, pdf, outpdf):
    infile = resources / pdf
    opt.main(infile, outpdf, level=3)

    assert Path(outpdf).stat().st_size <= Path(infile).stat().st_size


def test_mono_not_inverted(resources, outdir):
    infile = resources / '2400dpi.pdf'
    opt.main(infile, outdir / 'out.pdf', level=3)

    rasterize_pdf(
        outdir / 'out.pdf', outdir / 'im.png',
        xres=10, yres=10, raster_device='pnggray',
        log=logging.getLogger(name='test_mono_flip')
    )

    im = Image.open(fspath(outdir / 'im.png'))
    assert im.getpixel((0, 0)) == 255, "Expected white background"


@pytest.mark.skipif(not jbig2enc.available(), reason='need jbig2enc')
def test_jpg_png_params(resources, outpdf, spoof_tesseract_noop):
    check_ocrmypdf(
        resources / 'crom.png', outpdf, '--image-dpi', '200',
        '--optimize', '2', '--jpg-quality', '50', '--png-quality', '20',
        env=spoof_tesseract_noop
    )
