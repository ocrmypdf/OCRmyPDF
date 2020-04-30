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
from io import BytesIO, StringIO

import pytest
from tqdm import tqdm

import ocrmypdf


def test_raw_console():
    bio = StringIO()
    tqconsole = ocrmypdf.api.TqdmConsole(file=bio)
    tqconsole.write("Test")
    tqconsole.flush()
    assert "Test" in bio.getvalue()


def test_tqdm_console():
    log = logging.getLogger()
    log.setLevel(logging.INFO)

    formatter = logging.Formatter('%(message)s')

    bio = StringIO()
    console = logging.StreamHandler(ocrmypdf.api.TqdmConsole(file=bio))
    console.setFormatter(formatter)

    log.addHandler(console)

    def before_pbar(message):
        # Ensure that log messages appear before the progress bar, even when
        # printed after the progress bar updates.
        v = bio.getvalue()
        pbar_start_marker = '|#'
        return v.index(message) < v.index(pbar_start_marker)

    with tqdm(total=2, file=bio, disable=False) as pbar:
        pbar.update()
        msg = "1/2 above progress bar"
        log.info(msg)
        assert before_pbar(msg)

    log.info("done")
    assert not before_pbar("done")


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
