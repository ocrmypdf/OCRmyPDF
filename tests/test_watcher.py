from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

watchfiles = pytest.importorskip('watchfiles')

WATCHER = Path(__file__).parent.parent / 'misc' / 'watcher.py'


def _spawn_watcher(input_dir, output_dir, processed_dir, cwd, env_extra=None):
    """Launch watcher.py as a subprocess, cwd disjoint from the data dirs.

    The startup check treats the working directory as part of the code zone, so
    the subprocess must run from a directory that is neither an ancestor nor a
    descendant of the watched data directories.
    """
    return subprocess.Popen(
        [
            sys.executable,
            str(WATCHER),
            str(input_dir),
            str(output_dir),
            str(processed_dir),
        ],
        cwd=str(cwd),
        env=os.environ.copy() | (env_extra or {}),
    )


@pytest.fixture
def data_dirs(tmp_path):
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()
    work_dir = tmp_path / 'work'  # cwd, disjoint from the data dirs
    work_dir.mkdir()
    return input_dir, output_dir, processed_dir, work_dir


@pytest.mark.parametrize('year_month', [True, False])
def test_watcher(data_dirs, resources, year_month):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    env_extra = {'OCR_OUTPUT_DIRECTORY_YEAR_MONTH': '1'} if year_month else {}
    proc = _spawn_watcher(
        input_dir, output_dir, processed_dir, work_dir, env_extra=env_extra
    )
    time.sleep(5)

    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')
    time.sleep(5)

    if year_month:
        assert (
            output_dir
            / f'{dt.date.today().year}'
            / f'{dt.date.today().month:02d}'
            / 'trivial.pdf'
        ).exists()
    else:
        assert (output_dir / 'trivial.pdf').exists()

    proc.terminate()
    proc.wait()


def test_watcher_aborts_when_input_dir_in_code_zone(tmp_path):
    # Point the input directory at the interpreter prefix (a code zone). The
    # watcher must refuse to run and never enter the watch loop.
    input_dir = Path(sys.prefix)
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()
    work_dir = tmp_path / 'work'
    work_dir.mkdir()

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir)
    assert proc.wait(timeout=30) == 9  # ExitCode.invalid_config


def test_watcher_aborts_when_output_under_input(tmp_path):
    # Output nested inside the watched input directory would loop forever.
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = input_dir / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()
    work_dir = tmp_path / 'work'
    work_dir.mkdir()

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir)
    assert proc.wait(timeout=30) == 9


def test_watcher_rejects_world_writable_settings_file(data_dirs, tmp_path):
    input_dir, output_dir, processed_dir, work_dir = data_dirs
    settings = tmp_path / 'settings.json'
    settings.write_text('{}')
    settings.chmod(0o666)

    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        env_extra={'OCR_JSON_SETTINGS': str(settings)},
    )
    assert proc.wait(timeout=30) == 9


def test_watcher_rejects_plugin_in_data_dir(data_dirs):
    input_dir, output_dir, processed_dir, work_dir = data_dirs
    settings = json.dumps({'plugins': [str(input_dir / 'evil.py')]})

    proc = _spawn_watcher(
        input_dir,
        output_dir,
        processed_dir,
        work_dir,
        env_extra={'OCR_JSON_SETTINGS': settings},
    )
    assert proc.wait(timeout=30) == 9


@pytest.mark.skipif(os.name == 'nt', reason="POSIX fifo semantics")
def test_watcher_skips_fifo_input(data_dirs, resources):
    input_dir, output_dir, processed_dir, work_dir = data_dirs

    proc = _spawn_watcher(input_dir, output_dir, processed_dir, work_dir)
    time.sleep(5)

    # A fifo named like a PDF must be ignored, not OCR'd or crash the watcher.
    os.mkfifo(input_dir / 'pipe.pdf')
    time.sleep(2)
    # Then a genuine PDF should still be processed.
    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')
    time.sleep(5)

    assert (output_dir / 'trivial.pdf').exists()
    assert not (output_dir / 'pipe.pdf').exists()
    assert proc.poll() is None  # still running

    proc.terminate()
    proc.wait()
