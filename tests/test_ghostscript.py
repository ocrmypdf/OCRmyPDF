# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import secrets
import subprocess
import sys
from decimal import Decimal
from unittest.mock import patch

import pikepdf
import pytest
from packaging.version import Version
from PIL import Image, UnidentifiedImageError

from ocrmypdf._exec import ghostscript
from ocrmypdf._exec.ghostscript import DuplicateFilter, rasterize_pdf
from ocrmypdf.builtin_plugins.ghostscript import (
    PdfaImageCompression,
    _repair_gs106_jpeg_corruption,
    _resolve_auto_compression,
)
from ocrmypdf.exceptions import ColorConversionNeededError, ExitCode, InputFileError
from ocrmypdf.helpers import Resolution
from ocrmypdf.pluginspec import GhostscriptRasterDevice

from .conftest import check_ocrmypdf, run_ocrmypdf_api

# pylint: disable=redefined-outer-name


@pytest.fixture
def francais(resources):
    path = resources / 'francais.pdf'
    return path, pikepdf.open(path)


def test_rasterize_size(francais, outdir):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].mediabox[2], pdf.pages[0].mediabox[3])
    assert pdf.pages[0].mediabox[0] == pdf.pages[0].mediabox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('50.0'), Decimal('30.0')
    forced_dpi = Resolution(42.0, 4242.0)

    rasterize_pdf(
        path,
        outdir / 'out.png',
        raster_device=GhostscriptRasterDevice.PNGMONO,
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == target_size
        assert im.info['dpi'] == forced_dpi


def test_rasterize_rotated(francais, outdir, caplog):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].mediabox[2], pdf.pages[0].mediabox[3])
    assert pdf.pages[0].mediabox[0] == pdf.pages[0].mediabox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('50.0'), Decimal('30.0')
    forced_dpi = Resolution(42.0, 4242.0)

    caplog.set_level(logging.DEBUG)
    rasterize_pdf(
        path,
        outdir / 'out.png',
        raster_device=GhostscriptRasterDevice.PNGMONO,
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
        rotation=90,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == (target_size[1], target_size[0])
        assert im.info['dpi'] == forced_dpi.flip_axis()


def test_rasterize_low_dpi(francais, outdir):
    """Test that very low DPI values (below 10) produce correctly sized output.

    Ghostscript may fail with DPI values below 10. The workaround renders at
    a minimum of 10 DPI and resizes the output to match the expected dimensions.
    """
    path, pdf = francais
    page_size_pts = (pdf.pages[0].mediabox[2], pdf.pages[0].mediabox[3])
    assert pdf.pages[0].mediabox[0] == pdf.pages[0].mediabox[1] == 0
    page_size = (float(page_size_pts[0]) / 72, float(page_size_pts[1]) / 72)

    # Request a very small output (DPI below 10 on both axes)
    target_size = (5, 3)
    forced_dpi = Resolution(72.0, 72.0)

    rasterize_pdf(
        path,
        outdir / 'out_low_dpi.png',
        raster_device=GhostscriptRasterDevice.PNGMONO,
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
    )

    with Image.open(outdir / 'out_low_dpi.png') as im:
        assert im.size == target_size
        assert im.info['dpi'] == forced_dpi


def test_rasterize_low_dpi_one_axis(francais, outdir):
    """Test low DPI on only one axis produces correctly sized output."""
    path, pdf = francais
    page_size_pts = (pdf.pages[0].mediabox[2], pdf.pages[0].mediabox[3])
    assert pdf.pages[0].mediabox[0] == pdf.pages[0].mediabox[1] == 0
    page_size = (float(page_size_pts[0]) / 72, float(page_size_pts[1]) / 72)

    # Request low DPI on X axis only (below 10), normal on Y axis
    target_size = (5, 50)
    forced_dpi = Resolution(72.0, 72.0)

    rasterize_pdf(
        path,
        outdir / 'out_low_dpi_x.png',
        raster_device=GhostscriptRasterDevice.PNGMONO,
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
    )

    with Image.open(outdir / 'out_low_dpi_x.png') as im:
        assert im.size == target_size
        assert im.info['dpi'] == forced_dpi


def _capture_rasterize_args(resources, outdir, raster_device):
    """Run rasterize_pdf with the gs subprocess mocked; return the gs argv."""
    out = outdir / 'out.png'
    captured = {}

    def fake_run(args, **kwargs):
        captured['args'] = list(args)
        # Produce a valid PNG so rasterize_pdf's post-processing succeeds.
        Image.new('RGB', (2, 2)).save(out)
        return subprocess.CompletedProcess(args, returncode=0, stdout=b'', stderr=b'')

    with patch('ocrmypdf._exec.ghostscript.run', side_effect=fake_run):
        rasterize_pdf(
            resources / 'francais.pdf',
            out,
            raster_device=raster_device,
            raster_dpi=Resolution(150.0, 150.0),
        )
    return captured['args']


@pytest.mark.parametrize(
    'raster_device',
    [
        GhostscriptRasterDevice.PNGGRAY,
        GhostscriptRasterDevice.PNG256,
        GhostscriptRasterDevice.PNG16M,
    ],
)
def test_rasterize_antialiases_contone_devices(resources, outdir, raster_device):
    """Contone raster devices receive anti-aliasing flags to aid OCR.

    Ghostscript 10.x renders aliased glyphs that OCR misreads as extra word
    breaks; -dTextAlphaBits/-dGraphicsAlphaBits markedly improve accuracy,
    especially for small fonts at moderate DPI (see issue #1439).
    """
    args = _capture_rasterize_args(resources, outdir, raster_device)
    assert '-dTextAlphaBits=4' in args
    assert '-dGraphicsAlphaBits=4' in args


@pytest.mark.parametrize(
    'raster_device',
    [GhostscriptRasterDevice.PNGMONO, GhostscriptRasterDevice.PNGMONOD],
)
def test_rasterize_no_antialias_on_mono_devices(resources, outdir, raster_device):
    """1-bit mono devices must not receive alpha-bit flags.

    Older Ghostscript versions reject -dTextAlphaBits on 1-bit devices, and
    pngmonod performs its own anti-aliased downscaling.
    """
    args = _capture_rasterize_args(resources, outdir, raster_device)
    assert not any(a.startswith('-dTextAlphaBits') for a in args)
    assert not any(a.startswith('-dGraphicsAlphaBits') for a in args)


def test_generate_pdfa_default_jpeg_quality(outdir):
    """When jpeg_quality is None, Ghostscript receives -dJPEGQ=95 (default)."""
    with (
        patch('ocrmypdf._exec.ghostscript.version', return_value=Version('10.05.1')),
        patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as run_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ['gs'], returncode=0, stdout='', stderr=''
        )
        ghostscript.generate_pdfa(
            pdf_pages=[outdir / 'input.pdf'],
            output_file=outdir / 'out.pdf',
            compression='auto',
            color_conversion_strategy='LeaveColorUnchanged',
        )

    args = run_mock.call_args.args[0]
    assert '-dJPEGQ=95' in args
    # No downsample switches when jpeg_maxdpi is not set
    assert not any(a.startswith('-dDownsampleColorImages') for a in args)
    assert not any(a.startswith('-dColorImageResolution') for a in args)


def test_generate_pdfa_uses_user_jpeg_quality(outdir):
    with (
        patch('ocrmypdf._exec.ghostscript.version', return_value=Version('10.05.1')),
        patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as run_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ['gs'], returncode=0, stdout='', stderr=''
        )
        ghostscript.generate_pdfa(
            pdf_pages=[outdir / 'input.pdf'],
            output_file=outdir / 'out.pdf',
            compression='jpeg',
            color_conversion_strategy='RGB',
            jpeg_quality=72,
        )

    args = run_mock.call_args.args[0]
    assert '-dJPEGQ=72' in args
    assert '-dJPEGQ=95' not in args


def test_generate_pdfa_jpeg_quality_zero_is_max_compression(outdir):
    """Explicit jpeg_quality=0 must reach Ghostscript as -dJPEGQ=0.

    Ghostscript accepts 0 as a valid quality value (maximum compression);
    it must not be silently replaced by the default 95.
    """
    with (
        patch('ocrmypdf._exec.ghostscript.version', return_value=Version('10.05.1')),
        patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as run_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ['gs'], returncode=0, stdout='', stderr=''
        )
        ghostscript.generate_pdfa(
            pdf_pages=[outdir / 'input.pdf'],
            output_file=outdir / 'out.pdf',
            compression='jpeg',
            color_conversion_strategy='RGB',
            jpeg_quality=0,
        )

    args = run_mock.call_args.args[0]
    assert '-dJPEGQ=0' in args
    assert '-dJPEGQ=95' not in args


def test_generate_pdfa_honors_jpeg_maxdpi(outdir):
    with (
        patch('ocrmypdf._exec.ghostscript.version', return_value=Version('10.05.1')),
        patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as run_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ['gs'], returncode=0, stdout='', stderr=''
        )
        ghostscript.generate_pdfa(
            pdf_pages=[outdir / 'input.pdf'],
            output_file=outdir / 'out.pdf',
            compression='auto',
            color_conversion_strategy='LeaveColorUnchanged',
            jpeg_maxdpi=300,
        )

    args = run_mock.call_args.args[0]
    assert '-dJPEGQ=95' in args
    assert '-dDownsampleColorImages=true' in args
    assert '-dColorImageDownsampleThreshold=1.0' in args
    assert '-dDownsampleGrayImages=true' in args
    assert '-dGrayImageDownsampleThreshold=1.0' in args
    assert '-dDownsampleMonoImages=true' in args
    assert '-dMonoImageDownsampleThreshold=1.0' in args
    assert '-dColorImageResolution=300' in args
    assert '-dGrayImageResolution=300' in args
    assert '-dMonoImageResolution=300' in args


def test_ghostscript_jpeg_options_via_cli(resources, outpdf):
    """End-to-end: CLI flags reach the ghostscript plugin namespace."""
    with patch(
        'ocrmypdf._exec.ghostscript.generate_pdfa',
        wraps=ghostscript.generate_pdfa,
    ) as gen_mock:
        run_ocrmypdf_api(
            resources / 'francais.pdf',
            outpdf,
            '--output-type',
            'pdfa',
            '--ghostscript-jpeg-quality',
            '60',
            '--ghostscript-jpeg-maxdpi',
            '150',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )
    assert gen_mock.called
    call_kwargs = gen_mock.call_args.kwargs
    assert call_kwargs['jpeg_quality'] == 60
    assert call_kwargs['jpeg_maxdpi'] == 150


def test_gs_render_failure(resources, outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'blank.pdf',
        outpdf,
        '--output-type',
        'pdfa',  # Required to trigger Ghostscript PDF/A generation
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_render_failure.py',
    )
    assert 'TEST ERROR: gs_render_failure.py' in caplog.text
    assert exitcode == ExitCode.child_process_error


def test_gs_raster_failure(resources, outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_raster_failure.py',
    )
    assert 'TEST ERROR: gs_raster_failure.py' in caplog.text
    assert exitcode == ExitCode.child_process_error


def test_ghostscript_pdfa_failure(resources, outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'francais.pdf',
        outpdf,
        '--output-type',
        'pdfa',  # Required to trigger Ghostscript PDF/A generation
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_pdfa_failure.py',
    )
    assert exitcode == ExitCode.pdfa_conversion_failed, (
        "Unexpected return when PDF/A fails"
    )


def test_ghostscript_feature_elision(resources, outpdf):
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_feature_elision.py',
    )


