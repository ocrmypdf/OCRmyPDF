# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import functools
import json
import logging
import os
import platform
import re
import shutil
import sys
import time
import warnings
from pathlib import Path
from subprocess import CompletedProcess, run

import PIL.Image
import pytest

from ocrmypdf import api, pdfinfo
from ocrmypdf._exec import unpaper
from ocrmypdf.api import setup_plugin_infrastructure
from ocrmypdf.cli import get_options_and_plugins
from ocrmypdf.exceptions import ExitCode

from .plugins.tesseract_cache import CACHE_INFO_FILE


class Gs106WarningFilter(logging.Filter):
    """Filter out expected Ghostscript 10.6+ JPEG encoding warning from test logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Allow all records except the expected Ghostscript 10.6+ warning
        return "contains JPEG encoding errors" not in record.getMessage()


@pytest.fixture(autouse=True)
def suppress_gs106_warning():
    """Suppress the expected Ghostscript 10.6.x JPEG encoding warning in tests."""
    # Add filter to root logger to suppress expected warnings
    root_logger = logging.getLogger()
    warning_filter = Gs106WarningFilter()
    root_logger.addFilter(warning_filter)
    yield
    root_logger.removeFilter(warning_filter)


@pytest.fixture(autouse=True)
def preserve_pil_max_image_pixels():
    """Restore PIL.Image.MAX_IMAGE_PIXELS after each test.

    Running the pipeline in-process with an explicit max_image_mpixels
    (including the CLI default) sets the process-global Pillow limit and
    leaves it set. Since max_image_mpixels=None means "respect the host's
    limit", a low limit from one test can make unrelated later tests in the
    same worker fail with DecompressionBombError.
    """
    saved = PIL.Image.MAX_IMAGE_PIXELS
    yield
    PIL.Image.MAX_IMAGE_PIXELS = saved


def is_linux():
    return platform.system() == 'Linux'


def is_macos():
    return platform.system() == 'Darwin'


def have_unpaper():
    try:
        unpaper.version()
    except Exception:  # pylint: disable=broad-except
        return False
    return True


@functools.cache
def have_poppler_pdftotext() -> bool:
    """Whether the pdftotext on PATH is poppler's.

    xpdf ships a pdftotext too, but it lacks options such as -bbox and orders
    text differently, so tests written against poppler cannot use it.
    """
    if shutil.which('pdftotext') is None:
        return False
    proc = run(['pdftotext', '-v'], capture_output=True, text=True, check=False)
    return 'poppler' in (proc.stdout + proc.stderr).lower()


TESTS_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = TESTS_ROOT

RENDERERS = ['fpdf2', 'sandwich']


@pytest.fixture(scope="session")
def resources() -> Path:
    return Path(TESTS_ROOT) / 'resources'


@pytest.fixture
def ocrmypdf_exec() -> list[str]:
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


@pytest.fixture
def no_speculative_pdfa(monkeypatch):
    """Make PDF/A output go through Ghostscript, skipping speculative conversion.

    For tests of the Ghostscript PDF/A path whose inputs would otherwise pass
    speculative conversion.
    """

    def no_speculative(*args, **kwargs):
        return None

    monkeypatch.setattr('ocrmypdf._pipeline.try_speculative_pdfa', no_speculative)


@pytest.fixture
def los_angeles_tz(monkeypatch):
    """Make America/Los_Angeles the local time zone for the test.

    Skipped where time.tzset() is unavailable (Windows), since the local zone
    cannot be changed from within the process there.
    """
    if not hasattr(time, 'tzset'):
        pytest.skip("time.tzset() is not available on this platform")
    monkeypatch.setenv('TZ', 'America/Los_Angeles')
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.fixture(scope="function")
def no_outpdf(tmp_path) -> Path:
    """Document fact that a test is not expected to produce output.

    This just documents the fact that a test is not expected to produce
    output. Unfortunately an assertion failure inside a test fixture produces
    an error rather than a test failure, so no testing is done. It's up to
    the test to confirm that no output file was created.
    """
    return tmp_path / 'no_output.pdf'


@pytest.fixture(scope="session")
def multipage(resources):
    return resources / 'multipage.pdf'


@pytest.fixture(scope="session")
def jpeg_scan(resources):
    """One-page 150 dpi JPEG scan of an antique book page; difficult OCR."""
    return resources / 'c03-29.pdf'


def check_ocrmypdf(input_file: Path, output_file: Path, *args) -> Path:
    """Run ocrmypdf and confirm that a valid plausible PDF was created."""
    api_args = [str(input_file), str(output_file)] + [
        str(arg) for arg in args if arg is not None
    ]

    options, plugin_manager = get_options_and_plugins(args=api_args)
    api.check_options(options, plugin_manager)
    result = api.run_pipeline(options, plugin_manager=plugin_manager)

    assert result == 0
    assert output_file.exists(), "Output file not created"
    assert output_file.stat().st_size > 100, "PDF too small or empty"

    return output_file


def run_ocrmypdf_api(input_file: Path, output_file: Path, *args) -> ExitCode:
    """Run ocrmypdf via its API in-process, but return CLI-style ExitCode.

    This simulates calling the command line interface in a subprocess and allows us
    to check that the command line interface is working correctly, but since it is
    in-process it is easier to trace with a debugger or coverage tool.

    Any exception raised will be trapped and converted to an exit code.
    The return code must be checked by the caller to determine if the test passed.
    """
    api_args = [str(input_file), str(output_file)] + [
        str(arg) for arg in args if arg is not None
    ]
    options, plugin_manager = get_options_and_plugins(args=api_args)

    api.check_options(options, plugin_manager)
    return api.run_pipeline_cli(options, plugin_manager=plugin_manager)


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


def verapdf_failed_rules(path: Path, flavour: str) -> set[str] | None:
    """Return the ids of the veraPDF rules *path* fails, or None without veraPDF.

    Ids use pikepdf's form, e.g. ``ISO_19005_2:6.2.2-2``.
    """
    from ocrmypdf._exec import verapdf

    if not verapdf.available():
        return None
    proc = run(
        ['verapdf', '--format', 'json', '--flavour', flavour, str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    result = json.loads(proc.stdout)['report']['jobs'][0]['validationResult'][0]
    return {
        f"ISO_19005_{flavour[0]}:{rule['clause']}-{rule['testNumber']}"
        for rule in result['details']['ruleSummaries']
    }


def assert_verapdf_agrees(path: Path, flavour: str) -> None:
    """If veraPDF is installed, assert it also finds *path* compliant."""
    failed = verapdf_failed_rules(path, flavour)
    if failed is not None:
        assert failed == set(), f"veraPDF {flavour} fails {sorted(failed)}"


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


def _major_minor(version: str) -> tuple[int, int] | None:
    m = re.match(r'\s*(\d+)\.(\d+)', version)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _installed_tesseract_version() -> str | None:
    try:
        from ocrmypdf._exec.tesseract import version as tesseract_version

        return str(tesseract_version())
    except Exception:  # pylint: disable=broad-except
        return None  # Tesseract is not installed or not usable


def pytest_sessionstart(session):
    """Warn when the committed Tesseract cache was made by another Tesseract."""
    if hasattr(session.config, 'workerinput'):
        return  # xdist worker; the controller reports for the whole session
    try:
        info = json.loads(CACHE_INFO_FILE.read_text())
    except (OSError, ValueError):
        return  # No cache, or unreadable; nothing to compare against

    cached = _major_minor(str(info.get('tesseract_version', '')))
    installed_str = _installed_tesseract_version()
    if installed_str is None:
        return
    installed = _major_minor(installed_str)
    if cached is None or installed is None or cached == installed:
        return

    message = (
        f"The Tesseract OCR cache in {CACHE_INFO_FILE.parent} was generated by "
        f"Tesseract {info['tesseract_version']}, but Tesseract {installed_str} "
        "is installed. Cached OCR results will not match what your Tesseract "
        "produces, so some tests may fail or pass for the wrong reason. See the "
        "\"Tesseract OCR cache\" section of docs/contributing.md to regenerate "
        "the cache."
    )
    if os.environ.get('OCRMYPDF_TEST_CACHE_STRICT') == '1':
        pytest.exit(message, returncode=pytest.ExitCode.USAGE_ERROR)
    warnings.warn(
        message + " Set OCRMYPDF_TEST_CACHE_STRICT=1 to make this an error.",
        stacklevel=1,
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def get_test_plugin_manager(plugins=None):
    """Get a properly initialized plugin manager for testing."""
    return setup_plugin_infrastructure(plugins=plugins or [])
