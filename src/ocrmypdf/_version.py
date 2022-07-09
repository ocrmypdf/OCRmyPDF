# © 2017 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Get version by introspecting package information.

OCRmyPDF uses setuptools_scm to derive version from git tags.
"""

try:
    from importlib.metadata import version as _package_version
except ImportError:
    from importlib_metadata import version as _package_version  # type: ignore

PROGRAM_NAME = 'ocrmypdf'

# Official PEP 396
__version__ = _package_version('ocrmypdf')