def test_ghostscript_mandatory_color_conversion(resources, outpdf):
    with pytest.raises(ColorConversionNeededError):
        check_ocrmypdf(
            resources / 'jbig2_baddevicen.pdf',
            outpdf,
            '--output-type',
            'pdfa',  # Required to trigger Ghostscript PDF/A generation
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )


def _run_generate_pdfa_with_devicen_warning(outdir, color_conversion_strategy):
    """Invoke generate_pdfa with Ghostscript mocked to emit the DeviceN warning.

    Ghostscript emits this warning when it writes a DeviceN colorspace with an
    inappropriate alternate, i.e. when it could not normalize the colorspace for
    PDF/A. The output is then liable to render blank in viewers such as Adobe
    Reader (see issue #1187), regardless of which conversion strategy was
    requested.
    """
    (outdir / 'input.pdf').write_bytes(b'%PDF-1.5\n%fake\n')
    with (
        patch('ocrmypdf._exec.ghostscript.version', return_value=Version('10.05.1')),
        patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as run_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ['gs'],
            returncode=0,
            stdout='',
            stderr='Attempting to write a DeviceN space with an inappropriate '
            'alternate, reverting to the alternate color space.',
        )
        ghostscript.generate_pdfa(
            pdf_pages=[outdir / 'input.pdf'],
            output_file=outdir / 'out.pdf',
            compression='auto',
            color_conversion_strategy=color_conversion_strategy,
        )


