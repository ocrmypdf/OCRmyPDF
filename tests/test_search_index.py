# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging

import pikepdf
import pytest
from pikepdf import Dictionary, Name, String

from ocrmypdf._graft import discard_text_search_index

from .conftest import check_ocrmypdf

# pylint: disable=redefined-outer-name


def _add_search_index(pdf: pikepdf.Pdf, *, other_owner: bool = False) -> None:
    """Attach an Adobe-style embedded search index to the document catalog."""
    pieceinfo = Dictionary(
        SearchIndex=Dictionary(
            LastModified=String("D:20240101000000Z"),
            Private=Dictionary(IndexFile=String("dummy.pdx")),
        )
    )
    if other_owner:
        pieceinfo[Name.SomeOtherApp] = Dictionary(
            LastModified=String("D:20240101000000Z")
        )
    pdf.Root.PieceInfo = pdf.make_indirect(pieceinfo)


def test_discard_text_search_index_removes_only_search_index(resources):
    with pikepdf.open(resources / 'francais.pdf') as pdf:
        # No PieceInfo at all -> nothing to do
        assert not discard_text_search_index(pdf)

        _add_search_index(pdf, other_owner=True)
        assert discard_text_search_index(pdf), "Expected file to be modified"

        # SearchIndex gone, but the other application's private data is preserved
        assert Name.SearchIndex not in pdf.Root.PieceInfo
        assert Name.SomeOtherApp in pdf.Root.PieceInfo

        # Idempotent: a second call finds nothing to remove
        assert not discard_text_search_index(pdf)


def test_discard_text_search_index_drops_empty_pieceinfo(resources):
    with pikepdf.open(resources / 'francais.pdf') as pdf:
        _add_search_index(pdf, other_owner=False)
        assert discard_text_search_index(pdf)
        # PieceInfo held only the SearchIndex, so the whole husk is removed
        assert Name.PieceInfo not in pdf.Root


def test_discard_text_search_index_tolerates_malformed_pieceinfo(resources):
    with pikepdf.open(resources / 'francais.pdf') as pdf:
        pdf.Root.PieceInfo = String("not a dictionary")
        assert not discard_text_search_index(pdf)


@pytest.fixture
def pdf_with_search_index(resources, outdir):
    out = outdir / 'with_search_index.pdf'
    with pikepdf.open(resources / 'graph.pdf') as pdf:
        _add_search_index(pdf, other_owner=False)
        assert Name.SearchIndex in pdf.Root.PieceInfo
        pdf.save(out)
    return out


def test_search_index_discarded_end_to_end(pdf_with_search_index, outpdf, caplog):
    caplog.set_level(logging.DEBUG)
    check_ocrmypdf(
        pdf_with_search_index,
        outpdf,
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    with pikepdf.open(outpdf) as pdf:
        assert Name.PieceInfo not in pdf.Root
    assert 'search index' in caplog.text.lower()


def test_search_index_discarded_with_ocr_engine_none(pdf_with_search_index, outpdf):
    # Even in pure image-processing mode, OCRmyPDF rewrites the PDF, which
    # invalidates the embedded index, so it must still be discarded.
    check_ocrmypdf(
        pdf_with_search_index,
        outpdf,
        '--ocr-engine',
        'none',
        '--output-type',
        'pdf',
    )
    with pikepdf.open(outpdf) as pdf:
        assert Name.PieceInfo not in pdf.Root
