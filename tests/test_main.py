#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from __future__ import print_function
from subprocess import Popen, PIPE, check_output, check_call, DEVNULL
import os
import shutil
from contextlib import suppress
import sys
import pytest
from ocrmypdf.pageinfo import pdf_get_all_pageinfo
import PyPDF2 as pypdf
from ocrmypdf import ExitCode
from ocrmypdf import leptonica
from ocrmypdf.pdfa import file_claims_pdfa
import platform


if sys.version_info.major < 3:
    print("Requires Python 3.4+")
    sys.exit(1)

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
SPOOF_PATH = os.path.join(TESTS_ROOT, 'spoof')
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
TEST_RESOURCES = os.path.join(PROJECT_ROOT, 'tests', 'resources')
TEST_OUTPUT = os.environ.get(
    'OCRMYPDF_TEST_OUTPUT',
    default=os.path.join(PROJECT_ROOT, 'tests', 'output', 'main'))
OCRMYPDF = [sys.executable, '-m', 'ocrmypdf']


def running_in_docker():
    # Docker creates a file named /.dockerinit
    return os.path.exists('/.dockerinit')


def is_linux():
    return platform.system() == 'Linux'


def setup_module():
    with suppress(FileNotFoundError):
        shutil.rmtree(TEST_OUTPUT)
    with suppress(FileExistsError):
        os.makedirs(TEST_OUTPUT)


def _infile(input_basename):
    return os.path.join(TEST_RESOURCES, input_basename)


def _outfile(output_basename):
    return os.path.join(TEST_OUTPUT, os.path.basename(output_basename))


def check_ocrmypdf(input_basename, output_basename, *args, env=None):
    "Run ocrmypdf and confirmed that a valid file was created"
    input_file = _infile(input_basename)
    output_file = _outfile(output_basename)

    p, out, err = run_ocrmypdf(input_basename, output_basename, *args, env=env)
    print(err)  # ensure py.test collects the output, use -s to view
    if p.returncode != 0:
        print('stdout\n======')
        print(out)
        print('stderr\n======')
        print(err)
    assert p.returncode == 0
    assert os.path.exists(output_file), "Output file not created"
    assert os.stat(output_file).st_size > 100, "PDF too small or empty"
    assert out == "", \
        "The following was written to stdout and should not have been: \n" + \
        "<stdout>\n" + out + "\n</stdout>"
    return output_file


