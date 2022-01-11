# © 2015-17 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
from os import fspath
from unittest.mock import patch

import pytest
from PIL import Image

from ocrmypdf._exec import unpaper
from ocrmypdf._plugin_manager import get_parser_options_plugins
from ocrmypdf._validation import check_options
from ocrmypdf.exceptions import ExitCode, MissingDependencyError

from .conftest import check_ocrmypdf, have_unpaper, ocrmypdf_exec, run_ocrmypdf

# pylint: disable=redefined-outer-name

needs_unpaper = pytest.mark.skipif(not have_unpaper(), reason="requires unpaper")


def test_no_unpaper(resources, no_outpdf):
    input_ = fspath(resources / "c02-22.pdf")
    output = fspath(no_outpdf)

    _parser, options, pm = get_parser_options_plugins(["--clean", input_, output])
    with patch("ocrmypdf._exec.unpaper.version") as mock:
        mock.side_effect = FileNotFoundError("unpaper")

        with pytest.raises(MissingDependencyError):
            check_options(options, pm)
        mock.assert_called()


def test_old_unpaper(resources, no_outpdf):
    input_ = fspath(resources / "c02-22.pdf")
    output = fspath(no_outpdf)

    _parser, options, pm = get_parser_options_plugins(["--clean", input_, output])
    with patch("ocrmypdf._exec.unpaper.version") as mock:
        mock.return_value = '0.5'

        with pytest.raises(MissingDependencyError):
            check_options(options, pm)
        mock.assert_called()


@needs_unpaper
def test_clean(resources, outpdf):
    check_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@needs_unpaper
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


@needs_unpaper
def test_unpaper_args_invalid_filename(resources, outpdf):
    p = run_ocrmypdf(
        resources / "skew.pdf",
        outpdf,
        "-c",
        "--unpaper-args",
        "/etc/passwd",
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert "No filenames allowed" in p.stderr
    assert p.returncode == ExitCode.bad_args


@needs_unpaper
def test_unpaper_args_invalid(resources, outpdf):
    p = run_ocrmypdf(
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


@needs_unpaper
def test_unpaper_image_too_big(resources, outdir, caplog):
    with patch('ocrmypdf._exec.unpaper.UNPAPER_IMAGE_PIXEL_LIMIT', 42):
        infile = resources / 'crom.png'
        unpaper.clean(infile, outdir / 'out.png', dpi=300) == infile

        assert any(
            'too large for cleaning' in rec.message
            for rec in caplog.get_records('call')
            if rec.levelno == logging.WARNING
        )
