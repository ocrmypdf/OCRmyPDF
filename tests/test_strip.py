# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for --mode strip (remove the OCR text layer in place)."""

from __future__ import annotations

import pikepdf
import pytest

from ocrmypdf.exceptions import BadArgsError
from ocrmypdf.pdfinfo import PdfInfo

from .conftest import check_ocrmypdf, run_ocrmypdf_api


def _image_raw_bytes(pdf_path):
    """Return raw (still-compressed) stream bytes of each image on page 1."""
    out = []
    with pikepdf.open(pdf_path) as pdf:
        resources = pdf.pages[0].get('/Resources', {})
        for _name, xobj in resources.get('/XObject', {}).items():
            if xobj.get('/Subtype') == pikepdf.Name.Image:
                out.append(bytes(xobj.read_raw_bytes()))
    return out


def test_mode_strip_removes_ocr_layer(resources, outpdf):
    """--mode strip removes the invisible OCR layer without rasterizing.

    The page image is preserved byte-for-byte and the output is no larger than
    the input.
    """
    input_pdf = resources / 'graph_ocred.pdf'
    assert PdfInfo(input_pdf, detailed_analysis=True)[0].has_text

    out = check_ocrmypdf(
        input_pdf, outpdf, '--mode', 'strip', '--output-type', 'pdf', '--optimize', '0'
    )

    info = PdfInfo(out, detailed_analysis=True)
    assert len(info) == 1, "page count must be unchanged"
    assert not info[0].has_text, "OCR text layer should be removed"
    assert _image_raw_bytes(out) == _image_raw_bytes(input_pdf), (
        "page image must be preserved byte-for-byte (no rasterization)"
    )
    assert out.stat().st_size <= input_pdf.stat().st_size, (
        "removing the text layer must not grow the file"
    )


def test_mode_strip_preserves_visible_text(resources, outpdf):
    """--mode strip leaves visible/born-digital text untouched (render mode != 3).

    type3_font_nomapping.pdf is born-digital text with no images (the #1608
    case): its visible text must survive strip, which only removes invisible
    OCR text.
    """
    input_pdf = resources / 'type3_font_nomapping.pdf'
    out = check_ocrmypdf(
        input_pdf, outpdf, '--mode', 'strip', '--output-type', 'pdf', '--optimize', '0'
    )
    assert PdfInfo(out, detailed_analysis=True)[0].has_text


def test_mode_strip_rejects_image_processing_options(resources, no_outpdf):
    """Options requiring rasterization/OCR are rejected in strip mode."""
    with pytest.raises(BadArgsError, match=r'--deskew'):
        run_ocrmypdf_api(
            resources / 'graph_ocred.pdf', no_outpdf, '--mode', 'strip', '--deskew'
        )
