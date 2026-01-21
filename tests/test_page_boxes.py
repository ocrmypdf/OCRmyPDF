# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pikepdf
import pytest

from ocrmypdf._exec import verapdf

from .conftest import check_ocrmypdf

page_rect = [0, 0, 612, 792]
inset_rect = [200, 200, 612, 792]
wh_rect = [0, 0, 412, 592]

neg_rect = [-100, -100, 512, 692]

# When speculative PDF/A succeeds (verapdf available), MediaBox is preserved.
# Ghostscript would normalize MediaBox to start at origin, but speculative
# conversion bypasses Ghostscript.
_pdfa_inset_expected = inset_rect if verapdf.available() else wh_rect

mediabox_testdata = [
    ('fpdf2', 'pdfa', 'ccitt.pdf', None, inset_rect, _pdfa_inset_expected),
    ('sandwich', 'pdfa', 'ccitt.pdf', None, inset_rect, _pdfa_inset_expected),
    ('fpdf2', 'pdf', 'ccitt.pdf', None, inset_rect, inset_rect),
    ('sandwich', 'pdf', 'ccitt.pdf', None, inset_rect, inset_rect),
    (
        'fpdf2',
        'pdfa',
        'ccitt.pdf',
        '--force-ocr',
        inset_rect,
        wh_rect,
    ),
    (
        'fpdf2',
        'pdf',
        'ccitt.pdf',
        '--force-ocr',
        inset_rect,
        wh_rect,
    ),
    ('fpdf2', 'pdfa', 'ccitt.pdf', '--force-ocr', neg_rect, page_rect),
    ('fpdf2', 'pdf', 'ccitt.pdf', '--force-ocr', neg_rect, page_rect),
]


@pytest.mark.parametrize(
    'renderer, output_type, in_pdf, mode, crop_to, crop_expected', mediabox_testdata
)
def test_media_box(
    resources, outdir, renderer, output_type, in_pdf, mode, crop_to, crop_expected
):
    with pikepdf.open(resources / in_pdf) as pdf:
        page = pdf.pages[0]
        page.MediaBox = crop_to
        pdf.save(outdir / 'cropped.pdf')
    args = [
        '--jobs',
        '1',
        '--pdf-renderer',
        renderer,
        '--output-type',
        output_type,
    ]
    if mode:
        args.append(mode)

    check_ocrmypdf(outdir / 'cropped.pdf', outdir / 'processed.pdf', *args)

    with pikepdf.open(outdir / 'processed.pdf') as pdf:
        page = pdf.pages[0]
        assert [float(x) for x in page.mediabox] == crop_expected


cropbox_testdata = [
    ('fpdf2', 'pdfa', 'ccitt.pdf', None, inset_rect, inset_rect),
    ('sandwich', 'pdfa', 'ccitt.pdf', None, inset_rect, inset_rect),
    ('fpdf2', 'pdf', 'ccitt.pdf', None, inset_rect, inset_rect),
    ('sandwich', 'pdf', 'ccitt.pdf', None, inset_rect, inset_rect),
    (
        'fpdf2',
        'pdfa',
        'ccitt.pdf',
        '--force-ocr',
        inset_rect,
        inset_rect,
    ),
    (
        'fpdf2',
        'pdf',
        'ccitt.pdf',
        '--force-ocr',
        inset_rect,
        inset_rect,
    ),
]


@pytest.mark.parametrize(
    'renderer, output_type, in_pdf, mode, crop_to, crop_expected', cropbox_testdata
)
def test_crop_box(
    resources, outdir, renderer, output_type, in_pdf, mode, crop_to, crop_expected
):
    with pikepdf.open(resources / in_pdf) as pdf:
        page = pdf.pages[0]
        page.CropBox = crop_to
        pdf.save(outdir / 'cropped.pdf')
    args = [
        '--jobs',
        '1',
        '--pdf-renderer',
        renderer,
        '--output-type',
        output_type,
        '--optimize',
        '0',
    ]
    if mode:
        args.append(mode)

    check_ocrmypdf(outdir / 'cropped.pdf', outdir / 'processed.pdf', *args)

    with pikepdf.open(outdir / 'processed.pdf') as pdf:
        page = pdf.pages[0]
        assert [float(x) for x in page.cropbox] == crop_expected
