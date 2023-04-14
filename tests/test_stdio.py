# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os
from subprocess import DEVNULL, PIPE, run

import pytest

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
        run(p_args, capture_output=True, stdin=input_stream, check=True)


def test_stdout(ocrmypdf_exec, resources, outpdf):
    if 'COV_CORE_DATAFILE' in os.environ:
        pytest.skip("Coverage uses stdout")

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


def test_dev_null(resources):
    if 'COV_CORE_DATAFILE' in os.environ:
        pytest.skip("Coverage uses stdout")

    p = run_ocrmypdf(
        resources / 'trivial.pdf',
        os.devnull,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == 0, "could not send output to /dev/null"
    assert len(p.stdout) == 0, "wrote to stdout"
