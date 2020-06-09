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

from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins import ghostscript
from ocrmypdf.subprocess import run

elision_warning = """GPL Ghostscript 9.20: Setting Overprint Mode to 1
not permitted in PDF/A-2, overprint mode not set"""


def run_append_stderr(*args, **kwargs):
    proc = run(*args, **kwargs)
    proc.stderr = b'\n'.join([proc.stderr, elision_warning.encode('utf-8')])
    return proc


@hookimpl
def generate_pdfa(pdf_pages, pdfmark, output_file, compression, pdf_version, pdfa_part):
    with patch('ocrmypdf._exec.ghostscript.run', new=run_append_stderr):
        ghostscript.generate_pdfa(
            pdf_pages=pdf_pages,
            pdfmark=pdfmark,
            output_file=output_file,
            compression=compression,
            pdf_version=pdf_version,
            pdfa_part=pdfa_part,
        )
        return output_file
