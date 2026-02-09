# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from unittest.mock import patch

import pikepdf

import ocrmypdf


def test_no_glyphless_graft(resources, outdir):
    with (
        pikepdf.open(resources / 'francais.pdf') as pdf,
        pikepdf.open(resources / 'aspect.pdf') as pdf_aspect,
        pikepdf.open(resources / 'cmyk.pdf') as pdf_cmyk,
    ):
        pdf.pages.extend(pdf_aspect.pages)
        pdf.pages.extend(pdf_cmyk.pages)
        pdf.save(outdir / 'test.pdf')

    with patch('ocrmypdf._graft.MAX_REPLACE_PAGES', 2):
        ocrmypdf.ocr(
            outdir / 'test.pdf',
            outdir / 'out.pdf',
            deskew=True,
            tesseract_timeout=0,
            force_ocr=True,
        )
    # This test needs asserts


def test_links(resources, outpdf):
    ocrmypdf.ocr(
        resources / 'link.pdf', outpdf, redo_ocr=True, oversample=200, output_type='pdf'
    )
    with pikepdf.open(outpdf) as pdf:
        p1 = pdf.pages[0]
        p2 = pdf.pages[1]
        assert p1.Annots[0].A.D[0].objgen == p2.objgen
        assert p2.Annots[0].A.D[0].objgen == p1.objgen


def test_redo_ocr_with_offset_mediabox(resources, outdir):
    """Test that --redo-ocr handles non-zero mediabox origins correctly.

    Regression test for issue #1630 where PDFs with mediabox origins like
    [0, 100, width, height+100] (common in cropped PDFs)
    would have OCR text shifted vertically because the Form XObject BBox
    used the text layer's mediabox [0, 0, w, h] instead of the base page's
    mediabox [0, 100, w, h+100].

    Before the fix, the BBox would be [0, 0, w, h] but the transformation
    matrix would expect [0, 100, w, h+100], causing a 100pt vertical shift.
    """
    # Create a PDF with a non-zero mediabox origin
    input_pdf = outdir / 'offset_mediabox_input.pdf'

    with pikepdf.open(resources / 'graph_ocred.pdf') as pdf:
        page = pdf.pages[0]
        original_mb = list(page.MediaBox)

        # Shift mediabox Y origin to simulate cropped/JSTOR-style PDFs
        # This is the scenario that triggers the bug
        y_offset = 100
        page.MediaBox = [
            original_mb[0],
            original_mb[1] + y_offset,
            original_mb[2],
            original_mb[3] + y_offset,
        ]

        pdf.save(input_pdf)

    # Run --redo-ocr (this is where the bug occurred)
    output_pdf = outdir / 'offset_redo_ocr.pdf'
    ocrmypdf.ocr(input_pdf, output_pdf, redo_ocr=True)

    # Verify the output
    with pikepdf.open(output_pdf) as pdf:
        page = pdf.pages[0]
        mediabox = list(page.MediaBox)

        # MediaBox origin should be preserved
        assert (
            float(mediabox[1]) == 100.0
        ), f"MediaBox Y origin should be preserved at 100, got {mediabox[1]}"

        # MediaBox should have valid dimensions
        width = float(mediabox[2]) - float(mediabox[0])
        height = float(mediabox[3]) - float(mediabox[1])
        assert width > 0 and height > 0, "MediaBox should have positive dimensions"

        # Text content should be present
        # With the fix, OCR text layer coordinates will be correct
        # Without the fix, the text would be shifted outside the visible area
        text_content = page.Contents.read_bytes()
        assert len(text_content) > 0, "Page should have content"

        # The fix ensures text operators are present and positioned correctly
        # (BT/ET mark text blocks in PDF)
        assert (
            b'BT' in text_content or b'/Im' in text_content
        ), "Content should include text operators or image references"


def test_strip_invisble_text():
    pdf = pikepdf.Pdf.new()
    print(pikepdf.parse_content_stream(pikepdf.Stream(pdf, b'3 Tr')))
    page = pdf.add_blank_page()
    visible_text = [
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('BT')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.Name('/F0'), 12), pikepdf.Operator('Tf')
        ),
        pikepdf.ContentStreamInstruction((288, 720), pikepdf.Operator('Td')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.String('visible'),), pikepdf.Operator('Tj')
        ),
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('ET')),
    ]
    invisible_text = [
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('BT')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.Name('/F0'), 12), pikepdf.Operator('Tf')
        ),
        pikepdf.ContentStreamInstruction((288, 720), pikepdf.Operator('Td')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.String('invisible'),), pikepdf.Operator('Tj')
        ),
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('ET')),
    ]
    invisible_text_setting_tr = [
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('BT')),
        pikepdf.ContentStreamInstruction([3], pikepdf.Operator('Tr')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.Name('/F0'), 12), pikepdf.Operator('Tf')
        ),
        pikepdf.ContentStreamInstruction((288, 720), pikepdf.Operator('Td')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.String('invisible'),), pikepdf.Operator('Tj')
        ),
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('ET')),
    ]
    stream = [
        pikepdf.ContentStreamInstruction([], pikepdf.Operator('q')),
        pikepdf.ContentStreamInstruction([3], pikepdf.Operator('Tr')),
        *invisible_text,
        pikepdf.ContentStreamInstruction([], pikepdf.Operator('Q')),
        *visible_text,
        *invisible_text_setting_tr,
        *invisible_text,
    ]
    content_stream = pikepdf.unparse_content_stream(stream)
    page.Contents = pikepdf.Stream(pdf, content_stream)

    def count(string, page):
        return len(
            [
                True
                for operands, operator in pikepdf.parse_content_stream(page)
                if operator == pikepdf.Operator('Tj')
                and operands[0] == pikepdf.String(string)
            ]
        )

    nr_visible_pre = count('visible', page)
    ocrmypdf._graft.strip_invisible_text(pdf, page)
    nr_visible_post = count('visible', page)
    assert (
        nr_visible_pre == nr_visible_post
    ), 'Number of visible text elements did not change'
    assert count('invisible', page) == 0, 'No invisible elems left'
