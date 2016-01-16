#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from ocrmypdf import hocrtransform
from ocrmypdf.tesseract import HOCR_TEMPLATE
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
from tempfile import NamedTemporaryFile
from contextlib import suppress
import os
import shutil
import pytest
import img2pdf
import pytest
import sys


if sys.version_info.major < 3:
    print("Requires Python 3.4+")
    sys.exit(1)

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
SPOOF_PATH = os.path.join(TESTS_ROOT, 'spoof')
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
OCRMYPDF = os.path.join(PROJECT_ROOT, 'OCRmyPDF.sh')
TEST_RESOURCES = os.path.join(PROJECT_ROOT, 'tests', 'resources')
TEST_OUTPUT = os.environ.get(
    'OCRMYPDF_TEST_OUTPUT',
    default=os.path.join(PROJECT_ROOT, 'tests', 'output', 'hocrtransform'))


def setup_module():
    with suppress(FileNotFoundError):
        shutil.rmtree(TEST_OUTPUT)
    with suppress(FileExistsError):
        os.makedirs(TEST_OUTPUT)
    with open(_make_output('blank.hocr'), 'w') as f:
        f.write(HOCR_TEMPLATE)


def _make_input(input_basename):
    return os.path.join(TEST_RESOURCES, input_basename)


def _make_output(output_basename):
    return os.path.join(TEST_OUTPUT, output_basename)


def test_mono_image():
    im = Image.new('1', (8, 8), 0)
    for n in range(8):
        im.putpixel((n, n), 1)
    im.save(_make_output('mono.tif'), format='TIFF')

    hocr = hocrtransform.HocrTransform(_make_output('blank.hocr'), 300)
    hocr.to_pdf(_make_output('mono.pdf'), imageFileName=_make_output('mono.tif'))





