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

import pytest

import pikepdf
from ocrmypdf._weave import _fix_toc

def test_invalid_toc(resources, tmpdir, caplog):
    pdf = pikepdf.open(resources / 'toc.pdf')

    # Corrupt a TOC entry
    pdf.Root.Outlines.Last.Dest = pikepdf.Array([None, 0.0, 0.1, 0.2])
    pdf.save(tmpdir / 'test.pdf')

    pdf = pikepdf.open(tmpdir / 'test.pdf')
    remap = {}
    remap[pdf.pages[0].objgen] = pdf.pages[0].objgen  # Dummy remap

    # Confirm we complain about the TOC and don't throw an exception
    log = logging.getLogger()
    _fix_toc(pdf, remap, log)
    assert 'invalid table of contents entries' in caplog.text
