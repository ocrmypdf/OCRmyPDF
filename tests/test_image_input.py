# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from unittest.mock import patch

import img2pdf
import pikepdf
import pytest
from PIL import Image

import ocrmypdf

from .conftest import check_ocrmypdf, run_ocrmypdf_api

# pylint: disable=redefined-outer-name


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
    ) as mock:
        rc = run_ocrmypdf_api(
            resources / 'baiona_gray.png', no_outpdf, '--image-dpi', '200'
        )
        assert rc == ocrmypdf.ExitCode.input_file
        mock.assert_called()


@pytest.mark.xfail(reason="remove background disabled")
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
        assert next(iter(pdf.pages[0].images.values())).Filter == pikepdf.Name.DCTDecode
