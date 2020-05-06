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
