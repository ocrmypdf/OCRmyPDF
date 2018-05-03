# © 2018 James R. Barlow: github.com/jbarlow83
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


import pytest
import PyPDF2 as pypdf
import datetime
from datetime import timezone

from ocrmypdf.pdfa import file_claims_pdfa, encode_pdf_date, decode_pdf_date
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.lib import fitz

# pytest.helpers is dynamic
# pylint: disable=no-member
# pylint: disable=w0612

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_preserve_metadata(spoof_tesseract_noop, output_type,
                           resources, outpdf):
    pdf_before = pypdf.PdfFileReader(str(resources / 'graph.pdf'))

    output = check_ocrmypdf(
            resources / 'graph.pdf', outpdf,
            '--output-type', output_type,
            env=spoof_tesseract_noop)

    pdf_after = pypdf.PdfFileReader(str(output))

    for key in ('/Title', '/Author'):
        assert pdf_before.documentInfo[key] == pdf_after.documentInfo[key]

    pdfa_info = file_claims_pdfa(str(output))
    assert pdfa_info['output'] == output_type


@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_override_metadata(spoof_tesseract_noop, output_type, resources,
                           outpdf):
    input_file = resources / 'c02-22.pdf'
    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'

    p, out, err = run_ocrmypdf(
        input_file, outpdf,
        '--title', german,
        '--author', chinese,
        '--output-type', output_type,
        env=spoof_tesseract_noop)

    assert p.returncode == ExitCode.ok, err

    before = pypdf.PdfFileReader(str(input_file))
    after = pypdf.PdfFileReader(outpdf)

    assert after.documentInfo['/Title'] == german
    assert after.documentInfo['/Author'] == chinese
    assert after.documentInfo.get('/Keywords', '') == ''

    before_date = decode_pdf_date(before.documentInfo['/CreationDate'])
    after_date = decode_pdf_date(after.documentInfo['/CreationDate'])
    assert before_date == after_date

    pdfa_info = file_claims_pdfa(outpdf)
    assert pdfa_info['output'] == output_type


def test_high_unicode(spoof_tesseract_noop, resources, no_outpdf):

    # Ghostscript doesn't support high Unicode, so neither do we, to be
    # safe
    input_file = resources / 'c02-22.pdf'
    high_unicode = 'U+1030C is: 𐌌'

    p, out, err = run_ocrmypdf(
        input_file, no_outpdf,
        '--subject', high_unicode,
        '--output-type', 'pdfa',
        env=spoof_tesseract_noop)

    assert p.returncode == ExitCode.bad_args, err


@pytest.mark.xfail(not fitz, reason="needs fitz")
@pytest.mark.parametrize('ocr_option', ['--skip-text', '--force-ocr'])
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_bookmarks_preserved(spoof_tesseract_noop, output_type, ocr_option,
                             resources, outpdf):
    input_file = resources / 'toc.pdf'
    before_toc = fitz.Document(str(input_file)).getToC()

    check_ocrmypdf(
        input_file, outpdf,
        ocr_option,
        '--output-type', output_type,
        env=spoof_tesseract_noop)

    after_toc = fitz.Document(str(outpdf)).getToC()
    print(before_toc)
    print(after_toc)
    assert before_toc == after_toc


def seconds_between_dates(date1, date2):
    return (date2 - date1).total_seconds()


@pytest.mark.parametrize('infile', ['trivial.pdf', 'jbig2.pdf'])
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_creation_date_preserved(spoof_tesseract_noop, output_type, resources,
                                 infile, outpdf):
    input_file = resources / infile

    before = pypdf.PdfFileReader(str(input_file)).getDocumentInfo()
    check_ocrmypdf(
        input_file, outpdf, '--output-type', output_type, 
        env=spoof_tesseract_noop)
    after = pypdf.PdfFileReader(str(outpdf)).getDocumentInfo()

    if not before:
        # If there was input creation date, none should be output
        # because of Ghostscript quirks we set it to null
        # This test would be better if we had a test file with /DocumentInfo but
        # no /CreationDate, which we don't
        assert not after['/CreationDate'] or \
                isinstance(after['/CreationDate'], pypdf.generic.NullObject)
    else:
        # We expect that the creation date stayed the same
        date_before = decode_pdf_date(before['/CreationDate'])
        date_after = decode_pdf_date(after['/CreationDate'])
        assert seconds_between_dates(date_before, date_after) < 1000

    # We expect that the modified date is quite recent
    date_after = decode_pdf_date(after['/ModDate'])
    assert seconds_between_dates(
        date_after, datetime.datetime.now(timezone.utc)) < 1000


