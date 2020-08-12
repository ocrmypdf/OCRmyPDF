# © 2018 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import pytest

from ocrmypdf.helpers import check_pdf


def test_pdf_error(resources):
    assert check_pdf(resources / 'blank.pdf')
    assert not check_pdf(__file__)
