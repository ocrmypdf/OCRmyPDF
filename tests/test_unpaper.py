# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
from os import fspath
from unittest.mock import patch

import pytest
from packaging.version import Version

from ocrmypdf._exec import unpaper
from ocrmypdf._plugin_manager import get_parser_options_plugins
from ocrmypdf._validation import check_options
from ocrmypdf.exceptions import BadArgsError, ExitCode, MissingDependencyError

from .conftest import check_ocrmypdf, have_unpaper, run_ocrmypdf_api

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
        mock.return_value = Version('0.5')

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
def test_unpaper_args_invalid_filename(resources, outpdf, caplog):
    with pytest.raises(BadArgsError):
        run_ocrmypdf_api(
            resources / "skew.pdf",
            outpdf,
            "-c",
            "--unpaper-args",
            "/etc/passwd",
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )


@needs_unpaper
def test_unpaper_args_invalid(resources, outpdf):
    exitcode = run_ocrmypdf_api(
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
    assert exitcode == ExitCode.child_process_error


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


@needs_unpaper
def test_palette_image(resources, outpdf):
    check_ocrmypdf(
        resources / "palette.pdf",
        outpdf,
        "-c",
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
