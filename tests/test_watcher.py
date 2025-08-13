import datetime
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

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

    if year_month:
        env_extra = {'OCR_OUTPUT_DIRECTORY_YEAR_MONTH': '1'}
    else:
        env_extra = {}
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
            / f'{datetime.date.today().year}'
            / f'{datetime.date.today().month:02d}'
            / 'trivial.pdf'
        ).exists()
    else:
        assert (output_dir / 'trivial.pdf').exists()

    proc.terminate()
    proc.wait()
