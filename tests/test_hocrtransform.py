#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from ocrmypdf import hocrtransform
from ocrmypdf.exec.tesseract import HOCR_TEMPLATE
from ocrmypdf.exec import qpdf
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
from tempfile import NamedTemporaryFile
from contextlib import suppress
from pathlib import Path
import os
import shutil
import pytest
import img2pdf
import pytest
import sys


@pytest.fixture
def blank_hocr(tmpdir):
    filename = Path(str(tmpdir)) / "blank.hocr"
    with open(str(filename), 'w') as f:
        f.write(HOCR_TEMPLATE)
    return filename


def test_mono_image(blank_hocr, outdir):
    im = Image.new('1', (8, 8), 0)
    for n in range(8):
        im.putpixel((n, n), 1)
    im.save(outdir / 'mono.tif', format='TIFF')

    hocr = hocrtransform.HocrTransform(str(blank_hocr), 300)
    hocr.to_pdf(
        str(outdir / 'mono.pdf'), imageFileName=str(outdir / 'mono.tif'))

    qpdf.check(str(outdir / 'mono.pdf'))



