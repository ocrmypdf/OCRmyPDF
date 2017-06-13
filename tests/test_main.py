#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import Popen, PIPE, check_output, check_call, DEVNULL
import os
import shutil
import pytest
from ocrmypdf.pdfinfo import PdfInfo, Colorspace, Encoding
import PyPDF2 as pypdf
from ocrmypdf.exceptions import ExitCode
from ocrmypdf import leptonica
from ocrmypdf.pdfa import file_claims_pdfa
from ocrmypdf.exec import ghostscript, tesseract
import logging
from math import isclose


check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


RENDERERS = ['hocr', 'tesseract']
if tesseract.has_textonly_pdf():
    RENDERERS.append('sandwich')


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


@pytest.fixture
def spoof_no_tess_gs_render_fail():
    return spoof(tesseract='tesseract_noop.py', gs='gs_render_failure.py')


@pytest.fixture
def spoof_no_tess_gs_raster_fail():
    return spoof(tesseract='tesseract_noop.py', gs='gs_raster_failure.py')


@pytest.fixture
def spoof_qpdf_always_error():
    return spoof(qpdf='qpdf_dummy_return2.py')


def test_quick(spoof_tesseract_cache, resources, outpdf):
    check_ocrmypdf(resources / 'ccitt.pdf', outpdf, env=spoof_tesseract_cache)


def test_deskew(spoof_tesseract_noop, resources, outdir):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(
        resources / 'skew.pdf', outdir / 'skew.pdf', '-d', '-v', '1',
        env=spoof_tesseract_noop)

    # Now render as an image again and use Leptonica to find the skew angle
    # to confirm that it was deskewed
    log = logging.getLogger()

    deskewed_png = outdir / 'deskewed.png'

    ghostscript.rasterize_pdf(
        str(deskewed_pdf),
        str(deskewed_png),
        xres=150,
        yres=150,
        raster_device='pngmono',
        log=log)

    from ocrmypdf.leptonica import Pix
    pix = Pix.read(str(deskewed_png))
    skew_angle, skew_confidence = pix.find_skew()

    print(skew_angle)
    assert -0.5 < skew_angle < 0.5, "Deskewing failed"


def test_clean(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'skew.pdf', outpdf, '-c',
                   env=spoof_tesseract_noop)


