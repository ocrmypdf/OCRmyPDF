from enum import IntEnum
import os
from collections.abc import Iterable
import pkg_resources

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


def get_program(name):
    envvar = 'OCRMYPDF_' + name.upper()
    return os.environ.get(envvar, name)


def page_number(input_file):
    return int(os.path.basename(input_file)[0:6])


def is_iterable_notstr(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, str)

