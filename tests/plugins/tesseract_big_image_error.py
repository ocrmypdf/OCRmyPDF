# © 2020 James R. Barlow: github.com/jbarlow83
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

from subprocess import CalledProcessError
from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOcrEngine


def raise_size_exception(*args, **kwargs):
    raise CalledProcessError(
        1,
        'tesseract',
        output=b"Image too large: (33830, 14959)\nError during processing.",
        stderr=b"",
    )


class BigImageErrorOcrEngine(TesseractOcrEngine):
    @staticmethod
    def get_orientation(input_file, options):
        with patch('ocrmypdf._exec.tesseract.run', new=raise_size_exception):
            return TesseractOcrEngine.get_orientation(input_file, options)

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        with patch('ocrmypdf._exec.tesseract.run', new=raise_size_exception):
            TesseractOcrEngine.generate_hocr(
                input_file, output_hocr, output_text, options
            )

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        with patch('ocrmypdf._exec.tesseract.run', new=raise_size_exception):
            TesseractOcrEngine.generate_pdf(
                input_file, output_pdf, output_text, options
            )


@hookimpl
def get_ocr_engine():
    return BigImageErrorOcrEngine()
