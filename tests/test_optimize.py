# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from io import BytesIO
from os import fspath
from pathlib import Path
from unittest.mock import patch

import img2pdf
import pikepdf
import pytest
from packaging.version import Version
from pikepdf import Array, Dictionary, Name
from PIL import Image, ImageDraw

from ocrmypdf import optimize as opt
from ocrmypdf._exec import ghostscript, jbig2enc, pngquant
from ocrmypdf._exec.ghostscript import GS_GENERATED_PDFA, rasterize_pdf
from ocrmypdf._options import OcrOptions
from ocrmypdf.cli import get_options_and_plugins
from ocrmypdf.helpers import IMG2PDF_KWARGS, Resolution
from ocrmypdf.optimize import PdfImage, extract_image_filter
from ocrmypdf.pluginspec import GhostscriptRasterDevice
from tests.conftest import check_ocrmypdf
from tests.test_ghostscript import _dctdecode_streams

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
        raster_device=GhostscriptRasterDevice.PNGGRAY,
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


def test_jpeg_quality_cli_flag_reaches_options(resources, outpdf):
    # Regression test for #1723: --jpeg-quality was silently dropped by
    # namespace_to_options() because the argparse dest ('jpeg_quality') did
    # not match the OcrOptions field it was checked against.
    input_ = fspath(resources / 'c02-22.pdf')
    options, _pm = get_options_and_plugins(
        ['--jpeg-quality', '10', input_, fspath(outpdf)]
    )
    assert options.jpeg_quality == 10


def test_jpg_quality_cli_alias_reaches_options(resources, outpdf):
    # --jpg-quality is a hidden alias for --jpeg-quality (same argparse dest).
    input_ = fspath(resources / 'c02-22.pdf')
    options, _pm = get_options_and_plugins(
        ['--jpg-quality', '42', input_, fspath(outpdf)]
    )
    assert options.jpeg_quality == 42
    # The old field name is still readable as a deprecated compatibility alias.
    assert options.jpg_quality == 42


class TestGs106JpegWorkaroundScope:
    """The lossy JPEG re-encode workaround must fire only when it is needed.

    Ghostscript 10.6.x truncates JPEG passthrough data, so at -O0/-O1 the
    optimizer re-encodes JPEGs to get intact ones, at the cost of quality. That
    trade is only worth making when an affected Ghostscript actually produced the
    file (#1726).
    """

    @pytest.mark.parametrize(
        ('optimize', 'gs_version', 'gs_ran', 'expected'),
        [
            # -O2+ always re-encodes, for reasons unrelated to Ghostscript
            (2, '10.7.1', False, True),
            (3, '10.5.1', False, True),
            # affected Ghostscript that produced this file: workaround warranted
            (1, '10.6.0', True, True),
            (0, '10.6.0', True, True),
            # affected Ghostscript, but it never touched this file (--output-type
            # pdf, or speculative PDF/A conversion succeeded): pure quality loss
            (1, '10.6.0', False, False),
            # unaffected Ghostscript: nothing to work around either way
            (1, '10.7.1', True, False),
            (1, '10.5.1', True, False),
        ],
    )
    def test_should_optimize_jpeg(self, optimize, gs_version, gs_ran, expected):
        options = OcrOptions(input_file='a.pdf', output_file='b.pdf', optimize=optimize)
        if gs_ran:
            options.extra_attrs[GS_GENERATED_PDFA] = True
        with patch.object(opt.ghostscript, 'version', return_value=Version(gs_version)):
            assert opt._should_optimize_jpeg(options, None) is expected

    @pytest.mark.skipif(
        ghostscript.jpeg_truncation_bug(),
        reason="installed Ghostscript truncates JPEGs, so the workaround applies",
    )
    def test_jpeg_survives_default_optimization(self, resources, outpdf):
        """End-to-end: -O1 must not silently degrade JPEGs on a healthy gs.

        Uses a photographic JPEG that genuinely shrinks when re-encoded at the
        default quality - the optimizer discards a re-encode that came out larger,
        which would mask the regression on an already heavily compressed image.
        """
        source = resources / 'baiona_color.jpg'
        check_ocrmypdf(
            source,
            outpdf,
            '--image-dpi',
            '300',
            '--optimize',
            '1',
            '--output-type',
            'pdfa',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )
        # img2pdf embeds the source JPEG losslessly, so it must come out unchanged
        assert _dctdecode_streams(outpdf) == [source.read_bytes()], (
            "-O1 is a lossless optimization level, but the JPEG image was re-encoded"
        )


@needs_jbig2enc
def test_jbig2_lossless(resources, outpdf):
    """Test that JBIG2 lossless encoding works without JBIG2Globals."""
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

    check_ocrmypdf(*args)

    with pikepdf.open(outpdf) as pdf:
        pim = pikepdf.PdfImage(next(iter(pdf.pages[0].get_images().values())))
        assert pim.filters[0] == '/JBIG2Decode'
        # Lossless JBIG2 has no JBIG2Globals (no shared symbol dictionary)
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
        pim = pikepdf.PdfImage(next(iter(pdf.pages[0].get_images().values())))
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
            inim = next(iter(inpdf.pages[n].get_images().values()))
            outim = next(iter(outpdf.pages[n].get_images().values()))
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
        assert opt.extract_image_filter(im, im.objgen[0]) is not None, (
            "Group 4 should be allowed"
        )

        im.DecodeParms['/K'] = 0
        assert opt.extract_image_filter(im, im.objgen[0]) is None, (
            "Group 3 should be disallowed"
        )


