# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCR-related image manipulation."""

import logging
from math import ceil, sqrt

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
) -> float:
    """
    Calculate the scaling factor required to downsample an image to fit within
    the given limits.

    If no limit is exceeded, 1.0 is returned.

    Args:
        image: The image to downsample.
        max_size: The maximum width and height of the image.
        max_pixels: The maximum number of pixels in the image. Some image consumers
            limit the total number of pixels as some value other than width*height.
        max_bytes: The maximum number of bytes in the image. RGB is counted as 4
            bytes; all other modes are counted as 1 byte.
    """
    scaling_factor = 1.0

    if max_size is not None:
        major_axis = max(image.size)
        if major_axis > max(max_size):
            log.debug("Resizing image to fit Tesseract image size limit")
            scaling_factor = max(max_size) / major_axis

    if max_pixels is not None:
        if image.size[0] * image.size[1] * scaling_factor * scaling_factor > max_pixels:
            log.debug("Resizing image to fit image pixel limit")
            scaling_factor *= sqrt(
                max_pixels / (image.size[0] * image.size[1] * scaling_factor)
            )

    if max_bytes is not None:
        bpp = bytes_per_pixel(image.mode)
        # stride = bytes per line
        stride = ceil(image.size[0] * scaling_factor) * bpp
        height = ceil(image.size[1] * scaling_factor)
        size = stride * height
        if size > max_bytes:
            log.debug("Resizing image to fit image byte size limit")
            scaling_factor *= sqrt((max_bytes - 1) / size)
            scaled_bytes_per_line = ceil(image.size[0] * scaling_factor) * bpp
            height = ceil(image.size[1] * scaling_factor)
            size = scaled_bytes_per_line * height
            assert size <= max_bytes, f"{size} > {max_bytes}"

    return scaling_factor


def downsample_image(
    image: Image.Image,
    scaling_factor: float,
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
    if scaling_factor == 1.0:
        return image
    if scaling_factor > 1.0 or scaling_factor <= 0:
        raise ValueError("scaling_factor must be <= 1.0 and > 0")

    original_dpi = image.info['dpi']
    image = image.resize(
        (
            ceil(image.size[0] * scaling_factor),
            ceil(image.size[1] * scaling_factor),
        ),
        resample=resample_mode,
        reducing_gap=reducing_gap,
    )
    image.info['dpi'] = (
        original_dpi[0] * scaling_factor,
        original_dpi[1] * scaling_factor,
    )
    log.debug(f"Rescaled image to {image.size} pixels and {image.info['dpi']} dpi")
    return image
