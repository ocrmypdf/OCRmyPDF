# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Adds OCR layer to PDFs."""

from __future__ import annotations

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
    PriorOcrFoundError,
    SubprocessOutputError,
    TesseractConfigError,
    UnsupportedImageFormatError,
)
from ocrmypdf.pluginspec import OcrEngine, OrientationConfidence

hookimpl = _HookimplMarker('ocrmypdf')

__all__ = [
    '__version__',
    'BadArgsError',
    'configure_logging',
    'DpiError',
    'EncryptedPdfError',
    'Executor',
    'ExitCode',
    'ExitCodeException',
    'helpers',
    'hocrtransform',
    'hookimpl',
    'InputFileError',
    'MissingDependencyError',
    'ocr',
    'OcrEngine',
    'OrientationConfidence',
    'OutputFileAccessError',
    'PageContext',
    'pdfa',
    'PdfContext',
    'pdfinfo',
    'PriorOcrFoundError',
    'PROGRAM_NAME',
    'SubprocessOutputError',
    'TesseractConfigError',
    'UnsupportedImageFormatError',
    'Verbosity',
]
