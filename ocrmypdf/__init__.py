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
    child_process_error = 7
    other_error = 15


def get_program(name):
    envvar = 'OCRMYPDF_' + name.upper()
    return os.environ.get(envvar, name)


def page_number(input_file):
    return int(os.path.basename(input_file)[0:6])
