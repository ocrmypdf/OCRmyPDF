# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MIT
"""Test plugin that deliberately writes garbage to stdout.

Used to verify that OCRmyPDF's stdout protection diverts stray writes (from
plugins or libraries) to stderr, so that a PDF written to stdout is never
corrupted. Pollutes at three points: plugin import (main process), the
``validate`` hook (main process), and the ``filter_ocr_image`` hook (worker
process/thread).
"""

from __future__ import annotations

import os
import sys

from ocrmypdf import hookimpl

POLLUTION = b'POLLUTION'


def _pollute(where: bytes) -> None:
    # Write to file descriptor 1 directly (as a careless C library might) and
    # via Python's sys.stdout (as a stray print() might).
    os.write(1, POLLUTION + b'-fd1-' + where + b'\n')
    print(POLLUTION.decode() + '-stdout-' + where.decode())
    sys.stdout.flush()


# Pollute at import time, which happens while plugins are being loaded.
_pollute(b'import')


@hookimpl
def validate(pdfinfo, options):
    _pollute(b'validate')


@hookimpl
def filter_ocr_image(page, image):
    _pollute(b'filter_ocr_image')
    return image
