# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for the pypdfium2 rasterizer plugin."""

from __future__ import annotations

import logging
from contextlib import closing

import pikepdf
import pytest
from PIL import Image

from ocrmypdf.builtin_plugins import pypdfium
from ocrmypdf.builtin_plugins.pypdfium import (
    _bitmap_to_pil,
    _fit_to_size,
    _white,
    check_options,
    rasterize_pdf_page,
)
from ocrmypdf.cli import get_options_and_plugins
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.helpers import Resolution


def _process_image_for_output(*args, **kwargs):
    output = pypdfium._process_image_for_output(*args, **kwargs)
    return output.image, output.format_name


# Ghostscript's raster devices, and the PIL image mode each one must produce.
# Keys are the input image mode; values are the mode after conversion.
UNCHANGED = {mode: mode for mode in ('RGBA', 'RGB', 'L', 'P', '1')}
EXPECTED_MODE: dict[str, dict[str, str]] = {
    'pngmono': dict.fromkeys(UNCHANGED, '1'),
    'pngmonod': dict.fromkeys(UNCHANGED, '1'),
    # grayscale devices leave 1-bit input alone (it is already achromatic)
    'pnggray': {'RGBA': 'L', 'RGB': 'L', 'L': 'L', 'P': 'L', '1': '1'},
    'jpeggray': {'RGBA': 'L', 'RGB': 'L', 'L': 'L', 'P': 'L', '1': '1'},
    'png256': dict.fromkeys(UNCHANGED, 'P'),
    'png16m': dict.fromkeys(UNCHANGED, 'RGB'),
    'jpeg': dict.fromkeys(UNCHANGED, 'RGB'),
    # these devices do no conversion at all
    'pngalpha': UNCHANGED,
    'tiff': UNCHANGED,
    'bogus': UNCHANGED,
}

EXPECTED_FORMAT = {
    'pngmono': 'PNG',
    'pngmonod': 'PNG',
    'pnggray': 'PNG',
    'png256': 'PNG',
    'png16m': 'PNG',
    'pngalpha': 'PNG',
    'jpeg': 'JPEG',
    'jpeggray': 'JPEG',
    'tiff': 'TIFF',
    'bogus': 'PNG',  # unknown devices fall back to PNG
}


def make_image(mode: str) -> Image.Image:
    """Make a small image with some structure, so conversions are meaningful."""
    im = Image.new('RGB', (8, 8), (255, 255, 255))
    for x in range(4):
        for y in range(4):
            im.putpixel((x, y), (10, 90, 200))
    return im.convert(mode)


@pytest.mark.parametrize('raster_device', sorted(EXPECTED_MODE))
@pytest.mark.parametrize('mode', ['RGBA', 'RGB', 'L', 'P', '1'])
def test_process_image_mode_and_format(caplog, mode, raster_device):
    caplog.set_level(logging.WARNING)
    im = make_image(mode)
    out, format_name = _process_image_for_output(
        im,
        raster_device,
        Resolution(200.0, 200.0),
        None,
        stop_on_soft_error=False,
    )
    assert out.mode == EXPECTED_MODE[raster_device][mode]
    assert format_name == EXPECTED_FORMAT[raster_device]
    # Whatever the conversion, the image must survive a save in its own format
    assert out.size == (8, 8)


@pytest.mark.parametrize('raster_device', ['PNGMONO', 'PngGray', 'JPEG', 'TIF'])
def test_process_image_device_name_is_case_insensitive(raster_device):
    out, format_name = _process_image_for_output(
        make_image('RGB'),
        raster_device,
        Resolution(200.0, 200.0),
        None,
        stop_on_soft_error=True,
    )
    expected = {'PNGMONO': ('1', 'PNG'), 'PngGray': ('L', 'PNG')}.get(
        raster_device, ('RGB', {'JPEG': 'JPEG', 'TIF': 'TIFF'}.get(raster_device))
    )
    assert (out.mode, format_name) == expected


