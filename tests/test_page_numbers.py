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

import pytest

import ocrmypdf
from ocrmypdf._validation import _pages_from_ranges
from ocrmypdf.exceptions import BadArgsError
from ocrmypdf.pdfinfo import PdfInfo


@pytest.mark.parametrize(
    'pages, result',
    [
        ['1', {0}],
        ['1,2', {0, 1}],
        ['1-3', {0, 1, 2}],
        ['2,5,6', {1, 4, 5}],
        ['11-15, 18, ', {10, 11, 12, 13, 14, 17}],
        [',,3', {2}],
        ['3, 3, 3, 3,', {2}],
        ['3, 2, 1, 42', {0, 1, 2, 41}],
        ['-1', BadArgsError],
        ['1,3,-11', BadArgsError],
        ['1-,', BadArgsError],
        ['start-end', BadArgsError],
    ],
)
def test_pages(pages, result):
    if isinstance(result, type):
        with pytest.raises(result):
            _pages_from_ranges(pages)
    else:
        assert _pages_from_ranges(pages) == result


def test_nonmonotonic_warning(caplog):
    pages = _pages_from_ranges('1, 3, 2')
    assert pages == {0, 1, 2}
    assert 'out of order' in caplog.text


def test_list_range():
    assert _pages_from_ranges([0, 1, 2]) == {0, 1, 2}


def test_limited_pages(resources, outpdf):
    multi = resources / 'multipage.pdf'
    ocrmypdf.ocr(
        multi,
        outpdf,
        pages='5-6',
        optimize=0,
        output_type='pdf',
        plugins=['tests/plugins/tesseract_cache.py'],
    )
    pi = PdfInfo(outpdf)
    assert not pi.pages[0].has_text
    assert pi.pages[4].has_text
    assert pi.pages[5].has_text
