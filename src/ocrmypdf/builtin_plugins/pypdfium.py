# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement PDF page rasterization using pypdfium2."""

from __future__ import annotations

import logging
import threading
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import pypdfium2 as pdfium
else:
    try:
        import pypdfium2 as pdfium
    except ImportError:
        pdfium = None
from PIL import Image, ImageColor

from ocrmypdf import hookimpl
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.helpers import Resolution

log = logging.getLogger(__name__)

# pypdfium2/PDFium is not thread-safe. All calls to the library must be serialized.
# See: https://pypdfium2.readthedocs.io/en/stable/python_api.html#incompatibility-with-threading
# When using process-based parallelism (use_threads=False), each process has its own
# pdfium instance, so locking is not needed across processes.
_pdfium_lock = threading.Lock()


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


def _expand_cropbox_to_mediabox(page) -> None:
    """Set the page's CropBox to its MediaBox so PDFium renders the full page.

    PDFium renders to the CropBox by default. Negative ``crop`` values to
    ``render()`` are not supported and only pad the output canvas without
    expanding the rendered area — content outside the CropBox is clipped.
    The supported approach is to widen the CropBox in memory before rendering.
    The document is never saved back to disk, so this mutation is local.
    See https://github.com/ocrmypdf/OCRmyPDF/issues/1685.
    """
    mediabox = page.get_mediabox()  # (left, bottom, right, top)
    page.set_cropbox(*mediabox)


@dataclass(frozen=True, slots=True)
class _RenderedBitmap:
    """A rendered page, and the size in pixels it is expected to have."""

    bitmap: pdfium.PdfBitmap
    expected_width: int
    expected_height: int


@dataclass(frozen=True, slots=True)
class _OutputImage:
    """An image ready to save, and the format to save it in."""

    image: Image.Image
    format_name: Literal['PNG', 'TIFF', 'JPEG']


def _render_page_to_bitmap(
    page: pdfium.PdfPage,
    raster_device: str,
    raster_dpi: Resolution,
    rotation: int | None,
    use_cropbox: bool,
) -> _RenderedBitmap:
    """Render a PDF page to a bitmap."""
    # Round DPI to match Ghostscript's precision
    raster_dpi = raster_dpi.round(6)

    # Get page dimensions BEFORE applying rotation
    page_width_pts, page_height_pts = page.get_size()

    # Calculate expected output dimensions using separate x/y DPI
    expected_width = int(round(page_width_pts * raster_dpi.x / 72.0))
    expected_height = int(round(page_height_pts * raster_dpi.y / 72.0))

    # Calculate the scale factor based on DPI
    # pypdfium2 uses points (72 DPI) as base unit
    scale = raster_dpi.to_scalar() / 72.0

    # Apply rotation if specified
    if rotation:
        # pypdfium2 rotation is in degrees, same as our input
        # we track rotation in CCW, and pypdfium2 expects CW, so negate
        page.set_rotation(-rotation % 360)
        # When rotation is 90 or 270, dimensions are swapped in output
        if rotation % 180 == 90:
            expected_width, expected_height = expected_height, expected_width

    # Render the page to a bitmap
    # The scale parameter controls the resolution
    # Render in grayscale for mono and gray devices (better input for 1-bit conversion)
    grayscale = raster_device.lower() in (
        'pngmono',
        'pngmonod',
        'pnggray',
        'jpeggray',
    )

    # Default (use_cropbox=False) renders MediaBox for consistency with Ghostscript
    if not use_cropbox:
        _expand_cropbox_to_mediabox(page)

    bitmap = page.render(
        scale=scale,
        rotation=0,  # We already set rotation on the page
        may_draw_forms=True,
        draw_annots=True,
        grayscale=grayscale,
        # Note: pypdfium2 doesn't have a direct equivalent to filter_vector
        # This would require more complex implementation if needed
    )
    return _RenderedBitmap(bitmap, expected_width, expected_height)


# PIL image mode to build from each PDFium bitmap format. PDFium hands back
# little-endian pixels, so its BGR* formats are read with a matching raw decoder.
_BITMAP_MODE_TO_PIL = {
    'L': 'L',
    'BGR': 'RGB',
    'RGB': 'RGB',
    'BGRA': 'RGBA',
    'RGBA': 'RGBA',
    'BGRX': 'RGBX',
    'RGBX': 'RGBX',
}


