# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Wrappers to manage subprocess calls.

This package is split into three private submodules by concern:

- :mod:`ocrmypdf.subprocess._run` - low-level execution wrappers (``run``,
  ``run_polling_stderr``) that add OCRmyPDF-aware logging and Windows PATH
  resolution. Useful as drop-in replacements for :func:`subprocess.run`.
- :mod:`ocrmypdf.subprocess._version` - version probing (``get_version``).
- :mod:`ocrmypdf.subprocess._check` - startup validation
  (``check_external_program``) with platform-aware error messages.

The names below are the stable public API. Importing from the private
submodules directly is not supported for external code.
"""

from __future__ import annotations

from ocrmypdf.subprocess._check import check_external_program
from ocrmypdf.subprocess._run import Args, Environ, run, run_polling_stderr
from ocrmypdf.subprocess._version import get_version

__all__ = [
    'Args',
    'Environ',
    'check_external_program',
    'get_version',
    'run',
    'run_polling_stderr',
]
