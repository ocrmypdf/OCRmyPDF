# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import operator
from io import BytesIO
from math import cos, pi, sin
from os import fspath
from subprocess import run

import img2pdf
import pikepdf
import pytest
from PIL import Image, ImageChops
from reportlab.pdfgen.canvas import Canvas

from ocrmypdf._exec import ghostscript
from ocrmypdf._plugin_manager import get_plugin_manager
from ocrmypdf.helpers import IMG2PDF_KWARGS, Resolution
from ocrmypdf.pdfinfo import PdfInfo
from ocrmypdf.pluginspec import GhostscriptRasterDevice

from .conftest import check_ocrmypdf, run_ocrmypdf_api

# pylintx: disable=unused-variable

RENDERERS = ['fpdf2', 'sandwich']


def compare_images_monochrome(
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
            raster_device=GhostscriptRasterDevice.PNGMONO,
            raster_dpi=Resolution(100, 100),
            pageno=pageno,
            rotation=0,
        )

    rasterize(reference_pdf, reference_pageno, reference_png)
    rasterize(test_pdf, test_pageno, test_png)

    with Image.open(reference_png) as reference_im, Image.open(test_png) as test_im:
        assert reference_im.mode == test_im.mode == '1'
        assert reference_im.size == test_im.size, "Images must be the same size"

        # XOR the images: matching pixels become 0, different pixels become 1
        difference = ImageChops.logical_xor(reference_im, test_im)

        # Count matching pixels directly using getcolors()
        # For a binary image, getcolors returns [(count, 0), (count, 1)] or subset
        colors = difference.getcolors()
        color_counts = {color: count for count, color in colors}
        count_same = color_counts.get(0, 0)  # 0 = matching pixels (XOR result is 0)
        count_different = color_counts.get(255, 0)  # 255 = different pixels
        total = count_same + count_different

        return count_same / total


def test_monochrome_comparison(resources, outdir):
    # Self test: check that an incorrect rotated image has poor
    # comparison with reference
    cmp = compare_images_monochrome(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=1,  # north facing page
        test_pdf=resources / 'cardinal.pdf',
        test_pageno=3,  # south facing page
    )
    assert cmp < 0.90
    cmp = compare_images_monochrome(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=2,
        test_pdf=resources / 'cardinal.pdf',
        test_pageno=2,
    )
    assert cmp > 0.95


