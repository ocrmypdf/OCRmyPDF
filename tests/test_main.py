#!/usr/bin/env python3

from __future__ import print_function
from subprocess import Popen, PIPE, check_output
import os
import shutil
from contextlib import suppress
import sys
from unittest.mock import patch

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


def run_ocrmypdf_sh(input_file, output_file, *args):
    sh_args = ['sh', OCRMYPDF] + list(args) + [input_file, output_file]
    sh = Popen(
        sh_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True)
    out, err = sh.communicate()
    return sh, out, err


def check_ocrmypdf_sh(input_basename, output_basename, *args):
    input_file = os.path.join(TEST_RESOURCES, input_basename)
    output_file = os.path.join(TEST_OUTPUT, output_basename or input_basename)

    sh, _, err = run_ocrmypdf_sh(input_file, output_file, *args)
    assert sh.returncode == 0, err
    assert os.path.exists(output_file), "Output file not created"
    assert os.stat(output_file).st_size > 100, "PDF too small or empty"


def run_ocrmypdf(input_basename, output_basename, *args):
    input_file = os.path.join(TEST_RESOURCES, input_basename)
    output_file = os.path.join(TEST_OUTPUT, output_basename or input_basename)

    sys_argv = list(args) + [input_file, output_file]
    with patch.object(sys, 'argv', sys_argv):
        try:
            import ocrmypdf.main
            ocrmypdf.main.run_pipeline()
        except SystemExit as e:
            assert e.code == 0
    return output_file


def test_quick():
    check_ocrmypdf_sh('c02-22.pdf', 'test_quick.pdf')


def test_deskew():
    # Run with deskew
    deskewed_pdf = run_ocrmypdf('skew.pdf', 'test_deskew.pdf', '-d')

    # Now render as an image again and use Leptonica to find the skew angle
    # to confirm that it was deskewed
    from ocrmypdf.ghostscript import rasterize_pdf
    import logging
    log = logging.getLogger()

    deskewed_png = os.path.join(TEST_OUTPUT, 'deskewed.png')

    rasterize_pdf(
        deskewed_pdf,
        deskewed_png,
        xres=150,
        yres=150,
        raster_device='pngmono',
        log=log)

    from ocrmypdf.leptonica import pixRead, pixDestroy, pixFindSkew
    pix = pixRead(deskewed_png)
    skew_angle, skew_confidence = pixFindSkew(pix)
    pix = pixDestroy(pix)

    print(skew_angle)
    assert -0.5 < skew_angle < 0.5, "Deskewing failed"


def test_clean():
    check_ocrmypdf_sh('skew.pdf', 'test_clean.pdf', '-c')


def test_metadata():
    pdf = run_ocrmypdf(
        'c02-22.pdf', 'test_metadata.pdf',
        '--title', 'Du siehst den Wald vor lauter Bäumen nicht.',
        '--author', '孔子',
        '--subject', 'U+1030C is: 𐌌')

    out_pdfinfo = check_output(['pdfinfo', pdf], universal_newlines=True)
    lines_pdfinfo = out_pdfinfo.splitlines()
    pdfinfo = {}
    for line in lines_pdfinfo:
        k, v = line.strip().split(':', maxsplit=1)
        pdfinfo[k.strip()] = v.strip()

    assert pdfinfo['Title'] == 'Du siehst den Wald vor lauter Bäumen nicht.'
    assert pdfinfo['Author'] == '孔子'
    assert pdfinfo['Subject'] == 'U+1030C is: 𐌌'
    assert pdfinfo.get('Keywords', '') == ''
