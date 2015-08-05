#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from __future__ import print_function
from subprocess import Popen, PIPE, check_output
import os
import shutil
from contextlib import suppress
import sys
from unittest.mock import patch, create_autospec
import pytest
from ocrmypdf.pageinfo import pdf_get_all_pageinfo


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


def check_ocrmypdf(input_basename, output_basename, *args):
    input_file = os.path.join(TEST_RESOURCES, input_basename)
    output_file = os.path.join(TEST_OUTPUT, output_basename)

    sh, _, err = run_ocrmypdf_sh(input_file, output_file, *args)
    assert sh.returncode == 0, err
    assert os.path.exists(output_file), "Output file not created"
    assert os.stat(output_file).st_size > 100, "PDF too small or empty"
    return output_file


def test_quick():
    check_ocrmypdf('c02-22.pdf', 'test_quick.pdf')


def test_deskew():
    # Run with deskew
    deskewed_pdf = check_ocrmypdf('skew.pdf', 'test_deskew.pdf', '-d')

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
    check_ocrmypdf('skew.pdf', 'test_clean.pdf', '-c')


def test_override_metadata():
    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'
    high_unicode = 'U+1030C is: 𐌌'

    pdf = check_ocrmypdf(
        'c02-22.pdf', 'test_metadata.pdf',
        '--title', german,
        '--author', chinese,
        '--subject', high_unicode)

    out_pdfinfo = check_output(['pdfinfo', pdf], universal_newlines=True)
    lines_pdfinfo = out_pdfinfo.splitlines()
    pdfinfo = {}
    for line in lines_pdfinfo:
        k, v = line.strip().split(':', maxsplit=1)
        pdfinfo[k.strip()] = v.strip()

    assert pdfinfo['Title'] == german
    assert pdfinfo['Author'] == chinese
    assert pdfinfo['Subject'] == high_unicode
    assert pdfinfo.get('Keywords', '') == ''


def check_oversample(renderer):
    oversampled_pdf = check_ocrmypdf(
        'skew.pdf', 'test_oversample_%s.pdf' % renderer, '--oversample', '300',
        '--pdf-renderer', renderer)

    pdfinfo = pdf_get_all_pageinfo(oversampled_pdf)

    print(pdfinfo[0]['xres'])
    assert abs(pdfinfo[0]['xres'] - 300) < 1


def test_oversample():
    yield check_oversample, 'hocr'
    yield check_oversample, 'tesseract'


def test_repeat_ocr():
    sh, _, _ = run_ocrmypdf_sh('graph_ocred.pdf', 'wontwork.pdf')
    assert sh.returncode != 0


def test_force_ocr():
    out = check_ocrmypdf('graph_ocred.pdf', 'test_force.pdf', '-f')
    pdfinfo = pdf_get_all_pageinfo(out)
    assert pdfinfo[0]['has_text']


def test_skip_ocr():
    check_ocrmypdf('graph_ocred.pdf', 'test_skip.pdf', '-s')


def check_ocr_timeout(renderer):
    out = check_ocrmypdf('skew.pdf', 'test_timeout_%s.pdf' % renderer,
                         '--tesseract-timeout', '1.0')
    pdfinfo = pdf_get_all_pageinfo(out)
    assert pdfinfo[0]['has_text'] == False


def test_ocr_timeout():
    yield check_ocr_timeout, 'hocr'
    yield check_ocr_timeout, 'tesseract'


def test_skip_big():
    out = check_ocrmypdf('enormous.pdf', 'test_enormous.pdf',
                         '--skip-big', '10')
    pdfinfo = pdf_get_all_pageinfo(out)
    assert pdfinfo[0]['has_text'] == False


def check_maximum_options(renderer):
    check_ocrmypdf(
        'multipage.pdf', 'test_multipage%s.pdf' % renderer,
        '-d', '-c', '-i', '-g', '-f', '-k', '--oversample', '300',
        '--skip-big', '10', '--title', 'Too Many Weird Files',
        '--author', 'py.test', '--pdf-renderer', renderer)


def test_maximum_options():
    yield check_maximum_options, 'hocr'
    yield check_maximum_options, 'tesseract'
