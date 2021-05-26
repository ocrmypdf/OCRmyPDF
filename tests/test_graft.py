# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from unittest.mock import patch

import pikepdf
import pytest

import ocrmypdf


def test_no_glyphless_graft(resources, outdir):
    with pikepdf.open(resources / 'francais.pdf') as pdf, pikepdf.open(
        resources / 'aspect.pdf'
    ) as pdf_aspect, pikepdf.open(resources / 'cmyk.pdf') as pdf_cmyk:
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
