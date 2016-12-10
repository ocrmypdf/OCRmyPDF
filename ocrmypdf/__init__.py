import os
import pkg_resources

PROGRAM_NAME = 'ocrmypdf'

VERSION = pkg_resources.get_distribution('ocrmypdf').version


def page_number(input_file):
    return int(os.path.basename(input_file)[0:6])
