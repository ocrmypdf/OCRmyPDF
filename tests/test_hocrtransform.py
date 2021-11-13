# © 2015 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import re
from io import StringIO

import pytest
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from PIL import Image

from ocrmypdf import hocrtransform
from ocrmypdf._exec.tesseract import HOCR_TEMPLATE
from ocrmypdf.helpers import check_pdf

from .conftest import check_ocrmypdf


def text_from_pdf(filename):
    output_string = StringIO()
    with open(filename, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    return output_string.getvalue()


# pylint: disable=redefined-outer-name


@pytest.fixture
def blank_hocr(tmp_path):
    filename = tmp_path / "blank.hocr"
    filename.write_text(HOCR_TEMPLATE)
    return filename


def test_mono_image(blank_hocr, outdir):
    im = Image.new('1', (8, 8), 0)
    for n in range(8):
        im.putpixel((n, n), 1)
    im.save(outdir / 'mono.tif', format='TIFF')

    hocr = hocrtransform.HocrTransform(hocr_filename=str(blank_hocr), dpi=300)
    hocr.to_pdf(
        out_filename=str(outdir / 'mono.pdf'), image_filename=str(outdir / 'mono.tif')
    )

    check_pdf(str(outdir / 'mono.pdf'))


@pytest.mark.slow
def test_hocrtransform_matches_sandwich(resources, outdir):
    check_ocrmypdf(resources / 'ccitt.pdf', outdir / 'hocr.pdf', '--pdf-renderer=hocr')
    check_ocrmypdf(
        resources / 'ccitt.pdf', outdir / 'tess.pdf', '--pdf-renderer=sandwich'
    )

    # Slight differences in spacing and word order can appear, so at least ensure
    # that we get all of the same words...
    def clean(s):
        s = re.sub(r'\s+', ' ', s)
        words = s.split(' ')
        return '\n'.join(sorted(words))

    hocr_txt = clean(text_from_pdf(outdir / 'hocr.pdf'))
    tess_txt = clean(text_from_pdf(outdir / 'tess.pdf'))

    # from pathlib import Path
    # Path('hocr.txt').write_text(hocr_txt)
    # Path('tess.txt').write_text(tess_txt)

    assert hocr_txt == tess_txt
