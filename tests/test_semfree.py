# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import sys

import pytest

from ocrmypdf.exceptions import ExitCode

from .conftest import is_linux, run_ocrmypdf_api


@pytest.mark.skipif(not is_linux(), reason='semfree plugin only works on Linux')
@pytest.mark.skipif(
    sys.version_info >= (3, 14),
    reason='semfree plugin only works on Python 3.13 or earlier',
)
def test_semfree(resources, outpdf):
    with pytest.warns(DeprecationWarning, match="semfree.py is deprecated"):
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
        assert exitcode in (ExitCode.ok, ExitCode.pdfa_conversion_failed)
