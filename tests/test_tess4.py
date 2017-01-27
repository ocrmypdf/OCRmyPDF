#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE, check_output, check_call, DEVNULL
import os
import shutil
from contextlib import suppress
import sys
import pytest
from ocrmypdf.pageinfo import pdf_get_all_pageinfo
import PyPDF2 as pypdf
from ocrmypdf.exceptions import ExitCode
from ocrmypdf import leptonica
from ocrmypdf.pdfa import file_claims_pdfa
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



