#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from __future__ import print_function
from subprocess import Popen, PIPE, check_output, check_call
import os
import shutil
from contextlib import suppress
import sys
import pytest
from ocrmypdf.pageinfo import pdf_get_all_pageinfo
import PyPDF2 as pypdf
from ocrmypdf import ExitCode


if sys.version_info.major < 3:
    print("Requires Python 3.4+")
    sys.exit(1)

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
SPOOF_PATH = os.path.join(TESTS_ROOT, 'spoof')
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
OCRMYPDF = os.path.join(PROJECT_ROOT, 'OCRmyPDF.sh')
TEST_RESOURCES = os.path.join(PROJECT_ROOT, 'tests', 'resources')
TEST_OUTPUT = os.environ.get(
    'OCRMYPDF_TEST_OUTPUT',
    default=os.path.join(PROJECT_ROOT, 'tests', 'output'))
TEST_BINARY_PATH = os.path.join(TEST_OUTPUT, 'fakebin')


def setup_module():
    with suppress(FileNotFoundError):
        shutil.rmtree(TEST_OUTPUT)
    with suppress(FileExistsError):
        os.mkdir(TEST_OUTPUT)


def run_ocrmypdf_sh(input_file, output_file, *args, env=None):
    sh_args = ['sh', OCRMYPDF] + list(args) + [input_file, output_file]
    sh = Popen(
        sh_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = sh.communicate()
    return sh, out, err


def _make_input(input_basename):
    return os.path.join(TEST_RESOURCES, input_basename)


def _make_output(output_basename):
    return os.path.join(TEST_OUTPUT, output_basename)


def check_ocrmypdf(input_basename, output_basename, *args, env=None):
    input_file = _make_input(input_basename)
    output_file = _make_output(output_basename)

    sh, _, err = run_ocrmypdf_sh(input_file, output_file, *args, env=env)
    assert sh.returncode == 0, err
    assert os.path.exists(output_file), "Output file not created"
    assert os.stat(output_file).st_size > 100, "PDF too small or empty"
    return output_file


def run_ocrmypdf_env(input_basename, output_basename, *args, env=None):
    input_file = _make_input(input_basename)
    output_file = _make_output(output_basename)

    if env is None:
        env = os.environ

    p_args = ['ocrmypdf'] + list(args) + [input_file, output_file]
    p = Popen(
        p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = p.communicate()
    return p, out, err


def test_quick():
    check_ocrmypdf('c02-22.pdf', 'test_quick.pdf')


@pytest.fixture
def spoof_tesseract_hocr_empty():
    env = os.environ.copy()
    program = os.path.join(SPOOF_PATH, 'tesseract_hocr_empty.py')
    check_call(['chmod', "+x", program])
    env['OCRMYPDF_TESSERACT'] = program
    return env


def test_deskew(spoof_tesseract_hocr_empty):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(
        'skew.pdf', 'test_deskew.pdf', '-d', env=spoof_tesseract_hocr_empty)

    # Now render as an image again and use Leptonica to find the skew angle
    # to confirm that it was deskewed
    from ocrmypdf.ghostscript import rasterize_pdf
    import logging
    log = logging.getLogger()

    deskewed_png = _make_output('deskewed.png')

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


def check_exotic_image(pdf, renderer):
    check_ocrmypdf(
        pdf,
        'test_{0}_{1}.pdf'.format(pdf, renderer),
        '-dc',
        '--pdf-renderer', renderer)


def test_exotic_image():
    yield check_exotic_image, 'palette.pdf', 'hocr'
    yield check_exotic_image, 'palette.pdf', 'tesseract'
    yield check_exotic_image, 'cmyk.pdf', 'hocr'
    yield check_exotic_image, 'cmyk.pdf', 'tesseract'


def test_preserve_metadata():
    pdf_before = pypdf.PdfFileReader(_make_input('graph.pdf'))

    output = check_ocrmypdf('graph.pdf', 'test_metadata_preserve.pdf')

    pdf_after = pypdf.PdfFileReader(output)

    for key in ('/Title', '/Author'):
        assert pdf_before.documentInfo[key] == pdf_after.documentInfo[key]


def test_override_metadata():
    input_file = _make_input('c02-22.pdf')
    output_file = _make_output('test_override_metadata.pdf')

    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'
    high_unicode = 'U+1030C is: 𐌌'

    p, out, err = run_ocrmypdf_env(
        input_file, output_file,
        '--title', german,
        '--author', chinese,
        '--subject', high_unicode)

    assert p.returncode == ExitCode.ok

    pdf = output_file

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


def test_argsfile():
    with open(_make_output('test_argsfile.txt'), 'w') as argsfile:
        print('--title', 'ArgsFile Test', '--author', 'Test Cases',
              sep='\n', end='\n', file=argsfile)
    check_ocrmypdf('graph.pdf', 'test_argsfile.pdf',
                   '@' + _make_output('test_argsfile.txt'))


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


def test_tesseract_missing_tessdata():
    env = os.environ.copy()
    env['TESSDATA_PREFIX'] = '/tmp'

    p, _, err = run_ocrmypdf_env(
        'graph_ocred.pdf', 'not_a_pdfa.pdf', '-v', '1', '--skip-text', env=env)
    assert p.returncode == ExitCode.missing_dependency, err


def test_invalid_input_pdf():
    p, out, err = run_ocrmypdf_env(
        'invalid.pdf', 'wont_be_created.pdf')
    assert p.returncode == ExitCode.input_file, err


def test_blank_input_pdf():
    p, out, err = run_ocrmypdf_env(
        'blank.pdf', 'still_blank.pdf')
    assert p.returncode == ExitCode.ok


def test_french():
    p, out, err = run_ocrmypdf_env(
        'francais.pdf', 'francais.pdf', '-l', 'fra')
    assert p.returncode == ExitCode.ok, \
        "This test may fail if Tesseract language packs are missing"


def test_klingon():
    p, out, err = run_ocrmypdf_env(
        'francais.pdf', 'francais.pdf', '-l', 'klz')
    assert p.returncode == ExitCode.bad_args


def test_missing_docinfo():
    p, out, err = run_ocrmypdf_env(
        'missing_docinfo.pdf', 'missing_docinfo.pdf', '-l', 'eng', '-c')
    assert p.returncode == ExitCode.ok, err


def test_uppercase_extension():
    shutil.copy(_make_input("skew.pdf"), _make_input("UPPERCASE.PDF"))
    try:
        check_ocrmypdf("UPPERCASE.PDF", "UPPERCASE_OUT.PDF")
    finally:
        os.unlink(_make_input("UPPERCASE.PDF"))


def test_input_file_not_found():
    input_file = "does not exist.pdf"
    sh, out, err = run_ocrmypdf_sh(
        _make_input(input_file),
        _make_output("will not happen.pdf"))
    assert sh.returncode == ExitCode.input_file
    assert (input_file in out or input_file in err)


def test_input_file_not_a_pdf():
    input_file = __file__  # Try to OCR this file
    sh, out, err = run_ocrmypdf_sh(
        _make_input(input_file),
        _make_output("will not happen.pdf"))
    assert sh.returncode == ExitCode.input_file
    assert (input_file in out or input_file in err)


def test_qpdf_repair_fails():
    env = os.environ.copy()
    env['OCRMYPDF_QPDF'] = os.path.abspath('./spoof/qpdf_dummy_return2.py')
    p, out, err = run_ocrmypdf_env(
        '-v', '1',
        'c02-22.pdf', 'wont_be_created.pdf', env=env)
    print(out)
    print(err)
    assert p.returncode == ExitCode.input_file


def test_encrypted():
    p, out, err = run_ocrmypdf_env('skew-encrypted.pdf', 'wont_be_created.pdf')
    assert p.returncode == ExitCode.input_file
    assert out.find('password')
