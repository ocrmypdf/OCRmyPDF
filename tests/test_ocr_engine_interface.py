# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for OcrEngine interface extensions.

These tests verify that the OcrEngine ABC has the new generate_ocr() method
and that OcrElement classes are exported from the public API.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ocrmypdf.pluginspec import OcrEngine


class TestOcrEngineInterface:
    """Test that OcrEngine ABC has required methods."""

    def test_generate_ocr_method_exists(self):
        """OcrEngine must have generate_ocr() method signature."""
        assert hasattr(OcrEngine, 'generate_ocr')

    def test_supports_generate_ocr_method_exists(self):
        """OcrEngine must have supports_generate_ocr() method."""
        assert hasattr(OcrEngine, 'supports_generate_ocr')

    def test_supports_generate_ocr_default_false(self):
        """Default supports_generate_ocr() should return False."""
        from ocrmypdf.pluginspec import OrientationConfidence

        # Create a minimal concrete implementation
        class MinimalEngine(OcrEngine):
            @staticmethod
            def version():
                return "1.0"

            @staticmethod
            def creator_tag(options):
                return "test"

            def __str__(self):
                return "test"

            @staticmethod
            def languages(options):
                return set()

            @staticmethod
            def get_orientation(input_file, options):
                return OrientationConfidence(0, 0.0)

            @staticmethod
            def get_deskew(input_file, options):
                return 0.0

            @staticmethod
            def generate_hocr(input_file, output_hocr, output_text, options):
                pass

            @staticmethod
            def generate_pdf(input_file, output_pdf, output_text, options):
                pass

        engine = MinimalEngine()
        assert engine.supports_generate_ocr() is False

    def test_generate_ocr_raises_not_implemented_by_default(self):
        """Default generate_ocr() should raise NotImplementedError."""
        from ocrmypdf.pluginspec import OrientationConfidence

        class MinimalEngine(OcrEngine):
            @staticmethod
            def version():
                return "1.0"

            @staticmethod
            def creator_tag(options):
                return "test"

            def __str__(self):
                return "test"

            @staticmethod
            def languages(options):
                return set()

            @staticmethod
            def get_orientation(input_file, options):
                return OrientationConfidence(0, 0.0)

            @staticmethod
            def get_deskew(input_file, options):
                return 0.0

            @staticmethod
            def generate_hocr(input_file, output_hocr, output_text, options):
                pass

            @staticmethod
            def generate_pdf(input_file, output_pdf, output_text, options):
                pass

        engine = MinimalEngine()
        with pytest.raises(NotImplementedError):
            engine.generate_ocr(Path("test.png"), MagicMock(), 0)


class TestOcrElementExport:
    """Test that OcrElement is exported from public API."""

    def test_ocrelement_importable_from_ocrmypdf(self):
        """OcrElement should be importable from ocrmypdf package."""
        from ocrmypdf import OcrElement

        assert OcrElement is not None

    def test_ocrclass_importable_from_ocrmypdf(self):
        """OcrClass should be importable from ocrmypdf package."""
        from ocrmypdf import OcrClass

        assert OcrClass is not None

    def test_boundingbox_importable_from_ocrmypdf(self):
        """BoundingBox should be importable from ocrmypdf package."""
        from ocrmypdf import BoundingBox

        assert BoundingBox is not None
