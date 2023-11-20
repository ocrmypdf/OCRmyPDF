# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pikepdf
import pytest

from ocrmypdf import _validation as vd
from ocrmypdf._concurrent import NullProgressBar, SerialExecutor
from ocrmypdf._exec.tesseract import TesseractVersion
from ocrmypdf._plugin_manager import get_plugin_manager
from ocrmypdf.api import create_options
from ocrmypdf.cli import get_parser
from ocrmypdf.exceptions import BadArgsError, MissingDependencyError
from ocrmypdf.pdfinfo import PdfInfo

from .conftest import run_ocrmypdf_api


def make_opts_pm(input_file='a.pdf', output_file='b.pdf', language='eng', **kwargs):
    if language is not None:
        kwargs['language'] = language
    parser = get_parser()
    pm = get_plugin_manager(kwargs.get('plugins', []))
    pm.hook.add_options(parser=parser)  # pylint: disable=no-member
    return (
        create_options(
            input_file=input_file, output_file=output_file, parser=parser, **kwargs
        ),
        pm,
    )


def make_opts(*args, **kwargs):
    opts, _pm = make_opts_pm(*args, **kwargs)
    return opts


def test_old_tesseract_error():
    with patch(
        'ocrmypdf._exec.tesseract.version',
        return_value=TesseractVersion('4.00.00alpha'),
    ):
        with pytest.raises(MissingDependencyError):
            vd.check_options(*make_opts_pm(pdf_renderer='sandwich', language='eng'))


def test_tesseract_not_installed(caplog):
    with patch('ocrmypdf.subprocess.run') as not_found:
        not_found.side_effect = FileNotFoundError('tesseract')
        with pytest.raises(MissingDependencyError, match="Could not find program"):
            vd.check_options(*make_opts_pm())
            assert (
                "'tesseract' could not be executed" in caplog.text
            ), "Error message not printed"
            assert 'install' in caplog.text, "Install advice not printed"
        not_found.assert_called()


def test_lossless_redo():
    with pytest.raises(BadArgsError):
        options = make_opts(redo_ocr=True, deskew=True)
        vd.check_options_output(options)
        vd.set_lossless_reconstruction(options)


def test_mutex_options():
    with pytest.raises(BadArgsError):
        vd.check_options_ocr_behavior(make_opts(force_ocr=True, skip_text=True))
    with pytest.raises(BadArgsError):
        vd.check_options_ocr_behavior(make_opts(redo_ocr=True, skip_text=True))
    with pytest.raises(BadArgsError):
        vd.check_options_ocr_behavior(make_opts(redo_ocr=True, force_ocr=True))


def test_optimizing(caplog):
    vd.check_options(
        *make_opts_pm(optimize=0, jbig2_lossy=True, png_quality=18, jpeg_quality=10)
    )
    assert 'will be ignored because' in caplog.text


def test_pillow_options():
    vd.check_options_pillow(make_opts(max_image_mpixels=0))


def test_output_tty():
    with patch('sys.stdout.isatty', return_value=True):
        with pytest.raises(BadArgsError):
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


def test_language_warning(caplog):
    opts = make_opts(language=None)
    _plugin_manager = get_plugin_manager(opts.plugins)
    caplog.set_level(logging.DEBUG)
    with patch(
        'ocrmypdf._validation.locale.getlocale', return_value=('en_US', 'UTF-8')
    ) as mock:
        vd.check_options_languages(opts, ['eng'])
        assert opts.languages == ['eng']
        assert '' in caplog.text
        mock.assert_called_once()

    opts = make_opts(language=None)
    with patch(
        'ocrmypdf._validation.locale.getlocale', return_value=('fr_FR', 'UTF-8')
    ) as mock:
        vd.check_options_languages(opts, ['eng'])
        assert opts.languages == ['eng']
        assert 'assuming --language' in caplog.text
        mock.assert_called_once()


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
    plugin_manager = get_plugin_manager(opts.plugins)
    vd.check_options(opts, plugin_manager)
    assert 'disable OCR' in caplog.text


def test_two_languages():
    vd.check_options_languages(
        create_options(
            input_file='a.pdf',
            output_file='b.pdf',
            parser=get_parser(),
            language='fakelang1+fakelang2',
        ),
        ['fakelang1', 'fakelang2'],
    )


def test_sidecar_equals_output(resources, no_outpdf):
    op = no_outpdf
    with pytest.raises(BadArgsError, match=r'--sidecar'):
        run_ocrmypdf_api(resources / 'trivial.pdf', op, '--sidecar', op)


def test_devnull_sidecar(resources):
    with pytest.raises(BadArgsError, match=r'--sidecar.*NUL'):
        run_ocrmypdf_api(resources / 'trivial.pdf', os.devnull, '--sidecar')
