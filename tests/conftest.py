# © 2017 James R. Barlow: github.com/jbarlow83
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
import platform
import sys
from pathlib import Path
from subprocess import PIPE, run

import pytest

pytest_plugins = ['helpers_namespace']

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()

# pylint: disable=E1101
# pytest.helpers is dynamic so it confuses pylint

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


@pytest.helpers.register
def needs_pdfminer(fn):
    try:
        import pdfminer
    except ImportError:
        skip = pytest.mark.skipif(True, reason="pdfminer not available")
        return skip(fn)
    return fn


@pytest.helpers.register
def have_unpaper():
    try:
        from ocrmypdf.exec import unpaper

        unpaper.version()
    except Exception:
        return False
    return True


TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
SPOOF_PATH = os.path.join(TESTS_ROOT, 'spoof')
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
OCRMYPDF = [sys.executable, '-m', 'ocrmypdf']


@pytest.helpers.register
def spoof(tmpdir_factory, **kwargs):
    """Modify PATH to override subprocess executables

    spoof(program1='replacement', ...)

    Creates temporary directory with symlinks to targets.

    """
    env = os.environ.copy()
    slug = '-'.join(v.replace('.py', '') for v in sorted(kwargs.values()))
    spoofer_base = Path(str(tmpdir_factory.mktemp('spoofers')))
    tmpdir = spoofer_base / slug
    tmpdir.mkdir(parents=True)

    for replace_program, with_spoof in kwargs.items():
        spoofer = Path(SPOOF_PATH) / with_spoof
        spoofer.chmod(0o755)
        (tmpdir / replace_program).symlink_to(spoofer)

    env['_OCRMYPDF_SAVE_PATH'] = env['PATH']
    env['PATH'] = str(tmpdir) + ":" + env['PATH']

    return env


@pytest.fixture(scope='session')
def spoof_tesseract_noop(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_noop.py')


@pytest.fixture(scope='session')
def spoof_tesseract_cache(tmpdir_factory):
    if running_in_docker():
        return os.environ.copy()
    return spoof(tmpdir_factory, tesseract="tesseract_cache.py")


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
    """Run ocrmypdf and confirmed that a valid file was created"""

    p, out, err = run_ocrmypdf(input_file, output_file, *args, env=env)
    # ensure py.test collects the output, use -s to view
    print(err, file=sys.stderr)
    assert p.returncode == 0
    assert os.path.exists(str(output_file)), "Output file not created"
    assert os.stat(str(output_file)).st_size > 100, "PDF too small or empty"
    assert out == "", (
        "The following was written to stdout and should not have been: \n"
        + "<stdout>\n"
        + out
        + "\n</stdout>"
    )
    return output_file


@pytest.helpers.register
def run_ocrmypdf(input_file, output_file, *args, env=None, universal_newlines=True):
    "Run ocrmypdf and let caller deal with results"

    if env is None:
        env = os.environ

    p_args = (
        OCRMYPDF
        + [str(arg) for arg in args if arg is not None]
        + [str(input_file), str(output_file)]
    )
    p = run(
        p_args, stdout=PIPE, stderr=PIPE, universal_newlines=universal_newlines, env=env
    )
    # print(p.stderr)
    return p, p.stdout, p.stderr


@pytest.helpers.register
def first_page_dimensions(pdf):
    from ocrmypdf import pdfinfo

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
