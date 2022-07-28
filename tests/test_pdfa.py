# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os

import pikepdf
import pytest

from ocrmypdf.exceptions import MissingDependencyError

from .conftest import check_ocrmypdf


@pytest.mark.parametrize('optimize', (0, 3))
@pytest.mark.parametrize('pdfa_level', (1, 2, 3))
def test_pdfa(resources, outpdf, optimize, pdfa_level):
    try:
        check_ocrmypdf(
            resources / 'francais.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            f'--output-type=pdfa-{pdfa_level}',
            f'--optimize={optimize}',
        )
    except MissingDependencyError as e:
        if 'pngquant' in str(e) and optimize in (2, 3) and os.name == 'nt':
            pytest.xfail("pngquant currently not available on Windows")
    if pdfa_level in (2, 3):
        # PDF/A-2 allows ObjStm
        assert b'/ObjStm' in outpdf.read_bytes()
    elif pdfa_level == 1:
        # PDF/A-1 might allow ObjStm, but Acrobat does not approve it, so
        # we don't use it
        assert b'/ObjStm' not in outpdf.read_bytes()

    with pikepdf.open(outpdf) as pdf:
        with pdf.open_metadata() as m:
            assert m.pdfa_status == f'{pdfa_level}B'
