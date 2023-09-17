# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
from io import BytesIO, StringIO

import pytest

import ocrmypdf


def test_language_list():
    with pytest.raises(
        (ocrmypdf.exceptions.InputFileError, ocrmypdf.exceptions.MissingDependencyError)
    ):
        ocrmypdf.ocr('doesnotexist.pdf', '_.pdf', language=['eng', 'deu'])


def test_stream_api(resources):
    in_ = (resources / 'graph.pdf').open('rb')
    out = BytesIO()

    ocrmypdf.ocr(in_, out, tesseract_timeout=0.0)
    out.seek(0)
    assert b'%PDF' in out.read(1024)
