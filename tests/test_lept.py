# © 2018 James R. Barlow: github.com/jbarlow83
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


from os import fspath
from pickle import dumps, loads

import pytest
from PIL import Image, ImageChops

from ocrmypdf import leptonica as lp


def test_colormap_backgroundnorm(resources):
    # Issue #262 - unclear how to reproduce exactly, so just ensure leptonica
    # can handle that case
    pix = lp.Pix.open(resources / 'baiona_colormapped.png')
    pix.background_norm()


@pytest.fixture
def crom_pix(resources):
    pix = lp.Pix.open(resources / 'crom.png')
    im = Image.open(resources / 'crom.png')
    yield pix, im
    im.close()


def test_pix_basic(crom_pix):
    pix, im = crom_pix

    assert pix.width == im.width
    assert pix.height == im.height
    assert pix.mode == im.mode


def test_pil_conversion(crom_pix):
    pix, im = crom_pix

    # Check for pixel perfect
    assert ImageChops.difference(pix.topil(), im).getbbox() is None


def test_pix_otsu(crom_pix):
    pix, _ = crom_pix
    im1bpp = pix.otsu_adaptive_threshold()
    assert im1bpp.mode == '1'


@pytest.mark.skipif(
    lp.get_leptonica_version() < 'leptonica-1.76',
    reason="needs new leptonica for API change",
)
def test_crop(resources):
    pix = lp.Pix.open(resources / 'linn.png')
    foreground = pix.crop_to_foreground()
    assert foreground.width < pix.width


def test_clean_bg(resources):
    pix = lp.Pix.open(resources / 'congress.jpg')
    imbg = pix.clean_background_to_white()


def test_pickle(crom_pix):
    pix, _ = crom_pix
    pickled = dumps(pix)
    pix2 = loads(pickled)
    assert pix.mode == pix2.mode


def test_leptonica_compile(tmp_path):
    from ocrmypdf.lib.compile_leptonica import ffibuilder

    # Compile the library but build it somewhere that won't interfere with
    # existing compiled library. Also compile in API mode so that we test
    # the interfaces, even though we use it ABI mode.
    ffibuilder.compile(tmpdir=fspath(tmp_path), target=fspath(tmp_path / 'lepttest.*'))


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        lp.Pix.open("does_not_exist1")


@pytest.mark.skipif(
    lp.get_leptonica_version() < 'leptonica-1.79.0',
    reason="test not reliable on all platforms for old leptonica",
)
def test_error_trap():
    with pytest.raises(lp.LeptonicaError, match=r"Error in pixReadMem"):
        with lp._LeptonicaErrorTrap():
            lp.Pix(lp.lept.pixReadMem(lp.ffi.NULL, 0))
