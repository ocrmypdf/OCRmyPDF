# © 2016 James R. Barlow: github.com/jbarlow83
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


from enum import IntEnum

class ExitCode(IntEnum):
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
    other_error = 15
    ctrl_c = 130


class ExitCodeException(Exception):
    exit_code = ExitCode.other_error


class BadArgsError(ExitCodeException):
    exit_code = ExitCode.bad_args


class PdfMergeFailedError(ExitCodeException):
    exit_code = ExitCode.input_file


class MissingDependencyError(ExitCodeException):
    exit_code = ExitCode.missing_dependency


class UnsupportedImageFormatError(ExitCodeException):
    exit_code = ExitCode.input_file


class DpiError(ExitCodeException):
    exit_code = ExitCode.input_file


class OutputFileAccessError(ExitCodeException):
    exit_code = ExitCode.file_access_error


class PriorOcrFoundError(ExitCodeException):
    exit_code = ExitCode.already_done_ocr


class InputFileError(ExitCodeException):
    exit_code = ExitCode.input_file


class SubprocessOutputError(ExitCodeException):
    exit_code = ExitCode.child_process_error


class EncryptedPdfError(ExitCodeException):
    exit_code = ExitCode.encrypted_pdf


class TesseractConfigError(ExitCodeException):
    exit_code = ExitCode.invalid_config
