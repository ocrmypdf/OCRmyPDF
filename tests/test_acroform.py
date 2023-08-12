# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging

import pikepdf
import pytest

import ocrmypdf

from .conftest import check_ocrmypdf

# pylint: disable=redefined-outer-name


@pytest.fixture
def acroform(resources):
    return resources / 'acroform.pdf'


def test_acroform_and_redo(acroform, no_outpdf):
    with pytest.raises(
        ocrmypdf.exceptions.InputFileError, match='--redo-ocr is not currently possible'
    ):
        check_ocrmypdf(acroform, no_outpdf, '--redo-ocr')


def test_acroform_message(acroform, caplog, outpdf):
    caplog.set_level(logging.INFO)
    check_ocrmypdf(acroform, outpdf, '--plugin', 'tests/plugins/tesseract_noop.py')
    assert 'fillable form' in caplog.text
    assert '--force-ocr' in caplog.text


@pytest.fixture
def digitally_signed(acroform, outdir):
    out = outdir / 'acroform_signed.pdf'
    with pikepdf.open(acroform) as pdf:
        pdf.Root.AcroForm.SigFlags = 3
        pdf.save(out)
    yield out


def test_digital_signature(digitally_signed, no_outpdf):
    with pytest.raises(ocrmypdf.exceptions.DigitalSignatureError):
        check_ocrmypdf(digitally_signed, no_outpdf)


def test_digital_signature_invalidate(digitally_signed, no_outpdf):
    check_ocrmypdf(
        digitally_signed, no_outpdf, '--force-ocr', '--invalidate-digital-signatures'
    )
