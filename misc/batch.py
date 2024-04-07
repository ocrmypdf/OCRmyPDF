#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2016 findingorder <https://github.com/findingorder>
# SPDX-FileCopyrightText: 2024 nilsro <https://github.com/nilsro>
# SPDX-License-Identifier: MIT

"""Example of using ocrmypdf as a library in a script.

This script will recursively search a directory for PDF files and run OCR on
them. It will log the results. It runs OCR on every file, even if it already
has text. OCRmyPDF will detect files that already have text.

You should edit this script to meet your needs.
"""

from __future__ import annotations

import logging
import sys
import os
import posixpath
import shutil
import filecmp
from pathlib import Path

import ocrmypdf

# pylint: disable=logging-format-interpolation
# pylint: disable=logging-not-lazy


def filecompare(a, b):
    try:
        return filecmp.cmp(a, b, shallow=True)
    except FileNotFoundError:
        return False


script_dir = Path(__file__).parent
# set archive_dir to a path for backup original documents. Leave empty if not required.
archive_dir = "/pdfbak"

if len(sys.argv) > 1:
    start_dir = Path(sys.argv[1])
else:
    start_dir = Path(".")

if len(sys.argv) > 2:
    log_file = Path(sys.argv[2])
else:
    log_file = script_dir.with_name("ocr-tree.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    filename=log_file,
    filemode="a",
)

logging.info(f"Start directory {start_dir}")

ocrmypdf.configure_logging(ocrmypdf.Verbosity.default)

for filename in start_dir.glob("**/*.pdf"):
    logging.info(f"Processing {filename}")
    if ocrmypdf.pdfa.file_claims_pdfa(filename)["pass"]:
        logging.info("Skipped document because it already contained text")
    else:
        archive_filename = archive_dir + str(filename)
        if len(archive_dir) > 0 and not filecompare(filename, archive_filename):
            logging.info(f"Archiving document to {archive_filename}")
            try:
                shutil.copy2(filename, posixpath.dirname(archive_filename))
            except IOError as io_err:
                os.makedirs(posixpath.dirname(archive_filename))
                shutil.copy2(filename, posixpath.dirname(archive_filename))
        try:
            result = ocrmypdf.ocr(filename, filename, deskew=True)
            logging.info(result)
        except ocrmypdf.exceptions.EncryptedPdfError:
            logging.info("Skipped document because it is encrypted")
        except ocrmypdf.exceptions.PriorOcrFoundError:
            logging.info("Skipped document because it already contained text")
        except ocrmypdf.exceptions.DigitalSignatureError:
            logging.info("Skipped document because it has a digital signature")
        except ocrmypdf.exceptions.TaggedPDFError:
            logging.info(
                "Skipped document because it does not need ocr as it is tagged"
            )
        except:
            logging.error("Unhandled error occured")
        logging.info("OCR complete")
