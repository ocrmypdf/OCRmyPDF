#!/usr/bin/env python3

from ocrmypdf import pageinfo
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
from tempfile import NamedTemporaryFile
from contextlib import suppress
import os
import sys
import shutil


TEST_OUTPUT = os.path.join(os.path.dirname(__file__), 'output')


def setup_module():
    with suppress(FileNotFoundError):
        shutil.rmtree(TEST_OUTPUT)
    with suppress(FileExistsError):
        os.mkdir(TEST_OUTPUT)


def test_single_page_text():
    filename = os.path.join(TEST_OUTPUT, 'text.pdf')
    pdf = Canvas(filename, pagesize=(8*72, 6*72))
    text = pdf.beginText()
    text.setFont('Helvetica', 12)
    text.setTextOrigin(4*72, 3*72)
    text.textLine("Methink’st thou art a general offence and every"
                  " man should beat thee.")
    pdf.drawText(text)
    pdf.showPage()
    pdf.save()

    pdfinfo = pageinfo.pdf_get_all_pageinfo(filename)

    assert len(pdfinfo) == 1
    page = pdfinfo[0]

    assert page['has_text']
    assert len(page['images']) == 0


def test_single_page_image():
    filename = os.path.join(TEST_OUTPUT, 'image-mono.pdf')
    pdf = Canvas(filename, pagesize=(8*72, 6*72))
    with NamedTemporaryFile() as im_tmp:
        im = Image.new('1', (8, 8), 0)
        for n in range(8):
            im.putpixel((n, n), 1)
        im.save(im_tmp.name, format='PNG')
        # Draw image in a 72x72 pt or 1"x1" area
        pdf.drawImage(im_tmp.name, 0, 0, width=72, height=72)
        pdf.showPage()
        pdf.save()

    pdfinfo = pageinfo.pdf_get_all_pageinfo(filename)

    assert len(pdfinfo) == 1
    page = pdfinfo[0]

    assert not page['has_text']
    assert len(page['images']) == 1

    pdfimage = page['images'][0]
    assert pdfimage['width'] == 8
    assert pdfimage['color'] == 'gray'

    # While unexpected, this is correct
    # PDF spec says /FlateDecode image must have /BitsPerComponent 8
    # So mono images get upgraded to 8-bit
    assert pdfimage['bpc'] == 8

    # DPI in a 1"x1" is the image width
    assert pdfimage['dpi_w'] == 8
    assert pdfimage['dpi_h'] == 8


def test_single_page_inline_image():
    filename = os.path.join(TEST_OUTPUT, 'image-mono-inline.pdf')
    pdf = Canvas(filename, pagesize=(8*72, 6*72))
    with NamedTemporaryFile() as im_tmp:
        im = Image.new('1', (8, 8), 0)
        for n in range(8):
            im.putpixel((n, n), 1)
        im.save(im_tmp.name, format='PNG')
        # Draw image in a 72x72 pt or 1"x1" area
        pdf.drawInlineImage(im_tmp.name, 0, 0, width=72, height=72)
        pdf.showPage()
        pdf.save()

    pdfinfo = pageinfo.pdf_get_all_pageinfo(filename)

    assert len(pdfinfo) == 1
    page = pdfinfo[0]

    assert not page['has_text']
    assert len(page['images']) == 1

    pdfimage = page['images'][0]
    assert pdfimage['width'] == 8
    assert pdfimage['color'] == 'gray'

    # While unexpected, this is correct
    # PDF spec says /FlateDecode image must have /BitsPerComponent 8
    # So mono images get upgraded to 8-bit
    assert pdfimage['bpc'] == 8

    # DPI in a 1"x1" is the image width
    assert pdfimage['dpi_w'] == 8
    assert pdfimage['dpi_h'] == 8
