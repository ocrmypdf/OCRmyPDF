# © 2019 James R. Barlow: github.com/jbarlow83
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

import pytest

import ocrmypdf

check_ocrmypdf = pytest.helpers.check_ocrmypdf


@pytest.fixture
def acroform(resources):
    return resources / 'acroform.pdf'


def test_acroform_and_redo(acroform, caplog, no_outpdf):
    with pytest.raises(ocrmypdf.exceptions.InputFileError):
        check_ocrmypdf(acroform, no_outpdf, '--redo-ocr')
    assert '--redo-ocr is not currently possible' in caplog.text


def test_acroform_message(acroform, caplog, outpdf):
    caplog.set_level(logging.INFO)
    check_ocrmypdf(acroform, outpdf, '--plugin', 'tests/plugins/tesseract_noop.py')
    assert 'fillable form' in caplog.text
    assert '--force-ocr' in caplog.text