def test_remove_background(spoof_tesseract_noop, resources, outdir):
    from PIL import Image

    # Ensure the input image does not contain pure white/black
    im = Image.open(resources / 'congress.jpg')
    assert im.getextrema() != ((0, 255), (0, 255), (0, 255))

    output_pdf = check_ocrmypdf(
        resources / 'congress.jpg',
        outdir / 'test_remove_bg.pdf',
        '--remove-background',
        '--image-dpi', '150',
        env=spoof_tesseract_noop)

    log = logging.getLogger()

    output_png = outdir / 'remove_bg.png'

    ghostscript.rasterize_pdf(
        str(output_pdf),
        str(output_png),
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
@pytest.mark.parametrize("renderer", ['auto', 'tesseract'])
@pytest.mark.parametrize("output_type", ['pdf', 'pdfa'])
def test_exotic_image(spoof_tesseract_cache, pdf, renderer, output_type,
                      resources, outdir):
    outfile = outdir / 'test_{0}_{1}.pdf'.format(pdf, renderer)
    check_ocrmypdf(
        resources / pdf,
        outfile,
        '-dc',
        '-v', '1',
        '--output-type', output_type,
        '--sidecar',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    assert outfile.with_suffix('.pdf.txt').exists()


@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_preserve_metadata(spoof_tesseract_noop, output_type,
                           resources, outpdf):
    pdf_before = pypdf.PdfFileReader(str(resources / 'graph.pdf'))

    output = check_ocrmypdf(
            resources / 'graph.pdf', outpdf,
            '--output-type', output_type,
            env=spoof_tesseract_noop)

    pdf_after = pypdf.PdfFileReader(str(output))

    for key in ('/Title', '/Author'):
        assert pdf_before.documentInfo[key] == pdf_after.documentInfo[key]

    pdfa_info = file_claims_pdfa(str(output))
    assert pdfa_info['output'] == output_type


@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_override_metadata(spoof_tesseract_noop, output_type, resources,
                           outpdf):
    input_file = resources / 'c02-22.pdf'
    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'

    p, out, err = run_ocrmypdf(
        input_file, outpdf,
        '--title', german,
        '--author', chinese,
        '--output-type', output_type,
        env=spoof_tesseract_noop)

    assert p.returncode == ExitCode.ok, err

    reader = pypdf.PdfFileReader(outpdf)

    assert reader.documentInfo['/Title'] == german
    assert reader.documentInfo['/Author'] == chinese
    assert reader.documentInfo.get('/Keywords', '') == ''

    pdfa_info = file_claims_pdfa(outpdf)
    assert pdfa_info['output'] == output_type


def test_high_unicode(spoof_tesseract_noop, resources, no_outpdf):

    # Ghostscript doesn't support high Unicode, so neither do we, to be
    # safe
    input_file = resources / 'c02-22.pdf'
    high_unicode = 'U+1030C is: 𐌌'

    p, out, err = run_ocrmypdf(
        input_file, no_outpdf,
        '--subject', high_unicode,
        '--output-type', 'pdfa',
        env=spoof_tesseract_noop)

    assert p.returncode == ExitCode.bad_args, err


@pytest.mark.parametrize('renderer', RENDERERS)
def test_oversample(spoof_tesseract_cache, renderer, resources, outpdf):
    oversampled_pdf = check_ocrmypdf(
        resources / 'skew.pdf', outpdf, '--oversample', '350',
        '-f',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    pdfinfo = PdfInfo(oversampled_pdf)

    print(pdfinfo[0].xres)
    assert abs(pdfinfo[0].xres - 350) < 1


def test_repeat_ocr(resources, no_outpdf):
    p, _, _ = run_ocrmypdf(resources / 'graph_ocred.pdf', no_outpdf)
    assert p.returncode != 0


def test_force_ocr(spoof_tesseract_cache, resources, outpdf):
    out = check_ocrmypdf(resources / 'graph_ocred.pdf', outpdf, '-f',
                         env=spoof_tesseract_cache)
    pdfinfo = PdfInfo(out)
    assert pdfinfo[0].has_text


def test_skip_ocr(spoof_tesseract_cache, resources, outpdf):
    check_ocrmypdf(resources / 'graph_ocred.pdf', outpdf, '-s',
                   env=spoof_tesseract_cache)


def test_argsfile(spoof_tesseract_noop, resources, outdir):
    path_argsfile = outdir / 'test_argsfile.txt'
    with open(str(path_argsfile), 'w') as argsfile:
        print('--title', 'ArgsFile Test', '--author', 'Test Cases',
              sep='\n', end='\n', file=argsfile)
    check_ocrmypdf(resources / 'graph.pdf', path_argsfile,
                   '@' + str(outdir / 'test_argsfile.txt'),
                   env=spoof_tesseract_noop)


def check_monochrome_correlation(
        outdir,
        reference_pdf, reference_pageno, test_pdf, test_pageno):
    gslog = logging.getLogger()

    reference_png = outdir / '{}.ref{:04d}.png'.format(
        reference_pdf.name, reference_pageno)
    test_png = outdir / '{}.test{:04d}.png'.format(
        test_pdf.name, test_pageno)

    def rasterize(pdf, pageno, png):
        if png.exists():
            print(png)
            return
        ghostscript.rasterize_pdf(
            str(pdf),
            str(png),
            xres=100, yres=100,
            raster_device='pngmono', log=gslog, pageno=pageno)

    rasterize(reference_pdf, reference_pageno, reference_png)
    rasterize(test_pdf, test_pageno, test_png)

    pix_ref = leptonica.Pix.read(str(reference_png))
    pix_test = leptonica.Pix.read(str(test_png))

    return leptonica.Pix.correlation_binary(pix_ref, pix_test)


def test_monochrome_correlation(resources, outdir):
    # Verify leptonica: check that an incorrect rotated image has poor
    # correlation with reference
    corr = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=1,  # north facing page
        test_pdf=resources / 'cardinal.pdf',
        test_pageno=3,  # south facing page
        )
    assert corr < 0.10
    corr = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=2,
        test_pdf=resources / 'cardinal.pdf',
        test_pageno=2,
        )
    assert corr > 0.90


@pytest.mark.parametrize('renderer', RENDERERS)
def test_autorotate(spoof_tesseract_cache, renderer, resources, outdir):
    # cardinal.pdf contains four copies of an image rotated in each cardinal
    # direction - these ones are "burned in" not tagged with /Rotate
    out = check_ocrmypdf(resources / 'cardinal.pdf', outdir / 'out.pdf',
                         '-r', '-v', '1', env=spoof_tesseract_cache)
    for n in range(1, 4+1):
        correlation = check_monochrome_correlation(
            outdir,
            reference_pdf=resources / 'cardinal.pdf',
            reference_pageno=1,
            test_pdf=outdir / 'out.pdf',
            test_pageno=n)
        assert correlation > 0.80


@pytest.mark.parametrize('threshold, correlation_test', [
    ('1', 'correlation > 0.80'),  # Low thresh -> always rotate -> high corr
    ('99', 'correlation < 0.10'),  # High thres -> never rotate -> low corr
])
def test_autorotate_threshold(
    spoof_tesseract_cache, threshold, correlation_test, resources, outdir):
    out = check_ocrmypdf(resources / 'cardinal.pdf', outdir / 'out.pdf',
                         '--rotate-pages-threshold', threshold,
                         '-r', '-v', '1', env=spoof_tesseract_cache)

    correlation = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'cardinal.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'out.pdf',
        test_pageno=3)
    assert eval(correlation_test)


