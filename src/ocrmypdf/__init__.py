# © 2017 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import pkg_resources

PROGRAM_NAME = 'ocrmypdf'

# Official PEP 396
__version__ = pkg_resources.get_distribution('ocrmypdf').version

VERSION = __version__

from .exceptions import (
    ExitCode,
    BadArgsError,
    PdfMergeFailedError,
    MissingDependencyError,
    UnsupportedImageFormatError,
    DpiError,
    OutputFileAccessError,
    PriorOcrFoundError,
    InputFileError,
    SubprocessOutputError,
    EncryptedPdfError,
    TesseractConfigError,
)

from . import helpers
from . import hocrtransform
from . import leptonica
from . import pdfa
from . import pdfinfo
