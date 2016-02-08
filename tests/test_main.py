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
from ocrmypdf import leptonica


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
    default=os.path.join(PROJECT_ROOT, 'tests', 'output', 'main'))


def setup_module():
    with suppress(FileNotFoundError):
        shutil.rmtree(TEST_OUTPUT)
    with suppress(FileExistsError):
        os.makedirs(TEST_OUTPUT)


def run_ocrmypdf_sh(input_file, output_file, *args, env=None):
    sh_args = ['sh', OCRMYPDF] + list(args) + [input_file, output_file]
    sh = Popen(
        sh_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = sh.communicate()
    return sh, out, err


def _infile(input_basename):
    return os.path.join(TEST_RESOURCES, input_basename)


def _outfile(output_basename):
    return os.path.join(TEST_OUTPUT, output_basename)


def check_ocrmypdf(input_basename, output_basename, *args, env=None):
    input_file = _infile(input_basename)
    output_file = _outfile(output_basename)

    sh, out, err = run_ocrmypdf_sh(input_file, output_file, *args, env=env)
    assert sh.returncode == 0, dict(stdout=out, stderr=err)
    assert os.path.exists(output_file), "Output file not created"
    assert os.stat(output_file).st_size > 100, "PDF too small or empty"
    return output_file


def run_ocrmypdf_env(input_basename, output_basename, *args, env=None):
    input_file = _infile(input_basename)
    output_file = _outfile(output_basename)

    if env is None:
        env = os.environ

    p_args = ['ocrmypdf'] + list(args) + [input_file, output_file]
    p = Popen(
        p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = p.communicate()
    return p, out, err


@pytest.fixture
def spoof_tesseract_noop():
    env = os.environ.copy()
    program = os.path.join(SPOOF_PATH, 'tesseract_noop.py')
    check_call(['chmod', "+x", program])
    env['OCRMYPDF_TESSERACT'] = program
    return env


@pytest.fixture
def spoof_tesseract_cache():
    env = os.environ.copy()
    program = os.path.join(SPOOF_PATH, "tesseract_cache.py")
    check_call(['chmod', '+x', program])
    env['OCRMYPDF_TESSERACT'] = program
    return env


def test_quick(spoof_tesseract_noop):
    check_ocrmypdf('c02-22.pdf', 'test_quick.pdf', env=spoof_tesseract_noop)


def test_deskew(spoof_tesseract_noop):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(
        'skew.pdf', 'test_deskew.pdf', '-d', env=spoof_tesseract_noop)

    # Now render as an image again and use Leptonica to find the skew angle
    # to confirm that it was deskewed
    from ocrmypdf.ghostscript import rasterize_pdf
    import logging
    log = logging.getLogger()

    deskewed_png = _outfile('deskewed.png')

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


def test_clean(spoof_tesseract_noop):
    check_ocrmypdf('skew.pdf', 'test_clean.pdf', '-c', env=spoof_tesseract_noop)


@pytest.mark.parametrize("pdf,renderer", [
    ('palette.pdf', 'hocr'),
    ('palette.pdf', 'tesseract'),
    ('cmyk.pdf', 'hocr'),
    ('cmyk.pdf', 'tesseract'),
    ('ccitt.pdf', 'hocr'),
    ('ccitt.pdf', 'tesseract'),
    ('jbig2.pdf', 'hocr'),
    ('jbig2.pdf', 'tesseract')
])
def test_exotic_image(spoof_tesseract_cache, pdf, renderer):
    check_ocrmypdf(
        pdf,
        'test_{0}_{1}.pdf'.format(pdf, renderer),
        '-dc',
        '-v', '1',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)


def test_preserve_metadata(spoof_tesseract_noop):
    pdf_before = pypdf.PdfFileReader(_infile('graph.pdf'))

    output = check_ocrmypdf('graph.pdf', 'test_metadata_preserve.pdf',
                            env=spoof_tesseract_noop)

    pdf_after = pypdf.PdfFileReader(output)

    for key in ('/Title', '/Author'):
        assert pdf_before.documentInfo[key] == pdf_after.documentInfo[key]


def test_override_metadata(spoof_tesseract_noop):
    input_file = _infile('c02-22.pdf')
    output_file = _outfile('test_override_metadata.pdf')

    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'
    high_unicode = 'U+1030C is: 𐌌'

    p, out, err = run_ocrmypdf_env(
        input_file, output_file,
        '--title', german,
        '--author', chinese,
        '--subject', high_unicode,
        env=spoof_tesseract_noop)

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


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_oversample(spoof_tesseract_cache, renderer):
    oversampled_pdf = check_ocrmypdf(
        'skew.pdf', 'test_oversample_%s.pdf' % renderer, '--oversample', '300',
        '-f',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    pdfinfo = pdf_get_all_pageinfo(oversampled_pdf)

    print(pdfinfo[0]['xres'])
    assert abs(pdfinfo[0]['xres'] - 300) < 1


def test_repeat_ocr():
    sh, _, _ = run_ocrmypdf_sh('graph_ocred.pdf', 'wontwork.pdf')
    assert sh.returncode != 0


def test_force_ocr(spoof_tesseract_cache):
    out = check_ocrmypdf('graph_ocred.pdf', 'test_force.pdf', '-f',
                         env=spoof_tesseract_cache)
    pdfinfo = pdf_get_all_pageinfo(out)
    assert pdfinfo[0]['has_text']


def test_skip_ocr(spoof_tesseract_cache):
    check_ocrmypdf('graph_ocred.pdf', 'test_skip.pdf', '-s',
                   env=spoof_tesseract_cache)


def test_argsfile(spoof_tesseract_noop):
    with open(_outfile('test_argsfile.txt'), 'w') as argsfile:
        print('--title', 'ArgsFile Test', '--author', 'Test Cases',
              sep='\n', end='\n', file=argsfile)
    check_ocrmypdf('graph.pdf', 'test_argsfile.pdf',
                   '@' + _outfile('test_argsfile.txt'),
                   env=spoof_tesseract_noop)


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_autorotate(spoof_tesseract_cache, renderer):
    import ocrmypdf.ghostscript as ghostscript
    import logging

    gslog = logging.getLogger()

    out = check_ocrmypdf('cardinal.pdf', 'test_autorotate_%s.pdf' % renderer,
                         '-r', '-v', '1', env=spoof_tesseract_cache)
    for n in range(1, 4+1):
        ghostscript.rasterize_pdf(
            out, _outfile('cardinal-%i.png' % n), xres=100, yres=100,
            raster_device='pngmono', log=gslog, pageno=n)

    ghostscript.rasterize_pdf(
            _infile('cardinal.pdf'), _outfile('reference.png'),
            xres=100, yres=100, raster_device='pngmono', log=gslog, pageno=1)

    pix_ref = leptonica.Pix.read(_outfile('reference.png'))
    pix_ref_180 = pix_ref.rotate180()
    correlation = leptonica.correlation_binary(pix_ref.cpix, pix_ref_180.cpix)
    assert correlation < 0.10

    for n in range(1, 4+1):
        pix_other = leptonica.Pix.read(_outfile('cardinal-%i.png' % n))
        correlation = leptonica.Pix.correlation_binary(pix_ref, pix_other)
        assert correlation > 0.80

@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_ocr_timeout(renderer):
    out = check_ocrmypdf('skew.pdf', 'test_timeout_%s.pdf' % renderer,
                         '--tesseract-timeout', '1.0')
    pdfinfo = pdf_get_all_pageinfo(out)
    assert pdfinfo[0]['has_text'] == False


def test_skip_big(spoof_tesseract_cache):
    out = check_ocrmypdf('enormous.pdf', 'test_enormous.pdf',
                         '--skip-big', '10', env=spoof_tesseract_cache)
    pdfinfo = pdf_get_all_pageinfo(out)
    assert pdfinfo[0]['has_text'] == False


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_maximum_options(spoof_tesseract_cache, renderer):
    check_ocrmypdf(
        'multipage.pdf', 'test_multipage%s.pdf' % renderer,
        '-d', '-c', '-i', '-g', '-f', '-k', '--oversample', '300',
        '--skip-big', '10', '--title', 'Too Many Weird Files',
        '--author', 'py.test', '--pdf-renderer', renderer,
        env=spoof_tesseract_cache)


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


def test_french(spoof_tesseract_cache):
    p, out, err = run_ocrmypdf_env(
        'francais.pdf', 'francais.pdf', '-l', 'fra', env=spoof_tesseract_cache)
    assert p.returncode == ExitCode.ok, \
        "This test may fail if Tesseract language packs are missing"


def test_klingon():
    p, out, err = run_ocrmypdf_env(
        'francais.pdf', 'francais.pdf', '-l', 'klz')
    assert p.returncode == ExitCode.bad_args


def test_missing_docinfo(spoof_tesseract_noop):
    p, out, err = run_ocrmypdf_env(
        'missing_docinfo.pdf', 'missing_docinfo.pdf', '-l', 'eng', '-c',
        env=spoof_tesseract_noop)
    assert p.returncode == ExitCode.ok, err


def test_uppercase_extension(spoof_tesseract_noop):
    shutil.copy(_infile("skew.pdf"), _infile("UPPERCASE.PDF"))
    try:
        check_ocrmypdf("UPPERCASE.PDF", "UPPERCASE_OUT.PDF",
                       env=spoof_tesseract_noop)
    finally:
        os.unlink(_infile("UPPERCASE.PDF"))


def test_input_file_not_found():
    input_file = "does not exist.pdf"
    sh, out, err = run_ocrmypdf_sh(
        _infile(input_file),
        _outfile("will not happen.pdf"))
    assert sh.returncode == ExitCode.input_file
    assert (input_file in out or input_file in err)


def test_input_file_not_a_pdf():
    input_file = __file__  # Try to OCR this file
    sh, out, err = run_ocrmypdf_sh(
        _infile(input_file),
        _outfile("will not happen.pdf"))
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


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_pagesegmode(renderer, spoof_tesseract_cache):
    check_ocrmypdf(
        'skew.pdf', 'test_psm_%s.pdf' % renderer,
        '--tesseract-pagesegmode', '7',
        '-v', '1',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)