@pytest.mark.parametrize('renderer',RENDERERS)
def test_ocr_timeout(renderer, resources, outpdf):
    out = check_ocrmypdf(resources / 'skew.pdf', outpdf,
                         '--tesseract-timeout', '1.0')
    pdfinfo = PdfInfo(out)
    assert not pdfinfo[0].has_text


def test_skip_big(spoof_tesseract_cache, resources, outpdf):
    out = check_ocrmypdf(resources / 'enormous.pdf', outpdf,
                         '--skip-big', '10', env=spoof_tesseract_cache)
    pdfinfo = PdfInfo(out)
    assert not pdfinfo[0].has_text


@pytest.mark.parametrize('renderer', RENDERERS)
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_maximum_options(spoof_tesseract_cache, renderer, output_type,
                         resources, outpdf):
    check_ocrmypdf(
        resources / 'multipage.pdf', outpdf,
        '-d', '-c', '-i', '-g', '-f', '-k', '--oversample', '300',
        '--remove-background',
        '--skip-big', '10', '--title', 'Too Many Weird Files',
        '--author', 'py.test', '--pdf-renderer', renderer,
        '--output-type', output_type,
        env=spoof_tesseract_cache)


def test_tesseract_missing_tessdata(resources, no_outpdf):
    env = os.environ.copy()
    env['TESSDATA_PREFIX'] = '/tmp'

    p, _, err = run_ocrmypdf(
        resources / 'graph_ocred.pdf', no_outpdf,
        '-v', '1', '--skip-text', env=env)
    assert p.returncode == ExitCode.missing_dependency, err


def test_invalid_input_pdf(resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'invalid.pdf', no_outpdf)
    assert p.returncode == ExitCode.input_file, err


def test_blank_input_pdf(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'blank.pdf', outpdf)
    assert p.returncode == ExitCode.ok


def test_force_ocr_on_pdf_with_no_images(spoof_tesseract_crash, resources,
                                         no_outpdf):
    # As a correctness test, make sure that --force-ocr on a PDF with no
    # content still triggers tesseract. If tesseract crashes, then it was
    # called.
    p, _, err = run_ocrmypdf(
        resources / 'blank.pdf', no_outpdf, '--force-ocr',
        env=spoof_tesseract_crash)
    assert p.returncode == ExitCode.child_process_error, err
    assert not os.path.exists(no_outpdf)


@pytest.mark.skipif(
    pytest.helpers.is_macos() and pytest.helpers.running_in_travis(),
    reason="takes too long to install language packs in Travis macOS homebrew")
def test_french(spoof_tesseract_cache, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf', outpdf, '-l', 'fra',
        env=spoof_tesseract_cache)
    print(os.environ)
    assert p.returncode == ExitCode.ok, \
        "This test may fail if Tesseract language packs are missing"


