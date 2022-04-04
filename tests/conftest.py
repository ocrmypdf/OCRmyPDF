# © 2017 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
import platform
import sys
from pathlib import Path
from subprocess import PIPE, CompletedProcess, run
from typing import List

import pytest

from ocrmypdf import api, pdfinfo
from ocrmypdf._exec import unpaper
from ocrmypdf._plugin_manager import get_parser_options_plugins
from ocrmypdf.exceptions import ExitCode


def is_linux():
    return platform.system() == 'Linux'


def is_macos():
    return platform.system() == 'Darwin'


def running_in_docker():
    # Docker creates a file named /.dockerenv (newer versions) or
    # /.dockerinit (older) -- this is undocumented, not an offical test
    return Path('/.dockerenv').exists() or Path('/.dockerinit').exists()


def have_unpaper():
    try:
        unpaper.version()
    except Exception:  # pylint: disable=broad-except
        return False
    return True


TESTS_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = TESTS_ROOT


@pytest.fixture
def resources() -> Path:
    return Path(TESTS_ROOT) / 'resources'


@pytest.fixture
def ocrmypdf_exec() -> List[str]:
    return [sys.executable, '-m', 'ocrmypdf']


@pytest.fixture(scope="function")
def outdir(tmp_path) -> Path:
    return tmp_path


@pytest.fixture(scope="function")
def outpdf(tmp_path) -> Path:
    return tmp_path / 'out.pdf'


@pytest.fixture(scope="function")
def outtxt(tmp_path) -> Path:
    return tmp_path / 'out.txt'


@pytest.fixture(scope="function")
def no_outpdf(tmp_path) -> Path:
    """This just documents the fact that a test is not expected to produce
    output. Unfortunately an assertion failure inside a test fixture produces
    an error rather than a test failure, so no testing is done. It's up to
    the test to confirm that no output file was created."""
    return tmp_path / 'no_output.pdf'


def check_ocrmypdf(input_file: Path, output_file: Path, *args) -> Path:
    """Run ocrmypdf and confirm that a valid plausible PDF was created."""
    api_args = [str(input_file), str(output_file)] + [
        str(arg) for arg in args if arg is not None
    ]

    _parser, options, plugin_manager = get_parser_options_plugins(args=api_args)
    api.check_options(options, plugin_manager)
    result = api.run_pipeline(options, plugin_manager=plugin_manager, api=True)

    assert result == 0
    assert output_file.exists(), "Output file not created"
    assert output_file.stat().st_size > 100, "PDF too small or empty"

    return output_file


def run_ocrmypdf_api(input_file: Path, output_file: Path, *args) -> ExitCode:
    """Run ocrmypdf via its API in-process, and let test deal with results.

    This simulates calling the command line interface in a subprocess, but
    is easier for debuggers and code coverage to follow.

    Any exception raised will be trapped and converted to an exit code.
    The return code must always be checked or the test may declare a failure
    to be pass.
    """

    api_args = [str(input_file), str(output_file)] + [
        str(arg) for arg in args if arg is not None
    ]
    _parser, options, plugin_manager = get_parser_options_plugins(args=api_args)

    api.check_options(options, plugin_manager)
    return api.run_pipeline(options, plugin_manager=None, api=False)


def run_ocrmypdf(
    input_file: Path, output_file: Path, *args, text: bool = True
) -> CompletedProcess:
    """Run ocrmypdf in a subprocess and let test deal with results.

    If an exception is thrown this fact will be returned as part of the result
    text and return code rather than exception objects.
    """

    p_args = (
        [sys.executable, '-m', 'ocrmypdf']
        + [str(arg) for arg in args if arg is not None]
        + [str(input_file), str(output_file)]
    )

    p = run(
        p_args,
        capture_output=True,
        text=text,
        check=False,
    )
    # print(p.stderr)
    return p


def first_page_dimensions(pdf: Path):
    info = pdfinfo.PdfInfo(pdf)
    page0 = info[0]
    return (page0.width_inches, page0.height_inches)


def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help=(
            "run slow tests only useful for development (unlikely to be "
            "useful for downstream packagers)"
        ),
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
