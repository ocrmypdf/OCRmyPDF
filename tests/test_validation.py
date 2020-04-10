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
import os
from unittest.mock import patch

import pytest

import ocrmypdf._validation as vd
from ocrmypdf.api import create_options
from ocrmypdf.exceptions import BadArgsError, MissingDependencyError
from ocrmypdf.pdfinfo import PdfInfo


def make_opts(input_file='a.pdf', output_file='b.pdf', language='eng', **kwargs):
    if language is not None:
        kwargs['language'] = language
    return create_options(input_file=input_file, output_file=output_file, **kwargs)


def test_hocr_notlatin_warning(caplog):
    vd.check_options_output(make_opts(language='chi_sim', pdf_renderer='hocr'))
    assert 'PDF renderer is known to cause' in caplog.text


def test_old_ghostscript(caplog):
    with patch('ocrmypdf.exec.ghostscript.version', return_value='9.19'), patch(
        'ocrmypdf.exec.tesseract.has_textonly_pdf', return_value=True
    ):
        vd.check_options_output(make_opts(language='chi_sim', output_type='pdfa'))
        assert 'Ghostscript does not work correctly' in caplog.text

    with patch('ocrmypdf.exec.ghostscript.version', return_value='9.18'), patch(
        'ocrmypdf.exec.tesseract.has_textonly_pdf', return_value=True
    ):
        with pytest.raises(MissingDependencyError):
            vd.check_options_output(make_opts(output_type='pdfa-3'))

    with patch('ocrmypdf.exec.ghostscript.version', return_value='9.24'), patch(
        'ocrmypdf.exec.tesseract.has_textonly_pdf', return_value=True
    ):
        with pytest.raises(MissingDependencyError):
            vd.check_dependency_versions(make_opts())


def test_old_tesseract_error():
    with patch('ocrmypdf.exec.tesseract.has_textonly_pdf', return_value=False):
        with pytest.raises(MissingDependencyError):
            opts = make_opts(pdf_renderer='sandwich', language='eng')
            vd.check_options_output(opts)


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
    with patch('ocrmypdf.exec.tesseract.version', return_value='4.0.0'):
        vd.check_options_advanced(make_opts(user_words='foo'))
        assert '4.0 ignores --user-words' in caplog.text
    caplog.clear()
    with patch('ocrmypdf.exec.tesseract.version', return_value='4.1.0'):
        vd.check_options_advanced(make_opts(user_patterns='foo'))
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
    in_.write_bytes(b'123')
    out.write_bytes(b'')
    opts = make_opts()
    vd.report_output_file_size(opts, in_, out)
    assert caplog.text == ''
    caplog.clear()

    os.truncate(in_, 25001)
    os.truncate(out, 50000)
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

    opts = make_opts(in_, out, optimize=0)
    vd.report_output_file_size(opts, in_, out)
    assert 'disabled' in caplog.text
    caplog.clear()


def test_false_action_store_true():
    opts = make_opts(keep_temporary_files=True)
    assert opts.keep_temporary_files == True
    opts = make_opts(keep_temporary_files=False)
    assert opts.keep_temporary_files == False


@pytest.mark.parametrize('progress_bar', [True, False])
def test_no_progress_bar(progress_bar, resources):
    opts = make_opts(progress_bar=progress_bar, input_file=(resources / 'trivial.pdf'))
    with patch('ocrmypdf.pdfinfo.info.tqdm', autospec=True) as tqdmpatch:
        vd.check_options(opts)
        pdfinfo = PdfInfo(opts.input_file, progbar=opts.progress_bar)
        assert pdfinfo is not None
        assert tqdmpatch.called
        _args, kwargs = tqdmpatch.call_args
        assert kwargs['disable'] != progress_bar


def test_language_warning(caplog):
    opts = make_opts(language=None)
    caplog.set_level(logging.DEBUG)
    with patch(
        'ocrmypdf._validation.locale.getlocale', return_value=('en_US', 'UTF-8')
    ):
        vd.check_options_languages(opts)
        assert opts.language == ['eng']
        assert '' in caplog.text

    opts = make_opts(language=None)
    with patch(
        'ocrmypdf._validation.locale.getlocale', return_value=('fr_FR', 'UTF-8')
    ):
        vd.check_options_languages(opts)
        assert opts.language == ['eng']
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
