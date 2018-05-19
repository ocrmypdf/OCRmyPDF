# © 2018 James R. Barlow: github.com/jbarlow83
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

from pathlib import Path

import pytest

import pikepdf

from ocrmypdf import _optimize as opt


@pytest.mark.parametrize('pdf', ['multipage.pdf', 'palette.pdf'])
def test_basic(resources, pdf, outpdf):
    infile = resources / pdf
    opt.main(infile, outpdf, level=3)

    assert Path(outpdf).stat().st_size <= Path(infile).stat().st_size
