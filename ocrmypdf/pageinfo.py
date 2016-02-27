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
    '/DCT': 'jpeg'
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
    ['raster_settings', 'inline_images'])

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

    This code solves the general case where the image may be scaled (always),
    cropped, translated (often), and rotated in place (occasionally) to an
    arbitrary angle (rare). It will work as long as the image is a
    parallelogram from the perspective of a rectilinear coordinate system.
    It does not work for arbitrarily quadrilaterals that might be produced
    by shearing, but by that point DPI becomes a linear gradient rather than
    constant over the image.

    The transformation matrix describes the coordinate system at the time of
    rendering. We transform the image corner locations into the coordinate
    system and measure the width and height within the system, expressed in
    PDF units. From there we can compare to the actual image dimensions.

    pdfimages -list does calculate the DPI in some way that is not completely
    naive, but it does not the DPI of rotated images right, so cannot be
    used anymore to validate this. Photoshop works, or using Acrobat to
    rotate the image back to normal.

    It does not matter if the image is partially cropped, or even out of the
    /MediaBox.

    """
    matrix = _matrix_from_shorthand(ctm_shorthand)

    # Corners of the image in untransformed unit space; last
    # column is a dummy to assist matrix math
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

    # Calculate the width and height of the rotated image
    # the transformation matrix so the corner that was originally
    # (1, 1) can be ignored
    image_drawn_width = euclidean_distance(
        page_unit_corners[0], page_unit_corners[1])
    image_drawn_height = euclidean_distance(
        page_unit_corners[0], page_unit_corners[2])

    # print((image_drawn_width, image_drawn_height))

    # The scale of the image is pixels per PDF unit (1/72")
    scale_w = image_size[0] / image_drawn_width
    scale_h = image_size[1] / image_drawn_height

    # DPI = scale * 72
    dpi_w = scale_w * 72.0
    dpi_h = scale_h * 72.0

    return (dpi_w, dpi_h)


def _find_page_images(page, pageinfo, contentsinfo):

    for n, im in enumerate(contentsinfo.inline_images):
        settings, shorthand = im
        image = {}
        image['name'] = str('inline-%02d' % n)
        image['width'] = settings['/W']
        image['height'] = settings['/H']
        image['bpc'] = settings['/BPC']
        image['color'] = FRIENDLY_COLORSPACE.get(settings['/CS'], '-')
        image['comp'] = FRIENDLY_COMP.get(image['color'], '?')

        dpi_w, dpi_h = _get_dpi(shorthand, (image['width'], image['height']))
        image['dpi_w'], image['dpi_h'] = Decimal(dpi_w), Decimal(dpi_h)
        yield image

    # Look for XObject (out of line images)
    try:
        page['/Resources']['/XObject']
    except KeyError:
        return
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