def test_klingon(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf', outpdf, '-l', 'klz')
    assert p.returncode == ExitCode.bad_args


def test_missing_docinfo(spoof_tesseract_noop, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'missing_docinfo.pdf', outpdf, '-l', 'eng', '-c',
        env=spoof_tesseract_noop)
    assert p.returncode == ExitCode.ok, err


@pytest.mark.skipif(pytest.helpers.running_in_docker(),
                    reason="<no longer true> writes to tests/resources")
def test_uppercase_extension(spoof_tesseract_noop, resources, outdir):
    shutil.copy(
        str(resources / "skew.pdf"),
        str(outdir / "UPPERCASE.PDF"))

    check_ocrmypdf(outdir / "UPPERCASE.PDF", outdir / "UPPERCASE_OUT.PDF",
                   env=spoof_tesseract_noop)


def test_input_file_not_found(no_outpdf):
    input_file = "does not exist.pdf"
    p, out, err = run_ocrmypdf(
        input_file,
        no_outpdf)
    assert p.returncode == ExitCode.input_file
    assert (input_file in out or input_file in err)


def test_input_file_not_a_pdf(no_outpdf):
    input_file = __file__  # Try to OCR this file
    p, out, err = run_ocrmypdf(
        input_file,
        no_outpdf)
    assert p.returncode == ExitCode.input_file
    assert (input_file in out or input_file in err)


def test_qpdf_repair_fails(spoof_qpdf_always_error, resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'c02-22.pdf', no_outpdf,
        '-v', '1',
        env=spoof_qpdf_always_error)
    print(err)
    assert p.returncode == ExitCode.input_file


def test_encrypted(resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'skew-encrypted.pdf', no_outpdf)
    assert p.returncode == ExitCode.encrypted_pdf
    assert out.find('password')


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_pagesegmode(renderer, spoof_tesseract_cache, resources, outpdf):
    check_ocrmypdf(
        resources / 'skew.pdf', outpdf,
        '--tesseract-pagesegmode', '7',
        '-v', '1',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)


@pytest.mark.parametrize('renderer', [
    'hocr',
    'tesseract',
    ])
def test_tesseract_crash(renderer, spoof_tesseract_crash,
                         resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', no_outpdf, '-v', '1',
        '--pdf-renderer', renderer, env=spoof_tesseract_crash)
    assert p.returncode == ExitCode.child_process_error
    assert not os.path.exists(no_outpdf)
    assert "ERROR" in err


def test_tesseract_crash_autorotate(spoof_tesseract_crash,
                                    resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', no_outpdf,
        '-r', env=spoof_tesseract_crash)
    assert p.returncode == ExitCode.child_process_error
    assert not os.path.exists(no_outpdf)
    assert "ERROR" in err
    print(out)
    print(err)


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_image_too_big(renderer, spoof_tesseract_big_image_error,
                                 resources, outpdf):
    check_ocrmypdf(
        resources / 'hugemono.pdf', outpdf, '-r',
        '--pdf-renderer', renderer, env=spoof_tesseract_big_image_error)


def test_no_unpaper(resources, no_outpdf):
    env = os.environ.copy()
    env['OCRMYPDF_UNPAPER'] = os.path.abspath('./spoof/no_unpaper_here.py')
    p, out, err = run_ocrmypdf(
        resources / 'c02-22.pdf', no_outpdf, '--clean', env=env)
    assert p.returncode == ExitCode.missing_dependency


def test_old_unpaper(resources, no_outpdf):
    env = os.environ.copy()
    env['OCRMYPDF_UNPAPER'] = os.path.abspath('./spoof/unpaper_oldversion.py')
    p, out, err = run_ocrmypdf(
        resources / 'c02-22.pdf', no_outpdf, '--clean', env=env)
    assert p.returncode == ExitCode.missing_dependency


def test_algo4(resources, no_outpdf):
    p, _, _ = run_ocrmypdf(resources / 'encrypted_algo4.pdf', no_outpdf)
    assert p.returncode == ExitCode.encrypted_pdf


@pytest.mark.parametrize('renderer', [
    'hocr'])  # tesseract cannot pass this test - resamples to square image
def test_non_square_resolution(renderer, spoof_tesseract_cache,
                               resources, outpdf):
    # Confirm input image is non-square resolution
    in_pageinfo = PdfInfo(resources / 'aspect.pdf')
    assert in_pageinfo[0].xres != in_pageinfo[0].yres

    check_ocrmypdf(
        resources / 'aspect.pdf', outpdf,
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    out_pageinfo = PdfInfo(outpdf)

    # Confirm resolution was kept the same
    assert in_pageinfo[0].xres == out_pageinfo[0].xres
    assert in_pageinfo[0].yres == out_pageinfo[0].yres


@pytest.mark.parametrize('renderer', RENDERERS)
def test_convert_to_square_resolution(renderer, spoof_tesseract_cache,
                                      resources, outpdf):
    from math import isclose

    # Confirm input image is non-square resolution
    in_pageinfo = PdfInfo(resources / 'aspect.pdf')
    assert in_pageinfo[0].xres != in_pageinfo[0].yres

    # --force-ocr requires means forced conversion to square resolution
    check_ocrmypdf(
        resources / 'aspect.pdf', outpdf,
        '--force-ocr',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    out_pageinfo = PdfInfo(outpdf)

    in_p0, out_p0 = in_pageinfo[0], out_pageinfo[0]

    # Resolution show now be equal
    assert out_p0.xres == out_p0.yres

    # Page size should match input page size
    assert isclose(in_p0.width_inches,
                   out_p0.width_inches)
    assert isclose(in_p0.height_inches,
                   out_p0.height_inches)

    # Because we rasterized the page to produce a new image, it should occupy
    # the entire page
    out_im_w = out_p0.images[0]['width'] / out_p0.images[0]['dpi_w']
    out_im_h = out_p0.images[0]['height'] / out_p0.images[0]['dpi_h']
    assert isclose(out_p0.width_inches, out_im_w)
    assert isclose(out_p0.height_inches, out_im_h)


def test_image_to_pdf(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'LinnSequencer.jpg', outpdf, '--image-dpi', '200',
        env=spoof_tesseract_noop)


def test_jbig2_passthrough(spoof_tesseract_cache, resources, outpdf):
    out = check_ocrmypdf(
        resources / 'jbig2.pdf', outpdf,
        '--output-type', 'pdf',
        '--pdf-renderer', 'hocr',
        env=spoof_tesseract_cache)

    out_pageinfo = PdfInfo(out)
    assert out_pageinfo[0].images[0].enc == Encoding.jbig2


def test_stdin(spoof_tesseract_noop, ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf - output.pdf < testfile.pdf
    with open(input_file, 'rb') as input_stream:
        p_args = ocrmypdf_exec + ['-', output_file]
        p = Popen(
            p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
            stdin=input_stream, env=spoof_tesseract_noop)
        out, err = p.communicate()

        assert p.returncode == ExitCode.ok


def test_stdout(spoof_tesseract_noop, ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    # Runs: ocrmypdf francais.pdf - > test_stdout.pdf
    with open(output_file, 'wb') as output_stream:
        p_args = ocrmypdf_exec + [input_file, '-']
        p = Popen(
            p_args, close_fds=True, stdout=output_stream, stderr=PIPE,
            stdin=DEVNULL, env=spoof_tesseract_noop)
        out, err = p.communicate()

        assert p.returncode == ExitCode.ok

    from ocrmypdf.exec import qpdf
    assert qpdf.check(output_file, log=None)


def test_closed_streams(spoof_tesseract_noop, ocrmypdf_exec, resources, outpdf):
    input_file = str(resources / 'francais.pdf')
    output_file = str(outpdf)

    def evil_closer():
        os.close(0)
        os.close(1)

    p_args = ocrmypdf_exec + [input_file, output_file]
    p = Popen(
        p_args, close_fds=True, stdout=None, stderr=PIPE, stdin=None,
        env=spoof_tesseract_noop, preexec_fn=evil_closer)
    out, err = p.communicate()
    print(err.decode())
    assert p.returncode == ExitCode.ok


def test_masks(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'masks.pdf', outpdf, env=spoof_tesseract_noop)


def test_linearized_pdf_and_indirect_object(spoof_tesseract_noop,
        resources, outpdf):
    check_ocrmypdf(
        resources / 'epson.pdf', outpdf,
        env=spoof_tesseract_noop)


def test_rotated_skew_timeout(resources, outpdf):
    """This document contains an image that is rotated 90 into place with a
    /Rotate tag and intentionally skewed by altering the transformation matrix.

    This tests for a bug where the combinatino of preprocessing and a tesseract
    timeout produced a page whose dimensions did not match the original's.
    """

    input_file = str(resources / 'rotated_skew.pdf')
    in_pageinfo = PdfInfo(input_file)[0]

    assert in_pageinfo.height_pixels < in_pageinfo.width_pixels, \
        "Expected the input page to be landscape"
    assert in_pageinfo.rotation == 90, "Expected a rotated page"

    out = check_ocrmypdf(
        input_file, outpdf,
        '--pdf-renderer', 'hocr',
        '--deskew', '--tesseract-timeout', '0')

    out_pageinfo = PdfInfo(out)[0]

    assert out_pageinfo.height_pixels > out_pageinfo.width_pixels, \
        "Expected the output page to be portrait"

    assert out_pageinfo.rotation == 0, \
        "Expected no page rotation for output"

    assert in_pageinfo.width_pixels == out_pageinfo.height_pixels and \
        in_pageinfo.height_pixels == out_pageinfo.width_pixels, \
        "Expected page rotation to be baked in"


def test_ghostscript_pdfa_failure(spoof_no_tess_no_pdfa, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', outpdf,
        env=spoof_no_tess_no_pdfa)
    assert p.returncode == 4, "Expected return code 4 when PDF/A fails"


def test_ghostscript_feature_elision(spoof_no_tess_pdfa_warning,
        resources, outpdf):
    check_ocrmypdf(resources / 'ccitt.pdf', outpdf,
                   env=spoof_no_tess_pdfa_warning)


def test_very_high_dpi(spoof_tesseract_cache, resources, outpdf):
    "Checks for a Decimal quantize error with high DPI, etc"
    check_ocrmypdf(resources / '2400dpi.pdf', outpdf,
                   env=spoof_tesseract_cache)
    pdfinfo = PdfInfo(outpdf)

    image = pdfinfo[0].images[0]
    assert isclose(image.xres, image.yres)
    assert isclose(image.xres, 2400)


def test_overlay(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'overlay.pdf', outpdf,
                   env=spoof_tesseract_noop)


@pytest.mark.skipif(
    os.getuid() == 0 or os.geteuid() == 0,
    reason="root can write to anything"
    )
def test_destination_not_writable(spoof_tesseract_noop, resources, outdir):
    protected_file = outdir / 'protected.pdf'
    protected_file.touch()
    protected_file.chmod(0o400)  # Read-only
    p, out, err = run_ocrmypdf(
        resources / 'jbig2.pdf', protected_file,
        env=spoof_tesseract_noop)
    assert p.returncode == ExitCode.file_access_error, "Expected error"


def test_tesseract_config_valid(resources, outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write('''\
load_system_dawg 0
language_model_penalty_non_dict_word 0
language_model_penalty_non_freq_dict_word 0
''')

    check_ocrmypdf(
        resources / 'ccitt.pdf', outdir / 'out.pdf',
        '--tesseract-config', str(cfg_file))


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_config_notfound(renderer, resources, outdir):
    cfg_file = outdir / 'nofile.cfg'

    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', outdir / 'out.pdf',
        '--pdf-renderer', renderer,
        '--tesseract-config', str(cfg_file))
    assert "Can't open" in err, "No error message about missing config file"
    assert p.returncode == ExitCode.ok


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_config_invalid(renderer, resources, outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write('''\
THIS FILE IS INVALID
''')

    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', outdir / 'out.pdf',
        '--pdf-renderer', renderer,
        '--tesseract-config', str(cfg_file))
    assert "parameter not found" in err, "No error message"
    assert p.returncode == ExitCode.invalid_config


def test_form_xobject(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'formxobject.pdf', outpdf,
                   '--force-ocr',
                   env=spoof_tesseract_noop)


@pytest.mark.parametrize('renderer', RENDERERS)
def test_pagesize_consistency(renderer, resources, outpdf):
    from math import isclose

    first_page_dimensions = pytest.helpers.first_page_dimensions

    infile = resources / 'linn.pdf'

    before_dims = first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf, '--pdf-renderer', renderer,
        '--clean', '--deskew', '--remove-background', '--clean-final')

    after_dims = first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0])
    assert isclose(before_dims[1], after_dims[1])


def test_skip_big_with_no_images(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'blank.pdf', outpdf,
                   '--skip-big', '5',
                   '--force-ocr',
                   env=spoof_tesseract_noop)


def test_gs_render_failure(spoof_no_tess_gs_render_fail, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'blank.pdf', outpdf,
        env=spoof_no_tess_gs_render_fail)
    print(err)
    assert p.returncode == ExitCode.child_process_error


def test_gs_raster_failure(spoof_no_tess_gs_raster_fail, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', outpdf,
        env=spoof_no_tess_gs_raster_fail)
    print(err)
    assert p.returncode == ExitCode.child_process_error


def test_no_contents(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'no_contents.pdf', outpdf, '--force-ocr',
                   env=spoof_tesseract_noop)


@pytest.mark.parametrize('image', [
    'baiona.png',
    'baiona_gray.png',
    'congress.jpg'
    ])
def test_compression_preserved(spoof_tesseract_noop, ocrmypdf_exec,
                               resources, image, outpdf):
    from PIL import Image

    input_file = str(resources / image)
    output_file = str(outpdf)

    im = Image.open(input_file)

    # Runs: ocrmypdf - output.pdf < testfile
    with open(input_file, 'rb') as input_stream:
        p_args = ocrmypdf_exec + [
            '--image-dpi', '150', '--output-type', 'pdf', '-', output_file]
        p = Popen(
            p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
            stdin=input_stream, env=spoof_tesseract_noop)
        out, err = p.communicate()

        assert p.returncode == ExitCode.ok

    pdfinfo = PdfInfo(output_file)

    pdfimage = pdfinfo[0].images[0]

    if input_file.endswith('.png'):
        assert pdfimage.enc != Encoding.jpeg, \
            "Lossless compression changed to lossy!"
    elif input_file.endswith('.jpg'):
        assert pdfimage.enc == Encoding.jpeg, \
            "Lossy compression changed to lossless!"
    if im.mode.startswith('RGB') or im.mode.startswith('BGR'):
        assert pdfimage.color == Colorspace.rgb, \
            "Colorspace changed"
    elif im.mode.startswith('L'):
        assert pdfimage.color == Colorspace.gray, \
            "Colorspace changed"


@pytest.mark.parametrize('image,compression', [
    ('baiona.png', 'jpeg'),
    ('baiona_gray.png', 'lossless'),
    ('congress.jpg', 'lossless')
    ])
def test_compression_changed(spoof_tesseract_noop, ocrmypdf_exec,
                             resources, image, compression, outpdf):
    from PIL import Image

    input_file = str(resources / image)
    output_file = str(outpdf)

    im = Image.open(input_file)

    # Runs: ocrmypdf - output.pdf < testfile
    with open(input_file, 'rb') as input_stream:
        p_args = ocrmypdf_exec + [
            '--image-dpi', '150', '--output-type', 'pdfa',
            '--pdfa-image-compression', compression,
            '-', output_file]
        p = Popen(
            p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
            stdin=input_stream, env=spoof_tesseract_noop)
        out, err = p.communicate()

        assert p.returncode == ExitCode.ok

    pdfinfo = PdfInfo(output_file)

    pdfimage = pdfinfo[0].images[0]

    if compression == "jpeg":
        assert pdfimage.enc == Encoding.jpeg
    elif compression == 'lossless':
        assert pdfimage.enc not in (Encoding.jpeg, Encoding.jpeg2000)

    if im.mode.startswith('RGB') or im.mode.startswith('BGR'):
        assert pdfimage.color == Colorspace.rgb, \
            "Colorspace changed"
    elif im.mode.startswith('L'):
        assert pdfimage.color == Colorspace.gray, \
            "Colorspace changed"


def test_sidecar_pagecount(spoof_tesseract_cache, resources, outpdf):
    sidecar = outpdf + '.txt'
    check_ocrmypdf(
        resources / 'multipage.pdf', outpdf,
        '--skip-text',
        '--sidecar', sidecar,
        env=spoof_tesseract_cache)

    pdfinfo = PdfInfo(resources / 'multipage.pdf')
    num_pages = len(pdfinfo)

    with open(sidecar, 'r') as f:
        ocr_text = f.read()

    # There should a formfeed between each pair of pages, so the count of
    # formfeeds is the page count less one
    assert ocr_text.count('\f') == num_pages - 1, \
        "Sidecar page count does not match PDF page count"
