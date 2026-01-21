# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for pipeline support of generate_ocr().

These tests verify that the pipeline supports the new generate_ocr() API
alongside the existing hOCR path.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from unittest.mock import MagicMock, patch

from ocrmypdf import BoundingBox, OcrElement


class TestOcrEngineDirect:
    """Test the ocr_engine_direct() pipeline function."""

    def test_ocr_engine_direct_function_exists(self):
        """ocr_engine_direct function should exist in _pipeline module."""
        from ocrmypdf import _pipeline

        assert hasattr(_pipeline, 'ocr_engine_direct')

    def test_ocr_engine_direct_returns_tuple(self, tmp_path):
        """ocr_engine_direct should return (OcrElement, Path) tuple."""
        from ocrmypdf._pipeline import ocr_engine_direct

        # Mock page context with an engine that supports generate_ocr
        mock_context = MagicMock()
        mock_engine = MagicMock()
        mock_engine.supports_generate_ocr.return_value = True
        mock_engine.generate_ocr.return_value = (
            OcrElement(ocr_class='ocr_page', bbox=BoundingBox(0, 0, 100, 100)),
            "test text",
        )
        mock_context.plugin_manager.get_ocr_engine.return_value = mock_engine
        mock_context.get_path.return_value = tmp_path / Path("test.txt")
        mock_context.pageno = 0

        with patch('builtins.open', MagicMock()):
            result = ocr_engine_direct(Path("test.png"), mock_context)

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestPageResultExtension:
    """Test PageResult NamedTuple extension."""

    def test_page_result_has_ocr_tree_field(self):
        """PageResult should have ocr_tree field."""
        from ocrmypdf._pipelines._common import PageResult

        # PageResult is a NamedTuple, use _fields
        assert 'ocr_tree' in PageResult._fields

    def test_page_result_ocr_tree_default_none(self):
        """PageResult.ocr_tree should default to None."""
        from ocrmypdf._pipelines._common import PageResult

        result = PageResult(pageno=0)
        assert result.ocr_tree is None


class TestFpdf2DirectPage:
    """Test Fpdf2DirectPage dataclass for direct OcrElement input."""

    def test_fpdf2_direct_page_exists(self):
        """Fpdf2DirectPage dataclass should exist."""
        from ocrmypdf._graft import Fpdf2DirectPage

        assert Fpdf2DirectPage is not None

    def test_fpdf2_direct_page_has_ocr_tree(self):
        """Fpdf2DirectPage should have ocr_tree field."""
        from ocrmypdf._graft import Fpdf2DirectPage

        fields = {f.name for f in dataclasses.fields(Fpdf2DirectPage)}
        assert 'ocr_tree' in fields


class TestHOCRResultExtension:
    """Test HOCRResult dataclass extension."""

    def test_hocr_result_has_ocr_tree_field(self):
        """HOCRResult should have ocr_tree field."""
        from ocrmypdf._pipelines._common import HOCRResult

        fields = {f.name for f in dataclasses.fields(HOCRResult)}
        assert 'ocr_tree' in fields

    def test_hocr_result_ocr_tree_default_none(self):
        """HOCRResult.ocr_tree should default to None."""
        from ocrmypdf._pipelines._common import HOCRResult

        result = HOCRResult(pageno=0)
        assert result.ocr_tree is None
