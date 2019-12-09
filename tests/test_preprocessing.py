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
from math import isclose

import pytest
from PIL import Image

from ocrmypdf.exec import ghostscript
from ocrmypdf.leptonica import Pix
from ocrmypdf.pdfinfo import PdfInfo

# pytest.helpers is dynamic
# pylint: disable=no-member,redefined-outer-name

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf_api
spoof = pytest.helpers.spoof


RENDERERS = ['hocr', 'sandwich']


def test_deskew(spoof_tesseract_noop, resources, outdir):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(
        resources / 'skew.pdf', outdir / 'skew.pdf', '-d', env=spoof_tesseract_noop
    )

    # Now render as an image again and use Leptonica to find the skew angle
    # to confirm that it was deskewed
    log = logging.getLogger()

    deskewed_png = outdir / 'deskewed.png'

    ghostscript.rasterize_pdf(
        deskewed_pdf,
        deskewed_png,
        xres=150,
        yres=150,
        raster_device='pngmono',
        log=log,
        pageno=1,
    )

    pix = Pix.open(deskewed_png)
    skew_angle, _skew_confidence = pix.find_skew()

    print(skew_angle)
    assert -0.5 < skew_angle < 0.5, "Deskewing failed"


def test_remove_background(spoof_tesseract_noop, resources, outdir):
    # Ensure the input image does not contain pure white/black
    with Image.open(resources / 'congress.jpg') as im:
        assert im.getextrema() != ((0, 255), (0, 255), (0, 255))

    output_pdf = check_ocrmypdf(
        resources / 'congress.jpg',
        outdir / 'test_remove_bg.pdf',
        '--remove-background',
        '--image-dpi',
        '150',
        env=spoof_tesseract_noop,
    )

    log = logging.getLogger()

    output_png = outdir / 'remove_bg.png'

    ghostscript.rasterize_pdf(
        output_pdf,
        output_png,
        xres=100,
        yres=100,
        raster_device='png16m',
        log=log,
        pageno=1,
    )

    # The output image should contain pure white and black
    with Image.open(output_png) as im:
        assert im.getextrema() == ((0, 255), (0, 255), (0, 255))


# This will run 5 * 2 * 2 = 20 test cases
@pytest.mark.parametrize(
    "pdf", ['palette.pdf', 'cmyk.pdf', 'ccitt.pdf', 'jbig2.pdf', 'lichtenstein.pdf']
)
@pytest.mark.parametrize("renderer", ['sandwich', 'hocr'])
@pytest.mark.parametrize("output_type", ['pdf', 'pdfa'])
def test_exotic_image(
    spoof_tesseract_cache, pdf, renderer, output_type, resources, outdir
):
    outfile = outdir / f'test_{pdf}_{renderer}.pdf'
    check_ocrmypdf(
        resources / pdf,
        outfile,
        '-dc' if pytest.helpers.have_unpaper() else '-d',
        '-v',
        '1',
        '--output-type',
        output_type,
        '--sidecar',
        '--skip-text',
        '--pdf-renderer',
        renderer,
        env=spoof_tesseract_cache,
    )

    assert outfile.with_suffix('.pdf.txt').exists()


@pytest.mark.parametrize('renderer', RENDERERS)
def test_non_square_resolution(renderer, spoof_tesseract_cache, resources, outpdf):
    # Confirm input image is non-square resolution
    in_pageinfo = PdfInfo(resources / 'aspect.pdf')
    assert in_pageinfo[0].xres != in_pageinfo[0].yres

    check_ocrmypdf(
        resources / 'aspect.pdf',
        outpdf,
        '--pdf-renderer',
        renderer,
        env=spoof_tesseract_cache,
    )

    out_pageinfo = PdfInfo(outpdf)

    # Confirm resolution was kept the same
    assert in_pageinfo[0].xres == out_pageinfo[0].xres
    assert in_pageinfo[0].yres == out_pageinfo[0].yres


@pytest.mark.parametrize('renderer', RENDERERS)
def test_convert_to_square_resolution(
    renderer, spoof_tesseract_cache, resources, outpdf
):
    # Confirm input image is non-square resolution
    in_pageinfo = PdfInfo(resources / 'aspect.pdf')
    assert in_pageinfo[0].xres != in_pageinfo[0].yres

    # --force-ocr requires means forced conversion to square resolution
    check_ocrmypdf(
        resources / 'aspect.pdf',
        outpdf,
        '--force-ocr',
        '--pdf-renderer',
        renderer,
        env=spoof_tesseract_cache,
    )

    out_pageinfo = PdfInfo(outpdf)

    in_p0, out_p0 = in_pageinfo[0], out_pageinfo[0]

    # Resolution show now be equal
    assert out_p0.xres == out_p0.yres

    # Page size should match input page size
    assert isclose(in_p0.width_inches, out_p0.width_inches)
    assert isclose(in_p0.height_inches, out_p0.height_inches)

    # Because we rasterized the page to produce a new image, it should occupy
    # the entire page
    out_im_w = out_p0.images[0].width / out_p0.images[0].xres
    out_im_h = out_p0.images[0].height / out_p0.images[0].yres
    assert isclose(out_p0.width_inches, out_im_w)
    assert isclose(out_p0.height_inches, out_im_h)
