# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import hypothesis.strategies as st
from hypothesis import given
from PIL import Image

from ocrmypdf.imageops import (
    _calculate_downsample,
    bytes_per_pixel,
    calculate_downsample,
    downsample_image,
)


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


@given(
    st.one_of(st.just("RGB"), st.just('L')),
    st.integers(min_value=1, max_value=100000),
    st.integers(min_value=1, max_value=100000),
    st.integers(min_value=64, max_value=100000),
    st.integers(min_value=64, max_value=100000),
    st.integers(min_value=64 * 64, max_value=1000000),
)
def test_calculate_downsample_hypothesis(mode, im_w, im_h, max_x, max_y, max_bytes):
    result = _calculate_downsample(
        (im_w, im_h),
        bytes_per_pixel(mode),
        max_size=(max_x, max_y),
        max_bytes=max_bytes,
    )
    assert result[0] <= max_x
    assert result[1] <= max_y
    assert result[0] * result[1] * bytes_per_pixel(mode) <= max_bytes


def test_downsample_image():
    im = Image.new('RGB', (100, 100))
    im.info['dpi'] = (300, 300)
    ds = downsample_image(im, (50, 50))
    assert ds.size == (50, 50)
    assert ds.info['dpi'] == (150, 150)
