#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE, check_output, check_call, DEVNULL
import os
import shutil
from contextlib import suppress
import sys
import pytest
from ocrmypdf.pageinfo import pdf_get_all_pageinfo
import PyPDF2 as pypdf
from ocrmypdf.exceptions import ExitCode
from ocrmypdf import leptonica
from ocrmypdf.pdfa import file_claims_pdfa
from ocrmypdf.exec import tesseract
from common import is_linux, running_in_docker


TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
SPOOF_PATH = os.path.join(TESTS_ROOT, 'spoof')
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
TEST_RESOURCES = os.path.join(PROJECT_ROOT, 'tests', 'resources')
OCRMYPDF = [sys.executable, '-m', 'ocrmypdf']


# Skip all tests in this file if not tesseract 4
pytestmark = pytest.mark.skipif(not tesseract.v4(),
                                reason="tesseract 4.0 required")


def _infile(input_basename):
    return os.path.join(TEST_RESOURCES, input_basename)


def check_ocrmypdf(input_basename, output, *args, env=None):
    "Run ocrmypdf and confirmed that a valid file was created"
    input_file = _infile(input_basename)

    p, out, err = run_ocrmypdf(input_basename, output, *args, env=env)
    print(err)  # ensure py.test collects the output, use -s to view
    assert p.returncode == 0
    assert os.path.exists(output), "Output file not created"
    assert os.stat(output).st_size > 100, "PDF too small or empty"
    assert out == "", \
        "The following was written to stdout and should not have been: \n" + \
        "<stdout>\n" + out + "\n</stdout>"
    return output


def run_ocrmypdf(input_basename, output, *args, env=None):
    "Run ocrmypdf and let caller deal with results"
    input_file = _infile(input_basename)

    if env is None:
        env = os.environ

    p_args = OCRMYPDF + list(args) + [input_file, output]
    p = Popen(
        p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = p.communicate()
    print(err)

    return p, out, err


@pytest.mark.skipif(not tesseract.has_textonly_pdf(),
                    reason="requires textonly_pdf parameter")
def test_textonly_pdf(self, tmpdir):
    output = str(tmpdir.join("linn_textonly.pdf"))
    check_ocrmypdf('linn.pdf', output, '--pdf-renderer', 'tess4')



