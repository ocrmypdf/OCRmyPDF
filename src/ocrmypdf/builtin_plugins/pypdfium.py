# SPDX-FileCopyrightText: 2024 James R. Barlow
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
    """Check that pypdfium2 is available."""
    if pdfium is None:
        raise MissingDependencyError(
            "pypdfium2 is required for this plugin. Install it with: pip install pypdfium2"
        )


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
) -> Path:
    """Rasterize a single page of a PDF file using pypdfium2."""
    if pdfium is None:
        raise MissingDependencyError("pypdfium2 is not available")
    
    # Open the PDF document
    pdf = pdfium.PdfDocument(input_file)
    
    try:
        # Get the specific page (pypdfium2 uses 0-based indexing)
        page = pdf.get_page(pageno - 1)
        
        try:
            # Calculate the scale factor based on DPI
            # pypdfium2 uses points (72 DPI) as base unit
            scale = float(raster_dpi.x) / 72.0
            
            # Apply rotation if specified
            if rotation:
                # pypdfium2 rotation is in degrees, same as our input
                page.set_rotation(rotation)
            
            # Render the page to a bitmap
            # The scale parameter controls the resolution
            bitmap = page.render(
                scale=scale,
                rotation=0,  # We already set rotation on the page
                crop=None,
                may_draw_forms=True,
                may_draw_annots=True,
                # Note: pypdfium2 doesn't have a direct equivalent to filter_vector
                # This would require more complex implementation if needed
            )
            
            try:
                # Convert to PIL Image
                pil_image = bitmap.to_pil()
                
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
                if raster_device.lower() in ('png', 'png16m', 'pngalpha'):
                    format_name = 'PNG'
                elif raster_device.lower() in ('jpeg', 'jpg'):
                    format_name = 'JPEG'
                    # Convert RGBA to RGB for JPEG
                    if pil_image.mode == 'RGBA':
                        # Create white background
                        background = pil_image.new('RGB', pil_image.size, (255, 255, 255))
                        background.paste(pil_image, mask=pil_image.split()[-1])  # Use alpha channel as mask
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
                
                # Save the image
                save_kwargs = {}
                if format_name in ('PNG', 'TIFF') and 'dpi' in pil_image.info:
                    save_kwargs['dpi'] = pil_image.info['dpi']
                elif format_name == 'JPEG' and 'dpi' in pil_image.info:
                    save_kwargs['dpi'] = pil_image.info['dpi']
                
                pil_image.save(output_file, format=format_name, **save_kwargs)
                
            finally:
                bitmap.close()
        finally:
            page.close()
    finally:
        pdf.close()
    
    return output_file
