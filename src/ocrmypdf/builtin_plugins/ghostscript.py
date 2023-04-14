# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement PDF page rasterization and PDF/A production."""

from __future__ import annotations

import logging

from ocrmypdf import hookimpl
from ocrmypdf._exec import ghostscript
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import check_external_program

log = logging.getLogger(__name__)


@hookimpl
def check_options(options):
    """Check that the options are valid for this plugin."""
    check_external_program(
        program='gs',
        package='ghostscript',
        version_checker=ghostscript.version,
        need_version='9.50',  # Ubuntu 20.04's version
    )
    gs_version = ghostscript.version()
    if gs_version in ('9.51',):
        raise MissingDependencyError(
            f"Ghostscript {gs_version} contains serious regressions and is not "
            "supported. Please upgrade to a newer version, or downgrade to the "
            "previous version."
        )

    if options.output_type == 'pdfa':
        options.output_type = 'pdfa-2'


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
):
    """Rasterize a single page of a PDF file using Ghostscript."""
    ghostscript.rasterize_pdf(
        input_file,
        output_file,
        raster_device=raster_device,
        raster_dpi=raster_dpi,
        pageno=pageno,
        page_dpi=page_dpi,
        rotation=rotation,
        filter_vector=filter_vector,
    )
    return output_file


@hookimpl
def generate_pdfa(
    pdf_pages,
    pdfmark,
    output_file,
    compression,
    pdf_version,
    pdfa_part,
    progressbar_class,
):
    """Generate a PDF/A from the list of PDF pages and PDF/A metadata."""
    ghostscript.generate_pdfa(
        pdf_pages=[*pdf_pages, pdfmark],
        output_file=output_file,
        compression=compression,
        pdf_version=pdf_version,
        pdfa_part=pdfa_part,
        progressbar_class=progressbar_class,
    )
    return output_file
