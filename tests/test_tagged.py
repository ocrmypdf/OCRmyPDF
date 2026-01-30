# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pytest

import ocrmypdf


def test_block_tagged(resources):
    with pytest.raises(ocrmypdf.exceptions.TaggedPDFError):
        ocrmypdf.ocr(resources / 'tagged.pdf', '_.pdf')


def test_force_tagged_warns(resources, outpdf, caplog):
    caplog.set_level('WARNING')
    ocrmypdf.ocr(
        resources / 'tagged.pdf',
        outpdf,
        force_ocr=True,
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    assert 'marked as a Tagged PDF' in caplog.text


def test_tagged_pdf_mode_ignore_with_skip_text(resources, outpdf, caplog):
    """Ignore tagged_pdf_mode should warn but not error."""
    caplog.set_level('WARNING')
    ocrmypdf.ocr(
        resources / 'tagged.pdf',
        outpdf,
        tagged_pdf_mode='ignore',
        skip_text=True,  # Tagged PDF has text, so skip pages with text
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    assert 'marked as a Tagged PDF' in caplog.text


def test_tagged_pdf_mode_ignore_with_force(resources, outpdf, caplog):
    """Ignore tagged_pdf_mode with force mode should warn."""
    caplog.set_level('WARNING')
    ocrmypdf.ocr(
        resources / 'tagged.pdf',
        outpdf,
        tagged_pdf_mode='ignore',
        force_ocr=True,
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    assert 'marked as a Tagged PDF' in caplog.text
