# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pikepdf
import pytest

from ocrmypdf import _validation as vd
from ocrmypdf._concurrent import NullProgressBar, SerialExecutor
from ocrmypdf._exec.tesseract import TesseractVersion
from ocrmypdf._options import OcrOptions
from ocrmypdf.api import create_options, setup_plugin_infrastructure
from ocrmypdf.cli import get_parser
from ocrmypdf.exceptions import BadArgsError, ExitCode, MissingDependencyError
from ocrmypdf.pdfinfo import PdfInfo

from .conftest import run_ocrmypdf, run_ocrmypdf_api


def make_opts_pm(input_file='a.pdf', output_file='b.pdf', language='eng', **kwargs):
    if language is not None:
        kwargs['language'] = language
    parser = get_parser()
    pm = setup_plugin_infrastructure(plugins=kwargs.get('plugins', []))
    pm.add_options(parser=parser)
    return (
        create_options(
            input_file=input_file, output_file=output_file, parser=parser, **kwargs
        ),
        pm,
    )


def make_opts(*args, **kwargs):
    opts, _pm = make_opts_pm(*args, **kwargs)
    return opts


def make_ocr_opts(input_file='a.pdf', output_file='b.pdf', **kwargs):
    """Create OcrOptions directly for testing Pydantic validation."""
    return OcrOptions(input_file=input_file, output_file=output_file, **kwargs)


def test_old_tesseract_error():
    with (
        patch(
            'ocrmypdf._exec.tesseract.version',
            return_value=TesseractVersion('4.00.00alpha'),
        ),
        pytest.raises(MissingDependencyError),
    ):
        vd.check_options(*make_opts_pm(pdf_renderer='sandwich', language='eng'))


def test_tesseract_not_installed(caplog):
    with patch('ocrmypdf.subprocess.run') as not_found:
        not_found.side_effect = FileNotFoundError('tesseract')
        with pytest.raises(MissingDependencyError, match="Could not find program"):
            vd.check_options(*make_opts_pm())
            assert "'tesseract' could not be executed" in caplog.text, (
                "Error message not printed"
            )
            assert 'install' in caplog.text, "Install advice not printed"
        not_found.assert_called()


def test_lossless_redo():
    with pytest.raises(ValueError, match="--redo-ocr.*is not currently compatible"):
        make_ocr_opts(redo_ocr=True, deskew=True)


def test_mutex_options():
    with pytest.raises(
        ValueError, match="Choose only one of --force-ocr, --skip-text, --redo-ocr"
    ):
        make_ocr_opts(force_ocr=True, skip_text=True)
    with pytest.raises(
        ValueError, match="Choose only one of --force-ocr, --skip-text, --redo-ocr"
    ):
        make_ocr_opts(redo_ocr=True, skip_text=True)
    with pytest.raises(
        ValueError, match="Choose only one of --force-ocr, --skip-text, --redo-ocr"
    ):
        make_ocr_opts(redo_ocr=True, force_ocr=True)


def test_optimizing_png_quality_warns(caplog):
    vd.check_options(*make_opts_pm(optimize=0, png_quality=18))
    assert 'will be ignored because' in caplog.text


def test_optimizing_jpeg_quality_warns(caplog):
    # Isolated from png_quality so this actually exercises the jpeg_quality
    # path rather than being confounded by png_quality also being set.
    vd.check_options(*make_opts_pm(optimize=0, jpeg_quality=10))
    assert 'will be ignored because' in caplog.text


def test_clean_final_implies_clean():
    """--clean-final implies --clean, however clean_final comes to be set."""
    assert make_ocr_opts(clean_final=True).clean

    # Setting it by assignment must propagate too; this previously did not,
    # because the rule lived in a field validator that mutated ValidationInfo.
    opts = make_ocr_opts()
    assert not opts.clean
    opts.clean_final = True
    assert opts.clean

    # No implication in the other direction, and nothing is forced on by default
    assert not make_ocr_opts().clean_final
    assert not make_ocr_opts(clean=True).clean_final


