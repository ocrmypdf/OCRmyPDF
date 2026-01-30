# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""PDF type definitions and constants."""

from __future__ import annotations

from enum import Enum, auto


class Colorspace(Enum):
    """Description of common image colorspaces in a PDF."""

    # pylint: disable=invalid-name
    gray = auto()
    rgb = auto()
    cmyk = auto()
    lab = auto()
    icc = auto()
    index = auto()
    sep = auto()
    devn = auto()
    pattern = auto()
    jpeg2000 = auto()


class Encoding(Enum):
    """Description of common image encodings in a PDF."""

    # pylint: disable=invalid-name
    ccitt = auto()
    jpeg = auto()
    jpeg2000 = auto()
    jbig2 = auto()
    asciihex = auto()
    ascii85 = auto()
    lzw = auto()
    flate = auto()
    runlength = auto()
    flate_jpeg = auto()


FloatRect = tuple[float, float, float, float]

FRIENDLY_COLORSPACE: dict[str, Colorspace] = {
    '/DeviceGray': Colorspace.gray,
    '/CalGray': Colorspace.gray,
    '/DeviceRGB': Colorspace.rgb,
    '/CalRGB': Colorspace.rgb,
    '/DeviceCMYK': Colorspace.cmyk,
    '/Lab': Colorspace.lab,
    '/ICCBased': Colorspace.icc,
    '/Indexed': Colorspace.index,
    '/Separation': Colorspace.sep,
    '/DeviceN': Colorspace.devn,
    '/Pattern': Colorspace.pattern,
    '/G': Colorspace.gray,  # Abbreviations permitted in inline images
    '/RGB': Colorspace.rgb,
    '/CMYK': Colorspace.cmyk,
    '/I': Colorspace.index,
}

FRIENDLY_ENCODING: dict[str, Encoding] = {
    '/CCITTFaxDecode': Encoding.ccitt,
    '/DCTDecode': Encoding.jpeg,
    '/JPXDecode': Encoding.jpeg2000,
    '/JBIG2Decode': Encoding.jbig2,
    '/CCF': Encoding.ccitt,  # Abbreviations permitted in inline images
    '/DCT': Encoding.jpeg,
    '/AHx': Encoding.asciihex,
    '/A85': Encoding.ascii85,
    '/LZW': Encoding.lzw,
    '/Fl': Encoding.flate,
    '/RL': Encoding.runlength,
}

FRIENDLY_COMP: dict[Colorspace, int] = {
    Colorspace.gray: 1,
    Colorspace.rgb: 3,
    Colorspace.cmyk: 4,
    Colorspace.lab: 3,
    Colorspace.index: 1,
}

UNIT_SQUARE = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
