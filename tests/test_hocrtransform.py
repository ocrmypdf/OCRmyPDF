# © 2015 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

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

check_ocrmypdf = pytest.helpers.check_ocrmypdf  # pylint: disable=no-member


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

    hocr = hocrtransform.HocrTransform(str(blank_hocr), 300)
    hocr.to_pdf(str(outdir / 'mono.pdf'), image_filename=str(outdir / 'mono.tif'))

    check_pdf(str(outdir / 'mono.pdf'))


@pytest.mark.slow
def test_hocrtransform_matches_sandwich(resources, outdir):
    check_ocrmypdf(resources / 'ccitt.pdf', outdir / 'hocr.pdf', '--pdf-renderer=hocr')
    check_ocrmypdf(
        resources / 'ccitt.pdf', outdir / 'tess.pdf', '--pdf-renderer=sandwich'
    )

    def clean(s):
        s = re.sub(r'[ ]+', ' ', s)
        s = re.sub(r'[ ]?[\n]+', r'\n', s)
        return s

    hocr_txt = clean(text_from_pdf(outdir / 'hocr.pdf'))
    tess_txt = clean(text_from_pdf(outdir / 'tess.pdf'))

    # Path('hocr.txt').write_text(hocr_txt)
    # Path('tess.txt').write_text(tess_txt)

    assert hocr_txt == tess_txt
