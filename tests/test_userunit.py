# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from math import isclose

import pytest

from ocrmypdf.pdfinfo import PdfInfo

from .conftest import check_ocrmypdf

# pylint: disable=redefined-outer-name


@pytest.fixture
def poster(resources):
    return resources / 'poster.pdf'


@pytest.mark.parametrize("mode", ['pdf', 'pdfa'])
def test_userunit_pdf_passes(mode, poster, outpdf):
    before = PdfInfo(poster)
    check_ocrmypdf(
        poster,
        outpdf,
        f'--output-type={mode}',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    after = PdfInfo(outpdf)
    assert isclose(before[0].width_inches, after[0].width_inches)


def test_rotate_interaction(poster, outpdf):
    check_ocrmypdf(
        poster,
        outpdf,
        '--output-type=pdf',
        '--rotate-pages',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