def test_devicen_warning_default_strategy_raises_with_guidance(outdir):
    """Default (no conversion): raise and tell the user to pick a strategy."""
    with pytest.raises(ColorConversionNeededError) as exc_info:
        _run_generate_pdfa_with_devicen_warning(outdir, 'LeaveColorUnchanged')
    message = str(exc_info.value)
    assert '--color-conversion-strategy' in message
    assert 'RGB' in message


@pytest.mark.parametrize(
    'strategy',
    [
        # A strategy that genuinely cannot fix the colorspace; confirmed in #1187.
        'UseDeviceIndependentColor',
        # A normally-effective strategy that nonetheless failed on this input:
        # if Ghostscript still warns, the output is still broken and we must not
        # silently pass it through (the behaviour PR #1692 would have introduced).
        'RGB',
    ],
)
def test_devicen_warning_persists_despite_strategy_still_raises(outdir, strategy):
    """If the warning survives the requested conversion, the output is broken.

    We must still raise rather than silently emit a PDF/A that may render blank.
    The guidance should acknowledge that the chosen strategy did not work and
    point at strategies that do (or --output-type pdf).
    """
    with pytest.raises(ColorConversionNeededError) as exc_info:
        _run_generate_pdfa_with_devicen_warning(outdir, strategy)
    message = str(exc_info.value)
    assert strategy in message
    assert '--output-type pdf' in message


