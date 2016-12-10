from enum import IntEnum
import os
import pkg_resources

PROGRAM_NAME = 'ocrmypdf'

VERSION = pkg_resources.get_distribution('ocrmypdf').version


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
    other_error = 15
    ctrl_c = 130


def page_number(input_file):
    return int(os.path.basename(input_file)[0:6])


