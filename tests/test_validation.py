# © 2019 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import logging
from unittest.mock import patch

import pikepdf
import pytest

from ocrmypdf import _validation as vd
from ocrmypdf._plugin_manager import get_plugin_manager
from ocrmypdf.api import create_options
from ocrmypdf.cli import get_parser
from ocrmypdf.exceptions import BadArgsError, MissingDependencyError
from ocrmypdf.pdfinfo import PdfInfo


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


def test_hocr_notlatin_warning(caplog):
    # Bypass the test to see if the language is installed; we just want to pretend
    # that a non-Latin language is installed
    vd._check_options(
        *make_opts_pm(language='chi_sim', pdf_renderer='hocr', output_type='pdfa'),
        {'chi_sim'},
    )
    assert 'PDF renderer is known to cause' in caplog.text


def test_old_ghostscript(caplog):
    with patch('ocrmypdf._exec.ghostscript.version', return_value='9.19'), patch(
        'ocrmypdf._exec.tesseract.has_textonly_pdf', return_value=True
    ):
        vd._check_options(
            *make_opts_pm(language='chi_sim', output_type='pdfa'), {'chi_sim'}
        )
        assert 'Ghostscript does not work correctly' in caplog.text

    with patch('ocrmypdf._exec.ghostscript.version', return_value='9.18'), patch(
        'ocrmypdf._exec.tesseract.has_textonly_pdf', return_value=True
    ):
        with pytest.raises(MissingDependencyError):
            vd._check_options(*make_opts_pm(output_type='pdfa-3'), set())

    with patch('ocrmypdf._exec.ghostscript.version', return_value='9.24'), patch(
        'ocrmypdf._exec.tesseract.has_textonly_pdf', return_value=True
    ):
        with pytest.raises(MissingDependencyError):
            vd._check_options(*make_opts_pm(), set())


def test_old_tesseract_error():
    with patch('ocrmypdf._exec.tesseract.has_textonly_pdf', return_value=False):
        with pytest.raises(MissingDependencyError):
            opts = make_opts(pdf_renderer='sandwich', language='eng')
            plugin_manager = get_plugin_manager(opts.plugins)
            vd._check_options(opts, plugin_manager, {'eng'})


def test_lossless_redo():
    with pytest.raises(BadArgsError):
        vd.check_options_output(make_opts(redo_ocr=True, deskew=True))


def test_mutex_options():
    with pytest.raises(BadArgsError):
        vd.check_options_ocr_behavior(make_opts(force_ocr=True, skip_text=True))
    with pytest.raises(BadArgsError):
        vd.check_options_ocr_behavior(make_opts(redo_ocr=True, skip_text=True))
    with pytest.raises(BadArgsError):
        vd.check_options_ocr_behavior(make_opts(redo_ocr=True, force_ocr=True))
    with pytest.raises(BadArgsError):
        vd.check_options_ocr_behavior(make_opts(pages='1-3', sidecar='file.txt'))


def test_optimizing(caplog):
    vd.check_options_optimizing(
        make_opts(optimize=0, jbig2_lossy=True, png_quality=18, jpeg_quality=10)
    )
    assert 'will be ignored because' in caplog.text


def test_user_words(caplog):
    with patch('ocrmypdf._exec.tesseract.has_user_words', return_value=False):
        opts = make_opts(user_words='foo')
        plugin_manager = get_plugin_manager(opts.plugins)
        vd._check_options(opts, plugin_manager, set())
        assert '4.0 ignores --user-words' in caplog.text
    caplog.clear()
    with patch('ocrmypdf._exec.tesseract.has_user_words', return_value=True):
        opts = make_opts(user_patterns='foo')
        plugin_manager = get_plugin_manager(opts.plugins)
        vd._check_options(opts, plugin_manager, set())
        assert '4.0 ignores --user-words' not in caplog.text


def test_pillow_options():
    vd.check_options_pillow(make_opts(max_image_mpixels=0))


