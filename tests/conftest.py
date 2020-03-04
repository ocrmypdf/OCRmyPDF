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

import ast
import os
import platform
import sys
from pathlib import Path
from subprocess import PIPE, run

import pytest

from ocrmypdf import api, cli

pytest_plugins = ['helpers_namespace']


# pylint: disable=E1101
# pytest.helpers is dynamic so it confuses pylint

if sys.version_info < (3, 5):
    print("Requires Python 3.5+")
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


WINDOWS_SHIM_TEMPLATE = """
# This is a shim for Windows that has the same effect as a symlink to the target .py
# file
import os
import subprocess
import sys

args = [sys.executable, {spoofer}, *sys.argv[1:]]
p = subprocess.run(args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
sys.stdout.buffer.write(p.stdout)
sys.stderr.buffer.write(p.stderr)
sys.exit(p.returncode)
"""

assert ast.parse(WINDOWS_SHIM_TEMPLATE.format(spoofer=repr(r"C:\\Temp\\file.py")))


@pytest.helpers.register
def spoof(tmp_path_factory, **kwargs):
    """Modify PATH to override subprocess executables

    spoof(tmp_path_factory, program1='replacement', ...)

    For the test suite we need a way override executables, so that we can
    substitute desired results such as errors or just speed up OCR.

    On POSIXish platforms we create a temporary folder with overrides that
    are symlinks to the executables we want to run. We do not actually override
    PATH. We also set an environment variable _OCRMYPDF_TEST_PATH, which
    OCRmyPDF's subprocess wrapper will check before they use regular PATH. The
    output is a folder full of executables we are overriding. We can override
    multiple executables. The end result is a folder we can use in a PATH-style
    lookup to override some executables:

        /tmp/abcxyz/tesseract -> ocrmypdf/tests/resources/spoof/tesseract_crash.py
        /tmp/abcxyz/gs -> ocrmypdf/tests/resources/spoof/gs_backflip.py

    Windows needs extra help from us because usually, only the Administrator
    can create symlinks. Instead we create small Python scripts that call
    the programs we want, implementing the effect of a symlink. This is cleaner
    than creating Windows executables or trying to use non-Python scripts.
    The temporary folder generated for Windows could like:

        %TEMP%\abcxyz\tesseract.py:
            (script that runs ocrmypdf/tests/resources/spoof/tesseract_crash.py)
        %TEMP%\abcxyz\gswin32c.py:
            (script that runs ocrmypdf/tests/resources/spoof/gs_backflip.py)
        %TEMP%\abcxyz\gswin64c.py:
            (script that runs ocrmypdf/tests/resources/spoof/gs_backflip.py)

    We also address one quirk here, that Ghostscript may be known as gswin32c
    or gswin64c, depending on what the user installed (regardless of Windows
    itself). On POSIX, Ghostscript is just 'gs'.  We handle the special case here
    too.

    All of this is intimately dependent on the machinery in ocrmypdf.exec.run().
    In particular, for Windows, that code has to know that if there is a .py
    file, it needs to run it with Python, since Windows does not like being
    asked to execute files.

    We don't overload PATH directly because we have some tests where we call
    ocrmypdf as a subprocess (to exercise the command line interface) and some
    tests where we call it as an API.
    """
    env = os.environ.copy()
    slug = '-'.join(v.replace('.py', '') for v in sorted(kwargs.values()))
    spoofer_base = tmp_path_factory.mktemp('spoofers')
    tmpdir = Path(spoofer_base / slug)
    tmpdir.mkdir(parents=True)

    for replace_program, with_spoof in kwargs.items():
        spoofer = Path(SPOOF_PATH) / with_spoof
        if os.name != 'nt':
            spoofer.chmod(0o755)
            (tmpdir / replace_program).symlink_to(spoofer)
        else:
            py_file = WINDOWS_SHIM_TEMPLATE.format(
                spoofer=repr(os.fspath(spoofer.absolute()))
            )
            if replace_program == 'gs':
                programs = ['gswin64c', 'gswin32c']
            else:
                programs = [replace_program]
            for prog in programs:
                (tmpdir / f'{prog}.py').write_text(py_file, encoding='utf-8')

    env['_OCRMYPDF_TEST_PATH'] = str(tmpdir) + os.pathsep + env['PATH']
    if os.name == 'nt':
        if '.py' not in env['PATHEXT'].lower():
            raise EnvironmentError("PATHEXT is not configured to support .py")
    return env


