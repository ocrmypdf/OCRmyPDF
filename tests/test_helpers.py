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
import multiprocessing
import os
from unittest.mock import MagicMock

import pytest

import ocrmypdf.helpers as helpers
from ocrmypdf.subprocess import shim_paths_with_program_files


class TestSafeSymlink:
    def test_safe_symlink_link_self(self, tmp_path, caplog):
        helpers.safe_symlink(tmp_path / 'self', tmp_path / 'self')
        assert caplog.record_tuples[0][1] == logging.WARNING

    def test_safe_symlink_overwrite(self, tmp_path):
        (tmp_path / 'regular_file').touch()
        with pytest.raises(FileExistsError):
            helpers.safe_symlink(tmp_path / 'input', tmp_path / 'regular_file')

    def test_safe_symlink_relink(self, tmp_path):
        (tmp_path / 'regular_file_a').touch()
        (tmp_path / 'regular_file_b').write_bytes(b'ABC')
        (tmp_path / 'link').symlink_to(tmp_path / 'regular_file_a')
        helpers.safe_symlink(tmp_path / 'regular_file_b', tmp_path / 'link')
        assert (tmp_path / 'link').samefile(tmp_path / 'regular_file_b') or (
            tmp_path / 'link'
        ).read_bytes() == b'ABC'


def test_no_cpu_count(monkeypatch):
    def cpu_count_raises():
        raise NotImplementedError()

    monkeypatch.setattr(multiprocessing, 'cpu_count', cpu_count_raises)
    with pytest.warns(expected_warning=UserWarning):
        assert helpers.available_cpu_count() == 1


def test_deprecated():
    @helpers.deprecated
    def old_function():
        return 42

    with pytest.deprecated_call():
        assert old_function() == 42


skipif_docker = pytest.mark.skipif(
    pytest.helpers.running_in_docker(), reason="fails on Docker"
)


class TestFileIsWritable:
    @pytest.fixture
    def non_existent(self, tmp_path):
        return tmp_path / 'nofile'

    @pytest.fixture
    def basic_file(self, tmp_path):
        basic = tmp_path / 'basic'
        basic.touch()
        return basic

    def test_plain(self, non_existent):
        assert helpers.is_file_writable(non_existent)

    def test_symlink_loop(self, tmp_path):
        loop = tmp_path / 'loop'
        loop.symlink_to(loop)
        assert not helpers.is_file_writable(loop)

    @skipif_docker
    def test_chmod(self, basic_file):
        assert helpers.is_file_writable(basic_file)
        basic_file.chmod(0o400)
        assert not helpers.is_file_writable(basic_file)
        basic_file.chmod(0o000)
        assert not helpers.is_file_writable(basic_file)

    def test_permission_error(self, basic_file):
        pathmock = MagicMock(spec_set=basic_file)
        pathmock.is_symlink.return_value = False
        pathmock.exists.return_value = True
        pathmock.is_file.side_effect = PermissionError
        assert not helpers.is_file_writable(pathmock)


def test_shim_paths(tmp_path):
    progfiles = tmp_path / 'Program Files'
    progfiles.mkdir()
    (progfiles / 'tesseract-ocr').mkdir()
    (progfiles / 'gs' / '9.51' / 'bin').mkdir(parents=True)
    (progfiles / 'gs' / '9.52' / 'bin').mkdir(parents=True)
    syspath = tmp_path / 'bin'
    env = {'PROGRAMFILES': str(progfiles), 'PATH': str(syspath)}

    result_str = shim_paths_with_program_files(env=env)
    results = result_str.split(os.pathsep)
    assert results[0].endswith('tesseract-ocr')
    assert results[1].endswith(os.path.join('gs', '9.52', 'bin'))
    assert results[2].endswith(os.path.join('gs', '9.51', 'bin'))
    assert results[3] == str(syspath)