def test_output_tty():
    with patch('sys.stdout.isatty', return_value=True):
        with pytest.raises(BadArgsError):
            vd.check_requested_output_file(make_opts(output_file='-'))


def test_report_file_size(tmp_path, caplog):
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
    pdf.root.Dummy = waste_of_space
    pdf.save(in_)
    pdf.root.Dummy2 = waste_of_space + waste_of_space
    pdf.save(out)

    with patch('ocrmypdf._validation.jbig2enc.available', return_value=True), patch(
        'ocrmypdf._validation.pngquant.available', return_value=True
    ):
        vd.report_output_file_size(opts, in_, out)
        assert 'No reason' in caplog.text
    caplog.clear()

    with patch('ocrmypdf._validation.jbig2enc.available', return_value=False), patch(
        'ocrmypdf._validation.pngquant.available', return_value=True
    ):
        vd.report_output_file_size(opts, in_, out)
        assert 'optional dependency' in caplog.text
    caplog.clear()

    opts = make_opts(in_, out, optimize=0, output_type='pdf')
    vd.report_output_file_size(opts, in_, out)
    assert 'disabled' in caplog.text
    caplog.clear()


def test_false_action_store_true():
    opts = make_opts(keep_temporary_files=True)
    assert opts.keep_temporary_files
    opts = make_opts(keep_temporary_files=False)
    assert not opts.keep_temporary_files


@pytest.mark.parametrize('progress_bar', [True, False])
def test_no_progress_bar(progress_bar, resources):
    opts = make_opts(progress_bar=progress_bar, input_file=(resources / 'trivial.pdf'))
    plugin_manager = get_plugin_manager(opts.plugins)
    with patch('ocrmypdf._concurrent.tqdm', autospec=True) as tqdmpatch:
        vd._check_options(opts, plugin_manager, set())
        pdfinfo = PdfInfo(opts.input_file, progbar=opts.progress_bar)
        assert pdfinfo is not None
        assert tqdmpatch.called
        _args, kwargs = tqdmpatch.call_args
        assert kwargs['disable'] != progress_bar


def test_language_warning(caplog):
    opts = make_opts(language=None)
    plugin_manager = get_plugin_manager(opts.plugins)
    caplog.set_level(logging.DEBUG)
    with patch(
        'ocrmypdf._validation.locale.getlocale', return_value=('en_US', 'UTF-8')
    ):
        vd.check_options_languages(opts, {'eng'})
        assert opts.languages == {'eng'}
        assert '' in caplog.text

    opts = make_opts(language=None)
    with patch(
        'ocrmypdf._validation.locale.getlocale', return_value=('fr_FR', 'UTF-8')
    ):
        vd.check_options_languages(opts, {'eng'})
        assert opts.languages == {'eng'}
        assert 'assuming --language' in caplog.text


def test_version_comparison():
    vd.check_external_program(
        program="dummy_basic",
        package="dummy",
        version_checker=lambda: '9.0',
        need_version='8.0.2',
    )
    vd.check_external_program(
        program="dummy_doubledigit",
        package="dummy",
        version_checker=lambda: '10.0',
        need_version='8.0.2',
    )
    vd.check_external_program(
        program="tesseract",
        package="tesseract",
        version_checker=lambda: '4.0.0-beta.1',
        need_version='4.0.0',
    )
    vd.check_external_program(
        program="tesseract",
        package="tesseract",
        version_checker=lambda: 'v5.0.0-alpha.20200201',
        need_version='4.0.0',
    )
    with pytest.raises(MissingDependencyError):
        vd.check_external_program(
            program="dummy_fails",
            package="dummy",
            version_checker=lambda: '1.0',
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
    vd._check_options(opts, plugin_manager, set())
    assert 'disable OCR' in caplog.text


def test_two_languages():
    with patch('ocrmypdf._exec.tesseract.has_textonly_pdf', return_value=True):
        vd._check_options(
            *make_opts_pm(language='fakelang1+fakelang2'), {'fakelang1', 'fakelang2'}
        )
