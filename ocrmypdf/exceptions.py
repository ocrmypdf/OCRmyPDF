#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83


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
    pass


class PdfMergeFailedError(ExitCodeException):
    exit_code = ExitCode.input_file


class MissingDependencyError(ExitCodeException):
    exit_code = ExitCode.missing_dependency


class UnsupportedImageFormatError(ExitCodeException):
    exit_code = ExitCode.input_file


class DpiError(ExitCodeException):
    exit_code = ExitCode.input_file


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
