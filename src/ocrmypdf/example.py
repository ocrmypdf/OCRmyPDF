import logging

from ocrmypdf import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def install_cli(parser):
    parser.add_argument('--invert', action='store_true')


@hookimpl
def prepare(options):
    pass


@hookimpl
def validate(pdfinfo, options):
    pass


@hookimpl
def filter_ocr_image(page, image):
    if page.options.invert:
        log.info("inverting")
        return image.invert()
    return image
