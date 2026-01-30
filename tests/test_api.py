# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pickle
from io import BytesIO
from pathlib import Path

import pytest
from pdfminer.high_level import extract_text

import ocrmypdf
import ocrmypdf._pipelines
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
        sidecar=s,
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


def test_hocr_result_json():
    result = ocrmypdf._pipelines._common.HOCRResult(
        pageno=1,
        pdf_page_from_image=Path('a'),
        hocr=Path('b'),
        textpdf=Path('c'),
        orientation_correction=180,
    )
    assert (
        result.to_json()
        == '{"pageno": 1, "pdf_page_from_image": {"Path": "a"}, "hocr": {"Path": "b"}, '
        '"textpdf": {"Path": "c"}, "orientation_correction": 180, "ocr_tree": null}'
    )
    assert ocrmypdf._pipelines._common.HOCRResult.from_json(result.to_json()) == result


def test_hocr_result_pickle():
    result = ocrmypdf._pipelines._common.HOCRResult(
        pageno=1,
        pdf_page_from_image=Path('a'),
        hocr=Path('b'),
        textpdf=Path('c'),
        orientation_correction=180,
    )
    assert result == pickle.loads(pickle.dumps(result))


def test_nested_plugin_option_access():
    """Test that plugin options can be accessed via nested namespaces."""
    from ocrmypdf._options import OcrOptions
    from ocrmypdf.api import setup_plugin_infrastructure

    # Set up plugin infrastructure to register plugin models
    setup_plugin_infrastructure()

    # Create options with tesseract settings
    options = OcrOptions(
        input_file='test.pdf',
        output_file='output.pdf',
        tesseract_timeout=120.0,
        tesseract_oem=1,
        optimize=2,
    )

    # Test flat access still works
    assert options.tesseract_timeout == 120.0
    assert options.tesseract_oem == 1
    assert options.optimize == 2

    # Test nested access for tesseract
    tesseract = options.tesseract
    assert tesseract is not None
    assert tesseract.timeout == 120.0
    assert tesseract.oem == 1

    # Test nested access for ghostscript
    ghostscript = options.ghostscript
    assert ghostscript is not None
    assert ghostscript.color_conversion_strategy == "LeaveColorUnchanged"

    # Test that cached instances are returned
    assert options.tesseract is tesseract
