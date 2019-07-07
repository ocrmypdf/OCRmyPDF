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

import os

from PIL import Image
import pytest


import ocrmypdf
from ocrmypdf.filters import invert, whiteout
from ocrmypdf._plugins import load_plugin


check_ocrmypdf = pytest.helpers.check_ocrmypdf


def filter_42():
    return 42


def test_pyfile():
    obj = load_plugin(f'{__file__}::filter_42')
    assert obj() == 42


def test_pyfile_notexist():
    with pytest.raises(FileNotFoundError):
        load_plugin('thisfile.doesnot.exist.py::filter_42')


def test_pyfile_noobject():
    with pytest.raises(AttributeError):
        load_plugin(f'{__file__}::no_function_with_this_name')


def test_module():
    obj = load_plugin(f'os.getuid')
    assert obj() == os.getuid()


def test_module_notexist():
    with pytest.raises(ModuleNotFoundError):
        load_plugin('thismodule.doesnot.exist')


def test_filter_from_cmdline(resources, outdir):
    (outdir / 'temp.py').write_text(
        "from PIL import Image\n"
        "def whiteout(im):\n"
        "    return Image.new(im.mode, im.size)\n"
    )

    check_ocrmypdf(
        resources / 'crom.png',
        outdir / 'out.pdf',
        '--image-dpi',
        '100',
        '--sidecar',
        outdir / 'sidecar.txt',
        '--filter-ocr-image',
        f"{outdir / 'temp.py'}::whiteout",
    )

    assert (outdir / 'sidecar.txt').read_text().strip() == ''


def test_filter_from_api(resources, outdir):
    ocrmypdf.ocr(
        resources / 'crom.png',
        outdir / 'out.pdf',
        image_dpi=100,
        sidecar=outdir / 'sidecar.txt',
        filter_ocr_image=whiteout,
    )
    assert (outdir / 'sidecar.txt').read_text().strip() == ''
