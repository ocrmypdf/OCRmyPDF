#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2016 findingorder <https://github.com/findingorder>
# SPDX-License-Identifier: MIT

from __future__ import annotations

# This script must be edited to meet your needs.
import logging
import os
import sys
from pathlib import Path

import ocrmypdf

# pylint: disable=logging-format-interpolation
# pylint: disable=logging-not-lazy

script_dir = Path(__file__).parent

if len(sys.argv) > 1:
    start_dir = Path(sys.argv[1])
else:
    start_dir = Path('.')

if len(sys.argv) > 2:
    log_file = Path(sys.argv[2])
else:
    log_file = script_dir.with_name('ocr-tree.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    filename=log_file,
    filemode='a',
)

ocrmypdf.configure_logging(ocrmypdf.Verbosity.default)

for filename in start_dir.glob("**/*.py"):
    logging.info(f"Processing {filename}")
    result = ocrmypdf.ocr(filename, filename, deskew=True)
    if result == ocrmypdf.ExitCode.already_done_ocr:
        logging.error("Skipped document because it already contained text")
    elif result == ocrmypdf.ExitCode.ok:
        logging.info("OCR complete")
    logging.info(result)
