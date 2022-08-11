# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

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
        ['1-0', BadArgsError],
        ['99-98', BadArgsError],
        ['0-0', BadArgsError],
        ['1-0,3-4', BadArgsError],
        [',', BadArgsError],
        ['', BadArgsError],
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


def test_limited_pages(multipage, outpdf):
    ocrmypdf.ocr(
        multipage,
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