def test_no_devicen_warning_does_not_raise(outdir):
    """When Ghostscript does not warn, conversion succeeded; never raise."""
    (outdir / 'input.pdf').write_bytes(b'%PDF-1.5\n%fake\n')
    with (
        patch('ocrmypdf._exec.ghostscript.version', return_value=Version('10.05.1')),
        patch('ocrmypdf._exec.ghostscript.run_polling_stderr') as run_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ['gs'], returncode=0, stdout='', stderr=''
        )
        # Must not raise for any strategy when there is no DeviceN warning.
        ghostscript.generate_pdfa(
            pdf_pages=[outdir / 'input.pdf'],
            output_file=outdir / 'out.pdf',
            compression='auto',
            color_conversion_strategy='RGB',
        )


def test_rasterize_pdf_errors(resources, no_outpdf, caplog):
    with patch('ocrmypdf._exec.ghostscript.run') as mock:
        # ghostscript can produce empty files with return code 0
        mock.return_value = subprocess.CompletedProcess(
            ['fakegs'], returncode=0, stdout=b'', stderr=b'error this is an error'
        )
        with pytest.raises(UnidentifiedImageError):
            rasterize_pdf(
                resources / 'francais.pdf',
                no_outpdf,
                raster_device=GhostscriptRasterDevice.PNGMONO,
                raster_dpi=Resolution(100, 100),
            )
        assert "this is an error" in caplog.text
        assert "invalid page image file" in caplog.text


