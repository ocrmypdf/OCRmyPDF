#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

import pytest
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import tesseract
from ocrmypdf import pageinfo
import sys
import os
import PyPDF2 as pypdf


spoof = pytest.helpers.spoof


def tess4_possible_location():
    """The location of tesseract 4 may be OCRMYPDF_TESS4, OCRMYPDF_TESSERACT,
    or the installed version on PATH."""
    return os.environ.get('OCRMYPDF_TESS4') or \
           os.environ.get('OCRMYPDF_TESSERACT') or \
            'tesseract'


@pytest.fixture
def ensure_tess4():
    return spoof(tesseract=tess4_possible_location())


def tess4_available():
    """Check if a tesseract 4 binary is available, even if it's not the
    official "tesseract" on PATH

    """
    old_environ = os.environ.copy()
    try:
        os.environ['OCRMYPDF_TESSERACT'] = tess4_possible_location()
        return tesseract.v4() and tesseract.has_textonly_pdf()
    finally:
        os.environ = old_environ


# Skip all tests in this file if not tesseract 4
pytestmark = pytest.mark.skipif(
    not tess4_available(),
    reason="tesseract 4.0 with textonly_pdf feature required")

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


def test_textonly_pdf(ensure_tess4, resources, outdir):
    check_ocrmypdf(
        resources / 'linn.pdf',
        outdir / 'linn_textonly.pdf', '--pdf-renderer', 'tess4',
        env=ensure_tess4)


@pytest.mark.skipif(sys.version_info < (3, 5), reason="needs math.isclose")
def test_pagesize_consistency_tess4(ensure_tess4, resources, outpdf):
    from math import isclose

    infile = resources / 'linn.pdf'

    before_dims = pytest.helpers.first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf, '--pdf-renderer', 'tess4',
        '--clean', '--deskew', '--remove-background', '--clean-final',
        env=ensure_tess4)

    after_dims = pytest.helpers.first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0])
    assert isclose(before_dims[1], after_dims[1])


@pytest.mark.parametrize('basename', ['graph_ocred.pdf', 'cardinal.pdf'])
def test_skip_pages_does_not_replicate(
        ensure_tess4, resources, basename, outdir):
    infile = resources / basename
    outpdf = outdir / basename

    check_ocrmypdf(
        infile,
        outpdf, '--pdf-renderer', 'tess4', '--force-ocr',
        '--tesseract-timeout', '0',
        env=ensure_tess4
    )

    info_in = pageinfo.pdf_get_all_pageinfo(str(infile))

    info = pageinfo.pdf_get_all_pageinfo(str(outpdf))
    for page in info:
        assert len(page['images']) == 1, "skipped page was replicated"

    for n in range(len(info_in)):
        assert info[n]['width_inches'] == info_in[n]['width_inches']


def test_content_preservation(ensure_tess4, resources, outpdf):
    infile = resources / 'masks.pdf'

    check_ocrmypdf(
        infile,
        outpdf, '--pdf-renderer', 'tess4', '--tesseract-timeout', '0',
        env=ensure_tess4
    )

    info = pageinfo.pdf_get_all_pageinfo(str(outpdf))
    page = info[0]
    assert len(page['images']) > 1, "masked were rasterized"