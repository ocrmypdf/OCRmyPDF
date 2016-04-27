#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE
from decimal import Decimal, getcontext
from math import hypot
import re
import sys
import PyPDF2 as pypdf
from collections import namedtuple

matrix_mult = pypdf.pdf.utils.matrixMultiply

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
    '/Pattern': '-',
    '/G': 'gray',  # Abbreviations permitted in inline images
    '/RGB': 'rgb',
    '/CMYK': 'cmyk',
    '/I': 'index',
}

FRIENDLY_ENCODING = {
    '/CCITTFaxDecode': 'ccitt',
    '/DCTDecode': 'jpeg',
    '/JPXDecode': 'jpx',
    '/JBIG2Decode': 'jbig2',
    '/CCF': 'ccitt',  # Abbreviations permitted in inline images
    '/DCT': 'jpeg',
    '/AHx': 'asciihex',
    '/A85': 'ascii85',
    '/LZW': 'lzw',
    '/Fl': 'flate',
    '/RL': 'runlength'
}

FRIENDLY_COMP = {
    'gray': 1,
    'rgb': 3,
    'cmyk': 4,
    'lab': 3,
    'index': 1
}


def _matrix_from_shorthand(shorthand):
    """Convert from PDF matrix shorthand to full matrix

    PDF 1.7 spec defines a shorthand for describing the entries of a matrix
    since the last column is always (0, 0, 1).
    """

    a, b, c, d, e, f = map(float, shorthand)
    return ((a, b, 0),
            (c, d, 0),
            (e, f, 1))


def _shorthand_from_matrix(matrix):
    """Convert from transformation matrix to PDF shorthand."""
    a, b = matrix[0][0], matrix[0][1]
    c, d = matrix[1][0], matrix[1][1]
    e, f = matrix[2][0], matrix[2][1]
    return tuple(map(float, (a, b, c, d, e, f)))


ContentsInfo = namedtuple('ContentsInfo', ['raster_settings', 'inline_images'])


def _interpret_contents(contentstream):
    operations = contentstream.operations
    stack = []
    ctm = _matrix_from_shorthand((1, 0, 0, 1, 0, 0))
    image_raster_settings = []
    inline_images = []

    for op in operations:
        operands, command = op
        if command == b'q':
            stack.append(ctm)
            if len(stack) > 32:
                raise RuntimeError("PDF graphics stack overflow")
        elif command == b'Q':
            ctm = stack.pop()
        elif command == b'cm':
            ctm = matrix_mult(
                ctm, _matrix_from_shorthand(operands))
        elif command == b'Do':
            image_name = operands[0]
            image_raster_settings.append(
                (image_name, _shorthand_from_matrix(ctm)))
        elif command == b'INLINE IMAGE':
            settings = operands['settings']
            inline_images.append(
                (settings, _shorthand_from_matrix(ctm)))

    return ContentsInfo(
        raster_settings=image_raster_settings,
        inline_images=inline_images)


def _get_dpi(ctm_shorthand, image_size):
    """Given the transformation matrix and image size, find the image DPI.

    PDFs do not include image resolution information within image data.
    Instead, the PDF page content stream describes the location where the
    image will be rasterized, and the effective resolution is the ratio of the
    pixel size to raster target size.

    Normally a scanned PDF has the paper size set appropriately but this is
    not guaranteed. The most common case is a cropped image will change the
    page size (/CropBox) without altering the page content stream. That means
    it is not sufficient to assume that the image fills the page, even though
    that is the most common case.

    A PDF image may be scaled (always), cropped, translated, rotated in place
    to an arbitrary angle (rarely) and skewed. Only equal area mappings can
    be expressed, that is, it is not necessary to consider distortions where
    the effective DPI varies with position.

    To determine the image scale, transform an offset axis vector v0 (0, 0),
    width-axis vector v0 (1, 0), height-axis vector vh (0, 1) with the matrix,
    which gives the dimensions of the image in PDF units. From there we can
    compare to actual image dimensions. PDF uses
    row vector * matrix_tranposed unlike the traditional
    matrix * column vector.

    The offset, width and height vectors can be combined in a matrix and
    multiplied by the transform matrix. Then we want to calculated
        magnitude(width_vector - offset_vector)
    and
        magnitude(height_vector - offset_vector)

    When the above is worked out algebraically, the effect of translation
    cancels out, and the vector magnitudes become functions of the nonzero
    transformation matrix indices. The results of the derivation are used
    in this code.

    pdfimages -list does calculate the DPI in some way that is not completely
    naive, but it does not get the DPI of rotated images right, so cannot be
    used anymore to validate this. Photoshop works, or using Acrobat to
    rotate the image back to normal.

    It does not matter if the image is partially cropped, or even out of the
    /MediaBox.

    """

    a, b, c, d, _, _ = ctm_shorthand

    # Calculate the width and height of the image in PDF units
    image_drawn_width = hypot(a, b)
    image_drawn_height = hypot(c, d)

    # The scale of the image is pixels per PDF unit (1/72")
    scale_w = image_size[0] / image_drawn_width
    scale_h = image_size[1] / image_drawn_height

    # DPI = scale * 72
    dpi_w = scale_w * 72.0
    dpi_h = scale_h * 72.0

    return (dpi_w, dpi_h)


