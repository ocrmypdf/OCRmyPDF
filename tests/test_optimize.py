# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from io import BytesIO
from os import fspath
from pathlib import Path
from unittest.mock import MagicMock, patch

import img2pdf
import pikepdf
import pytest
from pikepdf import Array, Dictionary, Name
from PIL import Image, ImageDraw

from ocrmypdf import optimize as opt
from ocrmypdf._exec import jbig2enc, pngquant
from ocrmypdf._exec.ghostscript import rasterize_pdf
from ocrmypdf.helpers import IMG2PDF_KWARGS, Resolution
from ocrmypdf.optimize import PdfImage, extract_image_filter
from tests.conftest import check_ocrmypdf

needs_pngquant = pytest.mark.skipif(
    not pngquant.available(), reason="pngquant not installed"
)
needs_jbig2enc = pytest.mark.skipif(
    not jbig2enc.available(), reason="jbig2enc not installed"
)


# pylint:disable=redefined-outer-name


@pytest.fixture(scope="session")
def palette(resources):
    return resources / 'palette.pdf'


@needs_pngquant
@pytest.mark.parametrize('pdf', ['multipage', 'palette'])
def test_basic(multipage, palette, pdf, outpdf):
    infile = multipage if pdf == 'multipage' else palette
    opt.main(infile, outpdf, level=3)

    assert 0.98 * Path(outpdf).stat().st_size <= Path(infile).stat().st_size


@needs_pngquant
def test_mono_not_inverted(resources, outdir):
    infile = resources / '2400dpi.pdf'
    opt.main(infile, outdir / 'out.pdf', level=3)

    rasterize_pdf(
        outdir / 'out.pdf',
        outdir / 'im.png',
        raster_device='pnggray',
        raster_dpi=Resolution(10, 10),
    )

    with Image.open(fspath(outdir / 'im.png')) as im:
        assert im.getpixel((0, 0)) > 240, "Expected white background"


