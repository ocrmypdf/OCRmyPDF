# © 2021 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

from ocrmypdf import ExitCode

from .conftest import run_ocrmypdf_api


@pytest.mark.skipif(True, reason="--use-threads is currently default")
@pytest.mark.skipif(os.name == 'nt', reason="Windows doesn't have SIGKILL")
def test_simulate_oom_killer(resources, no_outpdf):
    exitcode = run_ocrmypdf_api(
        resources / 'multipage.pdf',
        no_outpdf,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_simulate_oom_killer.py',
    )
    assert exitcode == ExitCode.child_process_error
