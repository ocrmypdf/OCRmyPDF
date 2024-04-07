# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from pdfminer.high_level import extract_text

import ocrmypdf
import ocrmypdf.api


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


def test_sidecar_stringio(resources: Path, outdir: Path, outpdf: Path):
    s = BytesIO()
    ocrmypdf.ocr(
        resources / 'ccitt.pdf',
        outpdf,
        plugins=['tests/plugins/tesseract_cache.py'],
        sidecar=s
    )
    s.seek(0)
    assert b'the' in s.getvalue()


def test_hocr_api_multipage(resources: Path, outdir: Path, outpdf: Path):
    ocrmypdf.api._pdf_to_hocr(
        resources / 'multipage.pdf',
        outdir,
        language='eng',
        skip_text=True,
        plugins=['tests/plugins/tesseract_cache.py'],
    )
    assert (outdir / '000001_ocr_hocr.hocr').exists()
    assert (outdir / '000006_ocr_hocr.hocr').exists()
    assert not (outdir / '000004_ocr_hocr.hocr').exists()

    ocrmypdf.api._hocr_to_ocr_pdf(outdir, outpdf)
    assert outpdf.exists()


def test_hocr_to_pdf_api(resources: Path, outdir: Path, outpdf: Path):
    ocrmypdf.api._pdf_to_hocr(
        resources / 'ccitt.pdf',
        outdir,
        language='eng',
        skip_text=True,
        plugins=['tests/plugins/tesseract_cache.py'],
    )
    assert (outdir / '000001_ocr_hocr.hocr').exists()
    hocr = (outdir / '000001_ocr_hocr.hocr').read_text(encoding='utf-8')
    mangled = hocr.replace('the', 'hocr')
    (outdir / '000001_ocr_hocr.hocr').write_text(mangled, encoding='utf-8')

    ocrmypdf.api._hocr_to_ocr_pdf(outdir, outpdf, optimize=0)

    text = extract_text(outpdf)
    assert 'hocr' in text and 'the' not in text

