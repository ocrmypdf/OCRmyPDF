# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
from decimal import Decimal

import pikepdf
import pytest
from PIL import Image

from ocrmypdf._exec.ghostscript import rasterize_pdf
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.helpers import Resolution

from .conftest import check_ocrmypdf, run_ocrmypdf

# pylint: disable=redefined-outer-name


@pytest.fixture
def francais(resources):
    path = resources / 'francais.pdf'
    return path, pikepdf.open(path)


def test_rasterize_size(francais, outdir):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].MediaBox[2], pdf.pages[0].MediaBox[3])
    assert pdf.pages[0].MediaBox[0] == pdf.pages[0].MediaBox[1] == 0
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
    page_size_pts = (pdf.pages[0].MediaBox[2], pdf.pages[0].MediaBox[3])
    assert pdf.pages[0].MediaBox[0] == pdf.pages[0].MediaBox[1] == 0
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
        assert im.info['dpi'] == (forced_dpi[1], forced_dpi[0])


def test_gs_render_failure(resources, outpdf):
    p, _out, err = run_ocrmypdf(
        resources / 'blank.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_render_failure.py',
    )
    assert 'Casper is not a friendly ghost' in err
    assert p.returncode == ExitCode.child_process_error


def test_gs_raster_failure(resources, outpdf):
    p, _out, err = run_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_raster_failure.py',
    )
    assert 'Ghost story archive not found' in err
    assert p.returncode == ExitCode.child_process_error


def test_ghostscript_pdfa_failure(resources, outpdf):
    p, _out, _err = run_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_pdfa_failure.py',
    )
    assert (
        p.returncode == ExitCode.pdfa_conversion_failed
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
