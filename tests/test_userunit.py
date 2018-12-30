# © 2017 James R. Barlow: github.com/jbarlow83
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

import logging
import os
import shutil
from math import isclose
from subprocess import DEVNULL, PIPE, Popen, check_call, check_output

import PyPDF2 as pypdf
import pytest

from ocrmypdf import leptonica
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import ghostscript
from ocrmypdf.pdfa import file_claims_pdfa
from ocrmypdf.pdfinfo import Colorspace, Encoding, PdfInfo

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
    check_ocrmypdf(poster, outpdf, '--output-type=pdf', env=spoof_tesseract_cache)

    after = PdfInfo(outpdf)
    assert isclose(before[0].width_inches, after[0].width_inches)


def test_rotate_interaction(spoof_tesseract_cache, poster, outpdf):
    check_ocrmypdf(
        poster, outpdf, '--output-type=pdf', '--rotate-pages', env=spoof_tesseract_cache
    )
