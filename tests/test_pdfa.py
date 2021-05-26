# © 2021 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pikepdf
import pytest

from .conftest import check_ocrmypdf


@pytest.mark.parametrize('optimize', (0, 3))
@pytest.mark.parametrize('pdfa_level', (1, 2, 3))
def test_pdfa(resources, outpdf, optimize, pdfa_level):
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        f'--output-type=pdfa-{pdfa_level}',
        f'--optimize={optimize}',
    )
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
