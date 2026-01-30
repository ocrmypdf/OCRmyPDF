# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: CC-BY-SA-4.0

"""Tests for verapdf wrapper and speculative PDF/A conversion."""

from __future__ import annotations

import pikepdf
import pytest
from pikepdf import Name

from ocrmypdf._exec import verapdf
from ocrmypdf.pdfa import (
    _pdfa_part_conformance,
    add_pdfa_metadata,
    add_srgb_output_intent,
    speculative_pdfa_conversion,
)


class TestVerapdfModule:
    """Tests for verapdf wrapper module."""

    def test_output_type_to_flavour(self):
        assert verapdf.output_type_to_flavour('pdfa') == '2b'
        assert verapdf.output_type_to_flavour('pdfa-1') == '1b'
        assert verapdf.output_type_to_flavour('pdfa-2') == '2b'
        assert verapdf.output_type_to_flavour('pdfa-3') == '3b'
        # Unknown should default to 2b
        assert verapdf.output_type_to_flavour('unknown') == '2b'

    @pytest.mark.skipif(not verapdf.available(), reason='verapdf not installed')
    def test_version(self):
        ver = verapdf.version()
        assert ver.major >= 1

    @pytest.mark.skipif(not verapdf.available(), reason='verapdf not installed')
    def test_validate_non_pdfa(self, tmp_path):
        """Test validation of a non-PDF/A file returns invalid."""
        test_pdf = tmp_path / 'test.pdf'
        with pikepdf.new() as pdf:
            pdf.add_blank_page()
            pdf.save(test_pdf)

        result = verapdf.validate(test_pdf, '2b')
        assert not result.valid
        assert result.failed_rules > 0


class TestPdfaPartConformance:
    """Tests for _pdfa_part_conformance helper."""

    def test_pdfa_part_conformance(self):
        assert _pdfa_part_conformance('pdfa') == ('2', 'B')
        assert _pdfa_part_conformance('pdfa-1') == ('1', 'B')
        assert _pdfa_part_conformance('pdfa-2') == ('2', 'B')
        assert _pdfa_part_conformance('pdfa-3') == ('3', 'B')
        # Unknown should default to 2B
        assert _pdfa_part_conformance('unknown') == ('2', 'B')


class TestAddPdfaMetadata:
    """Tests for add_pdfa_metadata function."""

    def test_add_pdfa_metadata(self, tmp_path):
        """Test adding PDF/A XMP metadata."""
        test_pdf = tmp_path / 'test.pdf'
        with pikepdf.new() as pdf:
            pdf.add_blank_page()
            pdf.save(test_pdf)

        with pikepdf.open(test_pdf, allow_overwriting_input=True) as pdf:
            add_pdfa_metadata(pdf, '2', 'B')
            with pdf.open_metadata() as meta:
                assert meta.pdfa_status == '2B'
            pdf.save(test_pdf)

        # Verify it persists after save
        with pikepdf.open(test_pdf) as pdf, pdf.open_metadata() as meta:
            assert meta.pdfa_status == '2B'


class TestAddSrgbOutputIntent:
    """Tests for add_srgb_output_intent function."""

    def test_add_srgb_output_intent(self, tmp_path):
        """Test adding sRGB OutputIntent to a PDF."""
        test_pdf = tmp_path / 'test.pdf'
        with pikepdf.new() as pdf:
            pdf.add_blank_page()
            pdf.save(test_pdf)

        with pikepdf.open(test_pdf, allow_overwriting_input=True) as pdf:
            add_srgb_output_intent(pdf)
            assert Name.OutputIntents in pdf.Root
            assert len(pdf.Root.OutputIntents) == 1
            intent = pdf.Root.OutputIntents[0]
            assert str(intent.get(Name.OutputConditionIdentifier)) == 'sRGB'
            pdf.save(test_pdf)

    def test_add_srgb_output_intent_idempotent(self, tmp_path):
        """Test that adding OutputIntent twice doesn't duplicate."""
        test_pdf = tmp_path / 'test.pdf'
        with pikepdf.new() as pdf:
            pdf.add_blank_page()
            pdf.save(test_pdf)

        with pikepdf.open(test_pdf, allow_overwriting_input=True) as pdf:
            add_srgb_output_intent(pdf)
            add_srgb_output_intent(pdf)  # Second call should be a no-op
            assert len(pdf.Root.OutputIntents) == 1
            pdf.save(test_pdf)


class TestSpeculativePdfaConversion:
    """Tests for speculative PDF/A conversion."""

    def test_speculative_conversion_creates_pdfa_structures(self, tmp_path, resources):
        """Test that speculative conversion adds PDF/A structures."""
        input_pdf = resources / 'graph.pdf'
        output_pdf = tmp_path / 'output.pdf'

        result = speculative_pdfa_conversion(input_pdf, output_pdf, 'pdfa-2')

        assert result.exists()
        with pikepdf.open(result) as pdf:
            assert Name.OutputIntents in pdf.Root
            with pdf.open_metadata() as meta:
                assert meta.pdfa_status == '2B'

    def test_speculative_conversion_different_parts(self, tmp_path, resources):
        """Test speculative conversion with different PDF/A parts."""
        input_pdf = resources / 'graph.pdf'

        for output_type, expected_status in [
            ('pdfa-1', '1B'),
            ('pdfa-2', '2B'),
            ('pdfa-3', '3B'),
        ]:
            output_pdf = tmp_path / f'output_{output_type}.pdf'
            speculative_pdfa_conversion(input_pdf, output_pdf, output_type)

            with pikepdf.open(output_pdf) as pdf, pdf.open_metadata() as meta:
                assert meta.pdfa_status == expected_status


@pytest.mark.skipif(not verapdf.available(), reason='verapdf not installed')
class TestVerapdfIntegration:
    """Integration tests requiring verapdf."""

    def test_speculative_conversion_validation(self, tmp_path, resources):
        """Test that speculative conversion can be validated by verapdf.

        Note: Most test PDFs will fail validation because they have issues
        that require Ghostscript to fix (fonts, colorspaces, etc.). This test
        verifies the validation pipeline works, not that all PDFs pass.
        """
        input_pdf = resources / 'graph.pdf'
        output_pdf = tmp_path / 'output.pdf'

        speculative_pdfa_conversion(input_pdf, output_pdf, 'pdfa-2')

        # The converted file can be validated (even if it fails)
        result = verapdf.validate(output_pdf, '2b')
        assert isinstance(result.valid, bool)
        assert isinstance(result.failed_rules, int)
