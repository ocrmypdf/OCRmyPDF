# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for NullOcrEngine (--ocr-engine none).

Tests verify that the Null OCR engine exists and functions correctly
for scenarios where users want PDF processing without OCR.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestNullOcrEngineExists:
    """Test that NullOcrEngine plugin exists and is loadable."""

    def test_null_ocr_module_importable(self):
        """null_ocr module should be importable."""
        from ocrmypdf.builtin_plugins import null_ocr

        assert null_ocr is not None

    def test_null_ocr_engine_class_exists(self):
        """NullOcrEngine class should exist."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        assert NullOcrEngine is not None


class TestNullOcrEngineInterface:
    """Test NullOcrEngine implements OcrEngine interface."""

    def test_version_returns_none(self):
        """NullOcrEngine.version() should return 'none'."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        assert NullOcrEngine.version() == "none"

    def test_creator_tag(self):
        """NullOcrEngine.creator_tag() should indicate no OCR."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        tag = NullOcrEngine.creator_tag(MagicMock())
        tag_lower = tag.lower()
        assert "no ocr" in tag_lower or "null" in tag_lower or "none" in tag_lower

    def test_languages_returns_empty_set(self):
        """NullOcrEngine.languages() should return empty set."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        langs = NullOcrEngine.languages(MagicMock())
        assert langs == set()

    def test_supports_generate_ocr_returns_true(self):
        """NullOcrEngine should support generate_ocr()."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        assert NullOcrEngine.supports_generate_ocr() is True

    def test_get_orientation_returns_zero(self):
        """NullOcrEngine.get_orientation() should return angle=0."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        result = NullOcrEngine.get_orientation(Path("test.png"), MagicMock())
        assert result.angle == 0

    def test_get_deskew_returns_zero(self):
        """NullOcrEngine.get_deskew() should return 0.0."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        result = NullOcrEngine.get_deskew(Path("test.png"), MagicMock())
        assert result == 0.0


class TestNullOcrEngineGenerateOcr:
    """Test NullOcrEngine.generate_ocr() output."""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a simple test image."""
        from PIL import Image

        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (100, 100), color='white')
        img.save(img_path, dpi=(300, 300))
        return img_path

    def test_generate_ocr_returns_tuple(self, sample_image):
        """generate_ocr() should return (OcrElement, str) tuple."""
        from ocrmypdf import OcrElement
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        result = NullOcrEngine.generate_ocr(sample_image, MagicMock(), 0)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], OcrElement)
        assert isinstance(result[1], str)

    def test_generate_ocr_returns_empty_text(self, sample_image):
        """generate_ocr() should return empty text string."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        _, text = NullOcrEngine.generate_ocr(sample_image, MagicMock(), 0)

        assert text == ""

    def test_generate_ocr_returns_page_element(self, sample_image):
        """generate_ocr() should return OcrElement with ocr_class PAGE."""
        from ocrmypdf import OcrClass
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        ocr_tree, _ = NullOcrEngine.generate_ocr(sample_image, MagicMock(), 0)

        assert ocr_tree.ocr_class == OcrClass.PAGE

    def test_generate_ocr_page_has_correct_dimensions(self, sample_image):
        """generate_ocr() page element should have image dimensions."""
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        ocr_tree, _ = NullOcrEngine.generate_ocr(sample_image, MagicMock(), 0)

        # Image is 100x100
        assert ocr_tree.bbox.right == 100
        assert ocr_tree.bbox.bottom == 100


class TestOcrEngineOption:
    """Test --ocr-engine CLI option."""

    def test_ocr_engine_option_accepted(self):
        """CLI should accept --ocr-engine option."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        # Should not raise
        args = parser.parse_args(['--ocr-engine', 'none', 'in.pdf', 'out.pdf'])
        assert args.ocr_engine == 'none'

    def test_ocr_engine_choices_include_none(self):
        """--ocr-engine should include 'none' as a choice."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        # Find the --ocr-engine action
        for action in parser._actions:
            if '--ocr-engine' in action.option_strings:
                assert 'none' in action.choices
                break
        else:
            pytest.fail("--ocr-engine option not found")

    def test_ocr_engine_choices_include_auto(self):
        """--ocr-engine should include 'auto' as default."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        for action in parser._actions:
            if '--ocr-engine' in action.option_strings:
                assert 'auto' in action.choices
                assert action.default == 'auto'
                break


class TestNullOcrEngineInertOptions:
    """Warn about options the null engine cannot honor.

    Skew and orientation are measured by the OCR engine, and NullOcrEngine
    measures neither, so --deskew and --rotate-pages are silently inert under
    --ocr-engine none.
    """

    @staticmethod
    def _warnings(caplog, **kwargs) -> list[str]:
        import logging

        from ocrmypdf._options import OcrOptions
        from ocrmypdf._validation_coordinator import ValidationCoordinator
        from ocrmypdf.api import setup_plugin_infrastructure

        setup_plugin_infrastructure()
        options = OcrOptions(
            input_file=Path('in.pdf'), output_file=Path('out.pdf'), **kwargs
        )
        caplog.clear()
        with caplog.at_level(
            logging.WARNING, logger='ocrmypdf._validation_coordinator'
        ):
            ValidationCoordinator(MagicMock())._validate_cross_cutting_concerns(options)
        return [record.getMessage() for record in caplog.records]

    @pytest.mark.parametrize(
        'kwargs, expected',
        [
            ({'deskew': True}, ['--deskew']),
            ({'rotate_pages': True}, ['--rotate-pages']),
            ({'deskew': True, 'rotate_pages': True}, ['--deskew', '--rotate-pages']),
        ],
    )
    def test_warns_for_detection_dependent_options(self, caplog, kwargs, expected):
        """--ocr-engine none should name every inert detection option."""
        messages = self._warnings(caplog, ocr_engine='none', **kwargs)

        assert len(messages) == 1
        for option in expected:
            assert option in messages[0]
        for option in {'--deskew', '--rotate-pages'} - set(expected):
            assert option not in messages[0]

    def test_no_warning_without_the_inert_options(self, caplog):
        """--ocr-engine none on its own is a supported, silent configuration."""
        assert self._warnings(caplog, ocr_engine='none') == []

    @pytest.mark.parametrize('engine', ['auto', 'tesseract'])
    def test_no_warning_for_detecting_engines(self, caplog, engine):
        """Engines that do detect skew/orientation must not be warned about."""
        messages = self._warnings(
            caplog, ocr_engine=engine, deskew=True, rotate_pages=True
        )

        assert messages == []


class TestNullOcrEngineVectorPage:
    """Force-OCR a vector-only page, which has no image DPI in pdfinfo."""

    def test_force_ocr_vector_page(self, resources, outpdf):
        import pikepdf

        from .conftest import check_ocrmypdf

        check_ocrmypdf(
            resources / 'vector.pdf',
            outpdf,
            '--force-ocr',
            '--ocr-engine',
            'none',
            '--output-type',
            'pdf',
        )
        with pikepdf.open(outpdf) as pdf:
            assert len(pdf.pages) == 1