def test_process_image_rgba_flattened_onto_white_for_rgb_devices():
    """Transparency must become white, not black, for OCR-friendly output."""
    im = Image.new('RGBA', (4, 4), (0, 0, 0, 0))
    out, _format = _process_image_for_output(
        im,
        'png16m',
        Resolution(200.0, 200.0),
        None,
        stop_on_soft_error=True,
    )
    assert out.mode == 'RGB'
    assert out.getpixel((0, 0)) == (255, 255, 255)


def test_process_image_pngalpha_preserves_transparency():
    im = Image.new('RGBA', (4, 4), (0, 0, 0, 0))
    out, format_name = _process_image_for_output(
        im,
        'pngalpha',
        Resolution(200.0, 200.0),
        None,
        stop_on_soft_error=True,
    )
    assert format_name == 'PNG'
    assert out.getpixel((0, 0)) == (0, 0, 0, 0)


def test_process_image_uses_page_dpi_when_given():
    out, _format = _process_image_for_output(
        make_image('RGB'),
        'png16m',
        Resolution(200.0, 300.0),
        Resolution(42.0, 4242.0),
        stop_on_soft_error=True,
    )
    assert out.info['dpi'] == (42.0, 4242.0)


def test_process_image_falls_back_to_raster_dpi():
    out, _format = _process_image_for_output(
        make_image('RGB'),
        'png16m',
        Resolution(200.0, 300.0),
        None,
        stop_on_soft_error=True,
    )
    assert out.info['dpi'] == (200.0, 300.0)


@pytest.mark.parametrize(
    ('expected_size', 'resized'),
    [
        ((8, 8), False),  # exact match: no resize
        ((13, 13), False),  # off by more than 2 px: leave it alone
        ((9, 9), True),  # off by 1 px: nudge to the expected size
        ((8, 6), True),  # one axis off by 2 px
    ],
)
def test_process_image_corrects_small_dimension_errors(expected_size, resized):
    out, _format = _process_image_for_output(
        make_image('RGB'),
        'png16m',
        Resolution(200.0, 200.0),
        None,
        stop_on_soft_error=True,
        expected_width=expected_size[0],
        expected_height=expected_size[1],
    )
    assert out.size == (expected_size if resized else (8, 8))


def test_unsupported_device_raises_when_stopping_on_soft_error():
    with pytest.raises(ValueError, match='bogus'):
        _process_image_for_output(
            make_image('RGB'),
            'bogus',
            Resolution(200.0, 200.0),
            None,
            stop_on_soft_error=True,
        )


def test_unsupported_device_warns_and_uses_png(caplog):
    caplog.set_level(logging.WARNING)
    out, format_name = _process_image_for_output(
        make_image('RGB'),
        'bogus',
        Resolution(200.0, 200.0),
        None,
        stop_on_soft_error=False,
    )
    assert format_name == 'PNG'
    assert out.mode == 'RGB'
    assert 'Unsupported raster device bogus' in caplog.text


def _options(*args):
    options, _pm = get_options_and_plugins([*args, 'a.pdf', 'b.pdf'])
    return options


def test_check_options_requires_pypdfium2_when_requested(monkeypatch):
    monkeypatch.setattr(pypdfium, 'pdfium', None)
    with pytest.raises(MissingDependencyError, match='pypdfium2'):
        check_options(_options('--rasterizer', 'pypdfium'))


@pytest.mark.parametrize('rasterizer', ['auto', 'ghostscript'])
def test_check_options_tolerates_missing_pypdfium2(monkeypatch, rasterizer):
    """Without an explicit request, a missing pypdfium2 is not an error."""
    monkeypatch.setattr(pypdfium, 'pdfium', None)
    assert check_options(_options('--rasterizer', rasterizer)) is None


def test_check_options_accepts_installed_pypdfium2():
    assert check_options(_options('--rasterizer', 'pypdfium')) is None


