# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MIT

"""Transform .hocr and page image to text PDF."""

from __future__ import annotations

from ocrmypdf.hocrtransform._hocr import (
    DebugRenderOptions,
    HocrTransform,
    HocrTransformError,
)

__all__ = (
    'HocrTransform',
    'HocrTransformError',
    'DebugRenderOptions',
)