def test_find_formx(resources):
    with pikepdf.open(resources / 'formxobject.pdf') as pdf:
        working, pagenos = opt._find_image_xrefs(pdf)
        assert len(working) == 1
        xref = next(iter(working))
        assert pagenos[xref] == 0


def test_find_formx_circular_reference(resources, tmp_path, caplog):
    """Regression for issue #1321.

    Some PDFs (notably PowerPoint exports) contain Form XObjects that
    reference themselves or each other in a cycle. The recursion guard in
    _find_image_xrefs_container only deduplicates *image* xrefs, so a Form
    XObject cycle would re-enter every branch until the depth limit fired,
    producing thousands of "Recursion depth exceeded" warnings (and minutes
    of wall-clock time on real-world inputs).
    """
    import logging

    src = resources / 'formxobject.pdf'
    out = tmp_path / 'circular_form.pdf'
    with pikepdf.open(src) as pdf:
        # /Form1 lives at xref 10. Replace its Resources.XObject with three
        # entries that all point back to /Form1 itself, creating a fan-out
        # cycle of branching factor 3.
        form = pdf.pages[0].obj.Resources.XObject.Form1
        form.Resources.XObject = Dictionary({'/Fm0': form, '/Fm1': form, '/Fm2': form})
        pdf.save(out)

    caplog.set_level(logging.WARNING, logger='ocrmypdf.optimize')
    with pikepdf.open(out) as pdf:
        opt._find_image_xrefs(pdf)

    n_warnings = sum(
        1 for r in caplog.records if 'Recursion depth exceeded' in r.getMessage()
    )
    # Without the fix this is in the tens of thousands.
    assert n_warnings == 0, (
        f"Form XObject cycle should be detected without depth-limit warnings; "
        f"got {n_warnings}"
    )


def test_extract_images_traps_errors_as_warning(resources, tmp_path, caplog):
    """Regression for issue #846.

    The optimizer is best-effort: any image it cannot process can simply be
    passed through unchanged. When extraction of an image raises (e.g. an
    exotic colorspace pikepdf cannot transcode), the user should see a concise
    warning that the image was left unchanged, not an alarming traceback
    logged at ERROR level.
    """
    import logging
    from unittest.mock import Mock

    def boom(*, pdf, root, image, xref, options):
        raise NotImplementedError("synthetic extraction failure")

    caplog.set_level(logging.DEBUG, logger='ocrmypdf.optimize')
    with pikepdf.open(resources / 'francais.pdf') as pdf:
        results = list(opt.extract_images(pdf, tmp_path, Mock(), boom))

    # The error is trapped, not propagated, and nothing is extracted.
    assert results == []
    # A friendly warning is emitted...
    assert any(
        r.levelno == logging.WARNING and 'left unchanged' in r.getMessage()
        for r in caplog.records
    )
    # ...and no traceback is logged at ERROR level or above.
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)


def test_extract_image_filter_with_pdf_image():
    image = Dictionary()
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
    image = Dictionary()
    image.Subtype = Name.Form
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_small_stream_size():
    image = Dictionary()
    image.Subtype = Name.Image
    image.Length = 50
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_small_dimensions():
    image = Dictionary()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 5
    image.Height = 5
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_multiple_compression_filters():
    image = Dictionary()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 10
    image.Height = 10
    image.BitsPerComponent = 8
    image.Filter = [Name.ASCII85Decode, Name.FlateDecode, Name.DCTDecode]
    assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_wide_gamut_image():
    image = Dictionary()
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
    image = Dictionary()
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
#     image = Dictionary()
#     image.Subtype = Name.Image
#     image.Length = 200
#     image.Width = 10
#     image.Height = 10
#     image.Filter = Name.FlateDecode
#     image.BitsPerComponent = 8
#     image.ColorSpace = Name.DeviceGray
#     image.Decode = [42, 0]
#     assert extract_image_filter(image, None) is None


def test_extract_image_filter_with_rgb_smask_matte():
    image = Dictionary()
    image.Subtype = Name.Image
    image.Length = 200
    image.Width = 10
    image.Height = 10
    image.Filter = Name.FlateDecode
    image.BitsPerComponent = 8
    image.ColorSpace = Name.DeviceRGB
    image.SMask = Dictionary(
        Type=Name.Image,
        Subtype=Name.Image,
        Length=200,
        Width=10,
        Height=10,
        Filter=Name.FlateDecode,
        BitsPerComponent=8,
        ColorSpace=Name.DeviceGray,
        Matte=Array([1, 2, 3]),
    )
    assert extract_image_filter(image, None) is None
