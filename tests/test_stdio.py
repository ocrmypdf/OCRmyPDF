# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
import sys
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen, run

import pytest

from ocrmypdf.exceptions import ExitCode
from ocrmypdf.helpers import check_pdf

from .conftest import run_ocrmypdf


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
        run(p_args, stdout=PIPE, stderr=PIPE, stdin=input_stream, check=True)


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
        run(p_args, stdout=output_stream, stderr=PIPE, stdin=DEVNULL, check=True)

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