def test_pillow_options():
    # Test that max_image_mpixels=0 is valid (validation now in OcrOptions)
    opts = make_ocr_opts(max_image_mpixels=0)
    assert opts.max_image_mpixels == 0

    # Test that negative values are rejected
    with pytest.raises(
        ValueError, match=r"max_image_mpixels\n.*greater than or equal to 0"
    ):
        make_ocr_opts(max_image_mpixels=-1)

    # Default is None, meaning "do not override host-set PIL.Image.MAX_IMAGE_PIXELS"
    opts = make_ocr_opts()
    assert opts.max_image_mpixels is None


def test_pillow_max_image_pixels_not_overridden_when_unset():
    """Issue #1665: respect host-set PIL.Image.MAX_IMAGE_PIXELS.

    API callers (e.g. Paperless-NGX) that set PIL.Image.MAX_IMAGE_PIXELS
    before invoking ocrmypdf should not have their setting clobbered when
    max_image_mpixels is not explicitly passed.
    """
    import PIL.Image

    from ocrmypdf._pipelines._common import setup_pipeline

    parser = get_parser()
    pm = setup_plugin_infrastructure(plugins=[])
    pm.add_options(parser=parser)

    saved = PIL.Image.MAX_IMAGE_PIXELS
    try:
        PIL.Image.MAX_IMAGE_PIXELS = None  # host disables the limit
        opts = make_ocr_opts()
        assert opts.max_image_mpixels is None
        setup_pipeline(opts, pm)
        assert PIL.Image.MAX_IMAGE_PIXELS is None

        PIL.Image.MAX_IMAGE_PIXELS = 1_000_000_000  # host sets a high limit
        setup_pipeline(opts, pm)
        assert PIL.Image.MAX_IMAGE_PIXELS == 1_000_000_000

        # When explicitly passed, it still takes effect.
        opts = make_ocr_opts(max_image_mpixels=100)
        setup_pipeline(opts, pm)
        assert PIL.Image.MAX_IMAGE_PIXELS == 100_000_000
    finally:
        PIL.Image.MAX_IMAGE_PIXELS = saved


def test_output_tty():
    with patch('sys.stdout.isatty', return_value=True), pytest.raises(BadArgsError):
        vd.check_requested_output_file(make_opts(output_file='-'))


def test_report_file_size(tmp_path, caplog):
    logging.getLogger('pikepdf._qpdf').setLevel(logging.CRITICAL)  # Suppress logging

    in_ = tmp_path / 'a.pdf'
    out = tmp_path / 'b.pdf'
    pdf = pikepdf.new()
    pdf.save(in_)
    pdf.save(out)
    opts = make_opts(output_type='pdf')
    vd.report_output_file_size(opts, in_, out)
    assert caplog.text == ''
    caplog.clear()

    waste_of_space = b'Dummy' * 5000
    pdf.Root.Dummy = waste_of_space
    pdf.save(in_)
    pdf.Root.Dummy2 = waste_of_space + waste_of_space
    pdf.save(out)

    vd.report_output_file_size(opts, in_, out, ['The optional dependency...'])
    assert 'optional dependency' in caplog.text
    caplog.clear()

    vd.report_output_file_size(opts, in_, out, [])
    assert 'No reason' in caplog.text
    caplog.clear()

    opts = make_opts(in_, out, optimize=0, output_type='pdf')
    vd.report_output_file_size(opts, in_, out, ["Optimization was disabled."])
    assert 'disabled' in caplog.text
    caplog.clear()


def test_false_action_store_true():
    opts = make_opts(keep_temporary_files=True)
    assert opts.keep_temporary_files
    opts = make_opts(keep_temporary_files=False)
    assert not opts.keep_temporary_files


