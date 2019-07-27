# © 2017 James R. Barlow: github.com/jbarlow83
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

import os
from contextlib import contextmanager
from os import fspath
from pathlib import Path

import pytest

from ocrmypdf import pdfinfo
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.exec import tesseract

# pylint: disable=no-member,w0621

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


def test_tesseract_v4():
    assert tesseract.v4()


def test_pagesize_consistency_tess4(resources, outpdf):
    from math import isclose

    infile = resources / 'linn.pdf'

    before_dims = pytest.helpers.first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        'sandwich',
        '--clean' if pytest.helpers.have_unpaper() else None,
        '--deskew',
        '--remove-background',
        '--clean-final' if pytest.helpers.have_unpaper() else None,
    )

    after_dims = pytest.helpers.first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0])
    assert isclose(before_dims[1], after_dims[1])


@pytest.mark.parametrize('basename', ['graph_ocred.pdf', 'cardinal.pdf'])
def test_skip_pages_does_not_replicate(resources, basename, outdir):
    infile = resources / basename
    outpdf = outdir / basename

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        'sandwich',
        '--force-ocr',
        '--tesseract-timeout',
        '0',
    )

    info_in = pdfinfo.PdfInfo(infile)

    info = pdfinfo.PdfInfo(outpdf)
    for page in info:
        assert len(page.images) == 1, "skipped page was replicated"

    for n in range(len(info_in)):
        assert info[n].width_inches == info_in[n].width_inches


def test_content_preservation(resources, outpdf):
    infile = resources / 'masks.pdf'

    check_ocrmypdf(
        infile, outpdf, '--pdf-renderer', 'sandwich', '--tesseract-timeout', '0'
    )

    info = pdfinfo.PdfInfo(outpdf)
    page = info[0]
    assert len(page.images) > 1, "masks were rasterized"


def test_no_languages(tmp_path):
    env = os.environ.copy()
    (tmp_path / 'tessdata').mkdir()
    env['TESSDATA_PREFIX'] = fspath(tmp_path)

    with pytest.raises(MissingDependencyError):
        tesseract.languages(tesseract_env=env)