@needs_pngquant
def test_jpg_png_params(resources, outpdf):
    check_ocrmypdf(
        resources / 'crom.png',
        outpdf,
        '--image-dpi',
        '200',
        '--optimize',
        '3',
        '--jpg-quality',
        '50',
        '--png-quality',
        '20',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@needs_jbig2enc
@pytest.mark.parametrize('lossy', [False, True])
def test_jbig2_lossy(lossy, resources, outpdf):
    args = [
        resources / 'ccitt.pdf',
        outpdf,
        '--image-dpi',
        '200',
        '--optimize',
        '3',
        '--jpg-quality',
        '50',
        '--png-quality',
        '20',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--jbig2-threshold',
        '0.7',
    ]
    if lossy:
        args.append('--jbig2-lossy')

    check_ocrmypdf(*args)

    with pikepdf.open(outpdf) as pdf:
        pim = pikepdf.PdfImage(next(iter(pdf.pages[0].images.values())))
        assert pim.filters[0] == '/JBIG2Decode'

        if lossy:
            assert '/JBIG2Globals' in pim.decode_parms[0]
        else:
            assert len(pim.decode_parms) == 0


@needs_pngquant
@needs_jbig2enc
def test_flate_to_jbig2(resources, outdir):
    # This test requires an image that pngquant is capable of converting to
    # to 1bpp - so use an existing 1bpp image, convert up, confirm it can
    # convert down
    with Image.open(fspath(resources / 'typewriter.png')) as im:
        assert im.mode in ('1', 'P')
        im = im.convert('L')
        im.save(fspath(outdir / 'type8.png'))

    check_ocrmypdf(
        outdir / 'type8.png',
        outdir / 'out.pdf',
        '--image-dpi',
        '100',
        '--png-quality',
        '50',
        '--optimize',
        '3',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    with pikepdf.open(outdir / 'out.pdf') as pdf:
        pim = pikepdf.PdfImage(next(iter(pdf.pages[0].images.values())))
        assert pim.filters[0] == '/JBIG2Decode'


@needs_pngquant
def test_multiple_pngs(resources, outdir):
    with Path.open(outdir / 'in.pdf', 'wb') as inpdf:
        img2pdf.convert(
            fspath(resources / 'baiona_colormapped.png'),
            fspath(resources / 'baiona_gray.png'),
            outputstream=inpdf,
            **IMG2PDF_KWARGS,
        )

    def mockquant(input_file, output_file, *_args):
        with Image.open(input_file) as im:
            draw = ImageDraw.Draw(im)
            draw.rectangle((0, 0, im.width, im.height), fill=128)
            im.save(output_file)

    with patch('ocrmypdf.optimize.pngquant.quantize') as mock:
        mock.side_effect = mockquant
        check_ocrmypdf(
            outdir / 'in.pdf',
            outdir / 'out.pdf',
            '--optimize',
            '3',
            '--jobs',
            '1',
            '--use-threads',
            '--output-type',
            'pdf',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )
        mock.assert_called()

    with (
        pikepdf.open(outdir / 'in.pdf') as inpdf,
        pikepdf.open(outdir / 'out.pdf') as outpdf,
    ):
        for n in range(len(inpdf.pages)):
            inim = next(iter(inpdf.pages[n].images.values()))
            outim = next(iter(outpdf.pages[n].images.values()))
            assert len(outim.read_raw_bytes()) < len(inim.read_raw_bytes()), n


def test_optimize_off(resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--optimize=0',
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


def test_group3(resources):
    with pikepdf.open(resources / 'ccitt.pdf') as pdf:
        im = pdf.pages[0].Resources.XObject['/Im1']
        assert (
            opt.extract_image_filter(im, im.objgen[0]) is not None
        ), "Group 4 should be allowed"

        im.DecodeParms['/K'] = 0
        assert (
            opt.extract_image_filter(im, im.objgen[0]) is None
        ), "Group 3 should be disallowed"


def test_find_formx(resources):
    with pikepdf.open(resources / 'formxobject.pdf') as pdf:
        working, pagenos = opt._find_image_xrefs(pdf)
        assert len(working) == 1
        xref = next(iter(working))
        assert pagenos[xref] == 0


def test_extract_image_filter_with_pdf_image():
    image = MagicMock()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 10
    image.Height = 10
    image.Filter = [Name.FlateDecode, Name.DCTDecode]
    pdf_image = PdfImage(image)
    image.BitsPerComponent = 8
    assert extract_image_filter(image, None) == (
        pdf_image,
        pdf_image.filter_decodeparms[1],
    )


def test_extract_image_filter_with_non_image():
    image = MagicMock()
    image.Subtype = Name.Form
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_small_stream_size():
    image = MagicMock()
    image.Subtype = Name.Image
    image.Length = 50
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_small_dimensions():
    image = MagicMock()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 5
    image.Height = 5
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_multiple_compression_filters():
    image = MagicMock()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 10
    image.Height = 10
    image.BitsPerComponent = 8
    image.Filter = [Name.ASCII85Decode, Name.FlateDecode, Name.DCTDecode]
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_wide_gamut_image():
    image = MagicMock()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 10
    image.Height = 10
    image.BitsPerComponent = 16
    image.Filter = Name.FlateDecode
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_jpeg2000_image():
    im = Image.new('RGB', (10, 10))
    bio = BytesIO()
    im.save(bio, format='JPEG2000')
    pdf = pikepdf.new()
    stream = pdf.make_stream(
        data=bio.getvalue(),
        Subtype=Name.Image,
        Length=200,
        Width=10,
        Height=10,
        BitsPerComponent=8,
        Filter=Name.JPXDecode,
    )
    assert extract_image_filter(stream, None) is None


def test_extract_image_filter_with_ccitt_group_3_image():
    image = MagicMock()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 10
    image.Height = 10
    image.BitsPerComponent = 1
    image.Filter = Name.CCITTFaxDecode
    image.DecodeParms = Array([Dictionary(K=1)])
    assert extract_image_filter(image, None) is None


# Triggers pikepdf bug
# def test_extract_image_filter_with_decode_table():
#     image = MagicMock()
#     image.Subtype = Name.Image
#     image.Length = 200
#     image.Width = 10
#     image.Height = 10
#     image.Filter = Name.FlateDecode
#     image.BitsPerComponent = 8
#     image.ColorSpace = Name.DeviceGray
#     image.Decode = [42, 0]
#     assert extract_image_filter(image, None) is None
