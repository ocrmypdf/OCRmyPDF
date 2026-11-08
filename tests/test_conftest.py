# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Tests for helpers in the test harness itself."""

from __future__ import annotations

from subprocess import CompletedProcess

import pytest

from . import conftest

XPDF_VERSION = 'pdftotext version 4.06 [www.xpdfreader.com]\n'
POPPLER_VERSION = (
    'pdftotext version 25.11.0\n'
    'Copyright 2005-2025 The Poppler Developers - http://poppler.freedesktop.org\n'
)


@pytest.mark.parametrize(
    'which, version_text, expected',
    [
        (None, '', False),
        ('/usr/bin/pdftotext', XPDF_VERSION, False),
        ('/usr/bin/pdftotext', POPPLER_VERSION, True),
    ],
)
def test_have_poppler_pdftotext(monkeypatch, which, version_text, expected):
    monkeypatch.setattr(conftest.shutil, 'which', lambda _name: which)
    monkeypatch.setattr(
        conftest,
        'run',
        lambda args, **_kw: CompletedProcess(args, 0, stdout='', stderr=version_text),
    )
    assert conftest.have_poppler_pdftotext.__wrapped__() is expected
