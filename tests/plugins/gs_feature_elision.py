# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins import ghostscript
from ocrmypdf.subprocess import run_polling_stderr

ELISION_WARNING = """GPL Ghostscript 9.50: Setting Overprint Mode to 1
not permitted in PDF/A-2, overprint mode not set"""


def run_append_stderr(*args, **kwargs):
    proc = run_polling_stderr(*args, **kwargs)
    proc.stderr += '\n' + ELISION_WARNING + '\n'
    return proc


@hookimpl
def generate_pdfa(pdf_pages, pdfmark, output_file, context, pdf_version, pdfa_part):
    with patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as mock:
        mock.side_effect = run_append_stderr
        ghostscript.generate_pdfa(
            pdf_pages=pdf_pages,
            pdfmark=pdfmark,
            output_file=output_file,
            context=context,
            pdf_version=pdf_version,
            pdfa_part=pdfa_part,
            progressbar_class=None,
            stop_on_soft_error=True,
        )
        mock.assert_called_once()
    return output_file
