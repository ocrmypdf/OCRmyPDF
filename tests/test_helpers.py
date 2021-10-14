# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import multiprocessing
import os
from unittest.mock import MagicMock

import pytest

from ocrmypdf import helpers

from .conftest import running_in_docker

needs_symlink = pytest.mark.skipif(os.name == 'nt', reason='needs posix symlink')


class TestSafeSymlink:
    def test_safe_symlink_link_self(self, tmp_path, caplog):
        helpers.safe_symlink(tmp_path / 'self', tmp_path / 'self')
        assert caplog.record_tuples[0][1] == logging.WARNING

    def test_safe_symlink_overwrite(self, tmp_path):
        (tmp_path / 'regular_file').touch()
        with pytest.raises(FileExistsError):
            helpers.safe_symlink(tmp_path / 'input', tmp_path / 'regular_file')

    @needs_symlink
    def test_safe_symlink_relink(self, tmp_path):
        (tmp_path / 'regular_file_a').touch()
        (tmp_path / 'regular_file_b').write_bytes(b'ABC')
        (tmp_path / 'link').symlink_to(tmp_path / 'regular_file_a')
        helpers.safe_symlink(tmp_path / 'regular_file_b', tmp_path / 'link')
        assert (tmp_path / 'link').samefile(tmp_path / 'regular_file_b') or (
            tmp_path / 'link'
        ).read_bytes() == b'ABC'


def test_no_cpu_count(monkeypatch):
    invoked = False

    def cpu_count_raises():
        nonlocal invoked
        invoked = True
        raise NotImplementedError()

    monkeypatch.setattr(multiprocessing, 'cpu_count', cpu_count_raises)
    with pytest.warns(expected_warning=UserWarning):
        assert helpers.available_cpu_count() == 1
    assert invoked, "Patched function called during test"


def test_deprecated():
    @helpers.deprecated
    def old_function():
        return 42

    with pytest.deprecated_call():
        assert old_function() == 42


skipif_docker = pytest.mark.skipif(running_in_docker(), reason="fails on Docker")


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

    @needs_symlink
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


@pytest.mark.skipif(os.name != 'nt', reason="Windows test")
def test_shim_paths(tmp_path):
    # pylint: disable=import-outside-toplevel
    from ocrmypdf.subprocess._windows import shim_env_path

    progfiles = tmp_path / 'Program Files'
    progfiles.mkdir()
    (progfiles / 'tesseract-ocr').mkdir()
    (progfiles / 'gs' / '9.51' / 'bin').mkdir(parents=True)
    (progfiles / 'gs' / '9.52' / 'bin').mkdir(parents=True)
    syspath = tmp_path / 'bin'
    env = {'PROGRAMFILES': str(progfiles), 'PATH': str(syspath)}

    result_str = shim_env_path(env=env)
    results = result_str.split(os.pathsep)
    assert results[0] == str(syspath), results
    assert results[-3].endswith('tesseract-ocr'), results
    assert results[-2].endswith(os.path.join('gs', '9.52', 'bin')), results
    assert results[-1].endswith(os.path.join('gs', '9.51', 'bin')), results


def test_resolution():
    Resolution = helpers.Resolution
    dpi_100 = Resolution(100, 100)
    dpi_200 = Resolution(200, 200)
    assert dpi_100.is_square
    assert not Resolution(100, 200).is_square
    assert dpi_100 == Resolution(100, 100)
    assert str(dpi_100) != str(dpi_200)
    assert dpi_100.take_max([200, 300], [400]) == Resolution(300, 400)
