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

import os
from unittest.mock import MagicMock, patch

import pytest

import ocrmypdf._validation as vd
from ocrmypdf.api import create_options
from ocrmypdf.exceptions import MissingDependencyError, BadArgsError


def make_opts(input_file='a.pdf', output_file='b.pdf', language='eng', **kwargs):
    return create_options(
        input_file=input_file, output_file=output_file, language=language, **kwargs
    )


def test_hocr_notlatin_warning(caplog):
    vd.check_options_output(make_opts(language='chi_sim', pdf_renderer='hocr'))
    assert 'PDF renderer is known to cause' in caplog.text


def test_old_ghostscript(caplog):
    with patch('ocrmypdf.exec.ghostscript.version', return_value='9.19'):
        vd.check_options_output(make_opts(language='chi_sim', output_type='pdfa'))
        assert 'Ghostscript does not work correctly' in caplog.text

    with patch('ocrmypdf.exec.ghostscript.version', return_value='9.18'):
        with pytest.raises(MissingDependencyError):
            vd.check_options_output(make_opts(output_type='pdfa-3'))

    with patch('ocrmypdf.exec.ghostscript.version', return_value='9.24'):
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

    os.truncate(in_, 25001)
    os.truncate(out, 50000)
    vd.report_output_file_size(opts, in_, out)
    assert 'No reason' in caplog.text
