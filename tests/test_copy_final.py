# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""An existing output file is replaced only once the new one is complete."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

from ocrmypdf import _pipeline
from ocrmypdf._pipeline import copy_final

ORIGINAL = b'original contents'
RESULT = b'the result of a successful run' * 100


@pytest.fixture
def result_file(tmp_path):
    work = tmp_path / 'work'
    work.mkdir()
    path = work / 'result.pdf'
    path.write_bytes(RESULT)
    return path


@pytest.fixture
def outdir(tmp_path):
    path = tmp_path / 'out'
    path.mkdir()
    return path


@pytest.fixture
def existing_output(outdir):
    path = outdir / 'myfile.pdf'
    path.write_bytes(ORIGINAL)
    return path


def _interrupt_after_partial_write(monkeypatch):
    def interrupted_copy(src, dst, *args, **kwargs):
        dst.write(src.read(8))
        dst.flush()
        raise KeyboardInterrupt()

    monkeypatch.setattr(_pipeline, 'copyfileobj', interrupted_copy)


def test_interrupted_copy_keeps_existing_output(
    result_file, existing_output, monkeypatch
):
    _interrupt_after_partial_write(monkeypatch)
    with pytest.raises(KeyboardInterrupt):
        copy_final(result_file, existing_output)
    assert existing_output.read_bytes() == ORIGINAL
    assert list(existing_output.parent.iterdir()) == [existing_output]


def test_failed_copy_keeps_existing_output(result_file, existing_output, monkeypatch):
    def out_of_space(src, dst, *args, **kwargs):
        dst.write(src.read(8))
        raise OSError(28, 'No space left on device')

    monkeypatch.setattr(_pipeline, 'copyfileobj', out_of_space)
    with pytest.raises(OSError, match='No space left'):
        copy_final(result_file, existing_output)
    assert existing_output.read_bytes() == ORIGINAL
    assert list(existing_output.parent.iterdir()) == [existing_output]


def test_existing_output_replaced(result_file, existing_output):
    copy_final(result_file, existing_output)
    assert existing_output.read_bytes() == RESULT
    assert list(existing_output.parent.iterdir()) == [existing_output]


@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX permissions')
def test_existing_output_keeps_permissions(result_file, existing_output):
    existing_output.chmod(0o640)
    copy_final(result_file, existing_output)
    assert stat.S_IMODE(existing_output.stat().st_mode) == 0o640


def test_new_output_created(result_file, outdir):
    output = outdir / 'new.pdf'
    copy_final(result_file, output)
    assert output.read_bytes() == RESULT
    assert list(outdir.iterdir()) == [output]


def test_output_given_as_str(result_file, existing_output):
    copy_final(result_file, os.fspath(existing_output))
    assert existing_output.read_bytes() == RESULT


def test_symlink_output_stays_a_symlink(result_file, existing_output, outdir):
    link = outdir / 'link.pdf'
    try:
        link.symlink_to(existing_output)
    except OSError:
        pytest.skip('cannot create symlinks')
    copy_final(result_file, link)
    assert link.is_symlink()
    assert existing_output.read_bytes() == RESULT


def test_hard_linked_output_updates_every_link(result_file, existing_output, outdir):
    other_name = outdir / 'other.pdf'
    os.link(existing_output, other_name)
    copy_final(result_file, existing_output)
    assert existing_output.read_bytes() == RESULT
    assert other_name.read_bytes() == RESULT
    assert existing_output.samefile(other_name)


def test_falls_back_to_writing_in_place(result_file, existing_output, monkeypatch):
    """Such as a file bind-mounted into a container, which cannot be renamed over."""

    def busy(src, dst):
        raise OSError(16, 'Device or resource busy')

    monkeypatch.setattr(_pipeline.os, 'replace', busy)
    copy_final(result_file, existing_output)
    assert existing_output.read_bytes() == RESULT
    assert list(existing_output.parent.iterdir()) == [existing_output]


def test_falls_back_when_folder_is_not_writable(
    result_file, existing_output, monkeypatch
):
    def denied(*args, **kwargs):
        raise PermissionError(13, 'Permission denied')

    monkeypatch.setattr(_pipeline, 'mkstemp', denied)
    copy_final(result_file, existing_output)
    assert existing_output.read_bytes() == RESULT


@pytest.mark.skipif(sys.platform == 'win32', reason='no /dev/null')
def test_device_output_is_written_directly(result_file):
    copy_final(result_file, os.devnull)
    assert stat.S_ISCHR(Path(os.devnull).stat().st_mode)
