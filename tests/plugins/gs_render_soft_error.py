# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT

from __future__ import annotations

from subprocess import CalledProcessError
from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins import ghostscript
from ocrmypdf.subprocess import run_polling_stderr


def fail_if_stoponerror(args, **kwargs):
    if '-dPDFSTOPONERROR' in args:
        raise CalledProcessError(1, 'gs', output=b"", stderr=b"PDF STOP ON ERROR")
    return run_polling_stderr(args, **kwargs)


@hookimpl
def generate_pdfa(
    pdf_pages,
    pdfmark,
    output_file,
    context,
    pdf_version,
    pdfa_part,
    stop_on_soft_error,
):
    with patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as mock:
        mock.side_effect = fail_if_stoponerror
        ghostscript.generate_pdfa(
            pdf_pages=pdf_pages,
            pdfmark=pdfmark,
            output_file=output_file,
            context=context,
            pdf_version=pdf_version,
            pdfa_part=pdfa_part,
            progressbar_class=None,
            stop_on_soft_error=stop_on_soft_error,
        )
        mock.assert_called()
        return output_file
