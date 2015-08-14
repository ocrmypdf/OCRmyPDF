#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE
from decimal import Decimal, getcontext
import re
import sys
import PyPDF2 as pypdf


FRIENDLY_COLORSPACE = {
    '/DeviceGray': 'gray',
    '/CalGray': 'gray',
    '/DeviceRGB': 'rgb',
    '/CalRGB': 'rgb',
    '/DeviceCMYK': 'cmyk',
    '/Lab': 'lab',
    '/ICCBased': 'icc',
    '/Indexed': 'index',
    '/Separation': 'sep',
    '/DeviceN': 'devn',
    '/Pattern': '-'
}

FRIENDLY_ENCODING = {
    '/CCITTFaxDecode': 'ccitt',
    '/DCTDecode': 'jpeg',
    '/JPXDecode': 'jpx',
    '/JBIG2Decode': 'jbig2',
}

FRIENDLY_COMP = {
    'gray': 1,
    'rgb': 3,
    'cmyk': 4,
    'lab': 3,
}


def _page_has_inline_images(page):
    # PDF always uses \r\n for separator regardless of platform
    # Really basic heuristic that might trigger the odd false positive
    # This is only finds the first image and is not quite spec compliant
    try:
        contents = page.getContents()
        data = contents.getData()
    except AttributeError:
        # If we can't access the contents or data (empty page?) then there
        # are no inline images
        return False

    begin_image, image_data, end_image = False, False, False
    for data in re.split(b'\s+', data):
        if data == b'BI':
            begin_image = True
        elif data == b'ID':
            image_data = True
        elif data == b'EI':
            end_image = True
        if all((begin_image, image_data, end_image)):
            return True
    return False


def _find_page_images(page, pageinfo):
    try:
        page['/Resources']['/XObject']
    except KeyError:
        return

    # Look for XObject (out of line images)
    for xobj in page['/Resources']['/XObject']:
        # PyPDF2 returns the keys as an iterator
        pdfimage = page['/Resources']['/XObject'][xobj]
        if pdfimage['/Subtype'] != '/Image':
            continue
        if '/ImageMask' in pdfimage:
            if pdfimage['/ImageMask']:
                continue
        image = {}
        image['width'] = pdfimage['/Width']
        image['height'] = pdfimage['/Height']
        image['bpc'] = pdfimage['/BitsPerComponent']
        if '/Filter' in pdfimage:
            filter_ = pdfimage['/Filter']
            if isinstance(filter_, pypdf.generic.ArrayObject):
                filter_ = filter_[0]
            image['enc'] = FRIENDLY_ENCODING.get(filter_, 'image')
        else:
            image['enc'] = 'image'
        if '/ColorSpace' in pdfimage:
            cs = pdfimage['/ColorSpace']
            if isinstance(cs, pypdf.generic.ArrayObject):
                cs = cs[0]
            image['color'] = FRIENDLY_COLORSPACE.get(cs, '-')
        else:
            image['color'] = 'jpx' if image['enc'] == 'jpx' else '?'

        image['comp'] = FRIENDLY_COMP.get(image['color'], '?')
        image['dpi_w'] = image['width'] / pageinfo['width_inches']
        image['dpi_h'] = image['height'] / pageinfo['height_inches']
        image['dpi'] = (image['dpi_w'] * image['dpi_h']) ** Decimal(0.5)
        yield image


def _pdf_get_pageinfo(infile, page: int):
    pageinfo = {}
    pageinfo['pageno'] = page
    pageinfo['images'] = []

    pdf = pypdf.PdfFileReader(infile)
    page = pdf.pages[page - 1]

    text = page.extractText()
    pageinfo['has_text'] = (text.strip() != '')

    width_pt = page['/MediaBox'][2] - page['/MediaBox'][0]
    height_pt = page['/MediaBox'][3] - page['/MediaBox'][1]
    pageinfo['width_inches'] = width_pt / Decimal(72.0)
    pageinfo['height_inches'] = height_pt / Decimal(72.0)

    pageinfo['images'] = [im for im in _find_page_images(page, pageinfo)]

    # Look for inline images
    if _page_has_inline_images(page):
        raise NotImplementedError(
            "Warning: input PDF contains inline images - not supported")

    if pageinfo['images']:
        xres = max(image['dpi_w'] for image in pageinfo['images'])
        yres = max(image['dpi_h'] for image in pageinfo['images'])
        pageinfo['xres'], pageinfo['yres'] = xres, yres
        pageinfo['width_pixels'] = \
            int(round(xres * pageinfo['width_inches']))
        pageinfo['height_pixels'] = \
            int(round(yres * pageinfo['height_inches']))

    return pageinfo


def pdf_get_all_pageinfo(infile):
    pdf = pypdf.PdfFileReader(infile)
    getcontext().prec = 6
    return [_pdf_get_pageinfo(infile, n) for n in range(pdf.numPages)]
