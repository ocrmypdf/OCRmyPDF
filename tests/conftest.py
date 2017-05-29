#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

import sys
import os
import platform

pytest_plugins = ['helpers_namespace']

import pytest
from pathlib import Path
from subprocess import Popen, PIPE


if sys.version_info.major < 3:
    print("Requires Python 3.4+")
    sys.exit(1)


@pytest.helpers.register
def is_linux():
    return platform.system() == 'Linux'


@pytest.helpers.register
def is_macos():
    return platform.system() == 'Darwin'


@pytest.helpers.register
def running_in_docker():
    # Docker creates a file named /.dockerenv (newer versions) or
    # /.dockerinit (older) -- this is undocumented, not an offical test
    return os.path.exists('/.dockerenv') or os.path.exists('/.dockerinit')


@pytest.helpers.register
def running_in_travis():
    return os.environ.get('TRAVIS') == 'true'


TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
SPOOF_PATH = os.path.join(TESTS_ROOT, 'spoof')
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
OCRMYPDF = [sys.executable, '-m', 'ocrmypdf']


@pytest.helpers.register
def spoof(**kwargs):
    """Modify environment variables to override subprocess executables

    spoof(program1='replacement', ...)

    Before running any executable, ocrmypdf checks the environment variable
    OCRMYPDF_PROGRAMNAME to override default program name/location, e.g.
    OCRMYPDF_GS redirects from the system path Ghostscript ("gs") to elsewhere.

    """
    env = os.environ.copy()

    for replace_program, with_spoof in kwargs.items():
        spoofer = os.path.join(SPOOF_PATH, with_spoof)
        if not os.access(spoofer, os.X_OK):
            os.chmod(spoofer, 0o755)
        env['OCRMYPDF_' + replace_program.upper()] = spoofer
    return env


@pytest.fixture
def spoof_tesseract_noop():
    return spoof(tesseract='tesseract_noop.py')


@pytest.fixture
def spoof_tesseract_cache():
    if running_in_docker():
        return os.environ.copy()
    return spoof(tesseract="tesseract_cache.py")


@pytest.fixture
def resources():
    return Path(TESTS_ROOT) / 'resources'


@pytest.fixture
def ocrmypdf_exec():
    return OCRMYPDF


@pytest.fixture(scope="function")
def outdir(tmpdir):
    return Path(str(tmpdir))


@pytest.fixture(scope="function")
def outpdf(tmpdir):
    return str(Path(str(tmpdir)) / 'out.pdf')


@pytest.fixture(scope="function")
def no_outpdf(tmpdir):
    """This just documents the fact that a test is not expected to produce
    output. Unfortunately an assertion failure inside a test fixture produces
    an error rather than a test failure, so no testing is done. It's up to
    the test to confirm that no output file was created."""
    return str(Path(str(tmpdir)) / 'no_output.pdf')


@pytest.helpers.register
def check_ocrmypdf(input_file, output_file, *args, env=None):
    "Run ocrmypdf and confirmed that a valid file was created"

    p, out, err = run_ocrmypdf(input_file, output_file, *args, env=env)
    #print(err)  # ensure py.test collects the output, use -s to view
    assert p.returncode == 0, "<stderr>\n" + err + "\n</stderr>"
    assert os.path.exists(str(output_file)), "Output file not created"
    assert os.stat(str(output_file)).st_size > 100, "PDF too small or empty"
    assert out == "", \
        "The following was written to stdout and should not have been: \n" + \
        "<stdout>\n" + out + "\n</stdout>"
    return output_file


@pytest.helpers.register
def run_ocrmypdf(input_file, output_file, *args, env=None):
    "Run ocrmypdf and let caller deal with results"

    if env is None:
        env = os.environ

    p_args = OCRMYPDF + list(args) + [str(input_file), str(output_file)]
    p = Popen(
        p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = p.communicate()
    #print(err)

    return p, out, err


@pytest.helpers.register
def first_page_dimensions(pdf):
    from ocrmypdf import pdfinfo
    info = pdfinfo.PdfInfo(pdf)
    page0 = info[0]
    return (page0.width_inches, page0.height_inches)
