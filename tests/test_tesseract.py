# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import os
import subprocess
from os import fspath
from pathlib import Path

import pytest
from pydantic import ValidationError

import ocrmypdf
from ocrmypdf import pdfinfo
from ocrmypdf._exec import tesseract
from ocrmypdf._options import OcrOptions
from ocrmypdf.builtin_plugins.tesseract_ocr import _thresholding_method_converter
from ocrmypdf.exceptions import BadArgsError, ExitCode, MissingDependencyError

from .conftest import RENDERERS, check_ocrmypdf, run_ocrmypdf, run_ocrmypdf_api

# pylint: disable=redefined-outer-name


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
        assert info_out_n.width_inches == info_in[n].width_inches, "output resized"
        assert info_out_n.height_inches == info_in[n].height_inches, "output resized"


def test_content_preservation(resources, outpdf):
    infile = resources / 'masks.pdf'

    check_ocrmypdf(
        infile, outpdf, '--pdf-renderer', 'fpdf2', '--tesseract-timeout', '0'
    )

    info = pdfinfo.PdfInfo(outpdf)
    page = info[0]
    assert len(page.images) > 1, "masks were rasterized"


@pytest.mark.skipif(
    tesseract.version() >= tesseract.TesseractVersion('5'), reason="doesn't fool Tess 5"
)
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
        thresholding=0,
        user_words=None,
        user_patterns=None,
    )
    assert Path(outdir / 'out.hocr').read_text() == ''


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
        thresholding=0,
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


def test_tesseract_log_output_diacritics_raw(caplog):
    """Diacritics branch keeps the interpreted hint and surfaces raw (#1566)."""
    caplog.set_level(logging.DEBUG)
    tesseract.tesseract_log_output(b'lots of diacritics blah blah')
    assert 'possibly poor OCR' in caplog.text  # interpreted hint retained
    assert 'lots of diacritics blah blah' in caplog.text  # raw message surfaced


def test_tesseract_log_output_raises(caplog):
    with pytest.raises(tesseract.TesseractConfigError):
        tesseract.tesseract_log_output(b'parameter not found: moo')
    assert 'not found' in caplog.text


def test_tesseract_log_output_raises_on_missing_config(caplog):
    with pytest.raises(tesseract.TesseractConfigError) as excinfo:
        tesseract.tesseract_log_output(b"read_params_file: Can't open hocr")
    assert 'hocr' in excinfo.value.args[0]
    assert 'read_params_file' in caplog.text


