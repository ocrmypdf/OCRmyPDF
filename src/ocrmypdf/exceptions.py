# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF's exceptions."""

from __future__ import annotations

from enum import IntEnum
from textwrap import dedent


class ExitCode(IntEnum):
    """OCRmyPDF's exit codes."""

    # pylint: disable=invalid-name
    ok = 0
    bad_args = 1
    input_file = 2
    missing_dependency = 3
    invalid_output_pdf = 4
    file_access_error = 5
    already_done_ocr = 6
    child_process_error = 7
    encrypted_pdf = 8
    invalid_config = 9
    pdfa_conversion_failed = 10
    other_error = 15
    ctrl_c = 130


class ExitCodeException(Exception):
    """An exception which should return an exit code with sys.exit()."""

    exit_code = ExitCode.other_error
    message = ""

    def __str__(self):
        """Return a string representation of the exception."""
        super_msg = super().__str__()  # Don't do str(super())
        if self.message:
            return self.message.format(super_msg)
        return super_msg


class BadArgsError(ExitCodeException):
    """Invalid arguments on the command line or API."""

    exit_code = ExitCode.bad_args


class MissingDependencyError(ExitCodeException):
    """A third-party dependency is missing."""

    exit_code = ExitCode.missing_dependency


class UnsupportedImageFormatError(ExitCodeException):
    """The image format is not supported."""

    exit_code = ExitCode.input_file


class DpiError(ExitCodeException):
    """Missing information about input image DPI."""

    exit_code = ExitCode.input_file


class OutputFileAccessError(ExitCodeException):
    """Cannot access the intended output file path."""

    exit_code = ExitCode.file_access_error


class PriorOcrFoundError(ExitCodeException):
    """This file already has OCR."""

    exit_code = ExitCode.already_done_ocr


class InputFileError(ExitCodeException):
    """Something is wrong with the input file."""

    exit_code = ExitCode.input_file


class SubprocessOutputError(ExitCodeException):
    """A subprocess returned an unexpected error."""

    exit_code = ExitCode.child_process_error


class EncryptedPdfError(ExitCodeException):
    """Input PDF is encrypted."""

    exit_code = ExitCode.encrypted_pdf
    message = dedent(
        """\
        Input PDF is encrypted. The encryption must be removed to
        perform OCR.

        For information about this PDF's security use
            qpdf --show-encryption infilename

        You can remove the encryption using
            qpdf --decrypt [--password=[password]] infilename
        """
    )


class TesseractConfigError(ExitCodeException):
    """Tesseract config can't be parsed."""

    exit_code = ExitCode.invalid_config
    message = "Error occurred while parsing a Tesseract configuration file"
