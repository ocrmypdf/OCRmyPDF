# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from ocrmypdf.imageops import bytes_per_pixel, calculate_downsample, downsample_image
from PIL import Image


def test_bytes_per_pixel():
    assert bytes_per_pixel('RGB') == 4
    assert bytes_per_pixel('RGBA') == 4
    assert bytes_per_pixel('LA') == 2
    assert bytes_per_pixel('L') == 1


def test_calculate_downsample():
    im = Image.new('RGB', (100, 100))
    assert calculate_downsample(im, max_size=(50, 50)) == (50, 50)
    assert calculate_downsample(im, max_pixels=2500) == (50, 50)
    assert calculate_downsample(im, max_bytes=10000) == (50, 50)
    assert calculate_downsample(im, max_bytes=100000) == (100, 100)


def test_downsample_image():
    im = Image.new('RGB', (100, 100))
    im.info['dpi'] = (300, 300)
    ds = downsample_image(im, (50, 50))
    assert ds.size == (50, 50)
    assert ds.info['dpi'] == (150, 150)
