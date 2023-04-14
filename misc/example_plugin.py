# SPDX-FileCopyrightText: 2022 James R Barlow: https://github.com/jbarlow83
# SPDX-License-Identifier: MIT

"""An example of an OCRmyPDF plugin.

This plugin adds two new command line arguments
    --grayscale-ocr: converts the image to grayscale before performing OCR on it
        (This is occasionally useful for images whose color confounds OCR. It only
        affects the image shown to OCR. The image is not saved.)
    --mono-page: converts pages all pages in the output file to black and white

To use this from the command line:
    ocrmypdf --plugin path/to/example_plugin.py --mono-page input.pdf output.pdf

To use this as an API:
    import ocrmypdf
    ocrmypdf.ocr('input.pdf', 'output.pdf',
        plugins=['path/to/example_plugin.py'], mono_page=True
    )
"""

from __future__ import annotations

import logging

from PIL import Image

from ocrmypdf import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def add_options(parser):
    parser.add_argument('--grayscale-ocr', action='store_true')
    parser.add_argument('--mono-page', action='store_true')


@hookimpl
def prepare(options):
    pass


@hookimpl
def validate(pdfinfo, options):
    pass


@hookimpl
def filter_ocr_image(page, image):
    if page.options.grayscale_ocr:
        log.info("graying")
        return image.convert('L')
    return image


@hookimpl
def filter_page_image(page, image_filename):
    if page.options.mono_page:
        with Image.open(image_filename) as im:
            im = im.convert('1')
            im.save(image_filename)
        return image_filename
    else:
        output = image_filename.with_suffix('.jpg')
        with Image.open(image_filename) as im:
            im.save(output)
        return output