class TestDuplicateFilter:
    @pytest.fixture(scope='function')
    def duplicate_filter_logger(self):
        # token_urlsafe: ensure the logger has a unique name so tests are isolated
        logger = logging.getLogger(__name__ + secrets.token_urlsafe(8))
        logger.setLevel(logging.DEBUG)
        logger.addFilter(DuplicateFilter(logger))
        return logger

    @pytest.mark.xfail(
        (3, 13, 3) <= sys.version_info[:3] <= (3, 13, 5),
        reason="https://github.com/python/cpython/pull/135858",
    )
    def test_filter_duplicate_messages(self, duplicate_filter_logger, caplog):
        log = duplicate_filter_logger
        log.error("test error message")
        log.error("test error message")
        log.error("test error message")
        log.error("another error message")
        log.error("another error message")
        log.error("yet another error message")

        assert len(caplog.records) == 5
        assert caplog.records[0].msg == "test error message"
        assert caplog.records[1].msg == "(suppressed 2 repeated lines)"
        assert caplog.records[2].msg == "another error message"
        assert caplog.records[3].msg == "(suppressed 1 repeated lines)"
        assert caplog.records[4].msg == "yet another error message"

    def test_filter_does_not_affect_unique_messages(
        self, duplicate_filter_logger, caplog
    ):
        log = duplicate_filter_logger
        log.error("test error message")
        log.error("another error message")
        log.error("yet another error message")

        assert len(caplog.records) == 3
        assert caplog.records[0].msg == "test error message"
        assert caplog.records[1].msg == "another error message"
        assert caplog.records[2].msg == "yet another error message"

    @pytest.mark.xfail(
        (3, 13, 3) <= sys.version_info[:3] <= (3, 13, 5),
        reason="https://github.com/python/cpython/pull/135858",
    )
    def test_filter_alt_messages(self, duplicate_filter_logger, caplog):
        log = duplicate_filter_logger
        log.error("test error message")
        log.error("another error message")
        log.error("test error message")
        log.error("another error message")
        log.error("test error message")
        log.error("test error message")
        log.error("another error message")
        log.error("yet another error message")

        assert len(caplog.records) == 4
        assert caplog.records[0].msg == "test error message"
        assert caplog.records[1].msg == "another error message"
        assert caplog.records[2].msg == "(suppressed 5 repeated lines)"
        assert caplog.records[3].msg == "yet another error message"


@pytest.fixture
def pdf_with_invalid_image(outdir):
    # issue 1451
    Name = pikepdf.Name
    pdf = pikepdf.new()
    pdf.add_blank_page()
    pdf.pages[0].Contents = pdf.make_stream(b'612 0 0 612 0 0 cm /Image Do')
    # Create an invalid image object that has both ColorSpace and ImageMask set
    pdf.pages[0].Resources = pikepdf.Dictionary(
        XObject=pdf.make_indirect(
            pikepdf.Dictionary(
                Image=pdf.make_stream(
                    b"\xf0\x0f" * 8,
                    ColorSpace=Name.DeviceGray,
                    BitsPerComponent=1,
                    Width=8,
                    Height=8,
                    ImageMask=True,
                    Subtype=Name.Image,
                    Type=Name.XObject,
                )
            )
        )
    )
    pdf.save(outdir / 'invalid_image.pdf')
    pdf.save('invalid_image.pdf')
    return outdir / 'invalid_image.pdf'


@pytest.mark.xfail(
    ghostscript.version() < Version('10.04.0'),
    reason="Older Ghostscript behavior is different",
)
def test_recoverable_image_error(pdf_with_invalid_image, outdir, caplog):
    # When stop_on_error is False, we expect Ghostscript to print an error
    # but continue
    rasterize_pdf(
        outdir / 'invalid_image.pdf',
        outdir / 'out.png',
        raster_device=GhostscriptRasterDevice.PNGMONO,
        raster_dpi=Resolution(10, 10),
        stop_on_error=False,
    )
    assert 'Image has both ImageMask and ColorSpace' in caplog.text


