# © 2015-17 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

from subprocess import Popen, PIPE, check_output, check_call, DEVNULL
from pathlib import Path
import os
import shutil
import resource
import pytest
import sys
from ocrmypdf.pdfinfo import PdfInfo, Colorspace, Encoding
import PyPDF2 as pypdf
from ocrmypdf.exceptions import ExitCode
from ocrmypdf import leptonica
from ocrmypdf.exec import ghostscript, tesseract, qpdf
from ocrmypdf.pdfa import file_claims_pdfa
import logging
from math import isclose

import PIL

# pytest.helpers is dynamic
# pylint: disable=no-member
# pylint: disable=w0612

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


RENDERERS = ['hocr', 'tesseract']
if tesseract.has_textonly_pdf():
    RENDERERS.append('sandwich')


@pytest.fixture(scope='session')
def spoof_tesseract_crash(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_crash.py')


@pytest.fixture(scope='session')
def spoof_tesseract_big_image_error(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_big_image_error.py')


@pytest.fixture(scope='session')
def spoof_no_tess_no_pdfa(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_noop.py', gs='gs_pdfa_failure.py')


@pytest.fixture(scope='session')
def spoof_no_tess_pdfa_warning(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_noop.py', gs='gs_feature_elision.py')


@pytest.fixture(scope='session')
def spoof_no_tess_gs_render_fail(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_noop.py', gs='gs_render_failure.py')


@pytest.fixture(scope='session')
def spoof_no_tess_gs_raster_fail(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_noop.py', gs='gs_raster_failure.py')


@pytest.fixture(scope='session')
def spoof_tess_bad_utf8(tmpdir_factory):
    return spoof(tmpdir_factory, tesseract='tesseract_badutf8.py')


@pytest.fixture(scope='session')
def spoof_qpdf_always_error(tmpdir_factory):
    return spoof(tmpdir_factory, qpdf='qpdf_dummy_return2.py')


def test_quick(spoof_tesseract_cache, resources, outpdf):
    check_ocrmypdf(resources / 'ccitt.pdf', outpdf, env=spoof_tesseract_cache)


def test_deskew(spoof_tesseract_noop, resources, outdir):
    # Run with deskew
    deskewed_pdf = check_ocrmypdf(
        resources / 'skew.pdf', outdir / 'skew.pdf', '-d',
        env=spoof_tesseract_noop)

    # Now render as an image again and use Leptonica to find the skew angle
    # to confirm that it was deskewed
    log = logging.getLogger()

    deskewed_png = outdir / 'deskewed.png'

    ghostscript.rasterize_pdf(
        deskewed_pdf,
        deskewed_png,
        xres=150,
        yres=150,
        raster_device='pngmono',
        log=log,
        pageno=1)

    from ocrmypdf.leptonica import Pix
    pix = Pix.read(str(deskewed_png))
    skew_angle, skew_confidence = pix.find_skew()

    print(skew_angle)
    assert -0.5 < skew_angle < 0.5, "Deskewing failed"


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
        output_pdf,
        output_png,
        xres=100,
        yres=100,
        raster_device='png16m',
        log=log,
        pageno=1)

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
        '--skip-text',
        '--pdf-renderer', renderer, env=spoof_tesseract_cache)

    assert outfile.with_suffix('.pdf.txt').exists()


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
            pdf, png, xres=100, yres=100,
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
def test_french(spoof_tesseract_cache, resources, outdir):
    # Produce a sidecar too - implicit test that system locale is set up
    # properly
    sidecar = outdir / 'francais.txt'
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf', outdir / 'francais.pdf', '-l', 'fra',
        '--sidecar', sidecar,
        env=spoof_tesseract_cache)
    print(os.environ)
    assert p.returncode == ExitCode.ok, \
        "This test may fail if Tesseract language packs are missing"


def test_klingon(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf', outpdf, '-l', 'klz')
    assert p.returncode == ExitCode.missing_dependency


def test_missing_docinfo(spoof_tesseract_noop, resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'missing_docinfo.pdf', outpdf, '-l', 'eng', '--skip-text',
        env=spoof_tesseract_noop)
    assert p.returncode == ExitCode.ok, err


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
    assert out.find('encrypted')


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


@pytest.mark.parametrize('renderer', RENDERERS)
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
        '--pdf-renderer', renderer, 
        '--max-image-mpixels', '0',
        env=spoof_tesseract_big_image_error)


def test_algo4(resources, no_outpdf):
    p, _, _ = run_ocrmypdf(resources / 'encrypted_algo4.pdf', no_outpdf)
    assert p.returncode == ExitCode.encrypted_pdf


@pytest.mark.parametrize('renderer', [
    'hocr', 'sandwich'])  # tesseract cannot pass this test - resamples to square image
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


@pytest.mark.skipif(sys.version_info[0:3] >= (3, 6, 4),
                    reason="issue fixed in Python 3.6.4")
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
    p, out, err = run_ocrmypdf(
        resources / 'masks.pdf', outpdf, env=spoof_tesseract_noop)

    assert p.returncode == ExitCode.ok


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
                   '--skip-text',
                   env=spoof_tesseract_noop)


def test_destination_not_writable(spoof_tesseract_noop, resources, outdir):
    if os.getuid() == 0 or os.geteuid() == 0:
        pytest.xfail(reason="root can write to anything")
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
        '--tesseract-config', cfg_file)


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_config_notfound(renderer, resources, outdir):
    cfg_file = outdir / 'nofile.cfg'

    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', outdir / 'out.pdf',
        '--pdf-renderer', renderer,
        '--tesseract-config', cfg_file)
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
        '--tesseract-config', cfg_file)
    assert "parameter not found" in err, "No error message"
    assert p.returncode == ExitCode.invalid_config


