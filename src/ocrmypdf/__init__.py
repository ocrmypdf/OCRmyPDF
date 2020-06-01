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


from pluggy import HookimplMarker as _HookimplMarker

from ocrmypdf import helpers, hocrtransform, leptonica, pdfa, pdfinfo
from ocrmypdf._version import PROGRAM_NAME, __version__
from ocrmypdf.api import Verbosity, configure_logging, ocr
from ocrmypdf.exceptions import (
    BadArgsError,
    DpiError,
    EncryptedPdfError,
    ExitCode,
    ExitCodeException,
    InputFileError,
    MissingDependencyError,
    OutputFileAccessError,
    PdfMergeFailedError,
    PriorOcrFoundError,
    SubprocessOutputError,
    TesseractConfigError,
    UnsupportedImageFormatError,
)
from ocrmypdf.pluginspec import OcrEngine, OrientationConfidence

hookimpl = _HookimplMarker('ocrmypdf')
