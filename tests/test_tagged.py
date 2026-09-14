# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from unittest.mock import Mock

import pikepdf
import pytest
from pikepdf import Name

import ocrmypdf
from ocrmypdf._options import ProcessingMode, TaggedPdfMode
from ocrmypdf._pipeline import validate_pdfinfo_options
from ocrmypdf.exceptions import ExitCode, PriorOcrFoundError, TaggedPDFError
from ocrmypdf.pdfinfo import PdfInfo


def test_tagged_pdf_error_uses_already_done_ocr_exit_code():
    """Tagged PDFs are a distinct condition, but they do not need OCR.

    They should use the same exit code as a file that already contains text
    (already_done_ocr), not input_file. This must hold regardless of which
    OCR engine plugin is installed.
    """
    err = TaggedPDFError()
    assert not isinstance(err, PriorOcrFoundError)
    assert err.exit_code == ExitCode.already_done_ocr


def test_validate_tagged_pdf_before_plugin_hooks(resources):
    """Reject tagged PDFs before plugin validate, independent of OCR engine."""
    pdfinfo = PdfInfo(resources / 'tagged.pdf')
    context = Mock()
    context.pdfinfo = pdfinfo
    context.options.invalidate_digital_signatures = False
    context.options.tagged_pdf_mode = TaggedPdfMode.default
    context.options.mode = ProcessingMode.default
    context.plugin_manager.validate = Mock()

    with pytest.raises(TaggedPDFError) as excinfo:
        validate_pdfinfo_options(context)

    assert excinfo.value.exit_code == ExitCode.already_done_ocr
    context.plugin_manager.validate.assert_not_called()


def test_block_tagged(resources):
    with pytest.raises(ocrmypdf.exceptions.TaggedPDFError):
        ocrmypdf.ocr(resources / 'tagged.pdf', '_.pdf')


def test_detect_structure_tree(resources):
    assert PdfInfo(resources / 'tagged.pdf').has_structure_tree is True


def test_structure_tree_without_markinfo_blocks(resources, tmp_path):
    """A PDF with a structure tree but no /MarkInfo flag is still blocked."""
    untagged = tmp_path / 'struct_only.pdf'
    with pikepdf.open(resources / 'tagged.pdf') as pdf:
        del pdf.Root.MarkInfo
        pdf.save(untagged)

    info = PdfInfo(untagged)
    assert info.is_tagged is False
    assert info.has_structure_tree is True

    with pytest.raises(ocrmypdf.exceptions.TaggedPDFError):
        ocrmypdf.ocr(untagged, '_.pdf')


def test_force_tagged_warns(resources, outpdf, caplog):
    caplog.set_level('WARNING')
    ocrmypdf.ocr(
        resources / 'tagged.pdf',
        outpdf,
        force_ocr=True,
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    assert 'structural markup' in caplog.text


def test_tagged_pdf_mode_ignore_with_skip_text(resources, outpdf, caplog):
    """Ignore tagged_pdf_mode should warn but not error, and keep structure."""
    caplog.set_level('WARNING')
    ocrmypdf.ocr(
        resources / 'tagged.pdf',
        outpdf,
        tagged_pdf_mode='ignore',
        skip_text=True,  # Tagged PDF has text, so skip pages with text
        # output_type=pdf avoids the Ghostscript PDF/A step, whose treatment of
        # the structure tree is version-dependent (Ghostscript >= 10 discards it,
        # 9.x preserves it). We only want to assert OCRmyPDF's own behavior here.
        output_type='pdf',
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    assert 'structural markup' in caplog.text
    # skip-text leaves the text pages untouched, so OCRmyPDF keeps the structure tree
    with pikepdf.open(outpdf) as pdf:
        assert Name.StructTreeRoot in pdf.Root


def test_tagged_pdf_mode_ignore_with_force(resources, outpdf, caplog):
    """Ignore tagged_pdf_mode with force mode should warn and discard structure."""
    caplog.set_level('WARNING')
    ocrmypdf.ocr(
        resources / 'tagged.pdf',
        outpdf,
        tagged_pdf_mode='ignore',
        force_ocr=True,
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    assert 'structural markup' in caplog.text
    # force-ocr rasterizes every page, destroying the MCIDs the tree relies on
    with pikepdf.open(outpdf) as pdf:
        assert Name.StructTreeRoot not in pdf.Root
        assert Name.MarkInfo not in pdf.Root


def test_tagged_pdf_mode_ignore_with_redo(resources, outpdf):
    """Redo mode rewrites the text layer, so structure is discarded."""
    ocrmypdf.ocr(
        resources / 'tagged.pdf',
        outpdf,
        tagged_pdf_mode='ignore',
        redo_ocr=True,
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    with pikepdf.open(outpdf) as pdf:
        assert Name.StructTreeRoot not in pdf.Root
        assert Name.MarkInfo not in pdf.Root
