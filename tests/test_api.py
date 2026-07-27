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


def test_language_parameter_mapped_to_languages():
    """Test that the API 'language' parameter is mapped to OcrOptions 'languages'.

    Regression test for GitHub issue #1640: the Python API ignored the language
    parameter, always defaulting to 'eng'.
    """
    from ocrmypdf.api import create_options, setup_plugin_infrastructure
    from ocrmypdf.cli import get_parser

    setup_plugin_infrastructure()
    parser = get_parser()

    options = create_options(
        input_file='test.pdf',
        output_file='output.pdf',
        parser=parser,
        language=['tam'],
    )
    assert options.languages == ['tam']

    # Test with a list of multiple languages
    options = create_options(
        input_file='test.pdf',
        output_file='output.pdf',
        parser=parser,
        language=['fra', 'deu'],
    )
    assert options.languages == ['fra', 'deu']

    # Test with a bare string (single language)
    options = create_options(
        input_file='test.pdf',
        output_file='output.pdf',
        parser=parser,
        language='tam',
    )
    assert options.languages == ['tam']

    # Test '+'-separated string is split like CLI --language
    options = create_options(
        input_file='test.pdf',
        output_file='output.pdf',
        parser=parser,
        language='eng+spa',
    )
    assert options.languages == ['eng', 'spa']

    # Test '+'-separated entry within a list is also split
    options = create_options(
        input_file='test.pdf',
        output_file='output.pdf',
        parser=parser,
        language=['eng+spa'],
    )
    assert options.languages == ['eng', 'spa']


def test_jpeg_quality_parameter_reaches_options():
    """The canonical 'jpeg_quality' API parameter must reach OcrOptions.

    Regression test for GitHub issue #1723: --jpeg-quality was silently
    dropped by the CLI's namespace_to_options() because the OcrOptions field
    was named jpg_quality. create_options(), used by the Python API, has the
    same field-name matching logic and is affected the same way when passed
    the alias name.
    """
    from ocrmypdf.api import create_options, setup_plugin_infrastructure
    from ocrmypdf.cli import get_parser

    setup_plugin_infrastructure()
    parser = get_parser()

    options = create_options(
        input_file='test.pdf', output_file='output.pdf', parser=parser, jpeg_quality=10
    )
    assert options.jpeg_quality == 10


def test_jpg_quality_parameter_deprecated_alias():
    """The old 'jpg_quality' API parameter still works but warns."""
    from ocrmypdf.api import create_options, setup_plugin_infrastructure
    from ocrmypdf.cli import get_parser

    setup_plugin_infrastructure()
    parser = get_parser()

    with pytest.warns(UserWarning, match='jpg_quality'):
        options = create_options(
            input_file='test.pdf',
            output_file='output.pdf',
            parser=parser,
            jpg_quality=42,
        )
    assert options.jpeg_quality == 42


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


def test_default_tesseract_timeout():
    """Test that OcrOptions without explicit tesseract_timeout uses plugin default.

    Regression test for GitHub issue #1636: when using the Python API without
    specifying tesseract_timeout, the default was 0.0 which caused Tesseract
    to immediately time out and produce no OCR output.
    """
    from ocrmypdf._options import OcrOptions
    from ocrmypdf.api import setup_plugin_infrastructure

    setup_plugin_infrastructure()

    # Default OcrOptions should leave tesseract_timeout as None
    options = OcrOptions(
        input_file='test.pdf',
        output_file='output.pdf',
    )
    assert options.tesseract_timeout is None

    # The plugin default (180s) should be used when tesseract_timeout is None
    assert options.tesseract.timeout == 180.0
