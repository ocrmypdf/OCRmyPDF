# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement PDF page rasterization using pypdfium2."""

from __future__ import annotations

import logging
from pathlib import Path

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

from ocrmypdf import hookimpl
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.helpers import Resolution

log = logging.getLogger(__name__)


@hookimpl
def check_options(options):
    """Check that pypdfium2 is available if explicitly requested."""
    if options.rasterizer == 'pypdfium' and pdfium is None:
        raise MissingDependencyError(
            "The --rasterizer pypdfium option requires the pypdfium2 package. "
            "Install it with: pip install pypdfium2"
        )


def _open_pdf_document(input_file: Path):
    """Open a PDF document using pypdfium2."""
    assert pdfium is not None, "pypdfium2 must be available to call this function"
    return pdfium.PdfDocument(input_file)


def _render_page_to_bitmap(
    page, raster_device: str, raster_dpi: Resolution, rotation: int | None
):
    """Render a PDF page to a bitmap."""
    # Calculate the scale factor based on DPI
    # pypdfium2 uses points (72 DPI) as base unit
    scale = raster_dpi.to_scalar() / 72.0

    # Apply rotation if specified
    if rotation:
        # pypdfium2 rotation is in degrees, same as our input
        page.set_rotation(rotation)

    # Render the page to a bitmap
    # The scale parameter controls the resolution
    grayscale = raster_device.lower() in ('pnggray', 'jpeggray')

    bitmap = page.render(
        scale=scale,
        rotation=0,  # We already set rotation on the page
        may_draw_forms=True,
        draw_annots=True,
        grayscale=grayscale,
        # Note: pypdfium2 doesn't have a direct equivalent to filter_vector
        # This would require more complex implementation if needed
    )
    return bitmap


def _process_image_for_output(
    pil_image,
    raster_device: str,
    raster_dpi: Resolution,
    page_dpi: Resolution | None,
    stop_on_soft_error: bool,
):
    """Process PIL image for output format and set DPI metadata."""
    # Set the DPI metadata if page_dpi is specified
    if page_dpi:
        # PIL expects DPI as a tuple
        dpi_tuple = (float(page_dpi.x), float(page_dpi.y))
        pil_image.info['dpi'] = dpi_tuple
    else:
        # Use the raster DPI
        dpi_tuple = (float(raster_dpi.x), float(raster_dpi.y))
        pil_image.info['dpi'] = dpi_tuple

    # Determine output format based on raster_device
    if raster_device.lower() in ('png', 'pngmono', 'pnggray', 'png16m', 'pngalpha'):
        format_name = 'PNG'
    elif raster_device.lower() in ('jpeg', 'jpeggray', 'jpg'):
        format_name = 'JPEG'
        # Convert RGBA to RGB for JPEG
        if pil_image.mode == 'RGBA':
            # Create white background
            background = pil_image.new('RGB', pil_image.size, (255, 255, 255))
            background.paste(
                pil_image, mask=pil_image.split()[-1]
            )  # Use alpha channel as mask
            pil_image = background
    elif raster_device.lower() in ('tiff', 'tif'):
        format_name = 'TIFF'
    else:
        # Default to PNG for unknown formats
        format_name = 'PNG'
        if stop_on_soft_error:
            raise ValueError(f"Unsupported raster device: {raster_device}")
        else:
            log.warning(f"Unsupported raster device {raster_device}, using PNG")

    return pil_image, format_name


def _save_image(pil_image, output_file: Path, format_name: str):
    """Save PIL image to file with appropriate DPI metadata."""
    save_kwargs = {}
    if format_name in ('PNG', 'TIFF') and 'dpi' in pil_image.info:
        save_kwargs['dpi'] = pil_image.info['dpi']
    elif format_name == 'JPEG' and 'dpi' in pil_image.info:
        save_kwargs['dpi'] = pil_image.info['dpi']

    pil_image.save(output_file, format=format_name, **save_kwargs)


@hookimpl
def rasterize_pdf_page(
    input_file: Path,
    output_file: Path,
    raster_device: str,
    raster_dpi: Resolution,
    pageno: int,
    page_dpi: Resolution | None,
    rotation: int | None,
    filter_vector: bool,
    stop_on_soft_error: bool,
    options,
) -> Path | None:
    """Rasterize a single page of a PDF file using pypdfium2.

    Returns None if pypdfium2 is not available or if the user has selected
    a different rasterizer, allowing Ghostscript to be used.
    """
    # Check if user explicitly requested a different rasterizer
    if options is not None and options.rasterizer == 'ghostscript':
        return None  # Let Ghostscript handle it

    if pdfium is None:
        return None  # Fall back to Ghostscript

    # Open the PDF document
    pdf = _open_pdf_document(input_file)

    try:
        # Get the specific page (pypdfium2 uses 0-based indexing)
        page = pdf[pageno - 1]

        try:
            # Render the page to a bitmap
            bitmap = _render_page_to_bitmap(page, raster_device, raster_dpi, rotation)

            try:
                # Convert to PIL Image
                pil_image = bitmap.to_pil()

                # Process image for output format and DPI
                pil_image, format_name = _process_image_for_output(
                    pil_image, raster_device, raster_dpi, page_dpi, stop_on_soft_error
                )

                _save_image(pil_image, output_file, format_name)

            finally:
                bitmap.close()
        finally:
            page.close()
    finally:
        pdf.close()

    return output_file
