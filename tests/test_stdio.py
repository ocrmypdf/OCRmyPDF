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
from subprocess import DEVNULL, PIPE, Popen, run

import pytest

from ocrmypdf.exceptions import ExitCode
from ocrmypdf.helpers import check_pdf

# pytest.helpers is dynamic
# pylint: disable=no-member,redefined-outer-name

run_ocrmypdf = pytest.helpers.run_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf


def test_stdin(ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf - output.pdf < testfile.pdf
    with open(input_file, 'rb') as input_stream:
        p_args = ocrmypdf_exec + [
            '-',
            output_file,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        ]
        p = run(p_args, stdout=PIPE, stderr=PIPE, stdin=input_stream)
        assert p.returncode == ExitCode.ok


def test_stdout(ocrmypdf_exec, resources, outpdf):
    if 'COV_CORE_DATAFILE' in os.environ:
        pytest.skip(msg="Coverage uses stdout")

    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf francais.pdf - > test_stdout.pdf
    with open(output_file, 'wb') as output_stream:
        p_args = ocrmypdf_exec + [
            input_file,
            '-',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        ]
        p = run(p_args, stdout=output_stream, stderr=PIPE, stdin=DEVNULL)
        assert p.returncode == ExitCode.ok

    assert check_pdf(output_file)


@pytest.mark.skipif(
    sys.version_info[0:3] >= (3, 6, 4), reason="issue fixed in Python 3.6.4"
)
@pytest.mark.skipif(os.name == 'nt', reason="POSIX problem")
def test_closed_streams(ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    def evil_closer():
        os.close(0)
        os.close(1)

    p_args = ocrmypdf_exec + [
        input_file,
        output_file,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    ]
    p = Popen(  # pylint: disable=subprocess-popen-preexec-fn
        p_args,
        close_fds=True,
        stdout=None,
        stderr=PIPE,
        stdin=None,
        preexec_fn=evil_closer,
    )
    _out, err = p.communicate()
    print(err.decode())
    assert p.returncode == ExitCode.ok


@pytest.mark.skipif(sys.version_info >= (3, 7, 0), reason='better utf-8')
@pytest.mark.skipif(
    Path('/etc/alpine-release').exists(), reason="invalid test on alpine"
)
@pytest.mark.skipif(os.name == 'nt', reason="invalid test on Windows")
def test_bad_locale(monkeypatch):
    monkeypatch.setenv('LC_ALL', 'C')
    p, out, err = run_ocrmypdf('a', 'b')
    assert out == '', "stdout not clean"
    assert p.returncode != 0
    assert 'configured to use ASCII as encoding' in err, "should whine"


@pytest.mark.xfail(
    os.name == 'nt' and sys.version_info < (3, 8),
    reason="Windows does not like this; not sure how to fix",
)
def test_dev_null(resources):
    if 'COV_CORE_DATAFILE' in os.environ:
        pytest.skip(msg="Coverage uses stdout")

    p, out, _err = run_ocrmypdf(
        resources / 'trivial.pdf',
        os.devnull,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == 0, "could not send output to /dev/null"
    assert len(out) == 0, "wrote to stdout"
