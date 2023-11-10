# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import secrets
import subprocess
from decimal import Decimal
from unittest.mock import patch

import pikepdf
import pytest
from PIL import Image, UnidentifiedImageError

from ocrmypdf._exec.ghostscript import DuplicateFilter, rasterize_pdf
from ocrmypdf.exceptions import ColorConversionNeededError, ExitCode
from ocrmypdf.helpers import Resolution

from .conftest import check_ocrmypdf, run_ocrmypdf_api

# pylint: disable=redefined-outer-name


@pytest.fixture
def francais(resources):
    path = resources / 'francais.pdf'
    return path, pikepdf.open(path)


def test_rasterize_size(francais, outdir):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].mediabox[2], pdf.pages[0].mediabox[3])
    assert pdf.pages[0].mediabox[0] == pdf.pages[0].mediabox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('50.0'), Decimal('30.0')
    forced_dpi = Resolution(42.0, 4242.0)

    rasterize_pdf(
        path,
        outdir / 'out.png',
        raster_device='pngmono',
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == target_size
        assert im.info['dpi'] == forced_dpi


def test_rasterize_rotated(francais, outdir, caplog):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].mediabox[2], pdf.pages[0].mediabox[3])
    assert pdf.pages[0].mediabox[0] == pdf.pages[0].mediabox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('50.0'), Decimal('30.0')
    forced_dpi = Resolution(42.0, 4242.0)

    caplog.set_level(logging.DEBUG)
    rasterize_pdf(
        path,
        outdir / 'out.png',
        raster_device='pngmono',
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
        rotation=90,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == (target_size[1], target_size[0])
        assert im.info['dpi'] == forced_dpi.flip_axis()


def test_gs_render_failure(resources, outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'blank.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_render_failure.py',
    )
    assert 'TEST ERROR: gs_render_failure.py' in caplog.text
    assert exitcode == ExitCode.child_process_error


def test_gs_raster_failure(resources, outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_raster_failure.py',
    )
    assert 'TEST ERROR: gs_raster_failure.py' in caplog.text
    assert exitcode == ExitCode.child_process_error


def test_ghostscript_pdfa_failure(resources, outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_pdfa_failure.py',
    )
    assert (
        exitcode == ExitCode.pdfa_conversion_failed
    ), "Unexpected return when PDF/A fails"


def test_ghostscript_feature_elision(resources, outpdf):
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_feature_elision.py',
    )


def test_ghostscript_mandatory_color_conversion(resources, outpdf):
    with pytest.raises(ColorConversionNeededError):
        check_ocrmypdf(
            resources / 'jbig2_baddevicen.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )


def test_rasterize_pdf_errors(resources, no_outpdf, caplog):
    with patch('ocrmypdf._exec.ghostscript.run') as mock:
        # ghostscript can produce
        mock.return_value = subprocess.CompletedProcess(
            ['fakegs'], returncode=0, stdout=b'', stderr=b'error this is an error'
        )
        with pytest.raises(UnidentifiedImageError):
            rasterize_pdf(
                resources / 'francais.pdf',
                no_outpdf,
                raster_device='pngmono',
                raster_dpi=Resolution(100, 100),
            )
        assert "this is an error" in caplog.text
        assert "invalid page image file" in caplog.text


class TestDuplicateFilter:
    @pytest.fixture(scope='function')
    def duplicate_filter_logger(self):
        # token_urlsafe: ensure the logger has a unique name so tests are isolated
        logger = logging.getLogger(__name__ + secrets.token_urlsafe(8))
        logger.setLevel(logging.DEBUG)
        logger.addFilter(DuplicateFilter(logger))
        return logger

    def test_filter_duplicate_messages(self, duplicate_filter_logger, caplog):
        log = duplicate_filter_logger
        log.error("test error message")
        log.error("test error message")
        log.error("test error message")
        log.error("another error message")
        log.error("another error message")
        log.error("yet another error message")

        assert len(caplog.records) == 5
        assert caplog.records[0].msg == "test error message"
        assert caplog.records[1].msg == "(suppressed 2 repeated lines)"
        assert caplog.records[2].msg == "another error message"
        assert caplog.records[3].msg == "(suppressed 1 repeated lines)"
        assert caplog.records[4].msg == "yet another error message"

    def test_filter_does_not_affect_unique_messages(
        self, duplicate_filter_logger, caplog
    ):
        log = duplicate_filter_logger
        log.error("test error message")
        log.error("another error message")
        log.error("yet another error message")

        assert len(caplog.records) == 3
        assert caplog.records[0].msg == "test error message"
        assert caplog.records[1].msg == "another error message"
        assert caplog.records[2].msg == "yet another error message"

    def test_filter_alt_messages(self, duplicate_filter_logger, caplog):
        log = duplicate_filter_logger
        log.error("test error message")
        log.error("another error message")
        log.error("test error message")
        log.error("another error message")
        log.error("test error message")
        log.error("test error message")
        log.error("another error message")
        log.error("yet another error message")

        assert len(caplog.records) == 4
        assert caplog.records[0].msg == "test error message"
        assert caplog.records[1].msg == "another error message"
        assert caplog.records[2].msg == "(suppressed 5 repeated lines)"
        assert caplog.records[3].msg == "yet another error message"
