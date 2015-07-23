#!/usr/bin/env python3
#

from subprocess import Popen, PIPE
import PyPDF2 as pypdf
from decimal import Decimal


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


def _pdf_get_pageinfo(infile, page: int):
    pageinfo = {}
    pageinfo['pageno'] = page
    pageinfo['images'] = []

    p_pdftotext = Popen(['pdftotext', '-f', str(page), '-l', str(page),
                         '-raw', '-nopgbrk', infile, '-'],
                        close_fds=True, stdout=PIPE, stderr=PIPE,
                        universal_newlines=True)
    text, _ = p_pdftotext.communicate()
    if len(text.strip()) > 0:
        pageinfo['has_text'] = True
    else:
        pageinfo['has_text'] = False

    pdf = pypdf.PdfFileReader(infile)
    page = pdf.pages[page - 1]
    width_pt = page['/MediaBox'][2] - page['/MediaBox'][0]
    height_pt = page['/MediaBox'][3] - page['/MediaBox'][1]
    pageinfo['width_inches'] = width_pt / Decimal(72.0)
    pageinfo['height_inches'] = height_pt / Decimal(72.0)

    if '/XObject' not in page['/Resources']:
        # Missing /XObject means no images or possibly corrupt PDF
        return pageinfo

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
        pageinfo['images'].append(image)

    if pageinfo['images']:
        xres = max(image['dpi_w'] for image in pageinfo['images'])
        yres = max(image['dpi_h'] for image in pageinfo['images'])
        pageinfo['xres'], pageinfo['yres'] = xres, yres
        pageinfo['width_pixels'] = \
            int(round(xres * pageinfo['width_inches']))
        pageinfo['height_pixels'] = \
            int(round(yres * pageinfo['height_inches']))
        rx, ry = pageinfo['xres'], pageinfo['yres']
        pageinfo['xres_render'], pageinfo['yres_render'] = rx, ry

    return pageinfo


def pdf_get_all_pageinfo(infile):
    pdf = pypdf.PdfFileReader(infile)
    return [_pdf_get_pageinfo(infile, n) for n in range(pdf.numPages)]
