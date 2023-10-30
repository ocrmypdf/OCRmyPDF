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