def run_ocrmypdf(input_basename, output_basename, *args, env=None):
    "Run ocrmypdf and let caller deal with results"
    input_file = _infile(input_basename)
    output_file = _outfile(output_basename)

    if env is None:
        env = os.environ

    p_args = OCRMYPDF + list(args) + [input_file, output_file]
    p = Popen(
        p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = p.communicate()
    return p, out, err


def spoof(**kwargs):
    """Modify environment variables to override subprocess executables

    spoof(program1='replacement', ...)

    Before running any executable, ocrmypdf checks the environment variable
    OCRMYPDF_PROGRAMNAME to override default program name/location, e.g.
    OCRMYPDF_GS redirects from the system path Ghostscript ("gs") to elsewhere.

    """
    env = os.environ.copy()

    for replace_program, with_spoof in kwargs.items():
        spoofer = os.path.join(SPOOF_PATH, with_spoof)
        if not os.access(spoofer, os.X_OK):
            os.chmod(spoofer, 0o755)
        env['OCRMYPDF_' + replace_program.upper()] = spoofer
    return env


@pytest.fixture
def spoof_tesseract_noop():
    return spoof(tesseract='tesseract_noop.py')


@pytest.fixture
def spoof_tesseract_cache():
    if running_in_docker():
        return os.environ.copy()
    return spoof(tesseract="tesseract_cache.py")


@pytest.fixture
def spoof_tesseract_crash():
    return spoof(tesseract='tesseract_crash.py')


@pytest.fixture
def spoof_tesseract_big_image_error():
    return spoof(tesseract='tesseract_big_image_error.py')


@pytest.fixture
def spoof_no_tess_no_pdfa():
    return spoof(tesseract='tesseract_noop.py', gs='gs_pdfa_failure.py')


@pytest.fixture
def spoof_no_tess_pdfa_warning():
    return spoof(tesseract='tesseract_noop.py', gs='gs_feature_elision.py')


def test_quick(spoof_tesseract_cache):
    check_ocrmypdf('ccitt.pdf', 'test_quick.pdf', env=spoof_tesseract_cache)


def test_deskew(spoof_tesseract_noop):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(
        'skew.pdf', 'test_deskew.pdf', '-d', '-v', '1', env=spoof_tesseract_noop)

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

    from ocrmypdf.leptonica import Pix
    pix = Pix.read(deskewed_png)
    skew_angle, skew_confidence = pix.find_skew()

    print(skew_angle)
    assert -0.5 < skew_angle < 0.5, "Deskewing failed"


def test_clean(spoof_tesseract_noop):
    check_ocrmypdf('skew.pdf', 'test_clean.pdf', '-c',
                   env=spoof_tesseract_noop)


def test_remove_background(spoof_tesseract_noop):
    from PIL import Image

    # Ensure the input image does not contain pure white/black
    im = Image.open(_infile('congress.jpg'))
    assert im.getextrema() != ((0, 255), (0, 255), (0, 255))

    output_pdf = check_ocrmypdf(
        'congress.jpg', 'test_remove_bg.pdf', '--remove-background',
        '--image-dpi', '150',
        env=spoof_tesseract_noop)

    from ocrmypdf.ghostscript import rasterize_pdf
    import logging
    log = logging.getLogger()

    output_png = _outfile('remove_bg.png')

    rasterize_pdf(
        output_pdf,
        output_png,
        xres=100,
        yres=100,
        raster_device='png16m',
        log=log)


    # The output image should contain pure white and black
    im = Image.open(output_png)
    assert im.getextrema() == ((0, 255), (0, 255), (0, 255))


# This will run 5 * 2 * 2 = 20 test cases
@pytest.mark.parametrize(
    "pdf",
    ['palette.pdf', 'cmyk.pdf', 'ccitt.pdf', 'jbig2.pdf', 'lichtenstein.pdf'])
@pytest.mark.parametrize("renderer", ['hocr', 'tesseract'])
@pytest.mark.parametrize("output_type", ['pdf', 'pdfa'])
def test_exotic_image(spoof_tesseract_cache, pdf, renderer, output_type):
    check_ocrmypdf(
        pdf,
        'test_{0}_{1}.pdf'.format(pdf, renderer),
        '-dc',
        '-v', '1',
        '--output-type', output_type,
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)


@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_preserve_metadata(spoof_tesseract_noop, output_type):
    pdf_before = pypdf.PdfFileReader(_infile('graph.pdf'))

    output = check_ocrmypdf('graph.pdf', 'test_metadata_preserve.pdf',
                            '--output-type', output_type,
                            env=spoof_tesseract_noop)

    pdf_after = pypdf.PdfFileReader(output)

    for key in ('/Title', '/Author'):
        assert pdf_before.documentInfo[key] == pdf_after.documentInfo[key]

    pdfa_info = file_claims_pdfa(output)
    assert pdfa_info['output'] == output_type


@pytest.mark.skipif(
    is_linux() and not running_in_docker(),
    reason="likely to fail if Linux locale is not configured correctly")
@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_override_metadata(spoof_tesseract_noop, output_type):
    input_file = _infile('c02-22.pdf')
    output_file = _outfile('test_override_metadata.pdf')

    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'
    high_unicode = 'U+1030C is: 𐌌'

    p, out, err = run_ocrmypdf(
        input_file, output_file,
        '--title', german,
        '--author', chinese,
        '--subject', high_unicode,
        '--output-type', output_type,
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

    pdfa_info = file_claims_pdfa(output_file)
    assert pdfa_info['output'] == output_type


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_oversample(spoof_tesseract_cache, renderer):
    oversampled_pdf = check_ocrmypdf(
        'skew.pdf', 'test_oversample_%s.pdf' % renderer, '--oversample', '350',
        '-f',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    pdfinfo = pdf_get_all_pageinfo(oversampled_pdf)

    print(pdfinfo[0]['xres'])
    assert abs(pdfinfo[0]['xres'] - 350) < 1


def test_repeat_ocr():
    p, _, _ = run_ocrmypdf('graph_ocred.pdf', 'wontwork.pdf')
    assert p.returncode != 0


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


def check_monochrome_correlation(
        reference_pdf, reference_pageno, test_pdf, test_pageno):

    import ocrmypdf.ghostscript as ghostscript
    import logging

    gslog = logging.getLogger()

    reference_png = _outfile('{}.ref{:04d}.png'.format(
        reference_pdf, reference_pageno))
    test_png = _outfile('{}.test{:04d}.png'.format(
        test_pdf, test_pageno))

    def rasterize(pdf, pageno, png):
        if os.path.exists(png):
            print(png)
            return
        ghostscript.rasterize_pdf(
            pdf,
            png,
            xres=100, yres=100,
            raster_device='pngmono', log=gslog, pageno=pageno)

    rasterize(reference_pdf, reference_pageno, reference_png)
    rasterize(test_pdf, test_pageno, test_png)

    pix_ref = leptonica.Pix.read(reference_png)
    pix_test = leptonica.Pix.read(test_png)

    return leptonica.Pix.correlation_binary(pix_ref, pix_test)


def test_monochrome_correlation():
    # Verify leptonica: check that an incorrect rotated image has poor
    # correlation with reference
    corr = check_monochrome_correlation(
        reference_pdf=_infile('cardinal.pdf'),
        reference_pageno=1,  # north facing page
        test_pdf=_infile('cardinal.pdf'),
        test_pageno=3,  # south facing page
        )
    assert corr < 0.10
    corr = check_monochrome_correlation(
        reference_pdf=_infile('cardinal.pdf'),
        reference_pageno=2,
        test_pdf=_infile('cardinal.pdf'),
        test_pageno=2,
        )
    assert corr > 0.90


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_autorotate(spoof_tesseract_cache, renderer):
    # cardinal.pdf contains four copies of an image rotated in each cardinal
    # direction - these ones are "burned in" not tagged with /Rotate
    out = check_ocrmypdf('cardinal.pdf', 'test_autorotate_%s.pdf' % renderer,
                         '-r', '-v', '1', env=spoof_tesseract_cache)
    for n in range(1, 4+1):
        correlation = check_monochrome_correlation(
            reference_pdf=_infile('cardinal.pdf'),
            reference_pageno=1,
            test_pdf=out,
            test_pageno=n)
        assert correlation > 0.80


def test_autorotate_threshold_low(spoof_tesseract_cache):
    out = check_ocrmypdf('cardinal.pdf', 'test_autorotate_threshold_low.pdf',
                         '--rotate-pages-threshold', '1',
                         '-r', '-v', '1', env=spoof_tesseract_cache)

    # Low threshold -> always rotate -> expect high correlation between
    # reference page and test page
    correlation = check_monochrome_correlation(
        reference_pdf=_infile('cardinal.pdf'),
        reference_pageno=1,
        test_pdf=out,
        test_pageno=3)
    assert correlation > 0.80


def test_autorotate_threshold_high(spoof_tesseract_cache):
    out = check_ocrmypdf('cardinal.pdf', 'test_autorotate_threshold_high.pdf',
                         '--rotate-pages-threshold', '99',
                         '-r', '-v', '1', env=spoof_tesseract_cache)

    # High threshold -> never rotate -> expect low correlation since
    # test page will not be rotated
    correlation = check_monochrome_correlation(
        reference_pdf=_infile('cardinal.pdf'),
        reference_pageno=1,
        test_pdf=out,
        test_pageno=3)
    assert correlation < 0.10


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_ocr_timeout(renderer):
    out = check_ocrmypdf('skew.pdf', 'test_timeout_%s.pdf' % renderer,
                         '--tesseract-timeout', '1.0')
    pdfinfo = pdf_get_all_pageinfo(out)
    assert not pdfinfo[0]['has_text']


def test_skip_big(spoof_tesseract_cache):
    out = check_ocrmypdf('enormous.pdf', 'test_enormous.pdf',
                         '--skip-big', '10', env=spoof_tesseract_cache)
    pdfinfo = pdf_get_all_pageinfo(out)
    assert not pdfinfo[0]['has_text']


@pytest.mark.parametrize('renderer', ['hocr', 'tesseract'])
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_maximum_options(spoof_tesseract_cache, renderer, output_type):
    check_ocrmypdf(
        'multipage.pdf', 'test_multipage%s.pdf' % renderer,
        '-d', '-c', '-i', '-g', '-f', '-k', '--oversample', '300',
        '--remove-background',
        '--skip-big', '10', '--title', 'Too Many Weird Files',
        '--author', 'py.test', '--pdf-renderer', renderer,
        '--output-type', output_type,
        env=spoof_tesseract_cache)


def test_tesseract_missing_tessdata():
    env = os.environ.copy()
    env['TESSDATA_PREFIX'] = '/tmp'

    p, _, err = run_ocrmypdf(
        'graph_ocred.pdf', 'not_a_pdfa.pdf', '-v', '1', '--skip-text', env=env)
    assert p.returncode == ExitCode.missing_dependency, err


def test_invalid_input_pdf():
    p, out, err = run_ocrmypdf(
        'invalid.pdf', 'wont_be_created.pdf')
    assert p.returncode == ExitCode.input_file, err


def test_blank_input_pdf():
    p, out, err = run_ocrmypdf(
        'blank.pdf', 'still_blank.pdf')
    assert p.returncode == ExitCode.ok


def test_force_ocr_on_pdf_with_no_images(spoof_tesseract_crash):
    # As a correctness test, make sure that --force-ocr on a PDF with no
    # content still triggers tesseract. If tesseract crashes, then it was
    # called.
    p, _, err = run_ocrmypdf(
        'blank.pdf', 'wont_be_created.pdf', '--force-ocr',
        env=spoof_tesseract_crash)
    assert p.returncode == ExitCode.child_process_error, err
    assert not os.path.exists(_outfile('wontwork.pdf'))


def test_french(spoof_tesseract_cache):
    p, out, err = run_ocrmypdf(
        'francais.pdf', 'francais.pdf', '-l', 'fra', env=spoof_tesseract_cache)
    assert p.returncode == ExitCode.ok, \
        "This test may fail if Tesseract language packs are missing"


def test_klingon():
    p, out, err = run_ocrmypdf(
        'francais.pdf', 'francais.pdf', '-l', 'klz')
    assert p.returncode == ExitCode.bad_args


def test_missing_docinfo(spoof_tesseract_noop):
    p, out, err = run_ocrmypdf(
        'missing_docinfo.pdf', 'missing_docinfo.pdf', '-l', 'eng', '-c',
        env=spoof_tesseract_noop)
    assert p.returncode == ExitCode.ok, err


@pytest.mark.skipif(running_in_docker(),
                    reason="writes to tests/resources")
def test_uppercase_extension(spoof_tesseract_noop):
    shutil.copy(_infile("skew.pdf"), _infile("UPPERCASE.PDF"))
    try:
        check_ocrmypdf("UPPERCASE.PDF", "UPPERCASE_OUT.PDF",
                       env=spoof_tesseract_noop)
    finally:
        os.unlink(_infile("UPPERCASE.PDF"))


def test_input_file_not_found():
    input_file = "does not exist.pdf"
    p, out, err = run_ocrmypdf(
        _infile(input_file),
        _outfile("will not happen.pdf"))
    assert p.returncode == ExitCode.input_file
    assert (input_file in out or input_file in err)


def test_input_file_not_a_pdf():
    input_file = __file__  # Try to OCR this file
    p, out, err = run_ocrmypdf(
        _infile(input_file),
        _outfile("will not happen.pdf"))
    assert p.returncode == ExitCode.input_file
    assert (input_file in out or input_file in err)


def test_qpdf_repair_fails():
    env = os.environ.copy()
    env['OCRMYPDF_QPDF'] = os.path.abspath('./spoof/qpdf_dummy_return2.py')
    p, out, err = run_ocrmypdf(
        '-v', '1',
        'c02-22.pdf', 'wont_be_created.pdf', env=env)
    print(out)
    print(err)
    assert p.returncode == ExitCode.input_file


def test_encrypted():
    p, out, err = run_ocrmypdf('skew-encrypted.pdf', 'wont_be_created.pdf')
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


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_tesseract_crash(renderer, spoof_tesseract_crash):
    p, out, err = run_ocrmypdf(
        'ccitt.pdf', 'wontwork.pdf', '-v', '1',
        '--pdf-renderer', renderer, env=spoof_tesseract_crash)
    assert p.returncode == ExitCode.child_process_error
    assert not os.path.exists(_outfile('wontwork.pdf'))
    assert "ERROR" in err


def test_tesseract_crash_autorotate(spoof_tesseract_crash):
    p, out, err = run_ocrmypdf(
        'ccitt.pdf', 'wontwork.pdf',
        '-r', env=spoof_tesseract_crash)
    assert p.returncode == ExitCode.child_process_error
    assert not os.path.exists(_outfile('wontwork.pdf'))
    assert "ERROR" in err
    print(out)
    print(err)


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_tesseract_image_too_big(renderer, spoof_tesseract_big_image_error):
    check_ocrmypdf(
        'hugemono.pdf', 'hugemono_%s.pdf' % renderer, '-r',
        '--pdf-renderer', renderer, env=spoof_tesseract_big_image_error)


def test_no_unpaper():
    env = os.environ.copy()
    env['OCRMYPDF_UNPAPER'] = os.path.abspath('./spoof/no_unpaper_here.py')
    p, out, err = run_ocrmypdf(
        'c02-22.pdf', 'wont_be_created.pdf', '--clean', env=env)
    assert p.returncode == ExitCode.missing_dependency


def test_old_unpaper():
    env = os.environ.copy()
    env['OCRMYPDF_UNPAPER'] = os.path.abspath('./spoof/unpaper_oldversion.py')
    p, out, err = run_ocrmypdf(
        'c02-22.pdf', 'wont_be_created.pdf', '--clean', env=env)
    assert p.returncode == ExitCode.missing_dependency


def test_algo4():
    p, _, _ = run_ocrmypdf('encrypted_algo4.pdf', 'wontwork.pdf')
    assert p.returncode == ExitCode.encrypted_pdf


@pytest.mark.parametrize('renderer', [
    'hocr'])  # tesseract cannot pass this test - resamples to square image
def test_non_square_resolution(renderer, spoof_tesseract_cache):
    # Confirm input image is non-square resolution
    in_pageinfo = pdf_get_all_pageinfo(_infile('aspect.pdf'))
    assert in_pageinfo[0]['xres'] != in_pageinfo[0]['yres']

    out = 'aspect_%s.pdf' % renderer
    check_ocrmypdf(
        'aspect.pdf', out,
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    out_pageinfo = pdf_get_all_pageinfo(_outfile(out))

    # Confirm resolution was kept the same
    assert in_pageinfo[0]['xres'] == out_pageinfo[0]['xres']
    assert in_pageinfo[0]['yres'] == out_pageinfo[0]['yres']


def test_image_to_pdf(spoof_tesseract_noop):
    check_ocrmypdf(
        'LinnSequencer.jpg', 'image_to_pdf.pdf', '--image-dpi', '200',
        env=spoof_tesseract_noop)


def test_jbig2_passthrough(spoof_tesseract_cache):
    out = check_ocrmypdf(
        'jbig2.pdf', 'jbig2_out.pdf',
        '--output-type', 'pdf',
        '--pdf-renderer', 'hocr',
        env=spoof_tesseract_cache)

    out_pageinfo = pdf_get_all_pageinfo(out)
    assert out_pageinfo[0]['images'][0]['enc'] == 'jbig2'


def test_stdin(spoof_tesseract_noop):
    input_file = _infile('francais.pdf')
    output_file = _outfile('test_stdin.pdf')

    # Runs: ocrmypdf - output.pdf < testfile.pdf
    with open(input_file, 'rb') as input_stream:
        p_args = OCRMYPDF + ['-', output_file]
        p = Popen(
            p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
            stdin=input_stream, env=spoof_tesseract_noop)
        out, err = p.communicate()

        assert p.returncode == ExitCode.ok


def test_stdout(spoof_tesseract_noop):
    input_file = _infile('francais.pdf')
    output_file = _outfile('test_stdout.pdf')

    # Runs: ocrmypdf francais.pdf - > test_stdout.pdf
    with open(output_file, 'wb') as output_stream:
        p_args = OCRMYPDF + [input_file, '-']
        p = Popen(
            p_args, close_fds=True, stdout=output_stream, stderr=PIPE,
            stdin=DEVNULL, env=spoof_tesseract_noop)
        out, err = p.communicate()

        assert p.returncode == ExitCode.ok

    from ocrmypdf import qpdf
    assert qpdf.check(output_file, log=None)


def test_masks(spoof_tesseract_noop):
    check_ocrmypdf('masks.pdf', 'test_masks.pdf', env=spoof_tesseract_noop)


def test_linearized_pdf_and_indirect_object(spoof_tesseract_noop):
    check_ocrmypdf(
        'epson.pdf', 'test_epson.pdf',
        env=spoof_tesseract_noop)


def test_rotated_skew_timeout():
    """This document contains an image that is rotated 90 into place with a
    /Rotate tag and intentionally skewed by altering the transformation matrix.

    This tests for a bug where the combinatino of preprocessing and a tesseract
    timeout produced a page whose dimensions did not match the original's.
    """

    input_file = _infile('rotated_skew.pdf')
    in_pageinfo = pdf_get_all_pageinfo(input_file)[0]

    assert in_pageinfo['height_pixels'] < in_pageinfo['width_pixels'], \
        "Expected the input page to be landscape"
    assert in_pageinfo['rotate'] == 90, "Expected a rotated page"

    out = check_ocrmypdf(
        'rotated_skew.pdf', 'test_rotated_skew.pdf',
        '--pdf-renderer', 'hocr',
        '--deskew', '--tesseract-timeout', '0')

    out_pageinfo = pdf_get_all_pageinfo(out)[0]

    assert out_pageinfo['height_pixels'] > out_pageinfo['width_pixels'], \
        "Expected the output page to be portrait"

    assert out_pageinfo['rotate'] == 0, \
        "Expected no page rotation for output"

    assert in_pageinfo['width_pixels'] == out_pageinfo['height_pixels'] and \
        in_pageinfo['height_pixels'] == out_pageinfo['width_pixels'], \
        "Expected page rotation to be baked in"


def test_ghostscript_pdfa_failure(spoof_no_tess_no_pdfa):
    p, out, err = run_ocrmypdf(
        'ccitt.pdf', 'test_pdfa_failure.pdf',
        env=spoof_no_tess_no_pdfa)
    assert p.returncode == 4, "Expected return code 4 when PDF/A fails"


def test_ghostscript_feature_elision(spoof_no_tess_pdfa_warning):
    check_ocrmypdf('ccitt.pdf', 'test_feature_elision.pdf',
                   env=spoof_no_tess_pdfa_warning)


def test_very_high_dpi(spoof_tesseract_cache):
    "Checks for a Decimal quantize error with high DPI, etc"
    check_ocrmypdf('2400dpi.pdf', 'test_2400dpi.pdf',
                   env=spoof_tesseract_cache)