def _rasterize(options, input_file, output_file, **kwargs):
    kwargs.setdefault('raster_device', 'png16m')
    kwargs.setdefault('raster_dpi', Resolution(72.0, 72.0))
    kwargs.setdefault('rotation', None)
    kwargs.setdefault('use_cropbox', False)
    return rasterize_pdf_page(
        input_file=input_file,
        output_file=output_file,
        pageno=1,
        page_dpi=None,
        filter_vector=False,
        stop_on_soft_error=True,
        options=options,
        **kwargs,
    )


def test_rasterize_defers_to_ghostscript_when_selected(resources, outdir):
    """The hook opts out (returns None) so the Ghostscript hook can run."""
    out = outdir / 'out.png'
    assert (
        _rasterize(
            _options('--rasterizer', 'ghostscript'), resources / 'trivial.pdf', out
        )
        is None
    )
    assert not out.exists()


def test_rasterize_defers_when_pypdfium2_unavailable(monkeypatch, resources, outdir):
    monkeypatch.setattr(pypdfium, 'pdfium', None)
    out = outdir / 'out.png'
    assert (
        _rasterize(_options('--rasterizer', 'auto'), resources / 'trivial.pdf', out)
        is None
    )
    assert not out.exists()


def test_rasterize_produces_image_when_selected(resources, outdir):
    src = resources / 'trivial.pdf'
    out = outdir / 'out.png'
    assert _rasterize(_options('--rasterizer', 'pypdfium'), src, out) == out

    with pikepdf.open(src) as pdf:
        mediabox = [float(v) for v in pdf.pages[0].MediaBox]
    # Rendered at 72 dpi, so one pixel per PDF point
    expected_size = (
        round(mediabox[2] - mediabox[0]),
        round(mediabox[3] - mediabox[1]),
    )
    with Image.open(out) as im:
        assert im.mode == 'RGB'
        assert im.size == expected_size
        # PNG stores resolution in pixels/meter, so expect rounding
        assert im.info['dpi'] == pytest.approx((72.0, 72.0), rel=1e-3)


@pytest.mark.parametrize(
    ('rotation', 'swapped'),
    [(90, True), (270, True), (180, False), (0, False)],
)
def test_rasterize_rotation(resources, outdir, rotation, swapped):
    src = resources / 'francais.pdf'
    upright = outdir / 'upright.png'
    rotated = outdir / 'rotated.png'
    options = _options('--rasterizer', 'pypdfium')
    _rasterize(options, src, upright)
    _rasterize(options, src, rotated, rotation=rotation)

    with Image.open(upright) as im1, Image.open(rotated) as im2:
        expected = (im1.size[1], im1.size[0]) if swapped else im1.size
        assert im2.size == expected


def test_rasterize_uses_mediabox_by_default(resources, outdir):
    """CropBox-cropped content must not be lost, to match Ghostscript (#1685)."""
    src = outdir / 'cropped.pdf'
    with pikepdf.open(resources / 'francais.pdf') as pdf:
        mediabox = [float(v) for v in pdf.pages[0].MediaBox]
        pdf.pages[0].CropBox = [
            mediabox[0],
            mediabox[1],
            mediabox[0] + (mediabox[2] - mediabox[0]) / 2,
            mediabox[1] + (mediabox[3] - mediabox[1]) / 2,
        ]
        pdf.save(src)

    options = _options('--rasterizer', 'pypdfium')
    full = outdir / 'full.png'
    cropped = outdir / 'cropped.png'
    _rasterize(options, src, full)
    _rasterize(options, src, cropped, use_cropbox=True)

    with Image.open(full) as im1, Image.open(cropped) as im2:
        assert im1.size == (round(mediabox[2]), round(mediabox[3]))
        assert im2.size[0] < im1.size[0] and im2.size[1] < im1.size[1]


