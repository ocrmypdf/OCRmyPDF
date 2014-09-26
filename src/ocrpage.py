#!/usr/bin/env python3
# Reimplement ocrPage.sh as Python

import argparse
import logging
import sys
import os.path
from parse import parse
from subprocess import Popen, PIPE, check_call

logger = logging.getLogger(__name__)


SUBPROC_PIPE = dict(close_fds=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    universal_newlines=True)


def pdf_get_pageinfo(infile, page, width_pt, height_pt):
    pageinfo = {}
    pageinfo['pageno'] = page
    pageinfo['width_inches'] = width_pt / 72.0
    pageinfo['height_inches'] = height_pt / 72.0
    pageinfo['images'] = []

    p_pdffonts = Popen(['pdffonts', '-f', str(page), '-l', str(page), infile],
                       **SUBPROC_PIPE)
    pdffonts, _ = p_pdffonts.communicate()
    if len(pdffonts.splitlines()) > 2:
        logger.info("Page already contains font data !!!")
        pageinfo['has_text'] = True
    else:
        pageinfo['has_text'] = False

    # pdfimages: get image dimensions
    p_pdfimages = Popen(['pdfimages', '-list', '-f', str(page), '-l',
                        str(page), str(infile)], **SUBPROC_PIPE)
    pdfimages, _ = p_pdfimages.communicate()
    for n, line in enumerate(pdfimages.splitlines()):
        if n <= 1:
            continue  # Skip first two lines

        r = parse('{page:1d} {num:1d} {imtype:>} {width:1d} {height:1d} ' +
                  '{color:>} {comp:1d} {bpc:1d} {enc:>} {interp:>} ' +
                  '{pdfobject:1d} {pdfid:1d} {bad_dpi_w:1d} {bad_dpi_h:1d} ' +
                  '{size:>} {ratio:>}', line)
        image = r.named
        # pdfimages calculates DPI as 0.26.0, but adds +1 to dpi_h
        # apparent bug, so calculate explicitly
        image['dpi_w'] = image['width'] / pageinfo['width_inches']
        image['dpi_h'] = image['height'] / pageinfo['height_inches']
        image['dpi'] = (image['dpi_w'] * image['dpi_h']) ** 0.5
        pageinfo['images'].append(image)

    return pageinfo


def unpack_with_pdftoppm(pageinfo, infile, output_folder, prefix,
                         force_ppm=False):
    xres = max(image['dpi_w'] for image in pageinfo['images'])
    yres = max(image['dpi_h'] for image in pageinfo['images'])

    colorspace = 'color'
    compression = 'deflate'
    output_format = 'tiff'
    if all(image['comp'] == 1 for image in pageinfo['images']):
        if all(image['bpc'] == 1 for image in pageinfo['images']):
            colorspace = 'mono'
            compression = 'deflate'
        elif not any(image['color'] == 'color'
                     for image in pageinfo['images']):
            colorspace = 'gray'

    if all(image['enc'] == 'jpeg' for image in pageinfo['images']):
        output_format = 'jpeg'

    args_pdftoppm = [
        'pdftoppm',
        '-f', str(pageinfo['pageno']), '-l', str(pageinfo['pageno']),
        '-rx', str(int(round(xres))),
        '-ry', str(int(round(yres))),
    ]

    if not force_ppm:
        if output_format == 'tiff':
            args_pdftoppm.append('-tiff')
            if compression:
                args_pdftoppm.append('-tiffcompression')
                args_pdftoppm.append(compression)
        elif output_format == 'jpeg':
            args_pdftoppm.append('-jpeg')

    if colorspace == 'mono':
        args_pdftoppm.append('-mono')
    elif colorspace == 'gray':
        args_pdftoppm.append('-gray')

    args_pdftoppm.extend([str(infile)])

    with open(
        os.path.join(output_folder, "%04i.ppm" % pageinfo['pageno']), 'wb'
    ) as output_file:
        print(output_file.name)
        check_call(args_pdftoppm, close_fds=True, stdout=output_file)


parser = argparse.ArgumentParser(
    prog="ocrpage",
    description="Run OCR and related jobs on a single page of a PDF file")

parser.add_argument(
    'input_pdf',
    help="DF file containing the page to be OCRed")
parser.add_argument(
    'page_info',
    help="Various characteristics of the page to be OCRed")
parser.add_argument(
    'num_pages',
    help="Total number of page of the PDF file (required for logger)")
parser.add_argument(
    'tmp_fld',
    help="Folder where the temporary files should be placed")
parser.add_argument(
    'verbosity',
    help="Requested verbosity")
parser.add_argument(
    'lan',
    help="Language of the file to be OCRed")
parser.add_argument(
    'keep_tmp',
    help="Keep the temporary files after processing (helpful for debugging)")
parser.add_argument(
    'preprocess_deskew',
    help="Deskew the page to be OCRed")
parser.add_argument(
    'preprocess_clean',
    help="Clean the page to be OCRed")
parser.add_argument(
    'preprocess_cleantopdf',
    help="Put the cleaned paged in the OCRed PDF")
parser.add_argument(
    'oversampling_dpi',
    help="Oversampling resolution in dpi")
parser.add_argument(
    'pdf_noimg',
    help="Generate debug PDF pages with only the OCRed text and no image")
parser.add_argument(
    'force_ocr',
    help="Force to OCR, even if the page already contains fonts")
parser.add_argument(
    'skip_text',
    help="Skip OCR on pages that contain fonts and include the page anyway")
# parser.add_argument(
#     'tess_cfg_files',
#     help="Specific configuration files to be used by Tesseract during OCRing")


def main():
    args = parser.parse_args()

    pageno, width_pt, height_pt = map(int, args.page_info.split(' ', 3))

    logger.name += '(page=%i)' % pageno

    logger.info("Processing page %i / %i", pageno, args.num_pages)

    pageinfo = pdf_get_pageinfo(args.input_pdf, pageno, width_pt, height_pt)

    if pageinfo['has_text']:
        if args.force_ocr:
            logger.info("Has text but forcing OCR (-f)")
        else:
            sys.exit(2)

    if len(pageinfo['images']) > 1:
        logger.warn("Page has more than one single image, proceeding anyway")

    unpack_with_pdftoppm(pageinfo, args.input_pdf, args.tmp_fld, prefix='',
                         force_ppm=True)


if __name__ == '__main__':
    main()
