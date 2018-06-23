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

import pytest

from ocrmypdf import leptonica
from ocrmypdf.pdfinfo import PdfInfo
from ocrmypdf.exec import ghostscript


# pytest.helpers is dynamic
# pylint: disable=no-member
# pylint: disable=w0612

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf


RENDERERS = ['hocr', 'sandwich']


def check_monochrome_correlation(
        outdir,
        reference_pdf, reference_pageno, test_pdf, test_pageno):
    gslog = logging.getLogger()

    reference_png = outdir / '{}.ref{:04d}.png'.format(
        reference_pdf.name, reference_pageno)
    test_png = outdir / '{}.test{:04d}.png'.format(
        test_pdf.name, test_pageno)

    def rasterize(pdf, pageno, png):
        if png.exists():
            print(png)
            return
        ghostscript.rasterize_pdf(
            pdf, png, xres=100, yres=100,
            raster_device='pngmono', log=gslog, pageno=pageno)

    rasterize(reference_pdf, reference_pageno, reference_png)
    rasterize(test_pdf, test_pageno, test_png)

    pix_ref = leptonica.Pix.open(reference_png)
    pix_test = leptonica.Pix.open(test_png)

    return leptonica.Pix.correlation_binary(pix_ref, pix_test)


def test_monochrome_correlation(resources, outdir):
    # Verify leptonica: check that an incorrect rotated image has poor
    # correlation with reference
    corr = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=1,  # north facing page
        test_pdf=resources / 'cardinal.pdf',
        test_pageno=3,  # south facing page
        )
    assert corr < 0.10
    corr = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=2,
        test_pdf=resources / 'cardinal.pdf',
        test_pageno=2,
        )
    assert corr > 0.90


@pytest.mark.parametrize('renderer', RENDERERS)
def test_autorotate(spoof_tesseract_cache, renderer, resources, outdir):
    # cardinal.pdf contains four copies of an image rotated in each cardinal
    # direction - these ones are "burned in" not tagged with /Rotate
    out = check_ocrmypdf(resources / 'cardinal.pdf', outdir / 'out.pdf',
                         '-r', '-v', '1', '--pdf-renderer', renderer,
                         env=spoof_tesseract_cache)
    for n in range(1, 4+1):
        correlation = check_monochrome_correlation(
            outdir,
            reference_pdf=resources / 'cardinal.pdf',
            reference_pageno=1,
            test_pdf=outdir / 'out.pdf',
            test_pageno=n)
        assert correlation > 0.80


@pytest.mark.parametrize('threshold, correlation_test', [
    ('1', 'correlation > 0.80'),  # Low thresh -> always rotate -> high corr
    ('99', 'correlation < 0.10'),  # High thres -> never rotate -> low corr
])
def test_autorotate_threshold(
        spoof_tesseract_cache, threshold, correlation_test, resources, outdir):
    out = check_ocrmypdf(resources / 'cardinal.pdf', outdir / 'out.pdf',
                         '--rotate-pages-threshold', threshold,
                         '-r', '-v', '1', env=spoof_tesseract_cache)

    correlation = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'out.pdf',
        test_pageno=3)
    assert eval(correlation_test)


def test_rotated_skew_timeout(resources, outpdf):
    """This document contains an image that is rotated 90 into place with a
    /Rotate tag and intentionally skewed by altering the transformation matrix.

    This tests for a bug where the combination of preprocessing and a tesseract
    timeout produced a page whose dimensions did not match the original's.
    """

    input_file = resources / 'rotated_skew.pdf'
    in_pageinfo = PdfInfo(input_file)[0]

    assert in_pageinfo.height_pixels < in_pageinfo.width_pixels, \
        "Expected the input page to be landscape"
    assert in_pageinfo.rotation == 90, "Expected a rotated page"

    out = check_ocrmypdf(
        input_file, outpdf,
        '--pdf-renderer', 'hocr',
        '--deskew', '--tesseract-timeout', '0')

    out_pageinfo = PdfInfo(out)[0]
    w, h = out_pageinfo.width_pixels, out_pageinfo.height_pixels

    assert h > w, \
        "Expected the output page to be portrait"

    assert out_pageinfo.rotation == 0, \
        "Expected no page rotation for output"

    assert in_pageinfo.width_pixels == h and \
        in_pageinfo.height_pixels == w, \
        "Expected page rotation to be baked in"


def test_rotate_deskew_timeout(resources, outdir):
    check_ocrmypdf(
        resources / 'rotated_skew.pdf',
        outdir / 'deskewed.pdf',
        '--deskew',
        '--tesseract-timeout', '0',
        '--pdf-renderer', 'sandwich'
    )

    correlation = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'ccitt.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'deskewed.pdf',
        test_pageno=1)

    # Confirm that the page still got deskewed
    assert correlation > 0.50
