#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from ocrmypdf import pageinfo
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
from tempfile import NamedTemporaryFile
from contextlib import suppress
import os
import sys
import shutil
import pytest
import img2pdf
from pkg_resources import Requirement, resource_filename

req = Requirement.parse('ocrmypdf')

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
    text.setTextOrigin(1*72, 3*72)
    text.textLine("Methink'st thou art a general offence and every"
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

    with NamedTemporaryFile() as im_tmp:
        im = Image.new('1', (8, 8), 0)
        for n in range(8):
            im.putpixel((n, n), 1)
        im.save(im_tmp.name, format='PNG')

        pdf_bytes = img2pdf.convert([im_tmp.name], dpi=8)
        with open(filename, 'wb') as pdf:
            pdf.write(pdf_bytes)

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

    with pytest.raises(NotImplementedError):
        pageinfo.pdf_get_all_pageinfo(filename)


def test_jpeg():
    filename = resource_filename(req, 'tests/resources/c02-22.pdf')

    pdfinfo = pageinfo.pdf_get_all_pageinfo(filename)

    pdfimage = pdfinfo[0]['images'][0]
    assert pdfimage['enc'] == 'jpeg'

