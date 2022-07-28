# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Get version by introspecting package information.

OCRmyPDF uses setuptools_scm to derive version from git tags.
"""

from __future__ import annotations

try:
    from importlib.metadata import version as _package_version
except ImportError:
    from importlib_metadata import version as _package_version  # type: ignore

PROGRAM_NAME = 'ocrmypdf'

# Official PEP 396
__version__ = _package_version('ocrmypdf')