@pytest.mark.xfail(
    ghostscript.version() < Version('10.04.0'),
    reason="Older Ghostscript behavior is different",
)
def test_recoverable_image_error_with_stop(pdf_with_invalid_image, outdir, caplog):
    # When stop_on_error is True, Ghostscript will print an error and exit
    # but still produce a viable image. We intercept this case and raise
    # InputFileError because it will contain an image of the whole page minus
    # the image we are rendering.
    with pytest.raises(
        InputFileError, match="Try using --continue-on-soft-render-error"
    ):
        rasterize_pdf(
            outdir / 'invalid_image.pdf',
            outdir / 'out.png',
            raster_device=GhostscriptRasterDevice.PNGMONO,
            raster_dpi=Resolution(100, 100),
            stop_on_error=True,
        )
    # out2.png will not be created; if it were it would be blank.


class TestGs106JpegCorruptionRepair:
    """Test the Ghostscript 10.6 JPEG corruption repair function."""

    @pytest.fixture
    def create_damaged_pdf(self, resources, outdir):
        """Create a damaged PDF by truncating JPEG data by 2 bytes."""

        def _create_damaged(source_pdf_name='francais.pdf', truncate_bytes=2):
            source_path = resources / source_pdf_name
            damaged_path = outdir / 'damaged.pdf'

            with pikepdf.open(source_path) as pdf:
                # Find and truncate DCTDecode images
                Name = pikepdf.Name
                damaged_count = 0
                for page in pdf.pages:
                    if Name.Resources not in page:
                        continue
                    resources_dict = page[Name.Resources]
                    if Name.XObject not in resources_dict:
                        continue
                    for key in resources_dict[Name.XObject].keys():
                        obj = resources_dict[Name.XObject][key]
                        if obj.get(Name.Subtype) != Name.Image:
                            continue
                        if obj.get(Name.Filter) != Name.DCTDecode:
                            continue
                        # Truncate the JPEG data
                        original_bytes = obj.read_raw_bytes()
                        truncated_bytes = original_bytes[:-truncate_bytes]
                        obj.write(truncated_bytes, filter=Name.DCTDecode)
                        damaged_count += 1

                pdf.save(damaged_path)
                return source_path, damaged_path, damaged_count

        return _create_damaged

    def test_repair_truncated_jpeg(self, create_damaged_pdf, caplog):
        """Test that truncated JPEG images are repaired."""
        caplog.set_level(logging.DEBUG)
        source_path, damaged_path, damaged_count = create_damaged_pdf()

        assert damaged_count > 0, "Test PDF should have DCTDecode images"

        # Get original image bytes for comparison
        with pikepdf.open(source_path) as pdf:
            Name = pikepdf.Name
            original_bytes_list = []
            for page in pdf.pages:
                if Name.Resources not in page:
                    continue
                resources_dict = page[Name.Resources]
                if Name.XObject not in resources_dict:
                    continue
                for key in resources_dict[Name.XObject].keys():
                    obj = resources_dict[Name.XObject][key]
                    if obj.get(Name.Subtype) != Name.Image:
                        continue
                    if obj.get(Name.Filter) != Name.DCTDecode:
                        continue
                    original_bytes_list.append(obj.read_raw_bytes())

        # Run the repair function
        repaired = _repair_gs106_jpeg_corruption(source_path, damaged_path)
        assert repaired is True, "Repair should have been performed"

        # Verify the repaired PDF has correct image bytes
        with pikepdf.open(damaged_path) as pdf:
            Name = pikepdf.Name
            repaired_bytes_list = []
            for page in pdf.pages:
                if Name.Resources not in page:
                    continue
                resources_dict = page[Name.Resources]
                if Name.XObject not in resources_dict:
                    continue
                for key in resources_dict[Name.XObject].keys():
                    obj = resources_dict[Name.XObject][key]
                    if obj.get(Name.Subtype) != Name.Image:
                        continue
                    if obj.get(Name.Filter) != Name.DCTDecode:
                        continue
                    repaired_bytes_list.append(obj.read_raw_bytes())

        assert len(repaired_bytes_list) == len(original_bytes_list)
        for orig, repaired_bytes in zip(
            original_bytes_list, repaired_bytes_list, strict=False
        ):
            assert orig == repaired_bytes, "Repaired bytes should match original"

        # Check that error/warning was logged
        assert "JPEG corruption detected" in caplog.text

    def test_no_repair_when_not_truncated(self, resources, outdir, caplog):
        """Test that no repair is done when images are not truncated."""
        caplog.set_level(logging.DEBUG)
        source_path = resources / 'francais.pdf'

        # Copy source to output (no damage)
        output_path = outdir / 'undamaged.pdf'
        with pikepdf.open(source_path) as pdf:
            pdf.save(output_path)

        # Run the repair function - should not repair anything
        repaired = _repair_gs106_jpeg_corruption(source_path, output_path)
        assert repaired is False, "No repair should have been performed"
        assert "JPEG corruption detected" not in caplog.text

    def test_no_repair_when_truncation_too_large(self, create_damaged_pdf, caplog):
        """Test that images truncated by more than 15 bytes are not repaired."""
        caplog.set_level(logging.DEBUG)
        source_path, damaged_path, _ = create_damaged_pdf(truncate_bytes=20)

        repaired = _repair_gs106_jpeg_corruption(source_path, damaged_path)
        assert repaired is False, "Should not repair truncation > 15 bytes"
        assert "JPEG corruption detected" not in caplog.text


