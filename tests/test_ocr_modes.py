# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for the OCR mode options: force, skip, redo, skip-big and timeouts."""

from __future__ import annotations

import pikepdf
import pytest

from ocrmypdf.exceptions import ExitCode
from ocrmypdf.pdfinfo import PdfInfo

from .conftest import RENDERERS, check_ocrmypdf, run_ocrmypdf_api


def test_repeat_ocr(resources, no_outpdf):
    result = run_ocrmypdf_api(resources / 'graph_ocred.pdf', no_outpdf)
    assert result == ExitCode.already_done_ocr


RECORDER = 'tests/plugins/ocr_image_recorder.py'


@pytest.fixture
def text_on_last_page(resources, tmp_path):
    """Three image-only pages followed by one page that already has text."""
    path = tmp_path / 'text_on_last_page.pdf'
    with pikepdf.new() as pdf:
        for _ in range(3):
            with pikepdf.open(resources / 'ccitt.pdf') as image_pdf:
                pdf.pages.append(image_pdf.pages[0])
        with pikepdf.open(resources / 'graph_ocred.pdf') as text_pdf:
            pdf.pages.append(text_pdf.pages[0])
        pdf.save(path)
    return path


@pytest.fixture
def ocr_image_log(monkeypatch, tmp_path):
    """File that records each image handed to the OCR engine."""
    logfile = tmp_path / 'ocr_images.txt'
    monkeypatch.setenv('OCRMYPDF_TEST_OCR_IMAGE_LOG', str(logfile))
    return logfile


def test_prior_text_aborts_before_ocr(text_on_last_page, no_outpdf, ocr_image_log):
    """Prior text on any page aborts before any page is rasterized or OCR'd."""
    result = run_ocrmypdf_api(
        text_on_last_page, no_outpdf, '--jobs', '1', '--plugin', RECORDER
    )
    assert result == ExitCode.already_done_ocr
    assert not ocr_image_log.exists() or ocr_image_log.read_text() == ''


def test_prior_text_names_page(text_on_last_page, no_outpdf, caplog):
    result = run_ocrmypdf_api(text_on_last_page, no_outpdf, '--jobs', '1')
    assert result == ExitCode.already_done_ocr
    assert 'page 4 already has text' in caplog.text


def test_prior_text_outside_pages_ignored(text_on_last_page, outpdf, ocr_image_log):
    """Text on a page excluded by --pages does not abort the run."""
    check_ocrmypdf(
        text_on_last_page,
        outpdf,
        '--pages',
        '1',
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        RECORDER,
    )
    assert len(ocr_image_log.read_text().splitlines()) == 1


def test_force_ocr(resources, outpdf):
    out = check_ocrmypdf(
        resources / 'graph_ocred.pdf',
        outpdf,
        '-f',
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(out)
    assert pdfinfo[0].has_text


def test_skip_ocr(resources, outpdf):
    out = check_ocrmypdf(
        resources / 'graph_ocred.pdf',
        outpdf,
        '-s',
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(out)
    assert pdfinfo[0].has_text


def test_redo_ocr(resources, outpdf):
    in_ = resources / 'graph_ocred.pdf'
    before = PdfInfo(in_, detailed_analysis=True)
    out = outpdf
    out = check_ocrmypdf(in_, out, '--redo-ocr', '--output-type', 'pdf')
    after = PdfInfo(out, detailed_analysis=True)
    assert before[0].has_text and after[0].has_text
    assert before[0].get_textareas() != after[0].get_textareas(), (
        "Expected text to be different after re-OCR"
    )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_ocr_timeout(renderer, resources, outpdf):
    out = check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--tesseract-timeout',
        '0',
        '--pdf-renderer',
        renderer,
        '--output-type',
        'pdf',
    )
    pdfinfo = PdfInfo(out)
    assert not pdfinfo[0].has_text


def test_skip_big(resources, outpdf):
    out = check_ocrmypdf(
        resources / 'jbig2.pdf',
        outpdf,
        '--skip-big',
        '1',
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(out)
    assert not pdfinfo[0].has_text


def test_skip_big_with_no_images(resources, outpdf):
    check_ocrmypdf(
        resources / 'blank.pdf',
        outpdf,
        '--skip-big',
        '5',
        '--force-ocr',
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


def test_force_ocr_on_pdf_with_no_images(resources, no_outpdf):
    # As a correctness test, make sure that --force-ocr on a PDF with no
    # content still triggers tesseract. If tesseract crashes, then it was
    # called.
    exitcode = run_ocrmypdf_api(
        resources / 'blank.pdf',
        no_outpdf,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert exitcode == ExitCode.child_process_error
    assert not no_outpdf.exists()
