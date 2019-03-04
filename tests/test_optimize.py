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

import logging
from os import fspath
from pathlib import Path

import pytest
from PIL import Image

import pikepdf
from ocrmypdf import optimize as opt
from ocrmypdf.exec import jbig2enc, pngquant
from ocrmypdf.exec.ghostscript import rasterize_pdf

check_ocrmypdf = pytest.helpers.check_ocrmypdf  # pylint: disable=e1101


@pytest.mark.parametrize('pdf', ['multipage.pdf', 'palette.pdf'])
def test_basic(resources, pdf, outpdf):
    infile = resources / pdf
    opt.main(infile, outpdf, level=3)

    assert Path(outpdf).stat().st_size <= Path(infile).stat().st_size


def test_mono_not_inverted(resources, outdir):
    infile = resources / '2400dpi.pdf'
    opt.main(infile, outdir / 'out.pdf', level=3)

    rasterize_pdf(
        outdir / 'out.pdf',
        outdir / 'im.png',
        xres=10,
        yres=10,
        raster_device='pnggray',
        log=logging.getLogger(name='test_mono_flip'),
    )

    im = Image.open(fspath(outdir / 'im.png'))
    assert im.getpixel((0, 0)) == 255, "Expected white background"


def test_jpg_png_params(resources, outpdf, spoof_tesseract_noop):
    check_ocrmypdf(
        resources / 'crom.png',
        outpdf,
        '--image-dpi',
        '200',
        '--optimize',
        '3',
        '--jpg-quality',
        '50',
        '--png-quality',
        '20',
        env=spoof_tesseract_noop,
    )


@pytest.mark.skipif(not jbig2enc.available(), reason='need jbig2enc')
@pytest.mark.parametrize('lossy', [False, True])
def test_jbig2_lossy(lossy, resources, outpdf, spoof_tesseract_noop):
    args = [
        resources / 'ccitt.pdf',
        outpdf,
        '--image-dpi',
        '200',
        '--optimize',
        3,
        '--jpg-quality',
        '50',
        '--png-quality',
        '20',
    ]
    if lossy:
        args.append('--jbig2-lossy')

    check_ocrmypdf(*args, env=spoof_tesseract_noop)

    pdf = pikepdf.open(outpdf)
    pim = pikepdf.PdfImage(next(iter(pdf.pages[0].images.values())))
    assert pim.filters[0] == '/JBIG2Decode'

    if lossy:
        assert '/JBIG2Globals' in pim.decode_parms[0]
    else:
        assert len(pim.decode_parms) == 0


@pytest.mark.skipif(
    not jbig2enc.available() or not pngquant.available(),
    reason='need jbig2enc and pngquant',
)
def test_flate_to_jbig2(resources, outdir, spoof_tesseract_noop):
    # This test requires an image that pngquant is capable of converting to
    # to 1bpp - so use an existing 1bpp image, convert up, confirm it can
    # convert down
    im = Image.open(fspath(resources / 'typewriter.png'))
    assert im.mode in ('1', 'P')
    im = im.convert('L')
    im.save(fspath(outdir / 'type8.png'))

    check_ocrmypdf(
        outdir / 'type8.png',
        outdir / 'out.pdf',
        '--image-dpi',
        '100',
        '--png-quality',
        '50',
        '--optimize',
        '3',
        env=spoof_tesseract_noop,
    )

    pdf = pikepdf.open(outdir / 'out.pdf')
    pim = pikepdf.PdfImage(next(iter(pdf.pages[0].images.values())))
    assert pim.filters[0] == '/JBIG2Decode'
