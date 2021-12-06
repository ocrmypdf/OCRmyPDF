# © 2021 James R. Barlow: github.com/jbarlow83
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# type: ignore

"""Tesseract no-op plugin that simulates the OOM killer on page 4.

OCRmyPDF can use a lot of memory, even that it might trigger the
OOM killer on Linux or similar features on other platforms. We want to
ensure we fail with an error rather than deadlock in such cases.

Page 4 was chosen because of this number's association with bad luck
in many East Asian cultures.
"""

import os
import signal
import sys
from pathlib import Path

from ocrmypdf import hookimpl

# Ugly hack that let us use the NoopOcrEngine without setting up packaging for our
# tests.
# This hack also requires us to set type: ignore
parent_file = Path(__file__).with_name('tesseract_noop.py')
parent = compile(parent_file.read_text(), parent_file, mode='exec')
exec(parent)
NoopOcrEngine = locals()['NoopOcrEngine']


class Page4Engine(NoopOcrEngine):
    def __str__(self):
        return f"NO-OP Page 4 {NoopOcrEngine.version()}"

    @staticmethod
    def generate_hocr(input_file: Path, output_hocr, output_text, options):
        if input_file.stem.startswith('000004'):
            # Suicide
            os.kill(os.getpid(), signal.SIGKILL)
        else:
            return NoopOcrEngine.generate_hocr(
                input_file, output_hocr, output_text, options
            )

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        if input_file.stem.startswith('000004'):
            # Suicide
            os.kill(os.getpid(), signal.SIGKILL)
        else:
            return NoopOcrEngine.generate_pdf(
                input_file, output_pdf, output_text, options
            )


@hookimpl
def check_options(options):
    if options.use_threads:
        raise ValueError("I'm not compatible with use_threads")


@hookimpl
def get_ocr_engine():
    return Page4Engine()
