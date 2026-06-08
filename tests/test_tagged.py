# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pikepdf
import pytest
from pikepdf import Name

import ocrmypdf
from ocrmypdf.pdfinfo import PdfInfo


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
        plugins=['tests/plugins/tesseract_noop.py'],
    )
    assert 'structural markup' in caplog.text
    # skip-text leaves the text pages untouched, so the structure tree remains valid
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
