from enum import IntEnum


class ExitCode(IntEnum):
    bad_args = 1
    input_file = 2
    missing_dependency = 3
    invalid_output_pdfa = 4
    file_access_error = 5
    already_done_ocr = 6
    other_error = 15
