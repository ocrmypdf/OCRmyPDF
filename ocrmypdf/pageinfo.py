#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE
from decimal import Decimal, getcontext
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


def euclidean_distance(rowvec1, rowvec2):
    return ((rowvec1[0] - rowvec2[0]) ** 2
        + (rowvec1[1] - rowvec2[1]) ** 2) ** 0.5


ContentsInfo = namedtuple('ContentsInfo',
    ['raster_settings', 'has_inline_images'])

def _interpret_contents(contentstream):
    operations = contentstream.operations
    stack = []
    ctm = _matrix_from_shorthand((1, 0, 0, 1, 0, 0))
    image_raster_settings = []
    has_inline_images = False

    print(operations)
    for op in operations:
        operands, command = op
        if command == b'q':
            stack.append(ctm)
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
            # {'settings': {'/BPC': 8, '/H': 8, '/CS': '/RGB', '/F': ['/A85', '/Fl'], '/W': 8}, 'data': b'...'},
            has_inline_images = True

    return ContentsInfo(
        raster_settings=image_raster_settings,
        has_inline_images=has_inline_images)


def _find_page_images(page, pageinfo, contentsinfo):
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
            matrix = _matrix_from_shorthand(shorthand)

            # Corners of the image in untranslated square image space; last
            # column is a dummy
            corners = [[0, 0, 1],
                       [1, 0, 1],
                       [0, 1, 1],
                       [1, 1, 1]]

            # Rotate/translate/scale the corners into PDF coords (1/72")
            # ordering of points may change, e.g. if rotation is 180 then
            # the point (0, 0) may become the top right
            # The row vectors can all be transformed together here by building
            # a matrix of them
            page_unit_corners = matrix_mult(corners, matrix)
            print(matrix)
            print(page_unit_corners)

            # Calculate the width and height of the rotated image
            # the transformation matrix so the corner that was originally
            # (1, 1) can be ignored
            image_drawn_width = euclidean_distance(
                page_unit_corners[0], page_unit_corners[1])
            image_drawn_height = euclidean_distance(
                page_unit_corners[0], page_unit_corners[2])

            print((image_drawn_width, image_drawn_height))

            # The scale of the image is pixels per PDF unit (1/72")
            scale_w = image['width'] / image_drawn_width
            scale_h = image['height'] / image_drawn_height

            # DPI = scale * 72
            dpi_w = scale_w * 72.0
            dpi_h = scale_h * 72.0

            print((dpi_w, dpi_h))

            # If the image is drawn skewed or rotated analyzing its actual
            # bounding box is a bit more of headache. This is allowed, but
            # rare.
            if shorthand[1] != 0 or shorthand[2] != 0:
                print('image was rotated')

            # When image is used multiple times take the highest DPI it is
            # rendered at
            image['dpi_w'] = Decimal(max(dpi_w, image.get('dpi_w', 0)))
            image['dpi_h'] = Decimal(max(dpi_h, image.get('dpi_h', 0)))

        image['dpi'] = (image['dpi_w'] * image['dpi_h']) ** Decimal(0.5)
        yield image


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

    # Look for inline images
    if contentsinfo.has_inline_images:
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
