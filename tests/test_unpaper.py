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

from os import fspath
from unittest.mock import patch

import pytest

from ocrmypdf._plugin_manager import get_parser_options_plugins
from ocrmypdf._validation import check_options
from ocrmypdf.exceptions import ExitCode, MissingDependencyError

# pytest.helpers is dynamic
# pylint: disable=no-member,redefined-outer-name
# pylint: disable=w0612

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
have_unpaper = pytest.helpers.have_unpaper


def test_no_unpaper(resources, no_outpdf):
    input_ = fspath(resources / "c02-22.pdf")
    output = fspath(no_outpdf)

    _parser, options, pm = get_parser_options_plugins(["--clean", input_, output])
    with patch("ocrmypdf._exec.unpaper.version") as mock_unpaper_version:
        mock_unpaper_version.side_effect = FileNotFoundError("unpaper")

        with pytest.raises(MissingDependencyError):
            check_options(options, pm)


def test_old_unpaper(resources, no_outpdf):
    input_ = fspath(resources / "c02-22.pdf")
    output = fspath(no_outpdf)

    _parser, options, pm = get_parser_options_plugins(["--clean", input_, output])
    with patch("ocrmypdf._exec.unpaper.version") as mock_unpaper_version:
        mock_unpaper_version.return_value = '0.5'

        with pytest.raises(MissingDependencyError):
            check_options(options, pm)


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_clean(resources, outpdf):
    check_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_unpaper_args_valid(resources, outpdf):
    check_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        "--unpaper-args",
        "--layout double",  # Spaces required here
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_unpaper_args_invalid_filename(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        "--unpaper-args",
        "/etc/passwd",
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert "No filenames allowed" in err
    assert p.returncode == ExitCode.bad_args


@pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")
def test_unpaper_args_invalid(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        "--unpaper-args",
        "unpaper is not going to like these arguments",
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    # Can't tell difference between unpaper choking on bad arguments or some
    # other unpaper failure
    assert p.returncode == ExitCode.child_process_error
