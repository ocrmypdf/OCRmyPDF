# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT
from __future__ import annotations

import signal
from contextlib import contextmanager
from subprocess import CalledProcessError
from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOcrEngine


def raise_crash(*args, **kwargs):
    raise CalledProcessError(
        128 + signal.SIGABRT,
        'tesseract',
        output=b"",
        stderr=b"libc++abi.dylib: terminating with uncaught exception of type "
        + b"std::bad_alloc: std::bad_alloc",
    )


@contextmanager
def patch_tesseract_run():
    with patch('ocrmypdf._exec.tesseract.run') as mock:
        mock.side_effect = raise_crash
        yield
        mock.assert_called()


class CrashOcrEngine(TesseractOcrEngine):
    @staticmethod
    def get_orientation(input_file, options):
        with patch_tesseract_run():
            return TesseractOcrEngine.get_orientation(input_file, options)

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        with patch_tesseract_run():
            TesseractOcrEngine.generate_hocr(
                input_file, output_hocr, output_text, options
            )

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        with patch_tesseract_run():
            TesseractOcrEngine.generate_pdf(
                input_file, output_pdf, output_text, options
            )


@hookimpl
def get_ocr_engine():
    return CrashOcrEngine()
