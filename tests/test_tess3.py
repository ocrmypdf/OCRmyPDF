#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

import pytest
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import tesseract


# Skip all tests in this file if not tesseract 3
pytestmark = pytest.mark.skipif(tesseract.v4(),
                                reason="tesseract 3.x required")


def test_textonly_pdf_on_tess3(resources, no_outpdf):
    p, _, _ = pytest.helpers.run_ocrmypdf(
        resources / 'linn.pdf',
        no_outpdf, '--pdf-renderer', 'tess4')

    assert p.returncode == ExitCode.missing_dependency


def test_oem_on_tess3(resources, no_outpdf):
    p, _, err = pytest.helpers.run_ocrmypdf(
        resources / 'aspect.pdf',
        no_outpdf, '--tesseract-oem', '1')

    assert p.returncode == ExitCode.ok
    assert 'argument ignored' in err
