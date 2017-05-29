#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE, check_output, check_call, DEVNULL
import os
import shutil
import pytest
from ocrmypdf.pdfinfo import PdfInfo, Colorspace, Encoding
import PyPDF2 as pypdf
from ocrmypdf.exceptions import ExitCode
from ocrmypdf import leptonica
from ocrmypdf.pdfa import file_claims_pdfa
from ocrmypdf.exec import ghostscript
import logging
from math import isclose


check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


@pytest.fixture
def poster(resources):
    return resources / 'poster.pdf'


def test_userunit_ghostscript_fails(poster, no_outpdf):
    p, out, err = run_ocrmypdf(poster, no_outpdf, '--output-type=pdfa')
    assert p.returncode == ExitCode.input_file


def test_userunit_qpdf_passes(spoof_tesseract_cache, poster, outpdf):
    before = PdfInfo(poster)
    check_ocrmypdf(poster, outpdf, '--output-type=pdf',
                   env=spoof_tesseract_cache)

    after = PdfInfo(outpdf)
    assert isclose(before[0].width_inches, after[0].width_inches)


def test_rotate_interaction(spoof_tesseract_cache, poster, outpdf):
    check_ocrmypdf(poster, outpdf, '--output-type=pdf',
                   '--rotate-pages',
                   env=spoof_tesseract_cache)
