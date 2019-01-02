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

import pickle
from math import isclose
from tempfile import NamedTemporaryFile

import img2pdf
import pytest
from PIL import Image
from reportlab.pdfgen.canvas import Canvas

import pikepdf
from ocrmypdf import pdfinfo
from ocrmypdf.pdfinfo import Colorspace, Encoding

# pylint: disable=protected-access


def test_single_page_text(outdir):
    filename = outdir / 'text.pdf'
    pdf = Canvas(str(filename), pagesize=(8 * 72, 6 * 72))
    text = pdf.beginText()
    text.setFont('Helvetica', 12)
    text.setTextOrigin(1 * 72, 3 * 72)
    text.textLine(
        "Methink'st thou art a general offence and every" " man should beat thee."
    )
    pdf.drawText(text)
    pdf.showPage()
    pdf.save()

    info = pdfinfo.PdfInfo(filename)

    assert len(info) == 1
    page = info[0]

    assert page.has_text
    assert len(page.images) == 0


def test_single_page_image(outdir):
    filename = outdir / 'image-mono.pdf'

    im_tmp = outdir / 'tmp.png'
    im = Image.new('1', (8, 8), 0)
    for n in range(8):
        im.putpixel((n, n), 1)
    im.save(str(im_tmp), format='PNG')

    imgsize = ((img2pdf.ImgSize.dpi, 8), (img2pdf.ImgSize.dpi, 8))
    layout_fun = img2pdf.get_layout_fun(None, imgsize, None, None, None)

    im_bytes = im_tmp.read_bytes()
    pdf_bytes = img2pdf.convert(
        im_bytes, producer="img2pdf", with_pdfrw=False, layout_fun=layout_fun
    )
    filename.write_bytes(pdf_bytes)

    info = pdfinfo.PdfInfo(filename)

    assert len(info) == 1
    page = info[0]

    assert not page.has_text
    assert len(page.images) == 1

    pdfimage = page.images[0]
    assert pdfimage.width == 8
    assert pdfimage.color == Colorspace.gray

    # DPI in a 1"x1" is the image width
    assert isclose(pdfimage.xres, 8)
    assert isclose(pdfimage.yres, 8)


def test_single_page_inline_image(outdir):
    filename = outdir / 'image-mono-inline.pdf'
    pdf = Canvas(str(filename), pagesize=(8 * 72, 6 * 72))
    with NamedTemporaryFile() as im_tmp:
        im = Image.new('1', (8, 8), 0)
        for n in range(8):
            im.putpixel((n, n), 1)
        im.save(im_tmp.name, format='PNG')
        # Draw image in a 72x72 pt or 1"x1" area
        pdf.drawInlineImage(im_tmp.name, 0, 0, width=72, height=72)
        pdf.showPage()
        pdf.save()

    pdf = pdfinfo.PdfInfo(filename)
    print(pdf)
    pdfimage = pdf[0].images[0]
    assert isclose(pdfimage.xres, 8)
    assert pdfimage.color == Colorspace.rgb  # reportlab produces color image
    assert pdfimage.width == 8


def test_jpeg(resources, outdir):
    filename = resources / 'c02-22.pdf'

    pdf = pdfinfo.PdfInfo(filename)

    pdfimage = pdf[0].images[0]
    assert pdfimage.enc == Encoding.jpeg
    assert isclose(pdfimage.xres, 150)


def test_form_xobject(resources):
    filename = resources / 'formxobject.pdf'

    pdf = pdfinfo.PdfInfo(filename)
    pdfimage = pdf[0].images[0]
    assert pdfimage.width == 50


def test_no_contents(resources):
    filename = resources / 'no_contents.pdf'

    pdf = pdfinfo.PdfInfo(filename)
    assert len(pdf[0].images) == 0
    assert pdf[0].has_text == False


def test_oversized_page(resources):
    pdf = pdfinfo.PdfInfo(resources / 'poster.pdf')
    image = pdf[0].images[0]
    assert image.width * image.xres > 200, "this is supposed to be oversized"


def test_pickle(resources):
    # For multiprocessing we must be able to pickle our information - if
    # this fails then we are probably storing some unpickleabe pikepdf or
    # other external data around
    filename = resources / 'graph_ocred.pdf'
    pdf = pdfinfo.PdfInfo(filename)
    pickle.dumps(pdf)


def test_regex():
    rx = pdfinfo.ghosttext.regex_remove_char_tags

    must_match = [
        b'<char bbox="0 108 0 108" c="/"/>',
        b'<char bbox="0 108 0 108" c=">"/>',
        b'<char bbox="0 108 0 108" c="X"/>',
    ]
    must_not_match = [b'<span stuff="c">', b'<span>', b'</span>', b'</page>']

    for s in must_match:
        assert rx.match(s)
    for s in must_not_match:
        assert not rx.match(s)


def test_vector(resources):
    filename = resources / 'vector.pdf'
    pdf = pdfinfo.PdfInfo(filename)
    assert pdf[0].has_vector
    assert not pdf[0].has_text


def test_ocr_detection(resources):
    filename = resources / 'graph_ocred.pdf'
    pdf = pdfinfo.PdfInfo(filename)
    assert not pdf[0].has_vector
    assert pdf[0].has_text


@pytest.mark.parametrize(
    'testfile', ('truetype_font_nomapping.pdf', 'type3_font_nomapping.pdf')
)
@pytest.helpers.needs_pdfminer  # pylint: disable=e1101
def test_corrupt_font_detection(resources, testfile):
    try:
        import pdfminer
    except ImportError:
        pytest.skip("Needs pdfminer")
    filename = resources / testfile
    with pytest.raises(NotImplementedError):
        pdf = pdfinfo.PdfInfo(filename)
        pdf[0].has_corrupt_text

    pdf = pdfinfo.PdfInfo(filename, detailed_page_analysis=True)
    assert pdf[0].has_corrupt_text


def test_stack_abuse():
    p = pikepdf.Pdf.new()

    stream = pikepdf.Stream(p, b'q ' * 35)
    with pytest.warns(None) as record:
        pdfinfo._interpret_contents(stream)
    assert 'overflowed' in str(record[0].message)

    stream = pikepdf.Stream(p, b'q Q Q Q Q')
    with pytest.warns(None) as record:
        pdfinfo._interpret_contents(stream)
    assert 'underflowed' in str(record[0].message)

    stream = pikepdf.Stream(p, b'q ' * 135)
    with pytest.warns(None):
        with pytest.raises(RuntimeError):
            pdfinfo._interpret_contents(stream)
