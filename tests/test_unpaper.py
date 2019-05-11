# © 2015-17 James R. Barlow: github.com/jbarlow83
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

import argparse
import logging
from os import fspath
from pathlib import Path
from unittest.mock import patch

import pytest

from ocrmypdf import __main__ as main
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import unpaper

# pytest.helpers is dynamic
# pylint: disable=no-member
# pylint: disable=w0612

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


def have_unpaper():
    try:
        unpaper.version()
    except Exception:
        return False
    else:
        return True


@pytest.fixture(scope="session")
def spoof_unpaper_oldversion(tmpdir_factory):
    return spoof(tmpdir_factory, unpaper="unpaper_oldversion.py")


def test_no_unpaper(resources, no_outpdf):
    input_ = fspath(resources / "c02-22.pdf")
    output = fspath(no_outpdf)
    options = main.parser.parse_args(args=["--clean", input_, output])

    with patch("ocrmypdf.exec.unpaper.version") as mock_unpaper_version:
        mock_unpaper_version.side_effect = FileNotFoundError("unpaper")
        with pytest.raises(SystemExit):
            main.check_options(options, log=logging.getLogger())


def test_old_unpaper(spoof_unpaper_oldversion, resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / "c02-22.pdf", no_outpdf, "--clean", env=spoof_unpaper_oldversion
    )
    assert p.returncode == ExitCode.missing_dependency


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_clean(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / "skew.pdf", outpdf, "-c", env=spoof_tesseract_noop)


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_unpaper_args_valid(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        "--unpaper-args",
        "--layout double",  # Spaces required here
        env=spoof_tesseract_noop,
    )


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_unpaper_args_invalid_filename(spoof_tesseract_noop, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        "--unpaper-args",
        "/etc/passwd",
        env=spoof_tesseract_noop,
    )
    assert "No filenames allowed" in err
    assert p.returncode == ExitCode.bad_args


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_unpaper_args_invalid(spoof_tesseract_noop, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        "--unpaper-args",
        "unpaper is not going to like these arguments",
        env=spoof_tesseract_noop,
    )
    # Can't tell difference between unpaper choking on bad arguments or some
    # other unpaper failure
    assert p.returncode == ExitCode.child_process_error
