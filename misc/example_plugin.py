# © 2020 James R Barlow: https://github.com/jbarlow83
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
