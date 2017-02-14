#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from ocrmypdf import pageinfo
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
from tempfile import NamedTemporaryFile
from contextlib import suppress
import os
import shutil
import pytest
import img2pdf
import pytest
import sys


def test_single_page_text(outdir):
    filename = outdir / 'text.pdf'
    pdf = Canvas(str(filename), pagesize=(8*72, 6*72))
    text = pdf.beginText()
    text.setFont('Helvetica', 12)
    text.setTextOrigin(1*72, 3*72)
    text.textLine("Methink'st thou art a general offence and every"
                  " man should beat thee.")
    pdf.drawText(text)
    pdf.showPage()
    pdf.save()

    pdfinfo = pageinfo.pdf_get_all_pageinfo(str(filename))

    assert len(pdfinfo) == 1
    page = pdfinfo[0]

    assert page['has_text']
    assert len(page['images']) == 0


@pytest.mark.skipif(sys.version_info < (3, 5), reason="needs Path.read_bytes")
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
            im_bytes, producer="img2pdf", with_pdfrw=False,
            layout_fun=layout_fun)
    filename.write_bytes(pdf_bytes)

    pdfinfo = pageinfo.pdf_get_all_pageinfo(str(filename))

    assert len(pdfinfo) == 1
    page = pdfinfo[0]

    assert not page['has_text']
    assert len(page['images']) == 1

    pdfimage = page['images'][0]
    assert pdfimage['width'] == 8
    assert pdfimage['color'] == 'gray'

    # DPI in a 1"x1" is the image width
    assert abs(pdfimage['dpi_w'] - 8) < 1e-5
    assert abs(pdfimage['dpi_h'] - 8) < 1e-5


def test_single_page_inline_image(outdir):
    filename = outdir / 'image-mono-inline.pdf'
    pdf = Canvas(str(filename), pagesize=(8*72, 6*72))
    with NamedTemporaryFile() as im_tmp:
        im = Image.new('1', (8, 8), 0)
        for n in range(8):
            im.putpixel((n, n), 1)
        im.save(im_tmp.name, format='PNG')
        # Draw image in a 72x72 pt or 1"x1" area
        pdf.drawInlineImage(im_tmp.name, 0, 0, width=72, height=72)
        pdf.showPage()
        pdf.save()

    pdfinfo = pageinfo.pdf_get_all_pageinfo(str(filename))
    print(pdfinfo)
    pdfimage = pdfinfo[0]['images'][0]
    assert (pdfimage['dpi_w'] - 8) < 1e-5
    assert pdfimage['color'] != '-'
    assert pdfimage['width'] == 8


def test_jpeg(resources, outdir):
    filename = resources / 'c02-22.pdf'

    pdfinfo = pageinfo.pdf_get_all_pageinfo(str(filename))

    pdfimage = pdfinfo[0]['images'][0]
    assert pdfimage['enc'] == 'jpeg'
    assert (pdfimage['dpi_w'] - 150) < 1e-5


def test_form_xobject(resources):
    filename = resources / 'formxobject.pdf'

    pdfinfo = pageinfo.pdf_get_all_pageinfo(str(filename))
    pdfimage = pdfinfo[0]['images'][0]
    assert pdfimage['width'] == 50
