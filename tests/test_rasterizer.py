# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for the --rasterizer CLI option."""

from __future__ import annotations

from io import BytesIO

import img2pdf
import pikepdf
import pytest
from PIL import Image

from ocrmypdf._options import OcrOptions
from ocrmypdf._plugin_manager import get_plugin_manager
from ocrmypdf.helpers import IMG2PDF_KWARGS, Resolution

from .conftest import check_ocrmypdf

# Check if pypdfium2 is available
try:
    import pypdfium2  # noqa: F401

    PYPDFIUM_AVAILABLE = True
except ImportError:
    PYPDFIUM_AVAILABLE = False


class TestRasterizerOption:
    """Test the --rasterizer CLI option."""

    def test_rasterizer_auto_default(self, resources, outpdf):
        """Test that --rasterizer auto (default) works."""
        check_ocrmypdf(
            resources / 'graph.pdf',
            outpdf,
            '--rasterizer',
            'auto',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    def test_rasterizer_ghostscript(self, resources, outpdf):
        """Test that --rasterizer ghostscript works."""
        check_ocrmypdf(
            resources / 'graph.pdf',
            outpdf,
            '--rasterizer',
            'ghostscript',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    @pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed")
    def test_rasterizer_pypdfium(self, resources, outpdf):
        """Test that --rasterizer pypdfium works when pypdfium2 is installed."""
        check_ocrmypdf(
            resources / 'graph.pdf',
            outpdf,
            '--rasterizer',
            'pypdfium',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    def test_rasterizer_invalid(self):
        """Test that an invalid rasterizer value is rejected."""
        with pytest.raises(ValueError, match="rasterizer must be one of"):
            OcrOptions(
                input_file='test.pdf', output_file='out.pdf', rasterizer='invalid'
            )


class TestRasterizerWithRotation:
    """Test --rasterizer interaction with --rotate-pages."""

    def test_ghostscript_with_rotation(self, resources, outpdf):
        """Test Ghostscript rasterizer with page rotation."""
        check_ocrmypdf(
            resources / 'cardinal.pdf',
            outpdf,
            '--rasterizer',
            'ghostscript',
            '--rotate-pages',
            '--rotate-pages-threshold',
            '0.1',
            '--plugin',
            'tests/plugins/tesseract_cache.py',
        )

    @pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed")
    def test_pypdfium_with_rotation(self, resources, outpdf):
        """Test pypdfium rasterizer with page rotation."""
        check_ocrmypdf(
            resources / 'cardinal.pdf',
            outpdf,
            '--rasterizer',
            'pypdfium',
            '--rotate-pages',
            '--rotate-pages-threshold',
            '0.1',
            '--plugin',
            'tests/plugins/tesseract_cache.py',
        )

    def test_auto_with_rotation(self, resources, outpdf):
        """Test auto rasterizer with page rotation."""
        check_ocrmypdf(
            resources / 'cardinal.pdf',
            outpdf,
            '--rasterizer',
            'auto',
            '--rotate-pages',
            '--rotate-pages-threshold',
            '0.1',
            '--plugin',
            'tests/plugins/tesseract_cache.py',
        )


class TestRasterizerHookDirect:
    """Test rasterize_pdf_page hook directly with different rasterizer options."""

    def test_ghostscript_hook_respects_option(self, resources, tmp_path):
        """Test that Ghostscript hook returns None when pypdfium is requested."""
        pm = get_plugin_manager([])

        # Create options requesting pypdfium
        options = OcrOptions(
            input_file=resources / 'graph.pdf',
            output_file=tmp_path / 'out.pdf',
            rasterizer='pypdfium',
        )

        img = tmp_path / 'ghostscript_test.png'
        result = pm.rasterize_pdf_page(
            input_file=resources / 'graph.pdf',
            output_file=img,
            raster_device='pngmono',
            raster_dpi=Resolution(50, 50),
            page_dpi=Resolution(50, 50),
            pageno=1,
            rotation=0,
            filter_vector=False,
            stop_on_soft_error=True,
            options=options,
            use_cropbox=False,
        )
        # When pypdfium is requested:
        # - If pypdfium IS available, pypdfium handles it and returns the path
        # - If pypdfium is NOT available, both plugins return None
        #   (ghostscript returns None because pypdfium was requested,
        #    pypdfium returns None because it's not installed)
        if PYPDFIUM_AVAILABLE:
            assert result == img
        else:
            assert result is None

    def test_pypdfium_hook_respects_option(self, resources, tmp_path):
        """Test that pypdfium hook returns None when ghostscript is requested."""
        pm = get_plugin_manager([])

        # Create options requesting ghostscript
        options = OcrOptions(
            input_file=resources / 'graph.pdf',
            output_file=tmp_path / 'out.pdf',
            rasterizer='ghostscript',
        )

        img = tmp_path / 'pypdfium_test.png'
        result = pm.rasterize_pdf_page(
            input_file=resources / 'graph.pdf',
            output_file=img,
            raster_device='pngmono',
            raster_dpi=Resolution(50, 50),
            page_dpi=Resolution(50, 50),
            pageno=1,
            rotation=0,
            filter_vector=False,
            stop_on_soft_error=True,
            options=options,
            use_cropbox=False,
        )
        # Ghostscript should handle it
        assert result == img
        assert img.exists()

    def test_auto_uses_pypdfium_when_available(self, resources, tmp_path):
        """Test that auto mode uses pypdfium when available."""
        pm = get_plugin_manager([])

        options = OcrOptions(
            input_file=resources / 'graph.pdf',
            output_file=tmp_path / 'out.pdf',
            rasterizer='auto',
        )

        img = tmp_path / 'auto_test.png'
        result = pm.rasterize_pdf_page(
            input_file=resources / 'graph.pdf',
            output_file=img,
            raster_device='pngmono',
            raster_dpi=Resolution(50, 50),
            page_dpi=Resolution(50, 50),
            pageno=1,
            rotation=0,
            filter_vector=False,
            stop_on_soft_error=True,
            options=options,
            use_cropbox=False,
        )
        assert result == img
        assert img.exists()


def _create_gradient_image(width: int, height: int) -> Image.Image:
    """Create an image with multiple gradients to detect rasterization errors.

    The image contains:
    - Horizontal gradient from red to blue
    - Vertical gradient overlay from green to transparent
    - Diagonal bands for edge detection
    """
    img = Image.new('RGB', (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            # Horizontal gradient: red to blue
            r = int(255 * (1 - x / width))
            b = int(255 * (x / width))

            # Vertical gradient: add green component
            g = int(255 * (y / height))

            # Add diagonal bands for edge detection
            band = ((x + y) // 20) % 2
            if band:
                r = min(255, r + 40)
                g = min(255, g + 40)
                b = min(255, b + 40)

            pixels[x, y] = (r, g, b)

    return img


@pytest.fixture
def pdf_with_nonstandard_boxes(tmp_path):
    """Create a PDF with nonstandard MediaBox, TrimBox and CropBox."""
    # Create an image with gradients to detect rasterization errors
    img = _create_gradient_image(200, 300)
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    # Convert to PDF
    pdf_bytes = BytesIO()
    img2pdf.convert(
        img_bytes.read(),
        layout_fun=img2pdf.get_fixed_dpi_layout_fun((72, 72)),
        outputstream=pdf_bytes,
        **IMG2PDF_KWARGS,
    )
    pdf_bytes.seek(0)

    # Modify the PDF to have nonstandard boxes
    pdf_path = tmp_path / 'nonstandard_boxes.pdf'
    with pikepdf.open(pdf_bytes) as pdf:
        page = pdf.pages[0]
        # Set MediaBox larger than content
        page.MediaBox = pikepdf.Array([0, 0, 400, 500])
        # Set CropBox smaller - this is what viewers typically show
        page.CropBox = pikepdf.Array([50, 50, 350, 450])
        # Set TrimBox even smaller - indicates intended trim area
        page.TrimBox = pikepdf.Array([75, 75, 325, 425])
        pdf.save(pdf_path)

    return pdf_path


@pytest.fixture
def pdf_with_negative_mediabox(tmp_path):
    """Create a PDF with MediaBox that has negative origin coordinates."""
    # Create an image with gradients to detect rasterization errors
    img = _create_gradient_image(200, 300)
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    pdf_bytes = BytesIO()
    img2pdf.convert(
        img_bytes.read(),
        layout_fun=img2pdf.get_fixed_dpi_layout_fun((72, 72)),
        outputstream=pdf_bytes,
        **IMG2PDF_KWARGS,
    )
    pdf_bytes.seek(0)

    pdf_path = tmp_path / 'negative_mediabox.pdf'
    with pikepdf.open(pdf_bytes) as pdf:
        page = pdf.pages[0]
        # MediaBox with negative origin (valid PDF but unusual)
        page.MediaBox = pikepdf.Array([-100, -100, 300, 400])
        pdf.save(pdf_path)

    return pdf_path


class TestRasterizerWithNonStandardBoxes:
    """Test rasterizers with PDFs having nonstandard MediaBox/TrimBox/CropBox."""

    def test_ghostscript_nonstandard_boxes(self, pdf_with_nonstandard_boxes, outpdf):
        """Test Ghostscript handles nonstandard page boxes correctly."""
        check_ocrmypdf(
            pdf_with_nonstandard_boxes,
            outpdf,
            '--rasterizer',
            'ghostscript',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    @pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed")
    def test_pypdfium_nonstandard_boxes(self, pdf_with_nonstandard_boxes, outpdf):
        """Test pypdfium handles nonstandard page boxes correctly."""
        check_ocrmypdf(
            pdf_with_nonstandard_boxes,
            outpdf,
            '--rasterizer',
            'pypdfium',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    def test_ghostscript_negative_mediabox(self, pdf_with_negative_mediabox, outpdf):
        """Test Ghostscript handles negative MediaBox origin."""
        check_ocrmypdf(
            pdf_with_negative_mediabox,
            outpdf,
            '--rasterizer',
            'ghostscript',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    @pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed")
    def test_pypdfium_negative_mediabox(self, pdf_with_negative_mediabox, outpdf):
        """Test pypdfium handles negative MediaBox origin."""
        check_ocrmypdf(
            pdf_with_negative_mediabox,
            outpdf,
            '--rasterizer',
            'pypdfium',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

    def test_compare_rasterizers_nonstandard_boxes(
        self, pdf_with_nonstandard_boxes, tmp_path
    ):
        """Compare output dimensions between rasterizers for nonstandard boxes."""
        pm = get_plugin_manager([])

        options_gs = OcrOptions(
            input_file=pdf_with_nonstandard_boxes,
            output_file=tmp_path / 'out_gs.pdf',
            rasterizer='ghostscript',
        )

        img_gs = tmp_path / 'gs.png'
        pm.rasterize_pdf_page(
            input_file=pdf_with_nonstandard_boxes,
            output_file=img_gs,
            raster_device='png16m',
            raster_dpi=Resolution(72, 72),
            page_dpi=Resolution(72, 72),
            pageno=1,
            rotation=0,
            filter_vector=False,
            stop_on_soft_error=True,
            options=options_gs,
            use_cropbox=False,
        )

        with Image.open(img_gs) as im_gs:
            gs_size = im_gs.size

        if PYPDFIUM_AVAILABLE:
            options_pdfium = OcrOptions(
                input_file=pdf_with_nonstandard_boxes,
                output_file=tmp_path / 'out_pdfium.pdf',
                rasterizer='pypdfium',
            )

            img_pdfium = tmp_path / 'pdfium.png'
            pm.rasterize_pdf_page(
                input_file=pdf_with_nonstandard_boxes,
                output_file=img_pdfium,
                raster_device='png16m',
                raster_dpi=Resolution(72, 72),
                page_dpi=Resolution(72, 72),
                pageno=1,
                rotation=0,
                filter_vector=False,
                stop_on_soft_error=True,
                options=options_pdfium,
                use_cropbox=False,
            )

            with Image.open(img_pdfium) as im_pdfium:
                pdfium_size = im_pdfium.size

            # Both rasterizers should now produce MediaBox dimensions (400x500)
            # when use_cropbox=False (the default)
            assert gs_size == (400, 500), f"Ghostscript size: {gs_size}"
            assert pdfium_size == (400, 500), f"pypdfium size: {pdfium_size}"


class TestRasterizerWithRotationAndBoxes:
    """Test rasterizer + rotation + nonstandard boxes combinations."""

    # The pdf_with_nonstandard_boxes fixture creates a PDF with:
    # - MediaBox: [0, 0, 400, 500] → 400x500 points
    # - CropBox: [50, 50, 350, 450] → 300x400 points
    # - TrimBox: [75, 75, 325, 425] → 250x350 points
    #
    # With use_cropbox=False (default), both rasterizers use MediaBox
    MEDIABOX_WIDTH = 400
    MEDIABOX_HEIGHT = 500

    def _get_expected_size(self, rotation: int) -> tuple[int, int]:
        """Get expected image dimensions after rotation."""
        width, height = self.MEDIABOX_WIDTH, self.MEDIABOX_HEIGHT

        if rotation in (0, 180):
            return (width, height)
        else:  # 90, 270
            return (height, width)

    def test_ghostscript_rotation_dimensions(
        self, pdf_with_nonstandard_boxes, tmp_path
    ):
        """Test Ghostscript produces correct dimensions with rotation."""
        pm = get_plugin_manager([])

        options = OcrOptions(
            input_file=pdf_with_nonstandard_boxes,
            output_file=tmp_path / 'out.pdf',
            rasterizer='ghostscript',
        )

        for rotation in [0, 90, 180, 270]:
            img_path = tmp_path / f'gs_rot{rotation}.png'
            pm.rasterize_pdf_page(
                input_file=pdf_with_nonstandard_boxes,
                output_file=img_path,
                raster_device='png16m',
                raster_dpi=Resolution(72, 72),
                page_dpi=Resolution(72, 72),
                pageno=1,
                rotation=rotation,
                filter_vector=False,
                stop_on_soft_error=True,
                options=options,
                use_cropbox=False,
            )
            assert img_path.exists(), f"Failed to rasterize with rotation {rotation}"

            with Image.open(img_path) as img:
                expected = self._get_expected_size(rotation)
                # Allow small tolerance for rounding
                assert abs(img.size[0] - expected[0]) <= 2, (
                    f"Width mismatch at {rotation}°: got {img.size[0]}, "
                    f"expected {expected[0]}"
                )
                assert abs(img.size[1] - expected[1]) <= 2, (
                    f"Height mismatch at {rotation}°: got {img.size[1]}, "
                    f"expected {expected[1]}"
                )

    @pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed")
    def test_pypdfium_rotation_dimensions(self, pdf_with_nonstandard_boxes, tmp_path):
        """Test pypdfium produces correct dimensions with rotation."""
        pm = get_plugin_manager([])

        options = OcrOptions(
            input_file=pdf_with_nonstandard_boxes,
            output_file=tmp_path / 'out.pdf',
            rasterizer='pypdfium',
        )

        for rotation in [0, 90, 180, 270]:
            img_path = tmp_path / f'pdfium_rot{rotation}.png'
            pm.rasterize_pdf_page(
                input_file=pdf_with_nonstandard_boxes,
                output_file=img_path,
                raster_device='png16m',
                raster_dpi=Resolution(72, 72),
                page_dpi=Resolution(72, 72),
                pageno=1,
                rotation=rotation,
                filter_vector=False,
                stop_on_soft_error=True,
                options=options,
                use_cropbox=False,
            )
            assert img_path.exists(), f"Failed to rasterize with rotation {rotation}"

            with Image.open(img_path) as img:
                expected = self._get_expected_size(rotation)
                # Allow small tolerance for rounding
                assert abs(img.size[0] - expected[0]) <= 2, (
                    f"Width mismatch at {rotation}°: got {img.size[0]}, "
                    f"expected {expected[0]}"
                )
                assert abs(img.size[1] - expected[1]) <= 2, (
                    f"Height mismatch at {rotation}°: got {img.size[1]}, "
                    f"expected {expected[1]}"
                )

    @pytest.mark.skipif(not PYPDFIUM_AVAILABLE, reason="pypdfium2 not installed")
    def test_rasterizers_produce_same_dimensions(
        self, pdf_with_nonstandard_boxes, tmp_path
    ):
        """Verify ghostscript and pypdfium produce the same MediaBox dimensions.

        With use_cropbox=False (the default), both rasterizers should render
        to the MediaBox and produce identical dimensions.
        """
        pm = get_plugin_manager([])

        for rotation in [0, 90, 180, 270]:
            # Rasterize with Ghostscript
            gs_options = OcrOptions(
                input_file=pdf_with_nonstandard_boxes,
                output_file=tmp_path / 'out.pdf',
                rasterizer='ghostscript',
            )
            gs_img_path = tmp_path / f'gs_cmp_rot{rotation}.png'
            pm.rasterize_pdf_page(
                input_file=pdf_with_nonstandard_boxes,
                output_file=gs_img_path,
                raster_device='png16m',
                raster_dpi=Resolution(72, 72),
                page_dpi=Resolution(72, 72),
                pageno=1,
                rotation=rotation,
                filter_vector=False,
                stop_on_soft_error=True,
                options=gs_options,
                use_cropbox=False,
            )

            # Rasterize with pypdfium
            pdfium_options = OcrOptions(
                input_file=pdf_with_nonstandard_boxes,
                output_file=tmp_path / 'out.pdf',
                rasterizer='pypdfium',
            )
            pdfium_img_path = tmp_path / f'pdfium_cmp_rot{rotation}.png'
            pm.rasterize_pdf_page(
                input_file=pdf_with_nonstandard_boxes,
                output_file=pdfium_img_path,
                raster_device='png16m',
                raster_dpi=Resolution(72, 72),
                page_dpi=Resolution(72, 72),
                pageno=1,
                rotation=rotation,
                filter_vector=False,
                stop_on_soft_error=True,
                options=pdfium_options,
                use_cropbox=False,
            )

            # Verify both produce the same MediaBox dimensions
            with (
                Image.open(gs_img_path) as gs_img,
                Image.open(pdfium_img_path) as pdfium_img,
            ):
                expected = self._get_expected_size(rotation)

                assert abs(gs_img.size[0] - expected[0]) <= 2, (
                    f"GS width at {rotation}°: {gs_img.size[0]}, "
                    f"expected {expected[0]}"
                )
                assert abs(gs_img.size[1] - expected[1]) <= 2, (
                    f"GS height at {rotation}°: {gs_img.size[1]}, "
                    f"expected {expected[1]}"
                )
                assert abs(pdfium_img.size[0] - expected[0]) <= 2, (
                    f"pdfium width at {rotation}°: {pdfium_img.size[0]}, "
                    f"expected {expected[0]}"
                )
                assert abs(pdfium_img.size[1] - expected[1]) <= 2, (
                    f"pdfium height at {rotation}°: {pdfium_img.size[1]}, "
                    f"expected {expected[1]}"
                )
