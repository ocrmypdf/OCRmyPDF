# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os
import platform

import pytest

from ocrmypdf import ExitCode

from .conftest import run_ocrmypdf_api


@pytest.mark.skipif(os.name == 'nt', reason="Windows doesn't have SIGKILL")
@pytest.mark.skipif(
    platform.python_version_tuple() >= ('3', '12'), reason="can deadlock due to fork"
)
def test_simulate_oom_killer(multipage, no_outpdf):
    exitcode = run_ocrmypdf_api(
        multipage,
        no_outpdf,
        '--force-ocr',
        '--no-use-threads',
        '--plugin',
        'tests/plugins/tesseract_simulate_oom_killer.py',
    )
    assert exitcode == ExitCode.child_process_error
