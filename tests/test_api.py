# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

import ocrmypdf


def test_language_list():
    with pytest.raises(
        (ocrmypdf.exceptions.InputFileError, ocrmypdf.exceptions.MissingDependencyError)
    ):
        ocrmypdf.ocr('doesnotexist.pdf', '_.pdf', language=['eng', 'deu'])


def test_stream_api(resources: Path):
    in_ = (resources / 'graph.pdf').open('rb')
    out = BytesIO()

    ocrmypdf.ocr(in_, out, tesseract_timeout=0.0)
    out.seek(0)
    assert b'%PDF' in out.read(1024)


def test_hocr_api(resources: Path, outdir: Path):
    ocrmypdf.pdf_to_hocr(
        resources / 'multipage.pdf',
        outdir,
        language='eng',
        skip_text=True,
        plugins=['tests/plugins/tesseract_cache.py'],
    )
    assert (outdir / '000001_ocr_hocr.hocr').exists()
    assert (outdir / '000006_ocr_hocr.hocr').exists()

    assert not (outdir / '000004_ocr_hocr.hocr').exists()
