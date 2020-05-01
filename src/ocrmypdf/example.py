import logging

from ocrmypdf import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def prepare(options):
    pass


@hookimpl
def validate(pdfinfo, options):
    pass


@hookimpl
def filter_ocr_image(image):
    return image
