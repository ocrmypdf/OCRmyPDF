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

from os import fspath
from pathlib import Path
from unittest.mock import patch

import img2pdf
import pikepdf
import pytest
from PIL import Image, ImageDraw

from ocrmypdf import optimize as opt
from ocrmypdf._exec import jbig2enc, pngquant
from ocrmypdf._exec.ghostscript import rasterize_pdf
from ocrmypdf.helpers import Resolution

check_ocrmypdf = pytest.helpers.check_ocrmypdf  # pylint: disable=e1101


@pytest.mark.parametrize('pdf', ['multipage.pdf', 'palette.pdf'])
def test_basic(resources, pdf, outpdf):
    infile = resources / pdf
    opt.main(infile, outpdf, level=3)

    assert 0.98 * Path(outpdf).stat().st_size <= Path(infile).stat().st_size


def test_mono_not_inverted(resources, outdir):
    infile = resources / '2400dpi.pdf'
    opt.main(infile, outdir / 'out.pdf', level=3)

    rasterize_pdf(
        outdir / 'out.pdf',
        outdir / 'im.png',
        raster_device='pnggray',
        raster_dpi=Resolution(10, 10),
    )

    with Image.open(fspath(outdir / 'im.png')) as im:
        assert im.getpixel((0, 0)) == 255, "Expected white background"


@pytest.mark.skipif(not pngquant.available(), reason='need pngquant')
def test_jpg_png_params(resources, outpdf):
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
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@pytest.mark.skipif(not jbig2enc.available(), reason='need jbig2enc')
@pytest.mark.parametrize('lossy', [False, True])
def test_jbig2_lossy(lossy, resources, outpdf):
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
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    ]
    if lossy:
        args.append('--jbig2-lossy')

    check_ocrmypdf(*args)

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
def test_flate_to_jbig2(resources, outdir):
    # This test requires an image that pngquant is capable of converting to
    # to 1bpp - so use an existing 1bpp image, convert up, confirm it can
    # convert down
    with Image.open(fspath(resources / 'typewriter.png')) as im:
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
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    pdf = pikepdf.open(outdir / 'out.pdf')
    pim = pikepdf.PdfImage(next(iter(pdf.pages[0].images.values())))
    assert pim.filters[0] == '/JBIG2Decode'


def test_multiple_pngs(resources, outdir):
    with Path.open(outdir / 'in.pdf', 'wb') as inpdf:
        img2pdf.convert(
            fspath(resources / 'baiona_colormapped.png'),
            fspath(resources / 'baiona_gray.png'),
            with_pdfrw=False,
            outputstream=inpdf,
        )

    def mockquant(input_file, output_file, _quality_min, _quality_max):
        with Image.open(input_file) as im:
            draw = ImageDraw.Draw(im)
            draw.rectangle((0, 0, im.width, im.height), fill=128)
            im.save(output_file)

    with patch('ocrmypdf.optimize.pngquant.quantize', new=mockquant):
        check_ocrmypdf(
            outdir / 'in.pdf',
            outdir / 'out.pdf',
            '--optimize',
            '3',
            '--jobs',
            '1',
            '--use-threads',
            '--output-type',
            'pdf',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    with pikepdf.open(outdir / 'in.pdf') as inpdf, pikepdf.open(
        outdir / 'out.pdf'
    ) as outpdf:
        for n in range(len(inpdf.pages)):
            inim = next(iter(inpdf.pages[n].images.values()))
            outim = next(iter(outpdf.pages[n].images.values()))
            assert len(outim.read_raw_bytes()) < len(inim.read_raw_bytes()), n
