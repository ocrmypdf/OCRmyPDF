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

from unittest.mock import MagicMock
import logging
import os

import pytest

import pikepdf
from ocrmypdf._weave import _fix_toc, _update_page_resources

check_ocrmypdf = pytest.helpers.check_ocrmypdf


def test_invalid_toc(resources, outdir, caplog):
    pdf = pikepdf.open(resources / 'toc.pdf')

    # Corrupt a TOC entry
    pdf.Root.Outlines.Last.Dest = pikepdf.Array([None, 0.0, 0.1, 0.2])
    pdf.save(outdir / 'test.pdf')

    pdf = pikepdf.open(outdir / 'test.pdf')
    remap = {}
    remap[pdf.pages[0].objgen] = pdf.pages[0].objgen  # Dummy remap

    # Confirm we complain about the TOC and don't throw an exception
    log = logging.getLogger()
    _fix_toc(pdf, remap, log)
    assert 'invalid table of contents entries' in caplog.text


def test_no_glyphless_weave(resources, outdir):
    pdf = pikepdf.open(resources / 'francais.pdf')
    pdf_aspect = pikepdf.open(resources / 'aspect.pdf')
    pdf_cmyk = pikepdf.open(resources / 'cmyk.pdf')
    pdf.pages.extend(pdf_aspect.pages)
    pdf.pages.extend(pdf_cmyk.pages)
    pdf.save(outdir / 'test.pdf')

    env = os.environ.copy()
    env['_OCRMYPDF_MAX_OPEN_PAGE_PDFS'] = '2'
    check_ocrmypdf(
        outdir / 'test.pdf',
        outdir / 'out.pdf',
        '--deskew',
        '--tesseract-timeout',
        '0',
        env=env,
    )
