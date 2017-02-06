#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

import pytest
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import tesseract


# Skip all tests in this file if not tesseract 4
pytestmark = pytest.mark.skipif(not tesseract.v4(),
                                reason="tesseract 4.0 required")


@pytest.mark.skipif(not tesseract.has_textonly_pdf(),
                    reason="requires textonly_pdf feature")
def test_textonly_pdf(resources, outdir):
    pytest.helpers.check_ocrmypdf(
        resources / 'linn.pdf',
        outdir / 'linn_textonly.pdf', '--pdf-renderer', 'tess4')



