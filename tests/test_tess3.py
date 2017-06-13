#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

import pytest
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import tesseract


# Skip all tests in this file if not tesseract 3
pytestmark = pytest.mark.skipif(tesseract.v4(),
                                reason="tesseract 3.x required")


@pytest.mark.skipif(tesseract.has_textonly_pdf(),
                    reason="check that missing dep is reported on old tess3")
def test_textonly_pdf_on_older_tess3(resources, no_outpdf):
    p, _, _ = pytest.helpers.run_ocrmypdf(
        resources / 'linn.pdf',
        no_outpdf, '--pdf-renderer', 'sandwich')

    assert p.returncode == ExitCode.missing_dependency


@pytest.mark.skipif(not tesseract.has_textonly_pdf(),
                    reason="check that feature is exercised on new test3")
def test_textonly_pdf_on_newer_tess3(resources, no_outpdf):
    p, _, _ = pytest.helpers.run_ocrmypdf(
        resources / 'linn.pdf',
        no_outpdf, '--pdf-renderer', 'sandwich')

    assert p.returncode == ExitCode.ok


def test_oem_on_tess3(resources, no_outpdf):
    p, _, err = pytest.helpers.run_ocrmypdf(
        resources / 'aspect.pdf',
        no_outpdf, '--tesseract-oem', '1')

    assert p.returncode == ExitCode.ok
    assert 'argument ignored' in err
