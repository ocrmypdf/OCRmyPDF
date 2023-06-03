# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins import ghostscript
from ocrmypdf.subprocess import run


def fail_if_stoponerror(args, **kwargs):
    if '-dPDFSTOPONERROR' in args:
        raise CalledProcessError(1, 'gs', output=b"", stderr=b"PDF STOP ON ERROR")
    return run(args, **kwargs)


@hookimpl
def rasterize_pdf_page(
    input_file,
    output_file,
    raster_device,
    raster_dpi,
    pageno,
    page_dpi,
    rotation,
    filter_vector,
    stop_on_soft_error,
) -> Path:
    with patch('ocrmypdf._exec.ghostscript.run') as mock:
        mock.side_effect = fail_if_stoponerror
        ghostscript.rasterize_pdf_page(
            input_file=input_file,
            output_file=output_file,
            raster_device=raster_device,
            raster_dpi=raster_dpi,
            pageno=pageno,
            page_dpi=page_dpi,
            rotation=rotation,
            filter_vector=filter_vector,
            stop_on_soft_error=stop_on_soft_error,
        )
        mock.assert_called()
        return output_file
