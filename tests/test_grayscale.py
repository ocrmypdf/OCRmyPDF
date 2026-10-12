# SPDX-FileCopyrightText: 2026 ikeago
# SPDX-License-Identifier: CC-BY-SA-4.0

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PIL import Image

from ocrmypdf._grayscale import _candidate_weights, convert_to_grayscale
from ocrmypdf._options import OcrOptions
from ocrmypdf._pipelines import _common
from ocrmypdf.api import create_options
from ocrmypdf.cli import get_parser


def test_force_grayscale_cli_and_api_options():
    parser = get_parser()
    namespace = parser.parse_args(['--force-grayscale', 'in.pdf', 'out.pdf'])
    options = create_options(
        input_file='in.pdf',
        output_file='out.pdf',
        parser=parser,
        force_grayscale=True,
    )

    assert namespace.force_grayscale
    assert options.force_grayscale
    assert not options.lossless_reconstruction


def test_force_grayscale_is_incompatible_with_redo_ocr():
    with pytest.raises(ValueError, match='--force-grayscale'):
        OcrOptions(
            input_file='in.pdf',
            output_file='out.pdf',
            redo_ocr=True,
            force_grayscale=True,
        )


def test_process_page_only_converts_visible_image(monkeypatch, tmp_path):
    ocr_image = tmp_path / 'ocr.png'
    visible_image = tmp_path / 'visible.png'
    grayscale_image = tmp_path / 'grayscale.png'
    seen = {}
    options = SimpleNamespace(
        force_grayscale=True,
        lossless_reconstruction=False,
        rotate_pages=False,
    )
    page_context = SimpleNamespace(
        options=options,
        pageinfo=SimpleNamespace(),
        plugin_manager=SimpleNamespace(filter_page_image=lambda **kwargs: None),
        get_path=lambda name: tmp_path / name,
    )

    def convert_visible(image, output):
        seen['gray'] = (image, output)
        return output

    monkeypatch.setattr(
        _common,
        'make_intermediate_images',
        lambda page_context, correction: (ocr_image, visible_image),
    )
    monkeypatch.setattr(
        _common,
        'create_ocr_image',
        lambda image, page_context: seen.setdefault('ocr', image),
    )
    monkeypatch.setattr(
        _common,
        'convert_to_grayscale',
        convert_visible,
    )
    monkeypatch.setattr(
        _common, 'should_visible_page_image_use_jpg', lambda page: False
    )
    monkeypatch.setattr(
        _common,
        'create_pdf_page_from_image',
        lambda image, page_context, correction: seen.setdefault('pdf', image),
    )
    monkeypatch.setattr(_common, 'release_free_memory', lambda: None)

    _common.process_page(page_context)

    assert seen == {
        'ocr': ocr_image,
        'gray': (visible_image, grayscale_image),
        'pdf': grayscale_image,
    }


def test_candidate_weights_cover_simplex():
    weights = _candidate_weights()

    assert len(weights) == 66
    assert all(sum(candidate) == 1.0 for candidate in weights)


def test_conversion_preserves_equal_luminance_color_contrast(tmp_path):
    input_file = tmp_path / 'color.png'
    output_file = tmp_path / 'gray.png'
    image = Image.new('RGB', (64, 32))
    image.paste((255, 0, 0), (0, 0, 32, 32))
    image.paste((0, 130, 0), (32, 0, 64, 32))
    image.save(input_file, dpi=(300, 300))

    ordinary = image.convert('L')
    assert abs(ordinary.getpixel((8, 8)) - ordinary.getpixel((56, 8))) <= 1

    convert_to_grayscale(input_file, output_file)

    with Image.open(output_file) as result:
        assert result.mode == 'L'
        assert abs(result.getpixel((8, 8)) - result.getpixel((56, 8))) >= 32
        assert result.info['dpi'] == (
            pytest.approx(300, abs=0.1),
            pytest.approx(300, abs=0.1),
        )


def test_conversion_keeps_grayscale_pixels(tmp_path):
    input_file = tmp_path / 'input.png'
    output_file = tmp_path / 'output.png'
    Image.linear_gradient('L').save(input_file)

    convert_to_grayscale(input_file, output_file)

    with Image.open(input_file) as source, Image.open(output_file) as result:
        assert result.mode == 'L'
        assert result.tobytes() == source.tobytes()


@pytest.mark.parametrize('mode', ['RGBA', 'LA', 'P', 'CMYK'])
def test_conversion_handles_other_color_modes(mode, tmp_path):
    input_file = tmp_path / f'{mode}.png'
    output_file = tmp_path / f'{mode}-gray.png'
    if mode == 'RGBA':
        image = Image.new(mode, (2, 1), (0, 0, 0, 0))
    elif mode == 'LA':
        image = Image.new(mode, (2, 1), (0, 0))
    elif mode == 'P':
        image = Image.new(mode, (2, 1), 0)
        image.putpalette([0, 0, 0] + [255, 255, 255] * 255)
        image.info['transparency'] = 0
    else:
        image = Image.new(mode, (2, 1), (0, 0, 0, 0))
        input_file = tmp_path / f'{mode}.tif'
    image.putpixel((1, 0), 1 if mode == 'P' else image.getpixel((1, 0)))
    image.save(input_file)

    convert_to_grayscale(input_file, output_file)

    with Image.open(output_file) as result:
        assert result.mode == 'L'
        if mode in ('RGBA', 'LA', 'P'):
            assert result.getpixel((0, 0)) == 255


def test_conversion_preserves_black_white_and_is_deterministic(tmp_path):
    input_file = tmp_path / 'input.png'
    first_output = tmp_path / 'first.png'
    second_output = tmp_path / 'second.png'
    image = Image.new('RGB', (2, 1), 'black')
    image.putpixel((1, 0), (255, 255, 255))
    image.save(input_file)

    convert_to_grayscale(input_file, first_output)
    convert_to_grayscale(input_file, second_output)

    with Image.open(first_output) as result:
        assert result.getpixel((0, 0)) == 0
        assert result.getpixel((1, 0)) == 255
    assert first_output.read_bytes() == second_output.read_bytes()


def test_conversion_handles_one_pixel_image(tmp_path):
    input_file = tmp_path / 'input.png'
    output_file = tmp_path / 'output.png'
    Image.new('RGB', (1, 1), (12, 34, 56)).save(input_file)

    convert_to_grayscale(input_file, output_file)

    with Image.open(output_file) as result:
        assert result.size == (1, 1)
