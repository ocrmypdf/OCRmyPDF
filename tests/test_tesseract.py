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
import subprocess
from os import fspath
from pathlib import Path

import pytest

from ocrmypdf import pdfinfo
from ocrmypdf._exec import tesseract
from ocrmypdf.exceptions import MissingDependencyError

# pylint: disable=no-member,redefined-outer-name

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf


@pytest.mark.parametrize('basename', ['graph_ocred.pdf', 'cardinal.pdf'])
def test_skip_pages_does_not_replicate(resources, basename, outdir):
    infile = resources / basename
    outpdf = outdir / basename

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        'sandwich',
        '--force-ocr',
        '--tesseract-timeout',
        '0',
    )

    info_in = pdfinfo.PdfInfo(infile)

    info = pdfinfo.PdfInfo(outpdf)
    for page in info:
        assert len(page.images) == 1, "skipped page was replicated"

    for n, info_out_n in enumerate(info):
        assert info_out_n.width_inches == info_in[n].width_inches


def test_content_preservation(resources, outpdf):
    infile = resources / 'masks.pdf'

    check_ocrmypdf(
        infile, outpdf, '--pdf-renderer', 'sandwich', '--tesseract-timeout', '0'
    )

    info = pdfinfo.PdfInfo(outpdf)
    page = info[0]
    assert len(page.images) > 1, "masks were rasterized"


def test_no_languages(tmp_path, monkeypatch):
    (tmp_path / 'tessdata').mkdir()
    monkeypatch.setenv('TESSDATA_PREFIX', fspath(tmp_path))
    with pytest.raises(MissingDependencyError):
        tesseract.get_languages()


def test_image_too_large_hocr(monkeypatch, resources, outdir):
    def dummy_run(args, *, env=None, **kwargs):
        raise subprocess.CalledProcessError(1, 'tesseract', output=b'Image too large')

    monkeypatch.setattr(tesseract, 'run', dummy_run)
    tesseract.generate_hocr(
        input_file=resources / 'crom.png',
        output_hocr=outdir / 'out.hocr',
        output_text=outdir / 'out.txt',
        languages=['eng'],
        engine_mode=None,
        tessconfig=[],
        timeout=180.0,
        pagesegmode=None,
        user_words=None,
        user_patterns=None,
    )
    assert "name='ocr-capabilities'" in Path(outdir / 'out.hocr').read_text()


def test_image_too_large_pdf(monkeypatch, resources, outdir):
    def dummy_run(args, *, env=None, **kwargs):
        raise subprocess.CalledProcessError(1, 'tesseract', output=b'Image too large')

    monkeypatch.setattr(tesseract, 'run', dummy_run)
    tesseract.generate_pdf(
        input_file=resources / 'crom.png',
        output_pdf=outdir / 'pdf.pdf',
        output_text=outdir / 'txt.txt',
        languages=['eng'],
        engine_mode=None,
        tessconfig=[],
        timeout=180.0,
        pagesegmode=None,
        user_words=None,
        user_patterns=None,
    )
    assert Path(outdir / 'txt.txt').read_text() == '[skipped page]'
    if os.name != 'nt':  # different semantics
        assert Path(outdir / 'pdf.pdf').stat().st_size == 0


def test_timeout(caplog):
    tesseract.page_timedout(5)
    assert "took too long" in caplog.text


@pytest.mark.parametrize(
    'in_, logged',
    [
        (b'Tesseract Open Source', ''),
        (b'lots of diacritics blah blah', 'diacritics'),
        (b'Warning in pixReadMem', ''),
        (b'OSD: Weak margin', 'unsure about page orientation'),
        (b'Error in pixScanForForeground', ''),
        (b'Error in boxClipToRectangle', ''),
        (b'an unexpected error', 'an unexpected error'),
        (b'a dire warning', 'a dire warning'),
        (b'read_params_file something', 'read_params_file'),
        (b'an innocent message', 'innocent'),
        (b'\x7f\x7f\x80innocent unicode failure', 'innocent'),
    ],
)
def test_tesseract_log_output(caplog, in_, logged):
    caplog.set_level(logging.INFO)
    tesseract.tesseract_log_output(in_)
    if logged == '':
        assert caplog.text == ''
    else:
        assert logged in caplog.text


def test_tesseract_log_output_raises(caplog):
    with pytest.raises(tesseract.TesseractConfigError):
        tesseract.tesseract_log_output(b'parameter not found: moo')
    assert 'not found' in caplog.text