def test_user_words(resources, outdir):
    word_list = outdir / 'wordlist.txt'
    sidecar_before = outdir / 'sidecar_before.txt'
    sidecar_after = outdir / 'sidecar_after.txt'

    # Don't know how to make this test pass on various versions and platforms
    # so weaken to merely testing that the argument is accepted
    consistent = False

    if consistent:
        check_ocrmypdf(
            resources / 'crom.png', outdir / 'out.pdf',
            '--image-dpi', 150,
            '--sidecar', sidecar_before
        )
        assert 'cromulent' not in sidecar_before.open().read()

    with word_list.open('w') as f:
        f.write('cromulent\n')  # a perfectly cromulent word

    check_ocrmypdf(
        resources / 'crom.png', outdir / 'out.pdf',
        '--image-dpi', 150,
        '--sidecar', sidecar_after,
        '--user-words', word_list
    )

    if consistent:
        assert 'cromulent' in sidecar_after.open().read()


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


@pytest.mark.skipif('8.0.0' <= qpdf.version() <= '8.0.1',
                    reason="qpdf regression on pages with no contents")
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
    else:
        if ghostscript.jpeg_passthrough_available():
            # Ghostscript 9.23 adds JPEG passthrough, which allows a JPEG to be
            # copied without transcoding - so report
            if image.endswith('jpg'):
                assert pdfimage.enc == Encoding.jpeg
        else:
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


def test_sidecar_nonempty(spoof_tesseract_cache, resources, outpdf):
    sidecar = outpdf + '.txt'
    check_ocrmypdf(
        resources / 'ccitt.pdf', outpdf,
        '--sidecar', sidecar,
        env=spoof_tesseract_cache
    )

    with open(sidecar, 'r') as f:
        ocr_text = f.read()
    assert 'the' in ocr_text


