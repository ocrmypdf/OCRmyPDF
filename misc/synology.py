#!/bin/env python3
# Contributed by github.com/Enantiomerie

# This script must be edited to meet your needs.

import logging
import os
import shutil
import subprocess
import sys
import time

# pylint: disable=logging-format-interpolation
# pylint: disable=logging-not-lazy

script_dir = os.path.dirname(os.path.realpath(__file__))
timestamp = time.strftime("%Y-%m-%d-%H%M_")
log_file = script_dir + '/' + timestamp + 'ocrmypdf.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    filename=log_file,
    filemode='w',
)

if len(sys.argv) > 1:
    start_dir = sys.argv[1]
else:
    start_dir = '.'

for dir_name, subdirs, file_list in os.walk(start_dir):
    logging.info(dir_name)
    os.chdir(dir_name)
    for filename in file_list:
        file_stem, file_ext = os.path.splitext(filename)
        if file_ext != '.pdf':
            continue
        full_path = os.path.join(dir_name, filename)
        timestamp_ocr = time.strftime("%Y-%m-%d-%H%M_OCR_")
        filename_ocr = timestamp_ocr + file_stem + '.pdf'
        # create string for pdf processing
        # the script is processed as root user via chron
        cmd = [
            'docker',
            'run',
            '--rm',
            '-i',
            'jbarlow83/ocrmypdf',
            '--deskew',
            '-',
            '-',
        ]
        logging.info(cmd)
        full_path_ocr = os.path.join(dir_name, filename_ocr)
        with open(filename, 'rb') as input_file, open(
            full_path_ocr, 'wb'
        ) as output_file:
            proc = subprocess.run(
                cmd,
                stdin=input_file,
                stdout=output_file,
                stderr=subprocess.PIPE,
                check=False,
            )
        logging.info(proc.stderr.read())
        os.chmod(full_path_ocr, 0o664)
        os.chmod(full_path, 0o664)
        full_path_ocr_archive = sys.argv[2]
        full_path_archive = sys.argv[2] + '/no_ocr'
        shutil.move(full_path_ocr, full_path_ocr_archive)
        shutil.move(full_path, full_path_archive)
logging.info('Finished.\n')
