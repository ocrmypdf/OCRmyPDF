# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT

from __future__ import annotations

from subprocess import CalledProcessError
from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins import ghostscript


def raise_gs_fail(*args, **kwargs):
    raise CalledProcessError(
        1, 'gs', output=b"", stderr=b"ERROR: Casper is not a friendly ghost"
    )


@hookimpl
def generate_pdfa(pdf_pages, pdfmark, output_file, compression, pdf_version, pdfa_part):
    with patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as mock:
        mock.side_effect = raise_gs_fail
        ghostscript.generate_pdfa(
            pdf_pages=pdf_pages,
            pdfmark=pdfmark,
            output_file=output_file,
            compression=compression,
            pdf_version=pdf_version,
            pdfa_part=pdfa_part,
            progressbar_class=None,
        )
        mock.assert_called()
        return output_file
