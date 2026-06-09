# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pikepdf
import pytest

from ocrmypdf._exec import verapdf
from ocrmypdf._pageboxes import repair_page_boxes

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


# --- Unit tests for repair_page_boxes (issues #1398, #1526, #1400) ---


def _is_numeric(obj) -> bool:
    try:
        float(obj)
        return True
    except (TypeError, ValueError):
        return False


def _one_page_pdf(**boxes):
    """Build a one-page PDF, setting the named boxes to the given arrays."""
    pdf = pikepdf.new()
    page = pdf.add_blank_page(page_size=(612, 792))
    for name, rect in boxes.items():
        setattr(page.obj, name, pikepdf.Array(rect))
    return pdf, page


def test_repair_reversed_mediabox_is_normalized():
    # #1526: diagonally-opposite corners given in reversed order
    _pdf, page = _one_page_pdf(MediaBox=[0, 792, 612, 0])
    repairs = repair_page_boxes(page)
    assert [float(x) for x in page.obj.MediaBox] == [0, 0, 612, 792]
    assert any(r.box == 'MediaBox' and r.kind == 'reordered' for r in repairs)


def test_repair_cropbox_entirely_outside_mediabox_is_discarded():
    # #1400: CropBox lies entirely outside the MediaBox -> empty intersection
    _pdf, page = _one_page_pdf(
        MediaBox=[0, 0, 612, 792], CropBox=[1000, 1000, 1500, 1500]
    )
    repairs = repair_page_boxes(page)
    assert '/CropBox' not in page.obj
    assert any(r.box == 'CropBox' and r.kind == 'discarded' for r in repairs)


def test_repair_cropbox_partially_outside_mediabox_is_clamped():
    _pdf, page = _one_page_pdf(MediaBox=[0, 0, 612, 792], CropBox=[200, 200, 800, 900])
    repairs = repair_page_boxes(page)
    assert [float(x) for x in page.obj.CropBox] == [200, 200, 612, 792]
    assert any(r.box == 'CropBox' and r.kind == 'clamped' for r in repairs)


def test_repair_exponential_coordinate_is_coerced():
    # #1398: a coordinate stored as a string in exponential notation
    _pdf, page = _one_page_pdf(
        MediaBox=[0, 0, 612, 792],
        TrimBox=[pikepdf.String('3.05175781e-005'), 0, 612, 792],
    )
    repairs = repair_page_boxes(page)
    trim = page.obj.TrimBox
    assert all(_is_numeric(x) for x in trim)
    assert float(trim[0]) == pytest.approx(3.05175781e-5, abs=1e-4)
    assert any(r.box == 'TrimBox' and r.kind == 'recoded' for r in repairs)


def test_repair_degenerate_mediabox_is_reported():
    _pdf, page = _one_page_pdf(MediaBox=[0, 0, 0, 792])  # zero width
    repairs = repair_page_boxes(page)
    assert any(r.box == 'MediaBox' and r.kind == 'degenerate_mediabox' for r in repairs)


def test_repair_valid_page_makes_no_changes():
    _pdf, page = _one_page_pdf(MediaBox=[0, 0, 612, 792], CropBox=[10, 10, 600, 780])
    repairs = repair_page_boxes(page)
    assert repairs == []
    assert [float(x) for x in page.obj.MediaBox] == [0, 0, 612, 792]
    assert [float(x) for x in page.obj.CropBox] == [10, 10, 600, 780]


def test_summarize_box_repairs_aggregates_and_sets_severity():
    import logging

    from ocrmypdf._pageboxes import BoxRepair, summarize_box_repairs

    repairs_by_page = {
        0: [BoxRepair('CropBox', 'discarded')],
        2: [BoxRepair('CropBox', 'discarded')],
        3: [BoxRepair('CropBox', 'discarded')],
        1: [BoxRepair('MediaBox', 'reordered')],
    }
    messages = summarize_box_repairs(repairs_by_page)

    discard = [(lvl, m) for lvl, m in messages if 'discarded' in m]
    assert len(discard) == 1
    level, text = discard[0]
    assert level == logging.WARNING
    assert 'Page(s) 1, 3-4' in text  # 0-based keys shown 1-based, ranges compacted
    assert 'visually inspect' in text

    reordered = [(lvl, m) for lvl, m in messages if 'reversed' in m]
    assert len(reordered) == 1
    assert reordered[0][0] == logging.DEBUG
    assert 'visually inspect' not in reordered[0][1]


def test_cropbox_outside_mediabox_yields_valid_output(resources, outdir):
    # #1400: a CropBox entirely outside the MediaBox produces an effective
    # page of N x 0 pt; the pipeline must repair it to valid output.
    with pikepdf.open(resources / 'ccitt.pdf') as pdf:
        page = pdf.pages[0]
        mb = [float(x) for x in page.mediabox]
        page.CropBox = [mb[2] + 100, mb[3] + 100, mb[2] + 200, mb[3] + 200]
        pdf.save(outdir / 'badcrop.pdf')

    check_ocrmypdf(
        outdir / 'badcrop.pdf',
        outdir / 'out.pdf',
        '--output-type',
        'pdf',
        '--optimize',
        '0',
    )

    with pikepdf.open(outdir / 'out.pdf') as pdf:
        cb = [float(x) for x in pdf.pages[0].cropbox]  # resolves to MediaBox
        assert (cb[2] - cb[0]) > 0 and (cb[3] - cb[1]) > 0


def test_reversed_mediabox_does_not_crash(resources, outdir):
    # #1526: reversed MediaBox corners previously raised NegativeDimensionError.
    with pikepdf.open(resources / 'ccitt.pdf') as pdf:
        page = pdf.pages[0]
        mb = [float(x) for x in page.mediabox]
        page.MediaBox = [mb[0], mb[3], mb[2], mb[1]]  # swap y corners
        pdf.save(outdir / 'reversed.pdf')

    check_ocrmypdf(
        outdir / 'reversed.pdf',
        outdir / 'out.pdf',
        '--force-ocr',
        '--output-type',
        'pdf',
        '--optimize',
        '0',
    )

    with pikepdf.open(outdir / 'out.pdf') as pdf:
        mb = [float(x) for x in pdf.pages[0].mediabox]
        assert (mb[2] - mb[0]) > 0 and (mb[3] - mb[1]) > 0
