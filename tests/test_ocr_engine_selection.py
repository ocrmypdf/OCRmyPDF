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