@pytest.fixture
def spoof_tesseract_noop(tmp_path_factory):
    return spoof(tmp_path_factory, tesseract='tesseract_noop.py')


@pytest.fixture
def spoof_tesseract_cache(tmp_path_factory):
    if running_in_docker():
        return os.environ.copy()
    return spoof(tmp_path_factory, tesseract="tesseract_cache.py")


@pytest.fixture
def resources():
    return Path(TESTS_ROOT) / 'resources'


@pytest.fixture
def ocrmypdf_exec():
    return OCRMYPDF


@pytest.fixture(scope="function")
def outdir(tmp_path):
    return tmp_path


@pytest.fixture(scope="function")
def outpdf(tmp_path):
    return tmp_path / 'out.pdf'


@pytest.fixture(scope="function")
def no_outpdf(tmp_path):
    """This just documents the fact that a test is not expected to produce
    output. Unfortunately an assertion failure inside a test fixture produces
    an error rather than a test failure, so no testing is done. It's up to
    the test to confirm that no output file was created."""
    return tmp_path / 'no_output.pdf'


@pytest.helpers.register
def check_ocrmypdf(input_file, output_file, *args, env=None):
    """Run ocrmypdf and confirmed that a valid file was created"""

    options = cli.parser.parse_args(
        [str(input_file), str(output_file)]
        + [str(arg) for arg in args if arg is not None]
    )
    api.check_options(options)
    if env:
        options.tesseract_env = env
        options.tesseract_env['_OCRMYPDF_TEST_INFILE'] = os.fspath(input_file)
    result = api.run_pipeline(options, api=True)

    assert result == 0
    assert os.path.exists(str(output_file)), "Output file not created"
    assert os.stat(str(output_file)).st_size > 100, "PDF too small or empty"

    return output_file


@pytest.helpers.register
def run_ocrmypdf_api(input_file, output_file, *args, env=None):
    """Run ocrmypdf via API and let caller deal with results

    Does not currently have a way to manipulate the PATH except for Tesseract.
    """

    options = cli.parser.parse_args(
        [str(input_file), str(output_file)]
        + [str(arg) for arg in args if arg is not None]
    )
    api.check_options(options)
    if env:
        options.tesseract_env = env.copy()
        options.tesseract_env['_OCRMYPDF_TEST_INFILE'] = os.fspath(input_file)
        first_path = env.get('_OCRMYPDF_TEST_PATH', '').split(os.pathsep)[0]
        if 'spoof' in first_path:
            assert 'gs' not in first_path, "use run_ocrmypdf() for gs"
            assert 'tesseract' in first_path
    if options.tesseract_env:
        assert all(isinstance(v, (str, bytes)) for v in options.tesseract_env.values())

    return api.run_pipeline(options, api=False)


@pytest.helpers.register
def run_ocrmypdf(input_file, output_file, *args, env=None, universal_newlines=True):
    "Run ocrmypdf and let caller deal with results"

    if env is None:
        env = os.environ.copy()

    p_args = (
        OCRMYPDF
        + [str(arg) for arg in args if arg is not None]
        + [str(input_file), str(output_file)]
    )

    # Tell subprocess where to find coverage.py configuration
    # This has no effect except when coverage is running
    # Details: https://coverage.readthedocs.io/en/coverage-5.0/subprocess.html
    coverage_rc = Path(__file__).parent.parent / '.coveragerc'
    assert coverage_rc.exists()
    env['COVERAGE_PROCESS_START'] = os.fspath(coverage_rc)

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
