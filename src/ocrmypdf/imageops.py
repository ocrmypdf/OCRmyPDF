# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCR-related image manipulation."""

import logging
from math import ceil, floor, sqrt

from PIL import Image

log = logging.getLogger(__name__)


def bytes_per_pixel(mode: str) -> int:
    """
    Return the number of padded bytes per pixel for a given PIL image mode.

    In RGB mode we assume 4 bytes per pixel, which is the case for most
    consumers.
    """
    if mode in ('1', 'L', 'P'):
        return 1
    if mode in ('LA', 'PA', 'La') or mode.startswith('I;16'):
        return 2
    return 4


def calculate_downsample(
    image: Image.Image,
    *,
    max_size: tuple[int, int] | None = None,
    max_pixels: int | None = None,
    max_bytes: int | None = None,
) -> tuple[int, int]:
    """
    Calculate the new image size required to downsample an image to fit within
    the given limits.

    If no limit is exceeded, the input image's size is returned.

    Args:
        image: The image to downsample.
        max_size: The maximum width and height of the image.
        max_pixels: The maximum number of pixels in the image. Some image consumers
            limit the total number of pixels as some value other than width*height.
        max_bytes: The maximum number of bytes in the image. RGB is counted as 4
            bytes; all other modes are counted as 1 byte.
    """
    size = image.size

    if max_size is not None:
        major_axis = max(image.size)
        size_factor = max(max_size) / major_axis
        if size_factor < 1.0:
            log.debug("Resizing image to fit Tesseract image size limit")
            size = floor(size[0] * size_factor), floor(size[1] * size_factor)

    if max_pixels is not None:
        if size[0] * size[1] > max_pixels:
            log.debug("Resizing image to fit image pixel limit")
            pixels_factor = sqrt(max_pixels / (image.size[0] * image.size[1]))
            size = floor(size[0] * pixels_factor), floor(size[1] * pixels_factor)

    if max_bytes is not None:
        bpp = bytes_per_pixel(image.mode)
        # stride = bytes per line
        stride = size[0] * bpp
        height = size[1]
        if stride * height > max_bytes:
            log.debug("Resizing image to fit image byte size limit")
            bytes_factor = sqrt((max_bytes) / (stride * height))
            scaled_stride = floor(stride * bytes_factor)
            scaled_height = floor(height * bytes_factor)
            size = ceil(scaled_stride / bpp), scaled_height
            assert (size[0] * bpp * size[1]) <= max_bytes

    return size


def downsample_image(
    image: Image.Image,
    new_size: tuple[int, int],
    *,
    resample_mode: Image.Resampling = Image.Resampling.BICUBIC,
    reducing_gap: int = 3,
) -> Image.Image:
    """
    Downsample an image to fit within the given limits.

    The DPI is adjusted to match the new size, which is how we can ensure the
    OCR is positioned correctly.

    Args:
        image: The image to downsample
        scaling_factor: The scaling factor to apply to the image, calculated using
            calculate_downsample().
        resample_mode: The resampling mode to use when downsampling.
        reducing_gap: The reducing gap to use when downsampling (for larger
            reductions).
    """
    if new_size == image.size:
        return image

    original_size = image.size
    original_dpi = image.info['dpi']
    image = image.resize(
        new_size,
        resample=resample_mode,
        reducing_gap=reducing_gap,
    )
    image.info['dpi'] = (
        round(original_dpi[0] * new_size[0] / original_size[0]),
        round(original_dpi[1] * new_size[1] / original_size[1]),
    )
    log.debug(f"Rescaled image to {image.size} pixels and {image.info['dpi']} dpi")
    return image