def _find_page_inline_images(page, pageinfo, contentsinfo):
    "Find inline images on the page"

    for n, im in enumerate(contentsinfo.inline_images):
        settings, shorthand = im
        image = {}
        image['name'] = str('inline-%02d' % n)
        image['width'] = settings['/W']
        image['height'] = settings['/H']
        image['bpc'] = settings['/BPC']
        image['color'] = FRIENDLY_COLORSPACE.get(settings['/CS'], '-')
        image['comp'] = FRIENDLY_COMP.get(image['color'], '?')
        if '/F' in settings:
            filter_ = settings['/F']
            if isinstance(filter_, pypdf.generic.ArrayObject):
                filter_ = filter_[0]
            image['enc'] = FRIENDLY_ENCODING.get(filter_, 'image')
        else:
            image['enc'] = 'image'

        dpi_w, dpi_h = _get_dpi(shorthand, (image['width'], image['height']))
        image['dpi_w'], image['dpi_h'] = Decimal(dpi_w), Decimal(dpi_h)
        yield image


def _find_page_regular_images(page, pageinfo, contentsinfo):
    "Find images stored in XObject resources"

    try:
        page['/Resources']['/XObject']
    except KeyError:
        return
    for xobj in page['/Resources']['/XObject']:
        # PyPDF2 returns the keys as an iterator
        pdfimage = page['/Resources']['/XObject'][xobj]
        if pdfimage['/Subtype'] != '/Image':
            continue
        image = {}
        image['name'] = str(xobj)
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
        image['dpi_w'] = image['dpi_h'] = 0

        for raster in contentsinfo.raster_settings:
            # Loop in case the same image is display multiple times on a page
            if raster[0] != image['name']:
                continue
            shorthand = raster[1]

            dpi_w, dpi_h = _get_dpi(
                shorthand, (image['width'], image['height']))

            # When image is used multiple times take the highest DPI it is
            # rendered at
            image['dpi_w'] = max(dpi_w, image.get('dpi_w', 0))
            image['dpi_h'] = max(dpi_h, image.get('dpi_h', 0))

        image['dpi_w'] = Decimal(image['dpi_w'])
        image['dpi_h'] = Decimal(image['dpi_h'])
        image['dpi'] = (image['dpi_w'] * image['dpi_h']) ** Decimal(0.5)
        yield image


def _find_page_images(page, pageinfo, contentsinfo):
    yield from _find_page_inline_images(page, pageinfo, contentsinfo)
    yield from _find_page_regular_images(page, pageinfo, contentsinfo)


def _page_has_text(pdf, page):
    # Simple test
    text = page.extractText()
    if text.strip() != '':
        return True

    # More nuanced test to deal with quirks of Tesseract PDF generation
    # Check if there's a Glyphless font
    try:
        font = page['/Resources']['/Font']
    except KeyError:
        pass
    else:
        font_objects = list(font.keys())
        for font_object in font_objects:
            basefont = font[font_object]['/BaseFont']
            if basefont.endswith('GlyphLessFont'):
                return True

    return False


def _pdf_get_pageinfo(infile, pageno: int):
    pageinfo = {}
    pageinfo['pageno'] = pageno
    pageinfo['images'] = []

    pdf = pypdf.PdfFileReader(infile)
    page = pdf.pages[pageno]

    pageinfo['has_text'] = _page_has_text(pdf, page)

    width_pt = page.mediaBox.getWidth()
    height_pt = page.mediaBox.getHeight()
    pageinfo['width_inches'] = width_pt / Decimal(72.0)
    pageinfo['height_inches'] = height_pt / Decimal(72.0)

    try:
        contentstream = pypdf.pdf.ContentStream(page.getContents(), pdf)
    except AttributeError as e:
        return pageinfo

    contentsinfo = _interpret_contents(contentstream)
    pageinfo['images'] = [im for im in _find_page_images(
                                page, pageinfo, contentsinfo)]

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


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    args = parser.parse_args()
    info = pdf_get_all_pageinfo(args.infile)
    from pprint import pprint
    pprint(info)


if __name__ == '__main__':
    main()
