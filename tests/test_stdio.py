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

import os
import sys
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen, run

import pytest

from ocrmypdf.exceptions import ExitCode
from ocrmypdf.exec import qpdf

# pytest.helpers is dynamic
# pylint: disable=no-member,redefined-outer-name

run_ocrmypdf = pytest.helpers.run_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


@pytest.fixture
def spoof_tess_bad_utf8(tmp_path_factory):
    return spoof(tmp_path_factory, tesseract='tesseract_badutf8.py')


def test_stdin(spoof_tesseract_noop, ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf - output.pdf < testfile.pdf
    with open(input_file, 'rb') as input_stream:
        p_args = ocrmypdf_exec + ['-', output_file]
        p = run(
            p_args,
            stdout=PIPE,
            stderr=PIPE,
            stdin=input_stream,
            env=spoof_tesseract_noop,
        )
        assert p.returncode == ExitCode.ok


def test_stdout(spoof_tesseract_noop, ocrmypdf_exec, resources, outpdf):
    if 'COV_CORE_DATAFILE' in spoof_tesseract_noop:
        pytest.skip(msg="Coverage uses stdout")

    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf francais.pdf - > test_stdout.pdf
    with open(output_file, 'wb') as output_stream:
        p_args = ocrmypdf_exec + [input_file, '-']
        p = run(
            p_args,
            stdout=output_stream,
            stderr=PIPE,
            stdin=DEVNULL,
            env=spoof_tesseract_noop,
        )
        assert p.returncode == ExitCode.ok

    assert qpdf.check(output_file, log=None)


@pytest.mark.skipif(
    sys.version_info[0:3] >= (3, 6, 4), reason="issue fixed in Python 3.6.4"
)
@pytest.mark.skipif(os.name == 'nt', reason="POSIX problem")
def test_closed_streams(spoof_tesseract_noop, ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    def evil_closer():
        os.close(0)
        os.close(1)

    p_args = ocrmypdf_exec + [input_file, output_file]
    p = Popen(  # pylint: disable=subprocess-popen-preexec-fn
        p_args,
        close_fds=True,
        stdout=None,
        stderr=PIPE,
        stdin=None,
        env=spoof_tesseract_noop,
        preexec_fn=evil_closer,
    )
    out, err = p.communicate()
    print(err.decode())
    assert p.returncode == ExitCode.ok


@pytest.mark.skipif(sys.version_info >= (3, 7, 0), reason='better utf-8')
@pytest.mark.skipif(
    Path('/etc/alpine-release').exists(), reason="invalid test on alpine"
)
@pytest.mark.skipif(os.name == 'nt', reason="invalid test on Windows")
def test_bad_locale():
    env = os.environ.copy()
    env['LC_ALL'] = 'C'

    p, out, err = run_ocrmypdf('a', 'b', env=env)
    assert out == '', "stdout not clean"
    assert p.returncode != 0
    assert 'configured to use ASCII as encoding' in err, "should whine"


@pytest.mark.xfail(
    os.name == 'nt' and sys.version_info < (3, 8),
    reason="Windows does not like this; not sure how to fix",
)
def test_dev_null(spoof_tesseract_noop, resources):
    if 'COV_CORE_DATAFILE' in spoof_tesseract_noop:
        pytest.skip(msg="Coverage uses stdout")

    p, out, err = run_ocrmypdf(
        resources / 'trivial.pdf', os.devnull, '--force-ocr', env=spoof_tesseract_noop
    )
    assert p.returncode == 0, "could not send output to /dev/null"
    assert len(out) == 0, "wrote to stdout"
