# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import multiprocessing
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pikepdf
import pytest
from packaging.version import Version

from ocrmypdf import helpers
from ocrmypdf.helpers import running_in_docker
from ocrmypdf.pdfinfo import PdfInfo

needs_symlink = pytest.mark.skipif(os.name == 'nt', reason='needs posix symlink')
windows_only = pytest.mark.skipif(os.name != 'nt', reason="Windows test")


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


@windows_only
def test_gs_install_locations():
    # pylint: disable=import-outside-toplevel
    from ocrmypdf.subprocess._windows import _gs_version_in_path_key

    assert _gs_version_in_path_key(Path("C:\\Program Files\\gs\\gs9.52\\bin")) == (
        'gs',
        Version('9.52'),
    )


@windows_only
def test_shim_paths(tmp_path):
    # pylint: disable=import-outside-toplevel
    from ocrmypdf.subprocess._windows import shim_env_path

    progfiles = tmp_path / 'Program Files'
    progfiles.mkdir()
    (progfiles / 'tesseract-ocr').mkdir()
    (progfiles / 'gs' / '9.51' / 'bin').mkdir(parents=True)
    (progfiles / 'gs' / 'gs9.52.3' / 'bin').mkdir(parents=True)
    syspath = tmp_path / 'bin'
    env = {'PROGRAMFILES': str(progfiles), 'PATH': str(syspath)}

    result_str = shim_env_path(env=env)
    results = result_str.split(os.pathsep)
    assert results[0] == str(syspath), results
    assert results[-3].endswith('tesseract-ocr'), results
    assert results[-2].endswith(str(Path('gs9.52.3', 'bin'))), results
    assert results[-1].endswith(str(Path('gs', '9.51', 'bin'))), results


@windows_only
def test_shim_paths_missing_locations_are_not_warnings(tmp_path, caplog):
    """Searching for programs that aren't installed must not warn the user.

    Most of the locations searched won't exist on any given machine, so failing
    to find one is normal and must not be reported above debug level.
    See discussion #1671.
    """
    # pylint: disable=import-outside-toplevel
    from ocrmypdf.subprocess._windows import shim_env_path

    env = {'PROGRAMFILES': str(tmp_path / 'does not exist'), 'PATH': str(tmp_path)}

    with caplog.at_level(logging.DEBUG, logger='ocrmypdf.subprocess._windows'):
        shim_env_path(env=env)

    assert not [rec for rec in caplog.records if rec.levelno > logging.DEBUG], (
        "searching for uninstalled programs should only produce debug messages"
    )
    messages = [rec.getMessage() for rec in caplog.records]
    assert any('does not exist' in msg for msg in messages), (
        f"debug message should name the location that was searched: {messages}"
    )


def test_resolution():
    Resolution = helpers.Resolution
    dpi_100 = Resolution(100, 100)
    dpi_200 = Resolution(200, 200)
    assert dpi_100.is_square
    assert not Resolution(100, 200).is_square
    assert dpi_100 == Resolution(100, 100)
    assert str(dpi_100) != str(dpi_200)
    assert dpi_100.take_max([200, 300], [400]) == Resolution(300, 400)


def test_release_free_memory_is_harmless():
    # Whether or not this platform has glibc, calling it must always be safe.
    helpers.release_free_memory()
    helpers.release_free_memory()


def test_release_free_memory_no_op_without_glibc(monkeypatch):
    monkeypatch.setattr(helpers, '_malloc_trim', lambda: None)
    helpers.release_free_memory()


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason="glibc only")
def test_release_free_memory_calls_malloc_trim(monkeypatch):
    calls = []
    monkeypatch.setattr(helpers, '_malloc_trim', lambda: calls.append)
    helpers.release_free_memory()
    assert calls == [0], "malloc_trim must be called with a zero pad argument"


@pytest.fixture
def uncached_malloc_trim():
    """_malloc_trim() memoizes its answer; let each test resolve it afresh."""
    helpers._malloc_trim.cache_clear()
    yield
    helpers._malloc_trim.cache_clear()


def test_malloc_trim_absent_off_linux(monkeypatch, uncached_malloc_trim):
    monkeypatch.setattr(helpers.sys, 'platform', 'win32')
    assert helpers._malloc_trim() is None


def test_malloc_trim_absent_without_glibc(monkeypatch, uncached_malloc_trim):
    """Musl and friends have no libc.so.6 to load."""
    monkeypatch.setattr(helpers.sys, 'platform', 'linux')

    def no_libc(*args, **kwargs):
        raise OSError("libc.so.6: cannot open shared object file")

    monkeypatch.setattr(helpers.ctypes, 'CDLL', no_libc)
    assert helpers._malloc_trim() is None


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason="glibc only")
def test_malloc_trim_found_on_glibc(uncached_malloc_trim):
    assert callable(helpers._malloc_trim())


class TestPikepdfGetters:
    """Cover the untrusted-input paths of pikepdf_get_int/pikepdf_get_bool.

    Both helpers read optional hints out of arbitrary user PDFs, so a value of
    the wrong PDF type must fall back to the caller's default rather than
    propagate a Python-level error out of ``PdfInfo``.
    """

    @pytest.mark.parametrize(
        'value, expected',
        [
            (42, 42),
            (pikepdf.Object.parse(b'42'), 42),
            (3.9, 3),  # PDF Real truncates, as int() always has
            (True, 1),
            (pikepdf.String('nope'), 7),
            (pikepdf.Name.Nope, 7),
            (pikepdf.Array([1, 2]), 7),
            (None, 7),  # key absent
        ],
    )
    def test_get_int(self, value, expected):
        d = pikepdf.Dictionary()
        if value is not None:
            d[pikepdf.Name.K] = value
        assert helpers.pikepdf_get_int(d, pikepdf.Name.K, 7) == expected

    @pytest.mark.parametrize(
        'value, expected',
        [
            (True, True),
            (False, False),
            (1, True),  # malformed files store Booleans as 0/1
            (0, False),
            (pikepdf.Object.parse(b'true'), True),
            (pikepdf.String('nope'), False),
            (pikepdf.Name.Nope, False),
            (pikepdf.Array([1, 2]), False),
            (None, False),  # key absent
        ],
    )
    def test_get_bool(self, value, expected):
        d = pikepdf.Dictionary()
        if value is not None:
            d[pikepdf.Name.K] = value
        assert helpers.pikepdf_get_bool(d, pikepdf.Name.K, False) is expected

    def test_integer_marked_does_not_break_pdfinfo(self, outdir):
        """A /Marked written as an integer must not abort PdfInfo.

        ``pikepdf_get_bool`` only handled a native ``bool``, so an integer
        raised ``AttributeError: 'int' object has no attribute 'as_bool'``
        from ``PdfInfo.__init__`` -- before any OCR work began, and naming
        neither the file nor the field.
        """
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(200, 200))
        pdf.Root[pikepdf.Name.MarkInfo] = pdf.make_indirect(
            pikepdf.Dictionary(Marked=1)
        )
        target = outdir / 'marked_int.pdf'
        pdf.save(target)

        assert PdfInfo(target).is_tagged is True