@pytest.mark.parametrize('progress_bar', [True, False])
def test_no_progress_bar(progress_bar, resources):
    opts, pm = make_opts_pm(
        progress_bar=progress_bar, input_file=(resources / 'trivial.pdf')
    )
    vd.check_options(opts, pm)

    pbar_disabled = None

    class CheckProgressBar(NullProgressBar):
        def __init__(self, disable, **kwargs):
            nonlocal pbar_disabled
            pbar_disabled = disable
            super().__init__(disable=disable, **kwargs)

    executor = SerialExecutor(pbar_class=CheckProgressBar)
    pdfinfo = PdfInfo(opts.input_file, progbar=opts.progress_bar, executor=executor)

    assert pdfinfo is not None
    assert pbar_disabled is not None and pbar_disabled != progress_bar


def make_version(version):
    def _make_version():
        return TesseractVersion(version)

    return _make_version


def test_version_comparison():
    vd.check_external_program(
        program="dummy_basic",
        package="dummy",
        version_checker=make_version('9.0'),
        need_version='8.0.2',
    )
    vd.check_external_program(
        program="dummy_doubledigit",
        package="dummy",
        version_checker=make_version('10.0'),
        need_version='8.0.2',
    )
    with pytest.raises(MissingDependencyError):
        vd.check_external_program(
            program="tesseract",
            package="tesseract",
            version_checker=make_version('4.0.0-beta.1'),
            need_version='4.1.1',
            version_parser=TesseractVersion,
        )
    vd.check_external_program(
        program="tesseract",
        package="tesseract",
        version_checker=make_version('v5.0.0-alpha.20200201'),
        need_version='4.1.1',
        version_parser=TesseractVersion,
    )
    vd.check_external_program(
        program="tesseract",
        package="tesseract",
        version_checker=make_version('5.0.0-rc1.20211030'),
        need_version='4.1.1',
        version_parser=TesseractVersion,
    )
    vd.check_external_program(
        program="tesseract",
        package="tesseract",
        version_checker=make_version('v4.1.1.20181030'),  # Used in some Windows builds
        need_version='4.1.1',
        version_parser=TesseractVersion,
    )
    vd.check_external_program(
        program="gs",
        package="ghostscript",
        version_checker=make_version('10.0'),
        need_version='9.50',
    )
    with pytest.raises(MissingDependencyError):
        vd.check_external_program(
            program="tesseract",
            package="tesseract",
            version_checker=make_version('4.1.1-rc2-25-g9707'),
            need_version='4.1.1',
            version_parser=TesseractVersion,
        )
    with pytest.raises(MissingDependencyError):
        vd.check_external_program(
            program="dummy_fails",
            package="dummy",
            version_checker=make_version('1.0'),
            need_version='2.0',
        )


def test_optional_program_recommended(caplog):
    caplog.clear()

    def raiser():
        raise FileNotFoundError('jbig2')

    with caplog.at_level(logging.WARNING):
        vd.check_external_program(
            program="jbig2",
            package="jbig2enc",
            version_checker=raiser,
            need_version='42',
            required_for='this test case',
            recommended=True,
        )
        assert any(
            (loglevel == logging.WARNING and "recommended" in msg)
            for _logger_name, loglevel, msg in caplog.record_tuples
        )


def test_pagesegmode_warning(caplog):
    opts = make_opts(tesseract_pagesegmode='0')
    plugin_manager = setup_plugin_infrastructure(plugins=opts.plugins or [])
    vd.check_options(opts, plugin_manager)
    assert 'disable OCR' in caplog.text


def test_two_languages():
    vd.check_options_languages(
        create_options(
            input_file='a.pdf',
            output_file='b.pdf',
            parser=get_parser(),
            languages=['fakelang1', 'fakelang2'],
        ),
        ['fakelang1', 'fakelang2'],
    )


def test_sidecar_equals_output(resources, no_outpdf):
    op = no_outpdf
    with pytest.raises(BadArgsError, match=r'--sidecar'):
        run_ocrmypdf_api(resources / 'trivial.pdf', op, '--sidecar', op)


