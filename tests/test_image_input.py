# © 2019 James R. Barlow: github.com/jbarlow83
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

from unittest.mock import patch

import img2pdf
import pikepdf
import pytest
from PIL import Image

import ocrmypdf

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf_api


@pytest.fixture
def baiona(resources):
    return Image.open(resources / 'baiona_gray.png')


def test_image_to_pdf(resources, outpdf):
    check_ocrmypdf(
        resources / 'crom.png',
        outpdf,
        '--image-dpi',
        '200',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


def test_no_dpi_info(caplog, baiona, outdir, no_outpdf):
    im = baiona
    assert 'dpi' not in im.info
    input_image = outdir / 'baiona_no_dpi.png'
    im.save(input_image)

    rc = run_ocrmypdf_api(input_image, no_outpdf)
    assert rc == ocrmypdf.ExitCode.input_file
    assert "--image-dpi" in caplog.text


def test_dpi_not_credible(caplog, baiona, outdir, no_outpdf):
    im = baiona
    assert 'dpi' not in im.info
    input_image = outdir / 'baiona_no_dpi.png'
    im.save(input_image, dpi=(30, 30))

    rc = run_ocrmypdf_api(input_image, no_outpdf)
    assert rc == ocrmypdf.ExitCode.input_file
    assert "not credible" in caplog.text


def test_cmyk_no_icc(caplog, resources, no_outpdf):
    rc = run_ocrmypdf_api(resources / 'baiona_cmyk.jpg', no_outpdf)
    assert rc == ocrmypdf.ExitCode.input_file
    assert "no ICC profile" in caplog.text


def test_img2pdf_fails(resources, no_outpdf):
    with patch(
        'ocrmypdf._pipeline.img2pdf.convert', side_effect=img2pdf.ImageOpenError()
    ):
        rc = run_ocrmypdf_api(
            resources / 'baiona_gray.png', no_outpdf, '--image-dpi', '200'
        )
        assert rc == ocrmypdf.ExitCode.input_file


def test_jpeg_in_jpeg_out(resources, outpdf):
    check_ocrmypdf(
        resources / 'congress.jpg',
        outpdf,
        '--image-dpi',
        '100',
        '--output-type',
        'pdf',  # specifically check pdf because Ghostscript may convert to JPEG
        '--remove-background',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    with pikepdf.open(outpdf) as pdf:
        assert next(pdf.pages[0].images.values()).Filter == pikepdf.Name.DCTDecode
