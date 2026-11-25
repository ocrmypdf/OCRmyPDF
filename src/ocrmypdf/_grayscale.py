# SPDX-FileCopyrightText: 2026 ikeago
# SPDX-License-Identifier: MPL-2.0

"""Contrast-preserving conversion of color page images to grayscale.

This implements the discrete linear mapping from Lu, Xu, and Jia, "Real-time
Contrast Preserving Decolorization" (SIGGRAPH Asia 2012), DOI 10.1145/2407746.2407780.
The fixed sample includes neighboring pairs in addition to the paper's random pairs,
and discards very low contrast pairs so scanned-page noise does not steer the fit.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import cast

from PIL import Image

_SAMPLE_GRID_SIZE = 64
_WEIGHT_STEPS = 10
_SIGMA = 0.05
_CONTRAST_THRESHOLD = 0.05


def _sample_positions(width: int, height: int) -> list[tuple[int, int]]:
    """Return a grid containing approximately ``_SAMPLE_GRID_SIZE ** 2`` pixels."""
    scale = _SAMPLE_GRID_SIZE / math.sqrt(width * height)
    columns = min(width, max(1, round(width * scale)))
    rows = min(height, max(1, round(height * scale)))

    def center(index: int, count: int, extent: int) -> int:
        return min(extent - 1, int((index + 0.5) * extent / count))

    return [
        (center(column, columns, width), center(row, rows, height))
        for column in range(columns)
        for row in range(rows)
    ]


def _contrast_pairs(image: Image.Image) -> list[tuple[float, float, float, float]]:
    """Sample long-range and neighboring color differences from an RGB image."""
    positions = _sample_positions(*image.size)
    shuffled = positions.copy()
    random.Random(0).shuffle(shuffled)

    pairs = list(zip(positions, shuffled, strict=True))
    columns = sorted({x for x, _ in positions})
    rows = sorted({y for _, y in positions})
    pairs.extend(
        ((left, y), (right, y))
        for left, right in zip(columns, columns[1:], strict=False)
        for y in rows
    )
    pairs.extend(
        ((x, top), (x, bottom))
        for top, bottom in zip(rows, rows[1:], strict=False)
        for x in columns
    )

    sampled = []
    for first, second in pairs:
        a = cast(tuple[int, int, int], image.getpixel(first))
        b = cast(tuple[int, int, int], image.getpixel(second))
        dr, dg, db = ((a[channel] - b[channel]) / 255.0 for channel in range(3))
        contrast = math.sqrt(dr * dr + dg * dg + db * db) / math.sqrt(2.0)
        if contrast >= _CONTRAST_THRESHOLD:
            sampled.append((dr, dg, db, contrast))
    return sampled


def _candidate_weights() -> list[tuple[float, float, float]]:
    """Enumerate convex RGB weights in increments of one tenth."""
    return [
        (red / _WEIGHT_STEPS, green / _WEIGHT_STEPS, blue / _WEIGHT_STEPS)
        for red in range(_WEIGHT_STEPS + 1)
        for green in range(_WEIGHT_STEPS - red + 1)
        for blue in [_WEIGHT_STEPS - red - green]
    ]


def _select_weights(image: Image.Image) -> tuple[float, float, float]:
    """Select the linear mapping that best retains sampled color differences."""
    pairs = _contrast_pairs(image)
    if not pairs:
        return (0.299, 0.587, 0.114)

    inverse_variance = 1.0 / (_SIGMA * _SIGMA)

    def score(weights: tuple[float, float, float]) -> float:
        total = 0.0
        for dr, dg, db, contrast in pairs:
            gray_difference = weights[0] * dr + weights[1] * dg + weights[2] * db
            positive = -((gray_difference - contrast) ** 2) * inverse_variance
            negative = -((gray_difference + contrast) ** 2) * inverse_variance
            peak = max(positive, negative)
            total += peak + math.log(
                math.exp(positive - peak) + math.exp(negative - peak)
            )
        return total / len(pairs)

    return max(_candidate_weights(), key=score)


def _flatten_to_rgb(source: Image.Image) -> Image.Image:
    """Convert to RGB, compositing transparent pixels onto white paper."""
    if source.mode in ('RGBA', 'LA') or 'transparency' in source.info:
        rgba = source.convert('RGBA')
        rgb = Image.new('RGB', source.size, 'white')
        alpha = rgba.getchannel('A')
        rgb.paste(rgba, mask=alpha)
        alpha.close()
        rgba.close()
        return rgb
    return source.convert('RGB')


def convert_to_grayscale(input_file: Path, output_file: Path) -> Path:
    """Convert an image to grayscale while retaining contrast between colors."""
    with Image.open(input_file) as source:
        save_args = {'dpi': source.info['dpi']} if 'dpi' in source.info else {}
        if source.mode in ('1', 'L'):
            source.save(output_file, format='PNG', **save_args)
            return output_file

        with _flatten_to_rgb(source) as rgb:
            weights = _select_weights(rgb)
            grayscale = rgb.convert('L', matrix=(*weights, 0.0))
            grayscale.save(output_file, format='PNG', **save_args)
    return output_file