@pytest.mark.parametrize(
    ('compression', 'optimize', 'expected'),
    [
        # auto coerces to lossless only at -O0; -O1 is a historical exception
        # that keeps Ghostscript's (possibly lossy) heuristic, as do -O2/-O3
        (PdfaImageCompression.AUTO, 0, PdfaImageCompression.LOSSLESS),
        (PdfaImageCompression.AUTO, 1, PdfaImageCompression.AUTO),
        (PdfaImageCompression.AUTO, 2, PdfaImageCompression.AUTO),
        (PdfaImageCompression.AUTO, 3, PdfaImageCompression.AUTO),
        # explicit choices are always respected, regardless of optimize level
        (PdfaImageCompression.JPEG, 0, PdfaImageCompression.JPEG),
        (PdfaImageCompression.JPEG, 1, PdfaImageCompression.JPEG),
        (PdfaImageCompression.LOSSLESS, 1, PdfaImageCompression.LOSSLESS),
        (PdfaImageCompression.LOSSLESS, 3, PdfaImageCompression.LOSSLESS),
    ],
)
def test_resolve_auto_compression(compression, optimize, expected):
    assert _resolve_auto_compression(compression, optimize) == expected


def _capture_generate_pdfa_args(tmp_path, compression):
    """Run generate_pdfa with a mocked Ghostscript and return the argv it built."""
    from subprocess import CompletedProcess

    captured = {}

    def fake_run(args, **kwargs):
        captured['args'] = list(args)
        return CompletedProcess(args, 0, None, stderr='')

    out = tmp_path / 'out.pdf'
    with patch('ocrmypdf._exec.ghostscript.run_polling_stderr', side_effect=fake_run):
        ghostscript.generate_pdfa(
            pdf_pages=['dummy.pdf'],
            output_file=out,
            compression=compression,
            color_conversion_strategy='RGB',
        )
    return captured['args']


def test_lossless_compression_passes_through_jpegs(tmp_path):
    # Re-encoding an existing JPEG losslessly only bloats it (the lossy data is
    # already baked in), so lossless mode must let Ghostscript pass JPEGs through
    # untouched while still keeping lossless images lossless.
    args = _capture_generate_pdfa_args(tmp_path, 'lossless')
    assert '-dPassThroughJPEGImages=true' in args
    assert '-dColorImageFilter=/FlateEncode' in args


def test_jpeg_compression_does_not_force_passthrough(tmp_path):
    args = _capture_generate_pdfa_args(tmp_path, 'jpeg')
    assert '-dPassThroughJPEGImages=true' not in args
