# © 2019 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import logging
from decimal import Decimal

import pikepdf
import pytest
from PIL import Image

from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec.ghostscript import rasterize_pdf

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf_api
spoof = pytest.helpers.spoof


@pytest.fixture
def spoof_no_tess_gs_render_fail(tmp_path_factory):
    return spoof(
        tmp_path_factory, tesseract='tesseract_noop.py', gs='gs_render_failure.py'
    )


@pytest.fixture
def spoof_no_tess_gs_raster_fail(tmp_path_factory):
    return spoof(
        tmp_path_factory, tesseract='tesseract_noop.py', gs='gs_raster_failure.py'
    )


@pytest.fixture
def spoof_no_tess_no_pdfa(tmp_path_factory):
    return spoof(
        tmp_path_factory, tesseract='tesseract_noop.py', gs='gs_pdfa_failure.py'
    )


@pytest.fixture
def spoof_no_tess_pdfa_warning(tmp_path_factory):
    return spoof(
        tmp_path_factory, tesseract='tesseract_noop.py', gs='gs_feature_elision.py'
    )


@pytest.fixture
def francais(resources):
    path = resources / 'francais.pdf'
    return path, pikepdf.open(path)


def test_rasterize_size(francais, outdir, caplog):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].MediaBox[2], pdf.pages[0].MediaBox[3])
    assert pdf.pages[0].MediaBox[0] == pdf.pages[0].MediaBox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('50.0'), Decimal('30.0')
    forced_dpi = 42.0, 4242.0

    log = logging.getLogger()
    rasterize_pdf(
        path,
        outdir / 'out.png',
        target_size[0] / page_size[0],
        target_size[1] / page_size[1],
        raster_device='pngmono',
        log=log,
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
    forced_dpi = 42.0, 4242.0

    log = logging.getLogger()
    caplog.set_level(logging.DEBUG)
    rasterize_pdf(
        path,
        outdir / 'out.png',
        target_size[0] / page_size[0],
        target_size[1] / page_size[1],
        raster_device='pngmono',
        log=log,
        page_dpi=forced_dpi,
        rotation=90,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == (target_size[1], target_size[0])
        assert im.info['dpi'] == (forced_dpi[1], forced_dpi[0])


def test_gs_render_failure(spoof_no_tess_gs_render_fail, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'blank.pdf', outpdf, env=spoof_no_tess_gs_render_fail
    )
    assert 'Casper is not a friendly ghost' in err
    assert p.returncode == ExitCode.child_process_error


def test_gs_raster_failure(spoof_no_tess_gs_raster_fail, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf', outpdf, env=spoof_no_tess_gs_raster_fail
    )
    assert 'Ghost story archive not found' in err
    assert p.returncode == ExitCode.child_process_error


def test_ghostscript_pdfa_failure(spoof_no_tess_no_pdfa, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf', outpdf, env=spoof_no_tess_no_pdfa
    )
    assert (
        p.returncode == ExitCode.pdfa_conversion_failed
    ), "Unexpected return when PDF/A fails"


def test_ghostscript_feature_elision(spoof_no_tess_pdfa_warning, resources, outpdf):
    check_ocrmypdf(resources / 'francais.pdf', outpdf, env=spoof_no_tess_pdfa_warning)
