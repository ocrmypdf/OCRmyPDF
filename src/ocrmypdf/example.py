from ocrmypdf import hookimpl


@hookimpl
def prepare(options):
    pass


@hookimpl
def filter_ocr_image(image):
    return image
