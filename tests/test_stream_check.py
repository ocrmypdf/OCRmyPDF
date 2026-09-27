# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import io
import zlib

import pikepdf
import pytest
from pikepdf import Array, Name
from PIL import Image, features

from ocrmypdf._stream_check import check_streams
from ocrmypdf.helpers import check_pdf


def _noise_image() -> Image.Image:
    return Image.effect_noise((256, 256), 64).convert('RGB')


def _encoded(fmt: str) -> bytes:
    buf = io.BytesIO()
    _noise_image().save(buf, fmt)
    return buf.getvalue()


def _add_image(pdf: pikepdf.Pdf, data: bytes, filters: list[str]) -> pikepdf.Stream:
    image = pikepdf.Stream(pdf, data)
    image.Type = Name.XObject
    image.Subtype = Name.Image
    image.Width, image.Height = 256, 256
    image.ColorSpace = Name.DeviceRGB
    image.BitsPerComponent = 8
    image.Filter = Array([Name(f) for f in filters])
    return image


def _pdf_with(data: bytes, filters: list[str]) -> pikepdf.Pdf:
    pdf = pikepdf.new()
    pdf.add_blank_page()
    pdf.pages[0].Resources = pikepdf.Dictionary(
        XObject=pikepdf.Dictionary(Im0=_add_image(pdf, data, filters))
    )
    pdf.pages[0].Contents = pdf.make_stream(b'q 256 0 0 256 0 0 cm /Im0 Do Q')
    return pdf


def _truncated(data: bytes) -> bytes:
    return data[: len(data) * 6 // 10]


def _bit_flipped(data: bytes) -> bytes:
    damaged = bytearray(data)
    for i in range(len(damaged) // 3, len(damaged) // 3 + 64):
        damaged[i] ^= 0xFF
    return bytes(damaged)


def _jpeg() -> bytes:
    return _encoded('JPEG')


needs_jpx = pytest.mark.skipif(
    not features.check_codec('jpg_2000'), reason="Pillow lacks JPEG 2000"
)


def _flate_data() -> bytes:
    return zlib.compress(bytes(range(256)) * 4000)


@pytest.mark.parametrize(
    'make_data, filters',
    [
        pytest.param(_flate_data, ['/FlateDecode'], id='flate'),
        pytest.param(_jpeg, ['/DCTDecode'], id='dct'),
        pytest.param(
            lambda: zlib.compress(_jpeg()),
            ['/FlateDecode', '/DCTDecode'],
            id='flate-dct',
        ),
        pytest.param(lambda: b'48656c6c6f>', ['/ASCIIHexDecode'], id='asciihex'),
        pytest.param(
            lambda: _encoded('JPEG2000'), ['/JPXDecode'], id='jpx', marks=needs_jpx
        ),
    ],
)
def test_intact_streams_pass(make_data, filters):
    assert check_streams(_pdf_with(make_data(), filters)) == []


@pytest.mark.parametrize(
    'make_data, filters',
    [
        pytest.param(
            lambda: _truncated(_flate_data()), ['/FlateDecode'], id='flate-truncated'
        ),
        pytest.param(
            lambda: _bit_flipped(_flate_data()), ['/FlateDecode'], id='flate-corrupt'
        ),
        pytest.param(lambda: _truncated(_jpeg()), ['/DCTDecode'], id='dct-truncated'),
        pytest.param(
            lambda: zlib.compress(_truncated(_jpeg())),
            ['/FlateDecode', '/DCTDecode'],
            id='flate-dct-truncated',
        ),
        pytest.param(
            lambda: _truncated(_encoded('JPEG2000')),
            ['/JPXDecode'],
            id='jpx-truncated',
            marks=needs_jpx,
        ),
    ],
)
def test_damaged_streams_are_reported(make_data, filters):
    pdf = _pdf_with(make_data(), filters)
    problems = check_streams(pdf)
    assert len(problems) == 1
    objgen = pdf.pages[0].Resources.XObject.Im0.objgen
    assert f'{objgen[0]} {objgen[1]} R' in problems[0]


@pytest.mark.parametrize('name', ['ccitt.pdf', 'jbig2.pdf'])
def test_bilevel_resources_pass(resources, name):
    with pikepdf.open(resources / name) as pdf:
        assert check_streams(pdf) == []


def test_progress_reaches_100():
    percents: list[int] = []
    check_streams(_pdf_with(_jpeg(), ['/DCTDecode']), progress=percents.append)
    assert percents[-1] == 100
    assert percents == sorted(percents)


def test_check_pdf_rejects_truncated_jpeg(outpdf):
    _pdf_with(_truncated(_jpeg()), ['/DCTDecode']).save(outpdf)
    assert not check_pdf(outpdf)


def test_check_pdf_accepts_intact_jpeg(outpdf):
    _pdf_with(_jpeg(), ['/DCTDecode']).save(outpdf)
    assert check_pdf(outpdf)
