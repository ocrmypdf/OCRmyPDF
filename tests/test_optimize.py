# © 2018 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


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
from ocrmypdf.helpers import IMG2PDF_KWARGS, Resolution

from .conftest import check_ocrmypdf

needs_pngquant = pytest.mark.skipif(
    not pngquant.available(), reason="pngquant not installed"
)
needs_jbig2enc = pytest.mark.skipif(
    not jbig2enc.available(), reason="jbig2enc not installed"
)


@needs_pngquant
@pytest.mark.parametrize('pdf', ['multipage.pdf', 'palette.pdf'])
def test_basic(resources, pdf, outpdf):
    infile = resources / pdf
    opt.main(infile, outpdf, level=3)

    assert 0.98 * Path(outpdf).stat().st_size <= Path(infile).stat().st_size


@needs_pngquant
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
        assert im.getpixel((0, 0)) > 240, "Expected white background"


@needs_pngquant
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


@needs_jbig2enc
@pytest.mark.parametrize('lossy', [False, True])
def test_jbig2_lossy(lossy, resources, outpdf):
    args = [
        resources / 'ccitt.pdf',
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


@needs_pngquant
@needs_jbig2enc
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


@needs_pngquant
def test_multiple_pngs(resources, outdir):
    with Path.open(outdir / 'in.pdf', 'wb') as inpdf:
        img2pdf.convert(
            fspath(resources / 'baiona_colormapped.png'),
            fspath(resources / 'baiona_gray.png'),
            outputstream=inpdf,
            **IMG2PDF_KWARGS,
        )

    def mockquant(input_file, output_file, *_args):
        with Image.open(input_file) as im:
            draw = ImageDraw.Draw(im)
            draw.rectangle((0, 0, im.width, im.height), fill=128)
            im.save(output_file)

    with patch('ocrmypdf.optimize.pngquant.quantize') as mock:
        mock.side_effect = mockquant
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
        mock.assert_called()

    with pikepdf.open(outdir / 'in.pdf') as inpdf, pikepdf.open(
        outdir / 'out.pdf'
    ) as outpdf:
        for n in range(len(inpdf.pages)):
            inim = next(iter(inpdf.pages[n].images.values()))
            outim = next(iter(outpdf.pages[n].images.values()))
            assert len(outim.read_raw_bytes()) < len(inim.read_raw_bytes()), n


def test_optimize_off(resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--optimize=0',
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


def test_group3(resources, outdir):
    with pikepdf.open(resources / 'ccitt.pdf') as pdf:
        im = pdf.pages[0].Resources.XObject['/Im1']
        assert (
            opt.extract_image_filter(pdf, outdir, im, im.objgen[0]) is not None
        ), "Group 4 should be allowed"

        im.DecodeParms['/K'] = 0
        assert (
            opt.extract_image_filter(pdf, outdir, im, im.objgen[0]) is None
        ), "Group 3 should be disallowed"
