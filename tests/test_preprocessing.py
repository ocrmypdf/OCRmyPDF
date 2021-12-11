# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from math import isclose

import pytest
from PIL import Image

from ocrmypdf._exec import ghostscript, tesseract
from ocrmypdf.helpers import Resolution
from ocrmypdf.pdfinfo import PdfInfo

from .conftest import check_ocrmypdf, have_unpaper

RENDERERS = ['hocr', 'sandwich']


def test_deskew(resources, outdir):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(resources / 'skew.pdf', outdir / 'skew.pdf', '-d')

    # Now render as an image again...
    deskewed_png = outdir / 'deskewed.png'

    ghostscript.rasterize_pdf(
        deskewed_pdf,
        deskewed_png,
        raster_device='pngmono',
        raster_dpi=Resolution(150, 150),
        pageno=1,
    )

    # ...and use Tessera to find the skew angle to confirm that it was deskewed
    skew_angle = tesseract.get_deskew(deskewed_png, [], None, 5.0)
    print(skew_angle)
    assert -0.5 < skew_angle < 0.5, "Deskewing failed"


def test_deskew_blank_page(resources, outpdf):
    # Tesseract doesn't like blank pages - make sure we can get through
    check_ocrmypdf(resources / 'blank.pdf', outpdf, '--deskew')


@pytest.mark.xfail(reason="remove background disabled")
def test_remove_background(resources, outdir):
    # Ensure the input image does not contain pure white/black
    with Image.open(resources / 'congress.jpg') as im:
        assert im.getextrema() != ((0, 255), (0, 255), (0, 255))

    output_pdf = check_ocrmypdf(
        resources / 'congress.jpg',
        outdir / 'test_remove_bg.pdf',
        '--remove-background',
        '--image-dpi',
        '150',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    output_png = outdir / 'remove_bg.png'

    ghostscript.rasterize_pdf(
        output_pdf,
        output_png,
        raster_device='png16m',
        raster_dpi=Resolution(100, 100),
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
def test_exotic_image(pdf, renderer, output_type, resources, outdir):
    outfile = outdir / f'test_{pdf}_{renderer}.pdf'
    check_ocrmypdf(
        resources / pdf,
        outfile,
        '-dc' if have_unpaper() else '-d',
        '-v',
        '1',
        '--output-type',
        output_type,
        '--sidecar',
        '--skip-text',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    assert outfile.with_suffix('.pdf.txt').exists()


@pytest.mark.parametrize('renderer', RENDERERS)
def test_non_square_resolution(renderer, resources, outpdf):
    # Confirm input image is non-square resolution
    in_pageinfo = PdfInfo(resources / 'aspect.pdf')
    assert in_pageinfo[0].dpi.x != in_pageinfo[0].dpi.y

    check_ocrmypdf(
        resources / 'aspect.pdf',
        outpdf,
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    out_pageinfo = PdfInfo(outpdf)

    # Confirm resolution was kept the same
    assert in_pageinfo[0].dpi == out_pageinfo[0].dpi


@pytest.mark.parametrize('renderer', RENDERERS)
def test_convert_to_square_resolution(renderer, resources, outpdf):
    # Confirm input image is non-square resolution
    in_pageinfo = PdfInfo(resources / 'aspect.pdf')
    assert in_pageinfo[0].dpi.x != in_pageinfo[0].dpi.y

    # --force-ocr requires means forced conversion to square resolution
    check_ocrmypdf(
        resources / 'aspect.pdf',
        outpdf,
        '--force-ocr',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    out_pageinfo = PdfInfo(outpdf)

    in_p0, out_p0 = in_pageinfo[0], out_pageinfo[0]

    # Resolution show now be equal
    assert out_p0.dpi.x == out_p0.dpi.y

    # Page size should match input page size
    assert isclose(in_p0.width_inches, out_p0.width_inches)
    assert isclose(in_p0.height_inches, out_p0.height_inches)

    # Because we rasterized the page to produce a new image, it should occupy
    # the entire page
    out_im_w = out_p0.images[0].width / out_p0.images[0].dpi.x
    out_im_h = out_p0.images[0].height / out_p0.images[0].dpi.y
    assert isclose(out_p0.width_inches, out_im_w)
    assert isclose(out_p0.height_inches, out_im_h)
