# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pytest

from ocrmypdf.exceptions import ExitCode

from .conftest import is_linux, run_ocrmypdf_api


@pytest.mark.skipif(not is_linux(), reason='semfree plugin only works on Linux')
def test_semfree(resources, outpdf):
    exitcode = run_ocrmypdf_api(
        resources / 'multipage.pdf',
        outpdf,
        '--skip-text',
        '--skip-big',
        '2',
        '--plugin',
        'ocrmypdf.extra_plugins.semfree',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.ok