def _bitmap_to_pil(
    bitmap: pdfium.PdfBitmap,
    expected_width: int | None,
    expected_height: int | None,
) -> Image.Image:
    """Copy a PDFium bitmap into a PIL image, trimming any rounding overshoot.

    PDFium's rendered size can exceed the size implied by the page dimensions and
    DPI by a pixel or two of rounding. Trimming while the pixels are copied out of
    PDFium is free -- the raw decoder walks the buffer a row at a time, so a
    narrower width just skips the tail of each row and a shorter height stops
    early. Correcting the size after the fact would instead allocate a third
    full-page buffer alongside the bitmap and the image copied out of it, which on
    a large page costs hundreds of megabytes.

    The returned image always owns its pixels. ``PdfBitmap.to_pil()`` lets PIL
    alias the bitmap's buffer for some formats -- grayscale renders among them --
    and PDFium frees that buffer when the bitmap is closed, so the caller must be
    able to close the bitmap without invalidating the image.
    """
    width, height = bitmap.width, bitmap.height
    if expected_width and expected_height:
        # Only trim overshoot; a shortfall is padded later, once the mode is known.
        if 0 < width - expected_width <= 2:
            width = expected_width
        if 0 < height - expected_height <= 2:
            height = expected_height

    mode = _BITMAP_MODE_TO_PIL.get(bitmap.mode)
    if mode is None:
        # Unrecognized format: let pypdfium2 work it out, and copy so that we own
        # the pixels even if it handed back a view on the bitmap's buffer.
        return bitmap.to_pil().copy()

    # frombytes() copies, unlike frombuffer(), which may alias bitmap.buffer.
    return Image.frombytes(
        mode, (width, height), bitmap.buffer, 'raw', bitmap.mode, bitmap.stride, 1
    )


def _white(mode: str) -> int | tuple[int, ...]:
    """Return the value that represents white in the given PIL mode."""
    if mode == '1':
        return 1
    if mode in ('L', 'P'):
        return 255
    if mode == 'RGB':
        return (255, 255, 255)
    if mode == 'RGBA':
        return (255, 255, 255, 255)
    return ImageColor.getcolor('white', mode)


def _fit_to_size(image: Image.Image, width: int, height: int) -> Image.Image:
    """Crop or white-pad an image to exactly ``width`` x ``height``.

    PDFium's rendered size can disagree with the size implied by the page
    dimensions and DPI by a pixel or two of rounding. Resampling the whole image
    to erase that discrepancy costs a full extra buffer plus a scratch buffer for
    the resampling filter -- on a 35 megapixel page that is hundreds of megabytes
    of peak memory, and it softens every pixel in the image to correct an error of
    a few thousandths of an inch. Copying the pixels into a canvas of the exact
    size crops the excess and pads any shortfall with white instead, leaving the
    pixels that survive untouched.
    """
    canvas = Image.new(image.mode, (width, height), _white(image.mode))
    if image.palette is not None:
        canvas.putpalette(image.palette)
    canvas.paste(image, (0, 0))  # paste clips whatever falls outside the canvas
    canvas.info = image.info.copy()
    return canvas


