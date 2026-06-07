# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging

import pikepdf
import pytest
from pikepdf import Name

from ocrmypdf._graft import discard_page_thumbnails

from .conftest import check_ocrmypdf

# pylint: disable=redefined-outer-name


def _add_thumbnail(pdf: pikepdf.Pdf, pageindex: int = 0) -> None:
    """Attach a minimal /Thumb image XObject to a page."""
    width, height = 4, 4
    thumb = pikepdf.Stream(pdf, b'\x00' * (width * height))
    thumb.Type = Name.XObject
    thumb.Subtype = Name.Image
    thumb.Width = width
    thumb.Height = height
    thumb.ColorSpace = Name.DeviceGray
    thumb.BitsPerComponent = 8
    pdf.pages[pageindex].obj.Thumb = pdf.make_indirect(thumb)


def test_discard_page_thumbnails_removes_thumbnails(resources):
    with pikepdf.open(resources / 'francais.pdf') as pdf:
        # No thumbnails -> nothing to do
        assert discard_page_thumbnails(pdf) == 0

        _add_thumbnail(pdf, 0)
        assert Name.Thumb in pdf.pages[0].obj

        assert discard_page_thumbnails(pdf) == 1
        assert Name.Thumb not in pdf.pages[0].obj

        # Idempotent: a second call finds nothing to remove
        assert discard_page_thumbnails(pdf) == 0


def test_discard_page_thumbnails_counts_each_page(resources):
    with pikepdf.open(resources / 'multipage.pdf') as pdf:
        assert len(pdf.pages) >= 2
        _add_thumbnail(pdf, 0)
        _add_thumbnail(pdf, 1)
        assert discard_page_thumbnails(pdf) == 2
        assert all(Name.Thumb not in page.obj for page in pdf.pages)


@pytest.fixture
def pdf_with_thumbnail(resources, outdir):
    out = outdir / 'with_thumbnail.pdf'
    with pikepdf.open(resources / 'graph.pdf') as pdf:
        _add_thumbnail(pdf, 0)
        assert Name.Thumb in pdf.pages[0].obj
        pdf.save(out)
    return out


def test_thumbnail_discarded_end_to_end(pdf_with_thumbnail, outpdf, caplog):
    caplog.set_level(logging.DEBUG)
    check_ocrmypdf(
        pdf_with_thumbnail,
        outpdf,
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    with pikepdf.open(outpdf) as pdf:
        assert all(Name.Thumb not in page.obj for page in pdf.pages)
    assert 'thumbnail' in caplog.text.lower()


def test_thumbnail_discarded_with_ocr_engine_none(pdf_with_thumbnail, outpdf):
    # Even in pure image-processing mode, OCRmyPDF rewrites the PDF, which can
    # alter page appearance, so the stale thumbnail must still be discarded.
    check_ocrmypdf(
        pdf_with_thumbnail,
        outpdf,
        '--ocr-engine',
        'none',
        '--output-type',
        'pdf',
    )
    with pikepdf.open(outpdf) as pdf:
        assert all(Name.Thumb not in page.obj for page in pdf.pages)