@pytest.mark.slow
@pytest.mark.parametrize('renderer', RENDERERS)
def test_autorotate(renderer, resources, outdir):
    # cardinal.pdf contains four copies of an image rotated in each cardinal
    # direction - these ones are "burned in" not tagged with /Rotate
    check_ocrmypdf(
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
        cmp = compare_images_monochrome(
            outdir,
            reference_pdf=resources / 'cardinal.pdf',
            reference_pageno=1,
            test_pdf=outdir / 'out.pdf',
            test_pageno=n,
        )
        assert cmp > 0.95


@pytest.mark.parametrize(
    'threshold, op, comparison_threshold',
    [
        ('1', operator.ge, 0.95),  # Low thresh -> always rotate -> high score
        ('99', operator.le, 0.90),  # High thres -> never rotate -> low score
    ],
)
def test_autorotate_threshold(threshold, op, comparison_threshold, resources, outdir):
    check_ocrmypdf(
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

    cmp = compare_images_monochrome(  # pylint: disable=unused-variable
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'out.pdf',
        test_pageno=3,
    )

    assert op(cmp, comparison_threshold)


@pytest.mark.parametrize('rasterizer', ['pypdfium', 'ghostscript'])
def test_rotated_skew_timeout(resources, outpdf, rasterizer):
    """Check rotated skew timeout.

    This document contains an image that is rotated 90 into place with a
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
        'fpdf2',
        '--deskew',
        '--tesseract-timeout',
        '0',
        '--rasterizer',
        rasterizer,
    )

    out_pageinfo = PdfInfo(out)[0]
    w, h = out_pageinfo.width_pixels, out_pageinfo.height_pixels

    assert h > w, "Expected the output page to be portrait"

    assert out_pageinfo.rotation == 0, "Expected no page rotation for output"

    assert (
        in_pageinfo.width_pixels == h and in_pageinfo.height_pixels == w
    ), "Expected page rotation to be baked in"


@pytest.mark.parametrize('rasterizer', ['pypdfium', 'ghostscript'])
def test_rotate_deskew_ocr_timeout(resources, outdir, rasterizer):
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
        'fpdf2',
        '--rasterizer',
        rasterizer,
    )

    cmp = compare_images_monochrome(
        outdir,
        reference_pdf=resources / 'ccitt.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'deskewed.pdf',
        test_pageno=1,
    )

    # Confirm that the page still got deskewed
    # pypdfium anti-aliases so gets better visual quality, but lower score (0.88)
    # on monochrome comparison; ghostscript looks ugly but gets > 0.95
    assert cmp > 0.85


def make_rotate_test(imagefile, outdir, prefix, image_angle, page_angle, cropbox=None):
    memimg = BytesIO()
    with Image.open(fspath(imagefile)) as im:
        if image_angle != 0:
            ccw_angle = -image_angle % 360
            im = im.transpose(getattr(Image.Transpose, f'ROTATE_{ccw_angle}'))
        im.save(memimg, format='PNG')
    memimg.seek(0)
    mempdf = BytesIO()
    img2pdf.convert(
        memimg.read(),
        layout_fun=img2pdf.get_fixed_dpi_layout_fun((200, 200)),
        outputstream=mempdf,
        **IMG2PDF_KWARGS,
    )
    mempdf.seek(0)
    with pikepdf.open(mempdf) as pdf:
        pdf.pages[0].Rotate = page_angle
        target = outdir / f'{prefix}_{image_angle}_{page_angle}.pdf'
        if cropbox:
            pdf.pages[0].CropBox = cropbox
        pdf.save(target)
        return target


@pytest.mark.slow
@pytest.mark.parametrize('page_angle', (0, 90, 180, 270))
@pytest.mark.parametrize('image_angle', (0, 90, 180, 270))
def test_rotate_page_level(image_angle, page_angle, resources, outdir, caplog):
    reference = make_rotate_test(resources / 'typewriter.png', outdir, 'ref', 0, 0)
    test = make_rotate_test(
        resources / 'typewriter.png', outdir, 'test', image_angle, page_angle
    )
    out = test.with_suffix('.out.pdf')

    exitcode = run_ocrmypdf_api(
        test,
        out,
        '-O0',
        '--rotate-pages',
        '--rotate-pages-threshold',
        '0.001',
    )
    assert exitcode == 0, caplog.text

    assert compare_images_monochrome(outdir, reference, 1, out, 1) > 0.2


@pytest.mark.slow
@pytest.mark.parametrize('page_rotate_angle', (0, 90, 180, 270))
def test_page_rotate_tag(page_rotate_angle, resources, outdir, caplog):
    # Check that pages that have an image that is misrotated but restored to
    # correct rotation with a /Rotate will be processed correct and yield text.
    test = make_rotate_test(
        resources / 'crom.png', outdir, 'test', -page_rotate_angle, page_rotate_angle
    )
    out = test.with_suffix('.out.pdf')
    exitcode = run_ocrmypdf_api(
        test,
        out,
        '-O0',
    )
    assert exitcode == 0, caplog.text

    def pdftotext(filename):
        return (
            run(['pdftotext', '-enc', 'UTF-8', filename, '-'], capture_output=True)
            .stdout.strip()
            .decode('utf-8')
        )

    test_text = pdftotext(out)
    assert 'is a' in test_text, test_text


@pytest.mark.parametrize('page_rotate_angle', (0, 90, 180, 270))
@pytest.mark.parametrize('renderer', ['sandwich', 'fpdf2'])
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_rotate_and_crop(
    resources, outdir, page_rotate_angle, renderer, output_type, caplog
):
    cropbox = (100, 200, 1000, 800)
    reference = make_rotate_test(
        resources / 'typewriter.png', outdir, 'ref', 0, 0, cropbox
    )
    test = make_rotate_test(
        resources / 'typewriter.png',
        outdir,
        'test',
        -page_rotate_angle,
        page_rotate_angle,
        cropbox,
    )
    out = test.with_suffix('.out.pdf')

    exitcode = run_ocrmypdf_api(
        test,
        out,
        '-O0',
        '--rotate-pages',
        '--rotate-pages-threshold',
        '0',
        '--pdf-renderer',
        renderer,
        '--output-type',
        output_type,
        '--no-progress-bar',
    )
    assert exitcode == 0, caplog.text

    assert compare_images_monochrome(outdir, reference, 1, out, 1) > 0.9


@pytest.mark.parametrize('rasterizer', ['pypdfium', 'ghostscript'])
def test_rasterize_rotates(resources, tmp_path, rasterizer):
    from ocrmypdf._options import OcrOptions

    pm = get_plugin_manager([])

    options = OcrOptions(
        input_file=resources / 'graph.pdf',
        output_file=tmp_path / 'out.pdf',
        rasterizer=rasterizer,
    )

    img = tmp_path / 'img90.png'
    pm.rasterize_pdf_page(
        input_file=resources / 'graph.pdf',
        output_file=img,
        raster_device=GhostscriptRasterDevice.PNGMONO,
        raster_dpi=Resolution(20, 20),
        page_dpi=Resolution(20, 20),
        pageno=1,
        rotation=90,
        filter_vector=False,
        stop_on_soft_error=True,
        options=options,
        use_cropbox=False,
    )
    with Image.open(img) as im:
        assert im.size == (83, 200), "Image not rotated"

    img = tmp_path / 'img180.png'
    pm.rasterize_pdf_page(
        input_file=resources / 'graph.pdf',
        output_file=img,
        raster_device=GhostscriptRasterDevice.PNGMONO,
        raster_dpi=Resolution(20, 20),
        page_dpi=Resolution(20, 20),
        pageno=1,
        rotation=180,
        filter_vector=False,
        stop_on_soft_error=True,
        options=options,
        use_cropbox=False,
    )
    assert Image.open(img).size == (200, 83), "Image not rotated"


def test_simulated_scan(outdir):
    canvas = Canvas(
        fspath(outdir / 'fakescan.pdf'),
        pagesize=(209.8, 297.6),
    )

    page_vars = [(2, 36, 250), (91, 170, 240), (179, 190, 36), (271, 36, 36)]

    for n, page_var in enumerate(page_vars):
        text = canvas.beginText()
        text.setFont('Helvetica', 20)

        angle, x, y = page_var
        cos_a, sin_a = cos(angle / 180.0 * pi), sin(angle / 180.0 * pi)

        text.setTextTransform(cos_a, -sin_a, sin_a, cos_a, x, y)
        text.textOut(f'Page {n + 1}')
        canvas.drawText(text)
        canvas.showPage()
    canvas.save()

    check_ocrmypdf(
        outdir / 'fakescan.pdf',
        outdir / 'out.pdf',
        '--force-ocr',
        '--deskew',
        '--rotate-pages',
        '--plugin',
        'tests/plugins/tesseract_debug_rotate.py',
    )

    with pikepdf.open(outdir / 'out.pdf') as pdf:
        assert (
            pdf.pages[1].mediabox[2] > pdf.pages[1].mediabox[3]
        ), "Wrong orientation: not landscape"
        assert (
            pdf.pages[3].mediabox[2] > pdf.pages[3].mediabox[3]
        ), "Wrong orientation: Not landscape"

        assert (
            pdf.pages[0].mediabox[2] < pdf.pages[0].mediabox[3]
        ), "Wrong orientation: Not portrait"
        assert (
            pdf.pages[2].mediabox[2] < pdf.pages[2].mediabox[3]
        ), "Wrong orientation: Not portrait"
