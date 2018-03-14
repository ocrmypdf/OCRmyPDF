# © 2015 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

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



