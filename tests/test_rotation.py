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

from io import BytesIO
from os import fspath

import img2pdf
import pikepdf
import pytest
from PIL import Image

from ocrmypdf import leptonica
from ocrmypdf._exec import ghostscript, tesseract
from ocrmypdf.helpers import Resolution
from ocrmypdf.pdfinfo import PdfInfo

# pytest.helpers is dynamic
# pylint: disable=no-member
# pylint: disable=w0612

pytestmark = pytest.mark.skipif(
    leptonica.get_leptonica_version() < 'leptonica-1.72',
    reason="Leptonica is too old, correlation doesn't work",
)

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf


RENDERERS = ['hocr', 'sandwich']


def check_monochrome_correlation(
    outdir, reference_pdf, reference_pageno, test_pdf, test_pageno
):
    reference_png = outdir / f'{reference_pdf.name}.ref{reference_pageno:04d}.png'
    test_png = outdir / f'{test_pdf.name}.test{test_pageno:04d}.png'

    def rasterize(pdf, pageno, png):
        if png.exists():
            print(png)
            return
        ghostscript.rasterize_pdf(
            pdf,
            png,
            raster_device='pngmono',
            raster_dpi=Resolution(100, 100),
            pageno=pageno,
            rotation=0,
        )

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


@pytest.mark.slow
@pytest.mark.parametrize('renderer', RENDERERS)
def test_autorotate(renderer, resources, outdir):
    # cardinal.pdf contains four copies of an image rotated in each cardinal
    # direction - these ones are "burned in" not tagged with /Rotate
    out = check_ocrmypdf(
        resources / 'cardinal.pdf',
        outdir / 'out.pdf',
        '-r',
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    for n in range(1, 4 + 1):
        correlation = check_monochrome_correlation(
            outdir,
            reference_pdf=resources / 'cardinal.pdf',
            reference_pageno=1,
            test_pdf=outdir / 'out.pdf',
            test_pageno=n,
        )
        assert correlation > 0.80


@pytest.mark.parametrize(
    'threshold, correlation_test',
    [
        ('1', 'correlation > 0.80'),  # Low thresh -> always rotate -> high corr
        ('99', 'correlation < 0.10'),  # High thres -> never rotate -> low corr
    ],
)
def test_autorotate_threshold(threshold, correlation_test, resources, outdir):
    out = check_ocrmypdf(
        resources / 'cardinal.pdf',
        outdir / 'out.pdf',
        '--rotate-pages-threshold',
        threshold,
        '-r',
        # '-v',
        # '1',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    correlation = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'out.pdf',
        test_pageno=3,
    )
    assert eval(correlation_test)  # pylint: disable=w0123


def test_rotated_skew_timeout(resources, outpdf):
    """This document contains an image that is rotated 90 into place with a
    /Rotate tag and intentionally skewed by altering the transformation matrix.

    This tests for a bug where the combination of preprocessing and a tesseract
    timeout produced a page whose dimensions did not match the original's.
    """

    input_file = resources / 'rotated_skew.pdf'
    in_pageinfo = PdfInfo(input_file)[0]

    assert (
        in_pageinfo.height_pixels < in_pageinfo.width_pixels
    ), "Expected the input page to be landscape"
    assert in_pageinfo.rotation == 90, "Expected a rotated page"

    out = check_ocrmypdf(
        input_file,
        outpdf,
        '--pdf-renderer',
        'hocr',
        '--deskew',
        '--tesseract-timeout',
        '0',
    )

    out_pageinfo = PdfInfo(out)[0]
    w, h = out_pageinfo.width_pixels, out_pageinfo.height_pixels

    assert h > w, "Expected the output page to be portrait"

    assert out_pageinfo.rotation == 0, "Expected no page rotation for output"

    assert (
        in_pageinfo.width_pixels == h and in_pageinfo.height_pixels == w
    ), "Expected page rotation to be baked in"


def test_rotate_deskew_timeout(resources, outdir):
    check_ocrmypdf(
        resources / 'rotated_skew.pdf',
        outdir / 'deskewed.pdf',
        '--rotate-pages',
        '--rotate-pages-threshold',
        '0',
        '--deskew',
        '--tesseract-timeout',
        '0',
        '--pdf-renderer',
        'sandwich',
    )

    correlation = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'ccitt.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'deskewed.pdf',
        test_pageno=1,
    )

    # Confirm that the page still got deskewed
    assert correlation > 0.50


@pytest.mark.slow
@pytest.mark.parametrize('page_angle', (0, 90, 180, 270))
@pytest.mark.parametrize('image_angle', (0, 90, 180, 270))
def test_rotate_page_level(image_angle, page_angle, resources, outdir):
    def make_rotate_test(prefix, image_angle, page_angle):
        memimg = BytesIO()
        with Image.open(fspath(resources / 'typewriter.png')) as im:
            if image_angle != 0:
                ccw_angle = -image_angle % 360
                im = im.transpose(getattr(Image, f'ROTATE_{ccw_angle}'))
            im.save(memimg, format='PNG')
        memimg.seek(0)
        mempdf = BytesIO()
        img2pdf.convert(
            memimg.read(),
            layout_fun=img2pdf.get_fixed_dpi_layout_fun((200, 200)),
            outputstream=mempdf,
        )
        mempdf.seek(0)
        pike = pikepdf.open(mempdf)
        pike.pages[0].Rotate = page_angle
        target = outdir / f'{prefix}_{image_angle}_{page_angle}.pdf'
        pike.save(target)
        return target

    reference = make_rotate_test('ref', 0, 0)
    test = make_rotate_test('test', image_angle, page_angle)
    out = test.with_suffix('.out.pdf')

    p, _, err = run_ocrmypdf(
        test,
        out,
        '-O0',
        '--rotate-pages',
        '--rotate-pages-threshold',
        '0.001',
        universal_newlines=False,
    )
    err = err.decode('utf-8', errors='replace')
    assert p.returncode == 0, err

    assert check_monochrome_correlation(outdir, reference, 1, out, 1) > 0.2


def test_tesseract_orientation(resources, tmp_path):
    pix = leptonica.Pix.open(resources / 'crom.png')
    pix_rotated = pix.rotate_orth(2)  # 180 degrees clockwise
    pix_rotated.write_implied_format(tmp_path / '000001.png')

    tesseract.get_orientation(  # Test results of this are unreliable
        tmp_path / '000001.png', engine_mode='3', timeout=10
    )
