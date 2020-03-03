#!/usr/bin/env python3
# Original version by DeliciousPickle@github; modified

# This script must be edited to meet your needs.

import logging
import os
import sys

import ocrmypdf

# pylint: disable=logging-format-interpolation
# pylint: disable=logging-not-lazy

script_dir = os.path.dirname(os.path.realpath(__file__))
print(script_dir + '/batch.py: Start')

if len(sys.argv) > 1:
    start_dir = sys.argv[1]
else:
    start_dir = '.'

if len(sys.argv) > 2:
    log_file = sys.argv[2]
else:
    log_file = script_dir + '/ocr-tree.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    filename=log_file,
    filemode='w',
)

ocrmypdf.configure_logging(ocrmypdf.Verbosity.default)

for dir_name, subdirs, file_list in os.walk(start_dir):
    logging.info(dir_name + '\n')
    os.chdir(dir_name)
    for filename in file_list:
        file_ext = os.path.splitext(filename)[1]
        if file_ext == '.pdf':
            full_path = dir_name + '/' + filename
            print(full_path)
            result = ocrmypdf.ocr(filename, filename, deskew=True)
            if result == ocrmypdf.ExitCode.already_done_ocr:
                print("Skipped document because it already contained text")
            elif result == ocrmypdf.ExitCode.ok:
                print("OCR complete")
            logging.info(result)
