#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

import pytest
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import tesseract
from ocrmypdf import pageinfo
import sys


# Skip all tests in this file if not tesseract 4
pytestmark = pytest.mark.skipif(
    not (tesseract.v4() and tesseract.has_textonly_pdf()),
    reason="tesseract 4.0 with textonly_pdf feature required")

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


def test_textonly_pdf(resources, outdir):
    check_ocrmypdf(
        resources / 'linn.pdf',
        outdir / 'linn_textonly.pdf', '--pdf-renderer', 'tess4')


@pytest.mark.skipif(sys.version_info < (3, 5), reason="needs math.isclose")
def test_pagesize_consistency_tess4(resources, outpdf):
    from math import isclose

    infile = resources / 'linn.pdf'

    before_dims = pytest.helpers.first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf, '--pdf-renderer', 'tess4',
        '--clean', '--deskew', '--remove-background', '--clean-final')

    after_dims = pytest.helpers.first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0])
    assert isclose(before_dims[1], after_dims[1])
