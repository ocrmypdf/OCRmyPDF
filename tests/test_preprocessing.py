# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-FileCopyrightText: 2026 Surfire
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from io import BytesIO
from math import isclose

import img2pdf
import pikepdf
import pytest
from pdfminer.high_level import extract_text
from pikepdf.pdfa import validate_written
from PIL import Image, ImageDraw, ImageFont

from ocrmypdf._exec import ghostscript, tesseract
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.helpers import Resolution
from ocrmypdf.pdfa import output_type_to_flavour
from ocrmypdf.pdfinfo import PdfInfo
from ocrmypdf.pluginspec import GhostscriptRasterDevice

from .conftest import (
    RENDERERS,
    check_ocrmypdf,
    first_page_dimensions,
    have_unpaper,
    run_ocrmypdf,
)


def test_deskew(resources, outdir):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(resources / 'skew.pdf', outdir / 'skew.pdf', '-d')

    # Now render as an image again...
    deskewed_png = outdir / 'deskewed.png'

    ghostscript.rasterize_pdf(
        deskewed_pdf,
        deskewed_png,
        raster_device=GhostscriptRasterDevice.PNGMONO,
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
    with Image.open(resources / 'baiona_color.jpg') as im:
        assert im.getextrema() != ((0, 255), (0, 255), (0, 255))

    output_pdf = check_ocrmypdf(
        resources / 'baiona_color.jpg',
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
        raster_device=GhostscriptRasterDevice.PNG16M,
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
@pytest.mark.parametrize("renderer", ['sandwich', 'fpdf2'])
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

    proc = run_ocrmypdf(
        resources / 'aspect.pdf',
        outpdf,
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    # PDF/A conversion can fail for this file if Ghostscript >= 10.3, so don't test
    # exit code in that case
    if proc.returncode != ExitCode.pdfa_conversion_failed:
        proc.check_returncode()

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


@pytest.mark.parametrize('renderer', RENDERERS)
def test_oversample(renderer, resources, outpdf):
    oversampled_pdf = check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--oversample',
        '350',
        '-f',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    pdfinfo = PdfInfo(oversampled_pdf)

    print(pdfinfo[0].dpi.x)
    assert abs(pdfinfo[0].dpi.x - 350) < 1


@pytest.mark.parametrize(
    ('dpi', 'rotation', 'image_ext', 'output_type'),
    [
        (144, 0, 'png', 'pdf'),
        (144, 90, 'jpg', 'pdfa-2'),
        (432, 0, 'png', 'pdf'),
    ],
)
def test_oversample_deskew_visible_resolution(
    dpi, rotation, image_ext, output_type, outdir, outpdf, monkeypatch
):
    """Deskew may use oversampled pixels, but emits the ordinary raster DPI."""
    ocr_log = outdir / 'ocr_image.log'
    monkeypatch.setenv('OCRMYPDF_TEST_OCR_IMAGE_LOG', str(ocr_log))
    image = Image.new('L', (6 * dpi, 4 * dpi), 255)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=dpi // 3)
    for line, text in enumerate(
        ('QUARTZ SAMPLE', 'SEARCHABLE PAGE', 'PRESERVE GEOMETRY'), start=1
    ):
        draw.text((dpi // 2, line * dpi - dpi // 3), text, fill=0, font=font)
    if rotation:
        image = image.transpose(Image.Transpose.ROTATE_90)
    scan = outdir / f'scan.{image_ext}'
    image.save(scan, dpi=(dpi, dpi))
    source = outdir / 'scan.pdf'
    with pikepdf.Pdf.open(BytesIO(img2pdf.convert(str(scan)))) as pdf:
        if rotation:
            pdf.pages[0].obj.Rotate = rotation
        pdf.save(source)

    proc = run_ocrmypdf(
        source,
        outpdf,
        '--deskew',
        '--oversample',
        '360',
        '--plugin',
        'tests/plugins/ocr_image_recorder.py',
        '--output-type',
        output_type,
        '--pdfa-backend',
        'internal',
        '-O0',
        '-j1',
    )
    assert proc.returncode == 0, proc.stderr
    ocr_dpi = max(360, dpi)
    assert ocr_log.read_text().split() == [str(6 * ocr_dpi), str(4 * ocr_dpi), 'L']
    out_page = PdfInfo(outpdf)[0]
    assert out_page.images[0].dpi.x == pytest.approx(dpi, abs=1)
    assert out_page.images[0].dpi.y == pytest.approx(dpi, abs=1)
    page_size = float(out_page.width_inches), float(out_page.height_inches)
    if out_page.rotation % 180:
        page_size = page_size[::-1]
    assert page_size == pytest.approx((6, 4), abs=0.001)
    assert 'QUARTZ SAMPLE' in extract_text(outpdf)
    if output_type == 'pdfa-2':
        report = validate_written(outpdf, output_type_to_flavour(output_type))
        assert report.verdict == 'pass', report.summary()


def test_oversample_deskew_userunit(outdir, monkeypatch):
    """The visible-image hook gets the ordinary page DPI even with /UserUnit."""
    scan = outdir / 'userunit.png'
    image = Image.new('L', (600, 360), 255)
    draw = ImageDraw.Draw(image)
    draw.text((50, 100), 'QUARTZ SAMPLE', fill=0, font=ImageFont.load_default(size=48))
    image.save(scan, dpi=(120, 120))
    source = outdir / 'userunit.pdf'
    with pikepdf.Pdf.open(BytesIO(img2pdf.convert(str(scan)))) as pdf:
        pdf.pages[0].obj.UserUnit = 2
        pdf.save(source, min_version='1.6')

    for oversample, ocr_size in [(0, (300, 180)), (360, (1800, 1080))]:
        output = outdir / f'userunit-{oversample}.pdf'
        ocr_log = output.with_suffix('.ocr.log')
        visible_log = output.with_suffix('.visible.log')
        monkeypatch.setenv('OCRMYPDF_TEST_OCR_IMAGE_LOG', str(ocr_log))
        monkeypatch.setenv('OCRMYPDF_TEST_PAGE_IMAGE_LOG', str(visible_log))
        proc = run_ocrmypdf(
            source,
            output,
            '--deskew',
            '--oversample',
            str(oversample),
            '--plugin',
            'tests/plugins/ocr_image_recorder.py',
            '--output-type',
            'pdf',
            '-O0',
            '-j1',
        )
        assert proc.returncode == 0, proc.stderr
        assert tuple(map(int, ocr_log.read_text().split()[:2])) == ocr_size
        width, height, dpi_x, dpi_y = map(float, visible_log.read_text().split())
        assert (width, height) == (300, 180)
        assert (dpi_x, dpi_y) == pytest.approx((120, 120), abs=0.05)
        page = PdfInfo(output)[0]
        assert (float(page.width_inches), float(page.height_inches)) == (10, 6)
        assert (page.images[0].width, page.images[0].height) == (300, 180)


def test_very_high_dpi(resources, outpdf):
    """Checks for a Decimal quantize error with high DPI, etc."""
    check_ocrmypdf(
        resources / '2400dpi.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(outpdf)

    image = pdfinfo[0].images[0]
    assert isclose(image.dpi.x, image.dpi.y)
    assert isclose(image.dpi.x, 2400)


@pytest.mark.parametrize('renderer', RENDERERS)
def test_pagesize_consistency(renderer, resources, outpdf):
    infile = resources / '3small.pdf'

    before_dims = first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        renderer,
        '--clean' if have_unpaper() else None,
        '--deskew',
        # '--remove-background',
        '--clean-final' if have_unpaper() else None,
        '-k',
        '--pages',
        '1',
    )

    after_dims = first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0], rel_tol=1e-4)
    assert isclose(before_dims[1], after_dims[1], rel_tol=1e-4)


@pytest.mark.parametrize(
    'preproc',
    [
        '--deskew',
        pytest.param(
            '--clean-final',
            marks=pytest.mark.skipif(not have_unpaper(), reason="requires unpaper"),
        ),
    ],
)
def test_vector_only_page_preprocessing_keeps_page(preproc, resources, outpdf):
    check_ocrmypdf(resources / 'vector.pdf', outpdf, preproc, '--output-type', 'pdf')

    page = PdfInfo(outpdf)[0]
    assert not page.images, "vector-only page was replaced by a raster image"
    assert page.has_vector
    assert page.has_text, "vector-only page was not OCRed"