def test_blocked_language(resources, no_outpdf):
    infile = resources / 'masks.pdf'
    for bad_lang in ['osd', 'equ']:
        with pytest.raises(BadArgsError):
            run_ocrmypdf_api(infile, no_outpdf, '-l', bad_lang)


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_crash(renderer, resources, no_outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'ccitt.pdf',
        no_outpdf,
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert exitcode == ExitCode.child_process_error
    assert not no_outpdf.exists()
    assert "SubprocessOutputError" in caplog.text


def test_tesseract_crash_autorotate(resources, no_outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'ccitt.pdf',
        no_outpdf,
        '-r',
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert exitcode == ExitCode.child_process_error
    assert not no_outpdf.exists()
    assert "uncaught exception" in caplog.text


@pytest.mark.parametrize('renderer', RENDERERS)
@pytest.mark.slow
def test_tesseract_image_too_big(renderer, resources, outpdf):
    check_ocrmypdf(
        resources / 'hugemono.pdf',
        outpdf,
        '-r',
        '--pdf-renderer',
        renderer,
        '--max-image-mpixels',
        '0',
        '--plugin',
        'tests/plugins/tesseract_big_image_error.py',
    )


@pytest.fixture
def valid_tess_config(outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write(
            '''\
load_system_dawg 0
language_model_penalty_non_dict_word 0
language_model_penalty_non_freq_dict_word 0
'''
        )
    yield cfg_file


def test_tesseract_config_valid(resources, valid_tess_config, outpdf):
    check_ocrmypdf(
        resources / '3small.pdf',
        outpdf,
        '--tesseract-config',
        valid_tess_config,
        '--pages',
        '1',
    )


@pytest.fixture
def invalid_tess_config(outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write(
            '''\
THIS FILE IS INVALID
'''
        )
    yield cfg_file


@pytest.mark.slow  # This test sometimes times out in CI
@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_config_invalid(renderer, resources, invalid_tess_config, outpdf):
    p = run_ocrmypdf(
        resources / 'ccitt.pdf',
        outpdf,
        '--pdf-renderer',
        renderer,
        '--tesseract-config',
        invalid_tess_config,
    )
    assert (
        "parameter not found" in p.stderr.lower()
        or "error occurred while parsing" in p.stderr.lower()
    ), "No error message"
    assert p.returncode == ExitCode.invalid_config


@pytest.mark.parametrize('value', ['auto'])
def test_tesseract_thresholding(value, resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--tesseract-thresholding',
        value,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )


@pytest.mark.parametrize('value', ['abcxyz'])
def test_tesseract_thresholding_invalid(value, resources, no_outpdf):
    with pytest.raises(SystemExit, match='2'):
        run_ocrmypdf_api(
            resources / 'trivial.pdf',
            no_outpdf,
            '--tesseract-thresholding',
            value,
            '--plugin',
            'tests/plugins/tesseract_cache.py',
        )


@pytest.mark.skipif(
    tesseract.version() >= tesseract.TesseractVersion('5'),
    reason="tess 5 tries harder to find its files",
)
def test_tesseract_missing_tessdata(monkeypatch, resources, no_outpdf, tmpdir):
    monkeypatch.setenv("TESSDATA_PREFIX", os.fspath(tmpdir))
    with pytest.raises(MissingDependencyError):
        run_ocrmypdf_api(resources / 'graph.pdf', no_outpdf, '-v', '1', '--skip-text')


def _fake_tesseract_run(captured):
    """Return a stand-in for tesseract.run that records argv and fakes output."""

    def fake_run(args, *, env=None, **kwargs):
        argv = [os.fspath(arg) for arg in args]
        captured.append(argv)
        # Emulate tesseract writing <outputbase>.<configfile> for each requested
        # output format, so the builders' post-run existence checks pass.
        outputbase, configfiles = argv[-3], argv[-2:]
        for configfile in configfiles:
            Path(f'{outputbase}.{configfile}').write_bytes(b'')
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout=b'')

    return fake_run


def _build_tesseract_argv(monkeypatch, builder, input_file, outdir, **overrides):
    """Run one of the tesseract arg builders and return the argv it assembled."""
    captured: list[list[str]] = []
    monkeypatch.setattr(tesseract, 'run', _fake_tesseract_run(captured))
    # Pin the capability probe so the argv does not depend on the local tesseract
    monkeypatch.setattr(tesseract, 'has_thresholding', lambda: True)

    kwargs = dict(
        input_file=input_file,
        output_text=outdir / 'sidecar.txt',
        languages=['eng'],
        engine_mode=None,
        tessconfig=[],
        timeout=180.0,
        pagesegmode=None,
        thresholding=tesseract.ThresholdingMethod.AUTO,
        user_words=None,
        user_patterns=None,
    )
    kwargs.update(overrides)

    if builder == 'hocr':
        tesseract.generate_hocr(output_hocr=outdir / 'out.hocr', **kwargs)
    else:
        tesseract.generate_pdf(output_pdf=outdir / 'out.pdf', **kwargs)

    assert len(captured) == 1, "expected exactly one tesseract invocation"
    return captured[0]


def _argv_values(argv, flag):
    """Return every value that immediately follows flag in argv."""
    return [argv[n + 1] for n, arg in enumerate(argv[:-1]) if arg == flag]


@pytest.mark.parametrize('builder', ['hocr', 'pdf'])
@pytest.mark.parametrize(
    'thresholding_name, expected',
    [
        # auto and otsu both map to 0, which is tesseract's own default, so the
        # builders deliberately emit no -c setting for them
        ('auto', None),
        ('otsu', None),
        ('adaptive-otsu', 'thresholding_method=1'),
        ('sauvola', 'thresholding_method=2'),
    ],
)
def test_tesseract_argv_thresholding(
    builder, thresholding_name, expected, monkeypatch, resources, outdir
):
    argv = _build_tesseract_argv(
        monkeypatch,
        builder,
        resources / 'crom.png',
        outdir,
        thresholding=_thresholding_method_converter(thresholding_name),
    )
    settings = [
        value
        for value in _argv_values(argv, '-c')
        if value.startswith('thresholding_method=')
    ]
    assert settings == ([] if expected is None else [expected])


@pytest.mark.parametrize('builder', ['hocr', 'pdf'])
def test_tesseract_argv_oem_and_pagesegmode(builder, monkeypatch, resources, outdir):
    argv = _build_tesseract_argv(
        monkeypatch,
        builder,
        resources / 'crom.png',
        outdir,
        engine_mode=1,
        pagesegmode=7,
    )
    assert _argv_values(argv, '--oem') == ['1']
    assert _argv_values(argv, '--psm') == ['7']


@pytest.mark.parametrize('renderer', ['fpdf2'])
def test_pagesegmode(renderer, resources, outpdf):
    check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--tesseract-pagesegmode',
        '7',
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )


@pytest.mark.parametrize(
    'value, expected',
    [
        ('auto', tesseract.ThresholdingMethod.AUTO),
        ('otsu', tesseract.ThresholdingMethod.OTSU),
        ('adaptive-otsu', tesseract.ThresholdingMethod.ADAPTIVE_OTSU),
        ('Sauvola', tesseract.ThresholdingMethod.SAUVOLA),
        (1, tesseract.ThresholdingMethod.ADAPTIVE_OTSU),
        (None, None),
    ],
)
def test_tesseract_thresholding_api_names(value, expected):
    """The API accepts thresholding method names as well as integers (#1460)."""
    options = OcrOptions(
        input_file='a.pdf', output_file='b.pdf', tesseract_thresholding=value
    )
    assert options.tesseract_thresholding == expected


def test_tesseract_thresholding_api_invalid_name():
    with pytest.raises(ValidationError, match="Invalid thresholding method"):
        OcrOptions(
            input_file='a.pdf', output_file='b.pdf', tesseract_thresholding='abcxyz'
        )


@pytest.mark.skipif(
    not tesseract.has_thresholding(), reason="tesseract lacks thresholding"
)
def test_tesseract_thresholding_api_passes_method(resources, outpdf, monkeypatch):
    """A thresholding name given to ocrmypdf.ocr() reaches tesseract (#1460)."""
    captured = []
    real_run = tesseract.run

    def spy_run(args, *a, **kw):
        captured.append(list(args))
        return real_run(args, *a, **kw)

    monkeypatch.setattr(tesseract, 'run', spy_run)
    ocrmypdf.ocr(
        resources / 'trivial.pdf',
        outpdf,
        tesseract_thresholding='adaptive-otsu',
        use_threads=True,
        optimize=0,
        output_type='pdf',
        progress_bar=False,
    )
    assert any(
        'thresholding_method=1' in args
        for args in captured
        if args and 'tesseract' in str(args[0])
    )
