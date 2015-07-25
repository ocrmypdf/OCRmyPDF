#!/usr/bin/env python3

from __future__ import print_function
from subprocess import Popen, PIPE
import os
import shutil
from contextlib import suppress
import sys

if sys.version_info.major < 3:
    print("Requires Python 3.4+")
    sys.exit(1)

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
OCRMYPDF = os.path.join(PROJECT_ROOT, 'OCRmyPDF.sh')
TEST_RESOURCES = os.path.join(PROJECT_ROOT, 'tests', 'resources')
TEST_OUTPUT = os.path.join(PROJECT_ROOT, 'tests', 'output')


def setup_module():
    with suppress(FileNotFoundError):
        shutil.rmtree(TEST_OUTPUT)
    with suppress(FileExistsError):
        os.mkdir(TEST_OUTPUT)


def run_ocrmypdf(input_file, output_file, *args):
    sh_args = ['sh', OCRMYPDF] + list(args) + [input_file, output_file]
    sh = Popen(
        sh_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True)
    out, err = sh.communicate()
    return sh, out, err


def check_ocrmypdf(input_basename, output_basename, *args):
    input_file = os.path.join(TEST_RESOURCES, input_basename)
    output_file = os.path.join(TEST_OUTPUT, output_basename or input_basename)

    sh, _, err = run_ocrmypdf(input_file, output_file, *args)
    assert sh.returncode == 0, err
    assert os.path.exists(output_file), "Output file not created"
    assert os.stat(output_file).st_size > 100, "PDF too small, empty or near empty"


def test_quick():
    check_ocrmypdf('c02-22.pdf', 'test_quick.pdf')


def test_deskew():
    check_ocrmypdf('skew.pdf', 'test_deskew.pdf', '-d')


def test_clean():
    check_ocrmypdf('skew.pdf', 'test_clean.pdf', '-c')