@pytest.mark.parametrize(
    'spell_input, spell_sidecar',
    [
        pytest.param(lambda p: p, lambda p: f'./{p}', id='dot_slash'),
        pytest.param(lambda p: p, lambda p: Path(p).resolve(), id='absolute'),
        pytest.param(lambda p: f'sub/{p}', lambda p: f'sub//{p}', id='double_sep'),
        pytest.param(lambda p: f'sub/{p}', lambda p: f'sub/x/../{p}', id='dot_dot'),
        pytest.param(lambda p: p, lambda p: Path(p), id='path_vs_str'),
    ],
)
def test_sidecar_same_as_input_other_spelling(spell_input, spell_sidecar):
    """A sidecar that merely *spells* the input path differently must be caught.

    Comparing the raw option values only catches byte-identical strings, so
    ``./in.pdf`` or an absolute path would be accepted and the sidecar would
    then overwrite the input PDF.
    """
    opts = make_opts(
        input_file=spell_input('in.pdf'),
        output_file='out.pdf',
        sidecar=spell_sidecar('in.pdf'),
    )
    with pytest.raises(BadArgsError, match=r'--sidecar'):
        vd.check_options_sidecar(opts)


def test_sidecar_same_as_output_other_spelling():
    """The same aliasing must be caught for the output file."""
    opts = make_opts(input_file='in.pdf', output_file='out.pdf', sidecar='./out.pdf')
    with pytest.raises(BadArgsError, match=r'--sidecar'):
        vd.check_options_sidecar(opts)


@pytest.mark.parametrize(
    'sidecar',
    ['notes.txt', 'in.txt', 'sub/in.pdf'],
    ids=['distinct', 'same_stem', 'subdir'],
)
def test_sidecar_genuinely_different_is_allowed(sidecar):
    """Distinct files must keep working - the check must not over-reject."""
    opts = make_opts(input_file='in.pdf', output_file='out.pdf', sidecar=sidecar)
    vd.check_options_sidecar(opts)


def test_devnull_sidecar(resources):
    with pytest.raises(BadArgsError, match=r'--sidecar.*NUL'):
        run_ocrmypdf_api(resources / 'trivial.pdf', os.devnull, '--sidecar')


def test_output_type_none_requires_stdout(outpdf):
    with pytest.raises(ValueError, match='Set the output file to'):
        make_ocr_opts(output_file=outpdf, output_type='none')


def test_options_validation_error_is_not_a_traceback(resources, outpdf):
    """Options rejected while parsing must exit cleanly, not crash."""
    p = run_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--output-type=none',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == ExitCode.bad_args
    assert 'Traceback' not in p.stderr
    assert 'Set the output file to' in p.stderr


def test_argparse_error_still_exits_2(resources, outpdf):
    p = run_ocrmypdf(resources / 'trivial.pdf', outpdf, '--no-such-option')
    assert p.returncode == 2


@pytest.fixture
def protected_file(outdir):
    protected_file = outdir / 'protected.pdf'
    protected_file.touch()
    protected_file.chmod(0o400)  # Read-only
    yield protected_file


@pytest.mark.skipif(
    os.name == 'nt' or os.geteuid() == 0, reason="root can write to anything"
)
def test_destination_not_writable(resources, protected_file):
    exitcode = run_ocrmypdf_api(
        resources / 'jbig2.pdf',
        protected_file,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.file_access_error


def test_output_is_dir(resources, outdir, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'trivial.pdf',
        outdir,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.file_access_error
    assert 'is not a writable file' in caplog.text


@pytest.mark.skipif(os.name == 'nt', reason="symlink needs admin permissions")
def test_output_is_symlink(resources, outdir):
    sym = Path(outdir / 'this_is_a_symlink')
    sym.symlink_to(outdir / 'out.pdf')
    exitcode = run_ocrmypdf_api(
        resources / 'trivial.pdf',
        sym,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.ok
    assert (outdir / 'out.pdf').stat().st_size > 0, 'target file not created'
