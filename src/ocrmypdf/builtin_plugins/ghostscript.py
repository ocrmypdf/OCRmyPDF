# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement PDF page rasterization and PDF/A production."""

from __future__ import annotations

import logging

from packaging.version import Version

from ocrmypdf import hookimpl
from ocrmypdf._exec import ghostscript
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import check_external_program

log = logging.getLogger(__name__)

# Currently all blacklisted versions are lower than 9.55, so none need to
# be added here. If a future version is blacklisted, add it here.
BLACKLISTED_GS_VERSIONS: frozenset[Version] = frozenset()


@hookimpl
def add_options(parser):
    gs = parser.add_argument_group("Ghostscript", "Advanced control of Ghostscript")
    gs.add_argument(
        '--color-conversion-strategy',
        action='store',
        type=str,
        metavar='STRATEGY',
        choices=ghostscript.COLOR_CONVERSION_STRATEGIES,
        default='LeaveColorUnchanged',
        help="Set Ghostscript color conversion strategy",
    )
    gs.add_argument(
        '--pdfa-image-compression',
        choices=['auto', 'jpeg', 'lossless'],
        default='auto',
        help="Specify how to compress images in the output PDF/A. 'auto' lets "
        "OCRmyPDF decide.  'jpeg' changes all grayscale and color images to "
        "JPEG compression.  'lossless' uses PNG-style lossless compression "
        "for all images.  Monochrome images are always compressed using a "
        "lossless codec.  Compression settings "
        "are applied to all pages, including those for which OCR was "
        "skipped.  Not supported for --output-type=pdf ; that setting "
        "preserves the original compression of all images.",
    )


@hookimpl
def check_options(options):
    """Check that the options are valid for this plugin."""
    check_external_program(
        program='gs',
        package='ghostscript',
        version_checker=ghostscript.version,
        need_version='9.54',  # RHEL 9's version; Ubuntu 22.04 has 9.55
    )
    gs_version = ghostscript.version()
    if gs_version in BLACKLISTED_GS_VERSIONS:
        raise MissingDependencyError(
            f"Ghostscript {gs_version} contains serious regressions and is not "
            "supported. Please upgrade to a newer version."
        )
    if Version('10.0.0') <= gs_version < Version('10.02.1') and (
        options.skip_text or options.redo_ocr
    ):
        raise MissingDependencyError(
            f"Ghostscript 10.0.0 through 10.02.0 (your version: {gs_version}) "
            "contain serious regressions that corrupt PDFs with existing text, "
            "such as those processed using --skip-text or --redo-ocr. "
            "Please upgrade to a "
            "newer version, or use --output-type pdf to avoid Ghostscript, or "
            "use --force-ocr to discard existing text."
        )

    if options.output_type == 'pdfa':
        options.output_type = 'pdfa-2'
    if options.color_conversion_strategy not in ghostscript.COLOR_CONVERSION_STRATEGIES:
        raise ValueError(
            f"Invalid color conversion strategy: {options.color_conversion_strategy}"
        )
    if options.pdfa_image_compression != 'auto' and not options.output_type.startswith(
        'pdfa'
    ):
        log.warning(
            "--pdfa-image-compression argument only applies when "
            "--output-type is one of 'pdfa', 'pdfa-1', or 'pdfa-2'"
        )


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
        stop_on_error=stop_on_soft_error,
    )
    return output_file


@hookimpl
def generate_pdfa(
    pdf_pages,
    pdfmark,
    output_file,
    context,
    pdf_version,
    pdfa_part,
    progressbar_class,
    stop_on_soft_error,
):
    """Generate a PDF/A from the list of PDF pages and PDF/A metadata."""
    ghostscript.generate_pdfa(
        pdf_pages=[*pdf_pages, pdfmark],
        output_file=output_file,
        compression=context.options.pdfa_image_compression,
        color_conversion_strategy=context.options.color_conversion_strategy,
        pdf_version=pdf_version,
        pdfa_part=pdfa_part,
        progressbar_class=progressbar_class,
        stop_on_error=stop_on_soft_error,
    )
    return output_file