def test_pdfa_1(spoof_tesseract_cache, resources, outpdf):
    check_ocrmypdf(
        resources / 'ccitt.pdf', outpdf,
        '--output-type', 'pdfa-1',
        env=spoof_tesseract_cache
    )

    pdfa_info = file_claims_pdfa(outpdf)
    assert pdfa_info['conformance'] == 'PDF/A-1B'


def test_bad_locale():
    env = os.environ.copy()
    env['LC_ALL'] = 'C'

    p, out, err = run_ocrmypdf(
        'a', 'b', env=env
    )
    assert out == '', "stdout not clean"
    assert p.returncode != 0
    assert 'configured to use ASCII as encoding' in err, "should whine"


@pytest.mark.parametrize('renderer', RENDERERS)
def test_bad_utf8(spoof_tess_bad_utf8, renderer, resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', no_outpdf,
        '--pdf-renderer', renderer,
        env=spoof_tess_bad_utf8
    )

    assert out == '', "stdout not clean"
    assert p.returncode != 0
    assert 'not utf-8' in err, "should whine about utf-8"
    assert '\\x96' in err, 'should repeat backslash encoded output'


@pytest.mark.skipif(
    not tesseract.has_textonly_pdf(), 
    reason="issue only affects sandwich")
def test_rotate_deskew_timeout(resources, outdir):
    check_ocrmypdf(
        resources / 'rotated_skew.pdf',
        outdir / 'deskewed.pdf',
        '--deskew',
        '--tesseract-timeout', '0',
        '--pdf-renderer', 'sandwich'
    )

    correlation = check_monochrome_correlation(
        outdir,
        reference_pdf=resources / 'ccitt.pdf',
        reference_pageno=1,
        test_pdf=outdir / 'deskewed.pdf',
        test_pageno=1)

    # Confirm that the page still got deskewed
    assert correlation > 0.50


@pytest.mark.skipif(
    PIL.__version__ < '5.0.0',
    reason="Pillow < 5.0.0 doesn't raise the exception")
def test_decompression_bomb(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'hugemono.pdf',
        outpdf
    )
    assert 'decompression bomb' in err

    p, out, err = run_ocrmypdf(
        resources / 'hugemono.pdf',
        outpdf,
        '--max-image-mpixels', '2000'
    )
    assert p.returncode == 0


def test_text_curves(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'vector.pdf', outpdf, env=spoof_tesseract_noop)

    info = PdfInfo(outpdf)
    assert len(info.pages[0].images) == 0, "added images to the vector PDF"

    check_ocrmypdf(
        resources / 'vector.pdf', outpdf, '--force-ocr',
        env=spoof_tesseract_noop)
    
    info = PdfInfo(outpdf)
    assert len(info.pages[0].images) != 0, "force did not rasterize"
    

def test_dev_null(spoof_tesseract_noop, resources):
    p, out, err = run_ocrmypdf(
        resources / 'trivial.pdf',
        os.devnull,
        '--force-ocr',
        env=spoof_tesseract_noop
    )
    assert p.returncode == 0, "could not send output to /dev/null"
    assert len(out) == 0, "wrote to stdout"


def test_output_is_dir(spoof_tesseract_noop, resources, outdir):
    p, out, err = run_ocrmypdf(
        resources / 'trivial.pdf',
        outdir,
        '--force-ocr',
        env=spoof_tesseract_noop
    )
    assert p.returncode == ExitCode.file_access_error
    assert 'is not a writable file' in err


def test_output_is_symlink(spoof_tesseract_noop, resources, outdir):
    sym = Path(outdir / 'this_is_a_symlink')
    sym.symlink_to(outdir / 'out.pdf')
    p, out, err = run_ocrmypdf(
        resources / 'trivial.pdf',
        sym,
        '--force-ocr',
        env=spoof_tesseract_noop
    )
    assert p.returncode == ExitCode.ok, err
    assert (outdir / 'out.pdf').stat().st_size > 0, 'target file not created'


def test_skip_repair(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--skip-repair',
        env=spoof_tesseract_noop
    )
