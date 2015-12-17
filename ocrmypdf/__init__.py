from enum import IntEnum
import os


class ExitCode(IntEnum):
    ok = 0
    bad_args = 1
    input_file = 2
    missing_dependency = 3
    invalid_output_pdfa = 4
    file_access_error = 5
    already_done_ocr = 6
    other_error = 15


def get_program(name):
    envvar = 'OCRMYPDF_' + name.upper()
    return os.environ.get(envvar, name)
