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
from contextlib import contextmanager
from os import fspath
from pathlib import Path

import pytest

from ocrmypdf import pdfinfo
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.exec import tesseract

# pylint: disable=no-member,w0621

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


def test_tesseract_v4():
    assert tesseract.v4()


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

    for n in range(len(info_in)):
        assert info[n].width_inches == info_in[n].width_inches


def test_content_preservation(resources, outpdf):
    infile = resources / 'masks.pdf'

    check_ocrmypdf(
        infile, outpdf, '--pdf-renderer', 'sandwich', '--tesseract-timeout', '0'
    )

    info = pdfinfo.PdfInfo(outpdf)
    page = info[0]
    assert len(page.images) > 1, "masks were rasterized"


def test_no_languages(tmp_path):
    env = os.environ.copy()
    (tmp_path / 'tessdata').mkdir()
    env['TESSDATA_PREFIX'] = fspath(tmp_path)

    with pytest.raises(MissingDependencyError):
        tesseract.languages(tesseract_env=env)


def test_image_too_large_hocr(monkeypatch, resources, outdir):
    log = logging.getLogger('test_image_too_large_hocr')

    def dummy_run(args, *, env=None, **kwargs):
        raise subprocess.CalledProcessError(1, 'tesseract', output=b'Image too large')

    monkeypatch.setattr(tesseract, 'run', dummy_run)
    tesseract.generate_hocr(
        input_file=resources / 'crom.png',
        output_files=[outdir / 'out.hocr', outdir / 'out.txt'],
        language=['eng'],
        engine_mode=None,
        tessconfig=[],
        timeout=180.0,
        pagesegmode=None,
        log=log,
        user_words=None,
        user_patterns=None,
        tesseract_env=None,
    )
    assert "name='ocr-capabilities'" in Path(outdir / 'out.hocr').read_text()


def test_image_too_large_pdf(monkeypatch, resources, outdir):
    log = logging.getLogger('test_image_too_large_pdf')

    def dummy_run(args, *, env=None, **kwargs):
        raise subprocess.CalledProcessError(1, 'tesseract', output=b'Image too large')

    monkeypatch.setattr(tesseract, 'run', dummy_run)
    tesseract.generate_pdf(
        input_image=resources / 'crom.png',
        skip_pdf=resources / 'blank.pdf',
        output_pdf=outdir / 'pdf.pdf',
        output_text=outdir / 'txt.txt',
        language=['eng'],
        engine_mode=None,
        text_only=False,
        tessconfig=[],
        timeout=180.0,
        pagesegmode=None,
        log=log,
        user_words=None,
        user_patterns=None,
        tesseract_env=None,
    )
    assert Path(outdir / 'txt.txt').read_text() == '[skipped page]'
    if os.name != 'nt':  # different semantics
        assert Path(outdir / 'pdf.pdf').samefile(resources / 'blank.pdf')


def test_timeout(caplog):
    log = logging.getLogger('test_timeout')
    tesseract.page_timedout(log, '123456.png', 5)
    assert "123456" in caplog.text
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
    log = logging.getLogger('tesseract_log_output')
    log.setLevel(logging.INFO)

    tesseract.tesseract_log_output(log, in_, 'dummy')
    if logged == '':
        assert caplog.text == ''
    else:
        assert logged in caplog.text


def test_tesseract_log_output_raises(caplog):
    log = logging.getLogger('tesseract_log_output')
    with pytest.raises(tesseract.TesseractConfigError):
        tesseract.tesseract_log_output(log, b'parameter not found: moo', 'dummy')
    assert 'not found' in caplog.text
