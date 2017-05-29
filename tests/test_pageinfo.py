#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from ocrmypdf import pdfinfo
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
from tempfile import NamedTemporaryFile
from math import isclose
from ocrmypdf.pdfinfo import Colorspace, Encoding
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
            im_bytes, producer="img2pdf", with_pdfrw=False,
            layout_fun=layout_fun)
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