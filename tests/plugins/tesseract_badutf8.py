# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT

"""Tesseract bad utf8.

In some cases, some versions of Tesseract can output binary gibberish or data
that is not UTF-8 compatible, so we are forced to check that we can convert it
and present it to the user.
"""

from __future__ import annotations

from contextlib import contextmanager
from subprocess import CalledProcessError
from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOcrEngine


def bad_utf8(*args, **kwargs):
    raise CalledProcessError(
        1,
        'tesseract',
        output=b'\x96\xb3\x8c\xf8\x82\xc8UTF-8\x0a',  # "Invalid UTF-8" in Shift JIS
        stderr=b"",
    )


@contextmanager
def patch_tesseract_run():
    with patch('ocrmypdf._exec.tesseract.run') as mock:
        mock.side_effect = bad_utf8
        yield
        mock.assert_called()


class BadUtf8OcrEngine(TesseractOcrEngine):
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
    return BadUtf8OcrEngine()
