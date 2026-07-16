from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pikepdf
import pytest

watchdog = pytest.importorskip('watchdog')


@pytest.mark.parametrize('year_month', [True, False])
def test_watcher(tmp_path, resources, year_month):
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()

    env_extra = {'OCR_OUTPUT_DIRECTORY_YEAR_MONTH': '1'} if year_month else {}
    proc = subprocess.Popen(
        [
            sys.executable,
            Path(__file__).parent.parent / 'misc' / 'watcher.py',
            str(input_dir),
            str(output_dir),
            str(processed_dir),
        ],
        cwd=str(tmp_path),
        env=os.environ.copy() | env_extra,
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


def test_watcher_survives_encrypted_pdf(tmp_path, resources):
    # A password protected PDF raised an unhandled pikepdf.PasswordError that
    # killed the watchdog observer thread - the watcher process kept running
    # but silently ignored all files created afterwards.
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()

    encrypted = tmp_path / 'encrypted.pdf'
    with pikepdf.open(resources / 'trivial.pdf') as pdf:
        pdf.save(
            encrypted,
            encryption=pikepdf.models.encryption.Encryption(
                owner='ocrmypdf', user='ocrmypdf', R=6
            ),
        )

    proc = subprocess.Popen(
        [
            sys.executable,
            Path(__file__).parent.parent / 'misc' / 'watcher.py',
            str(input_dir),
            str(output_dir),
            str(processed_dir),
        ],
        cwd=str(tmp_path),
        env=os.environ.copy(),
    )
    time.sleep(5)

    shutil.copy(encrypted, input_dir / 'encrypted.pdf')
    time.sleep(5)

    # The watcher must still process files arriving after the encrypted one
    shutil.copy(resources / 'trivial.pdf', input_dir / 'trivial.pdf')
    time.sleep(5)

    assert (output_dir / 'trivial.pdf').exists()
    assert not (output_dir / 'encrypted.pdf').exists()

    proc.terminate()
    proc.wait()
