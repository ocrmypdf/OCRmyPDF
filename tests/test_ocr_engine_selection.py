# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for OCR engine selection mechanism.

Tests verify that the --ocr-engine option works correctly and that
engine-specific options are available.
"""

from __future__ import annotations

import pytest


class TestOcrEngineCliOption:
    """Test --ocr-engine CLI option."""

    def test_ocr_engine_option_exists(self):
        """CLI should have --ocr-engine option."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        option_strings = []
        for action in parser._actions:
            option_strings.extend(action.option_strings)

        assert '--ocr-engine' in option_strings

    def test_ocr_engine_accepts_tesseract(self):
        """--ocr-engine should accept 'tesseract'."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        args = parser.parse_args(['--ocr-engine', 'tesseract', 'in.pdf', 'out.pdf'])
        assert args.ocr_engine == 'tesseract'

    def test_ocr_engine_accepts_auto(self):
        """--ocr-engine should accept 'auto'."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        args = parser.parse_args(['--ocr-engine', 'auto', 'in.pdf', 'out.pdf'])
        assert args.ocr_engine == 'auto'

    def test_ocr_engine_accepts_none(self):
        """--ocr-engine should accept 'none'."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        args = parser.parse_args(['--ocr-engine', 'none', 'in.pdf', 'out.pdf'])
        assert args.ocr_engine == 'none'

    def test_ocr_engine_default_is_auto(self):
        """--ocr-engine should default to 'auto'."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        args = parser.parse_args(['in.pdf', 'out.pdf'])
        assert args.ocr_engine == 'auto'

    def test_ocr_engine_rejects_invalid(self):
        """--ocr-engine should reject invalid values."""
        from ocrmypdf.cli import get_parser

        parser = get_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(['--ocr-engine', 'invalid_engine', 'in.pdf', 'out.pdf'])


class TestOcrEngineOptionsModel:
    """Test OcrOptions has ocr_engine field."""

    def test_ocr_options_has_ocr_engine_field(self):
        """OcrOptions should have ocr_engine field."""
        from ocrmypdf._options import OcrOptions

        # Check field exists in model
        assert 'ocr_engine' in OcrOptions.model_fields


class TestOcrEnginePluginSelection:
    """Test that get_ocr_engine() hook selects correct engine based on options."""

    def test_tesseract_selected_when_auto(self):
        """TesseractOcrEngine should be returned when ocr_engine='auto'."""
        from unittest.mock import MagicMock

        from ocrmypdf.builtin_plugins import tesseract_ocr
        from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOcrEngine

        options = MagicMock()
        options.ocr_engine = 'auto'

        engine = tesseract_ocr.get_ocr_engine(options=options)
        assert isinstance(engine, TesseractOcrEngine)

    def test_tesseract_selected_when_tesseract(self):
        """TesseractOcrEngine should be returned when ocr_engine='tesseract'."""
        from unittest.mock import MagicMock

        from ocrmypdf.builtin_plugins import tesseract_ocr
        from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOcrEngine

        options = MagicMock()
        options.ocr_engine = 'tesseract'

        engine = tesseract_ocr.get_ocr_engine(options=options)
        assert isinstance(engine, TesseractOcrEngine)

    def test_null_selected_when_none(self):
        """NullOcrEngine should be returned when ocr_engine='none'."""
        from unittest.mock import MagicMock

        from ocrmypdf.builtin_plugins import null_ocr
        from ocrmypdf.builtin_plugins.null_ocr import NullOcrEngine

        options = MagicMock()
        options.ocr_engine = 'none'

        engine = null_ocr.get_ocr_engine(options=options)
        assert isinstance(engine, NullOcrEngine)

    def test_null_returns_none_when_auto(self):
        """null_ocr.get_ocr_engine() should return None when ocr_engine='auto'."""
        from unittest.mock import MagicMock

        from ocrmypdf.builtin_plugins import null_ocr

        options = MagicMock()
        options.ocr_engine = 'auto'

        engine = null_ocr.get_ocr_engine(options=options)
        assert engine is None

    def test_rapidocr_returns_none_when_auto(self):
        """rapidocr_ocr.get_ocr_engine() only claims ocr_engine='rapidocr'."""
        from unittest.mock import MagicMock

        from ocrmypdf.builtin_plugins import rapidocr_ocr

        for name in ('auto', 'tesseract', 'none'):
            options = MagicMock()
            options.ocr_engine = name
            assert rapidocr_ocr.get_ocr_engine(options=options) is None

    def test_rapidocr_selected_when_rapidocr(self):
        """RapidOcrEngine should be returned when ocr_engine='rapidocr'."""
        from unittest.mock import MagicMock

        from ocrmypdf.builtin_plugins import rapidocr_ocr

        options = MagicMock()
        options.ocr_engine = 'rapidocr'
        engine = rapidocr_ocr.get_ocr_engine(options=options)
        assert isinstance(engine, rapidocr_ocr.RapidOcrEngine)


class TestNonTesseractEngineWithoutTesseract:
    """Selecting an engine other than Tesseract must not require Tesseract."""

    @pytest.fixture
    def no_tesseract(self, monkeypatch):
        """Make every Tesseract entry point behave as if it is not installed."""
        from ocrmypdf._exec import tesseract

        def missing(*args, **kwargs):
            raise FileNotFoundError('tesseract')

        for name in (
            'version',
            'get_languages',
            'has_thresholding',
            'get_orientation',
            'get_deskew',
            'generate_hocr',
            'generate_pdf',
        ):
            monkeypatch.setattr(tesseract, name, missing)

    @staticmethod
    def _check(resources, outpdf, *args):
        from ocrmypdf import api
        from ocrmypdf.cli import get_options_and_plugins

        options, plugin_manager = get_options_and_plugins(
            args=[str(resources / 'linn.pdf'), str(outpdf), *args]
        )
        api.check_options(options, plugin_manager)
        return options, plugin_manager

    def test_cli_accepts_rapidocr(self):
        from ocrmypdf.cli import get_parser

        args = get_parser().parse_args(
            ['--ocr-engine', 'rapidocr', 'in.pdf', 'out.pdf']
        )
        assert args.ocr_engine == 'rapidocr'

    def test_tesseract_required_by_default(self, no_tesseract, resources, outpdf):
        from ocrmypdf.exceptions import MissingDependencyError

        with pytest.raises(MissingDependencyError):
            self._check(resources, outpdf)

    def test_tesseract_required_when_selected(self, no_tesseract, resources, outpdf):
        from ocrmypdf.exceptions import MissingDependencyError

        with pytest.raises(MissingDependencyError):
            self._check(resources, outpdf, '--ocr-engine', 'tesseract')

    def test_null_engine(self, no_tesseract, resources, outpdf):
        options, plugin_manager = self._check(resources, outpdf, '--ocr-engine', 'none')
        assert str(plugin_manager.get_ocr_engine(options=options)) == "No OCR engine"

    def test_null_engine_ignores_tesseract_options(
        self, no_tesseract, resources, outpdf
    ):
        # Tesseract-specific options are inert for other engines; they must
        # not pull in a Tesseract version or feature check.
        self._check(
            resources,
            outpdf,
            '--ocr-engine',
            'none',
            '--tesseract-thresholding',
            'sauvola',
        )

    def test_rapidocr_engine(self, no_tesseract, resources, outpdf):
        pytest.importorskip('rapidocr')
        options, plugin_manager = self._check(
            resources, outpdf, '--ocr-engine', 'rapidocr'
        )
        assert 'RapidOCR' in str(plugin_manager.get_ocr_engine(options=options))