def _process_image_for_output(
    pil_image: Image.Image,
    raster_device: str,
    raster_dpi: Resolution,
    page_dpi: Resolution | None,
    stop_on_soft_error: bool,
    expected_width: int | None = None,
    expected_height: int | None = None,
) -> _OutputImage:
    """Process PIL image for output format and set DPI metadata."""
    # Correct dimensions if slightly off (within 2 pixels tolerance)
    if expected_width and expected_height:
        actual_width, actual_height = pil_image.width, pil_image.height
        width_diff = abs(actual_width - expected_width)
        height_diff = abs(actual_height - expected_height)

        # Only adjust if off by small amount (1-2 pixels)
        if (width_diff <= 2 or height_diff <= 2) and (
            width_diff > 0 or height_diff > 0
        ):
            log.debug(
                f"Adjusting rendered dimensions from "
                f"{actual_width}x{actual_height} to expected "
                f"{expected_width}x{expected_height}"
            )
            pil_image = _fit_to_size(pil_image, expected_width, expected_height)

    # Set the DPI metadata if page_dpi is specified
    if page_dpi:
        # PIL expects DPI as a tuple
        dpi_tuple = (float(page_dpi.x), float(page_dpi.y))
        pil_image.info['dpi'] = dpi_tuple
    else:
        # Use the raster DPI
        dpi_tuple = (float(raster_dpi.x), float(raster_dpi.y))
        pil_image.info['dpi'] = dpi_tuple

    # Convert image mode to match raster_device
    # This ensures pypdfium output matches Ghostscript's native device output
    raster_device_lower = raster_device.lower()

    if raster_device_lower in ('pngmono', 'pngmonod'):
        # Convert to 1-bit black and white (matches Ghostscript pngmono/pngmonod)
        if pil_image.mode != '1':
            if pil_image.mode not in ('L', '1'):
                pil_image = pil_image.convert('L')
            pil_image = pil_image.convert('1')
    elif raster_device_lower in ('pnggray', 'jpeggray'):
        # Convert to 8-bit grayscale
        if pil_image.mode not in ('L', '1'):
            pil_image = pil_image.convert('L')
    elif raster_device_lower == 'png256':
        # Convert to 8-bit indexed color (256 colors)
        if pil_image.mode != 'P':
            if pil_image.mode not in ('RGB', 'RGBA'):
                pil_image = pil_image.convert('RGB')
            pil_image = pil_image.quantize(colors=256)
    elif raster_device_lower in ('png16m', 'jpeg'):
        # Convert to RGB
        if pil_image.mode == 'RGBA':
            background = Image.new('RGB', pil_image.size, (255, 255, 255))
            background.paste(pil_image, mask=pil_image.split()[-1])
            pil_image = background
        elif pil_image.mode not in ('RGB',):
            pil_image = pil_image.convert('RGB')
    # pngalpha: keep RGBA as-is

    # Determine output format based on raster_device
    png_devices = (
        'png',
        'pngmono',
        'pngmonod',
        'pnggray',
        'png256',
        'png16m',
        'pngalpha',
    )
    format_name: Literal['PNG', 'TIFF', 'JPEG']
    if raster_device_lower in png_devices:
        format_name = 'PNG'
    elif raster_device_lower in ('jpeg', 'jpeggray', 'jpg'):
        format_name = 'JPEG'
    elif raster_device_lower in ('tiff', 'tif'):
        format_name = 'TIFF'
    else:
        # Default to PNG for unknown formats
        format_name = 'PNG'
        if stop_on_soft_error:
            raise ValueError(f"Unsupported raster device: {raster_device}")
        else:
            log.warning(f"Unsupported raster device {raster_device}, using PNG")

    return _OutputImage(pil_image, format_name)


def _save_image(pil_image: Image.Image, output_file: Path, format_name: str) -> None:
    """Save PIL image to file with appropriate DPI metadata."""
    save_kwargs = {}
    if (
        format_name in ('PNG', 'TIFF')
        and 'dpi' in pil_image.info
        or format_name == 'JPEG'
        and 'dpi' in pil_image.info
    ):
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
    use_cropbox: bool,
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

    log.debug("Rasterizing page %d with the pypdfium2 rasterizer", pageno)

    # Acquire lock to ensure thread-safe access to pypdfium2
    with (
        _pdfium_lock,
        closing(_open_pdf_document(input_file)) as pdf,
        closing(pdf[pageno - 1]) as page,
    ):
        # Render the page to a bitmap
        rendered = _render_page_to_bitmap(
            page, raster_device, raster_dpi, rotation, use_cropbox
        )
        with closing(rendered.bitmap):
            # Convert to PIL Image, which must own its pixels because closing the
            # bitmap frees the buffer PIL would otherwise alias.
            pil_image = _bitmap_to_pil(
                rendered.bitmap, rendered.expected_width, rendered.expected_height
            )

    # Process and save image outside the lock (PIL operations are thread-safe)
    output = _process_image_for_output(
        pil_image,
        raster_device,
        raster_dpi,
        page_dpi,
        stop_on_soft_error,
        rendered.expected_width,
        rendered.expected_height,
    )

    _save_image(output.image, output_file, output.format_name)

    return output_file