@pytest.mark.parametrize('grayscale', [True, False])
def test_bitmap_to_pil_owns_its_pixels(resources, grayscale):
    """The image must survive the bitmap being closed.

    PDFium frees the bitmap's buffer on close, and PIL aliases that buffer for
    some formats, so a view would become a dangling read.
    """
    pdfium = pytest.importorskip('pypdfium2')
    with closing(pdfium.PdfDocument(resources / 'francais.pdf')) as pdf:
        page = pdf[0]
        bitmap = page.render(scale=2, grayscale=grayscale)
        with closing(bitmap):
            image = _bitmap_to_pil(bitmap, None, None)
            assert (bitmap.width, bitmap.height) == image.size
            expected = image.tobytes()
            # Scribbling on the buffer proves the image is a copy, not a view.
            bitmap.buffer[0] ^= 0xFF
        assert image.tobytes() == expected


@pytest.mark.parametrize(
    ('expected', 'result'),
    [
        ((None, None), None),  # no expectation: keep the rendered size
        ((-1, -2), (-1, -2)),  # off by 1 and 2 px: trim to the expected size
        ((-3, -3), None),  # off by more than 2 px: not a rounding error
        ((+1, +1), None),  # rendered short: padded later, once the mode is known
    ],
)
def test_bitmap_to_pil_trims_rounding_overshoot(resources, expected, result):
    pdfium = pytest.importorskip('pypdfium2')
    with closing(pdfium.PdfDocument(resources / 'francais.pdf')) as pdf:
        page = pdf[0]
        bitmap = page.render(scale=2)
        with closing(bitmap):
            rendered = (bitmap.width, bitmap.height)
            offsets = expected
            want = (
                (None, None)
                if offsets == (None, None)
                else (rendered[0] + offsets[0], rendered[1] + offsets[1])
            )
            image = _bitmap_to_pil(bitmap, *want)
            assert image.size == (rendered if result is None else want)


@pytest.mark.parametrize(
    ('mode', 'expected'),
    [
        ('1', 1),
        ('L', 255),
        ('P', 255),
        ('RGB', (255, 255, 255)),
        ('RGBA', (255, 255, 255, 255)),
        ('LA', (255, 255)),  # falls through to ImageColor
        ('CMYK', (255, 255, 255)),  # ditto
    ],
)
def test_white_for_every_mode_we_pad_with(mode, expected):
    assert _white(mode) == expected


@pytest.mark.parametrize(
    ('target', 'description'),
    [((4, 4), 'crop both axes'), ((12, 12), 'pad both axes'), ((4, 12), 'one of each')],
)
def test_fit_to_size_crops_and_pads_without_resampling(target, description):
    image = Image.new('L', (8, 8), 0)
    out = _fit_to_size(image, *target)
    assert out.size == target, description
    # Surviving pixels keep their value; anything added is white.
    assert out.getpixel((0, 0)) == 0
    if target[1] > 8:
        assert out.getpixel((0, 11)) == 255, "padding must be white, not black"


def test_fit_to_size_keeps_the_palette():
    image = Image.new('P', (8, 8), 3)
    image.putpalette([0, 0, 0] * 3 + [10, 20, 30] + [0, 0, 0] * 252)
    out = _fit_to_size(image, 6, 6)
    assert out.mode == 'P'
    assert out.convert('RGB').getpixel((0, 0)) == (10, 20, 30)


def test_bitmap_to_pil_falls_back_for_an_unknown_format():
    """A PDFium format we do not map is handed to pypdfium2, and still copied."""
    source = Image.new('RGB', (4, 4), 'red')

    class UnknownBitmap:
        mode = 'no-such-format'
        width = height = 4

        def to_pil(self):
            return source

    out = _bitmap_to_pil(UnknownBitmap(), None, None)
    assert out.size == (4, 4)
    assert out is not source, "must copy: pypdfium2 may return a view on the buffer"
