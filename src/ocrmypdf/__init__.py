# © 2017 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from pluggy import HookimplMarker as _HookimplMarker

from ocrmypdf import helpers, hocrtransform, pdfa, pdfinfo
from ocrmypdf._concurrent import Executor
from ocrmypdf._jobcontext import PageContext, PdfContext
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
