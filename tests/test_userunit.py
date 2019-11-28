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

from math import isclose

import pytest

from ocrmypdf.exceptions import ExitCode
from ocrmypdf.pdfinfo import PdfInfo

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf_api
spoof = pytest.helpers.spoof


@pytest.fixture
def poster(resources):
    return resources / 'poster.pdf'


def test_userunit_ghostscript_fails(poster, no_outpdf, caplog):
    result = run_ocrmypdf_api(poster, no_outpdf, '--output-type=pdfa')
    assert result == ExitCode.input_file
    assert 'not supported by Ghostscript' in caplog.text


def test_userunit_qpdf_passes(spoof_tesseract_cache, poster, outpdf):
    before = PdfInfo(poster)
    check_ocrmypdf(poster, outpdf, '--output-type=pdf', env=spoof_tesseract_cache)

    after = PdfInfo(outpdf)
    assert isclose(before[0].width_inches, after[0].width_inches)


def test_rotate_interaction(spoof_tesseract_cache, poster, outpdf):
    check_ocrmypdf(
        poster, outpdf, '--output-type=pdf', '--rotate-pages', env=spoof_tesseract_cache
    )
