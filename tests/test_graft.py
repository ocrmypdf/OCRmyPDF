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
