# © 2020 James R Barlow: https://github.com/jbarlow83
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from PIL import Image

from ocrmypdf import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def add_options(parser):
    parser.add_argument('--grayscale-ocr', action='store_true')


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
    output = image_filename.with_suffix('.jpg')
    with Image.open(image_filename) as im:
        im.save(output)
    return output
