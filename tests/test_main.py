#!/usr/bin/env python3

from subprocess import Popen, PIPE
import os

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
OCRMYPDF = os.path.join(PROJECT_ROOT, 'OCRmyPDF.sh')
TEST_RESOURCES = os.path.join(PROJECT_ROOT, 'tests', 'resources')


def run_ocrmypdf(input_file, output_file, *args):
    input_path = os.path.join(TEST_RESOURCES, input_file)
    output_path = os.path.join(TEST_RESOURCES, output_file)

    sh_args = ['sh', './OCRmyPDF.sh'] + list(args) + [input_path, output_path]
    sh = Popen(
        sh_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True)
    out, err = sh.communicate()
    return sh, out, err


def check_ocrmypdf(input_file, output_file, *args):
    sh, _, err = run_ocrmypdf(input_file, output_file, *args)
    assert sh.returncode == 0, err


def test_quick():
    check_ocrmypdf('graph.pdf', 'graph_out.pdf')
