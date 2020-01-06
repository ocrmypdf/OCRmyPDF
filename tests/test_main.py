# © 2015-19 James R. Barlow: github.com/jbarlow83
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

import os
import shutil
from math import isclose
from pathlib import Path
from subprocess import PIPE, run
from unittest.mock import patch

import pikepdf
import PIL
import pytest
from PIL import Image

import ocrmypdf
from ocrmypdf.exceptions import ExitCode, MissingDependencyError
from ocrmypdf.exec import ghostscript, qpdf, tesseract
from ocrmypdf.pdfa import file_claims_pdfa
from ocrmypdf.pdfinfo import Colorspace, Encoding, PdfInfo

# pytest.helpers is dynamic
# pylint: disable=no-member,redefined-outer-name

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf_api
spoof = pytest.helpers.spoof


RENDERERS = ['hocr', 'sandwich']


@pytest.fixture
def spoof_tesseract_crash(tmp_path_factory):
    return spoof(tmp_path_factory, tesseract='tesseract_crash.py')


@pytest.fixture
def spoof_tesseract_big_image_error(tmp_path_factory):
    return spoof(tmp_path_factory, tesseract='tesseract_big_image_error.py')


def test_quick(spoof_tesseract_cache, resources, outpdf):
    check_ocrmypdf(resources / 'ccitt.pdf', outpdf, env=spoof_tesseract_cache)


@pytest.mark.parametrize('renderer', RENDERERS)
def test_oversample(spoof_tesseract_cache, renderer, resources, outpdf):
    oversampled_pdf = check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--oversample',
        '350',
        '-f',
        '--pdf-renderer',
        renderer,
        env=spoof_tesseract_cache,
    )

    pdfinfo = PdfInfo(oversampled_pdf)

    print(pdfinfo[0].xres)
    assert abs(pdfinfo[0].xres - 350) < 1


def test_repeat_ocr(resources, no_outpdf):
    result = run_ocrmypdf_api(resources / 'graph_ocred.pdf', no_outpdf)
    assert result == ExitCode.already_done_ocr


def test_force_ocr(spoof_tesseract_cache, resources, outpdf):
    out = check_ocrmypdf(
        resources / 'graph_ocred.pdf', outpdf, '-f', env=spoof_tesseract_cache
    )
    pdfinfo = PdfInfo(out)
    assert pdfinfo[0].has_text


def test_skip_ocr(spoof_tesseract_cache, resources, outpdf):
    out = check_ocrmypdf(
        resources / 'graph_ocred.pdf', outpdf, '-s', env=spoof_tesseract_cache
    )
    pdfinfo = PdfInfo(out)
    assert pdfinfo[0].has_text


def test_redo_ocr(resources, outpdf):
    in_ = resources / 'graph_ocred.pdf'
    before = PdfInfo(in_, detailed_page_analysis=True)
    out = outpdf
    out = check_ocrmypdf(in_, out, '--redo-ocr')
    after = PdfInfo(out, detailed_page_analysis=True)
    assert before[0].has_text and after[0].has_text
    assert (
        before[0].get_textareas() != after[0].get_textareas()
    ), "Expected text to be different after re-OCR"


def test_argsfile(spoof_tesseract_noop, resources, outdir):
    path_argsfile = outdir / 'test_argsfile.txt'
    with open(str(path_argsfile), 'w') as argsfile:
        print(
            '--title',
            'ArgsFile Test',
            '--author',
            'Test Cases',
            sep='\n',
            end='\n',
            file=argsfile,
        )
    check_ocrmypdf(
        resources / 'graph.pdf',
        path_argsfile,
        '@' + str(outdir / 'test_argsfile.txt'),
        env=spoof_tesseract_noop,
    )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_ocr_timeout(renderer, resources, outpdf):
    out = check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--tesseract-timeout',
        '0',
        '--pdf-renderer',
        renderer,
    )
    pdfinfo = PdfInfo(out)
    assert not pdfinfo[0].has_text


def test_skip_big(spoof_tesseract_cache, resources, outpdf):
    out = check_ocrmypdf(
        resources / 'jbig2.pdf', outpdf, '--skip-big', '1', env=spoof_tesseract_cache
    )
    pdfinfo = PdfInfo(out)
    assert not pdfinfo[0].has_text


@pytest.mark.parametrize('renderer', RENDERERS)
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_maximum_options(
    spoof_tesseract_cache, renderer, output_type, resources, outpdf
):
    check_ocrmypdf(
        resources / 'multipage.pdf',
        outpdf,
        '-d',
        '-ci' if pytest.helpers.have_unpaper() else None,
        '-f',
        '-k',
        '--oversample',
        '300',
        '--remove-background',
        '--skip-big',
        '10',
        '--title',
        'Too Many Weird Files',
        '--author',
        'py.test',
        '--pdf-renderer',
        renderer,
        '--output-type',
        output_type,
        env=spoof_tesseract_cache,
    )


def test_tesseract_missing_tessdata(resources, no_outpdf, tmpdir):
    env = os.environ.copy()
    env['TESSDATA_PREFIX'] = os.fspath(tmpdir)

    returncode = run_ocrmypdf_api(
        resources / 'graph.pdf', no_outpdf, '-v', '1', '--skip-text', env=env
    )
    assert returncode == ExitCode.missing_dependency


def test_invalid_input_pdf(resources, no_outpdf):
    result = run_ocrmypdf_api(resources / 'invalid.pdf', no_outpdf)
    assert result == ExitCode.input_file


def test_blank_input_pdf(resources, outpdf):
    result = run_ocrmypdf_api(resources / 'blank.pdf', outpdf)
    assert result == ExitCode.ok


def test_force_ocr_on_pdf_with_no_images(spoof_tesseract_crash, resources, no_outpdf):
    # As a correctness test, make sure that --force-ocr on a PDF with no
    # content still triggers tesseract. If tesseract crashes, then it was
    # called.
    p, _, _ = run_ocrmypdf(
        resources / 'blank.pdf', no_outpdf, '--force-ocr', env=spoof_tesseract_crash
    )
    assert p.returncode == ExitCode.child_process_error
    assert not os.path.exists(no_outpdf)


@pytest.mark.skipif(
    pytest.helpers.is_macos() and pytest.helpers.running_in_travis(),
    reason="takes too long to install language packs in Travis macOS homebrew",
)
def test_german(spoof_tesseract_cache, resources, outdir):
    # Produce a sidecar too - implicit test that system locale is set up
    # properly. It is fine that we are testing -l deu on a French file because
    # we are exercising the functionality not going for accuracy.
    sidecar = outdir / 'francais.txt'
    try:
        check_ocrmypdf(
            resources / 'francais.pdf',
            outdir / 'francais.pdf',
            '-l',
            'deu',  # more commonly installed
            '--sidecar',
            sidecar,
            env=spoof_tesseract_cache,
        )
    except MissingDependencyError:
        if 'deu' not in tesseract.languages():
            pytest.xfail(reason="tesseract-deu language pack not installed")
        raise


def test_klingon(resources, outpdf):
    p, _, _ = run_ocrmypdf(resources / 'francais.pdf', outpdf, '-l', 'klz')
    assert p.returncode == ExitCode.missing_dependency


def test_missing_docinfo(spoof_tesseract_noop, resources, outpdf):
    result = run_ocrmypdf_api(
        resources / 'missing_docinfo.pdf',
        outpdf,
        '-l',
        'eng',
        '--skip-text',
        env=spoof_tesseract_noop,
    )
    assert result == ExitCode.ok


def test_uppercase_extension(spoof_tesseract_noop, resources, outdir):
    shutil.copy(str(resources / "skew.pdf"), str(outdir / "UPPERCASE.PDF"))

    check_ocrmypdf(
        outdir / "UPPERCASE.PDF", outdir / "UPPERCASE_OUT.PDF", env=spoof_tesseract_noop
    )


def test_input_file_not_found(caplog, no_outpdf):
    input_file = "does not exist.pdf"
    result = run_ocrmypdf_api(input_file, no_outpdf)
    assert result == ExitCode.input_file
    assert input_file in caplog.text


@pytest.mark.skipif(os.name == 'nt', reason="chmod")
def test_input_file_not_readable(caplog, resources, outdir, no_outpdf):
    input_file = outdir / 'trivial.pdf'
    shutil.copy(resources / 'trivial.pdf', input_file)
    input_file.chmod(0o000)
    result = run_ocrmypdf_api(input_file, no_outpdf)
    assert result == ExitCode.input_file
    assert str(input_file) in caplog.text


def test_input_file_not_a_pdf(caplog, no_outpdf):
    input_file = __file__  # Try to OCR this file
    result = run_ocrmypdf_api(input_file, no_outpdf)
    assert result == ExitCode.input_file
    if os.name != 'nt':  # name will be mangled with \\'s on nt
        assert input_file in caplog.text


def test_encrypted(resources, caplog, no_outpdf):
    result = run_ocrmypdf_api(resources / 'skew-encrypted.pdf', no_outpdf)
    assert result == ExitCode.encrypted_pdf
    assert 'encryption must be removed' in caplog.text


@pytest.mark.parametrize('renderer', RENDERERS)
def test_pagesegmode(renderer, spoof_tesseract_cache, resources, outpdf):
    check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--tesseract-pagesegmode',
        '7',
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        env=spoof_tesseract_cache,
    )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_crash(renderer, spoof_tesseract_crash, resources, no_outpdf, caplog):
    p, _, err = run_ocrmypdf(
        resources / 'ccitt.pdf',
        no_outpdf,
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        env=spoof_tesseract_crash,
    )
    assert p.returncode == ExitCode.child_process_error
    assert not os.path.exists(no_outpdf)
    assert "SubprocessOutputError" in err


def test_tesseract_crash_autorotate(spoof_tesseract_crash, resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf', no_outpdf, '-r', env=spoof_tesseract_crash
    )
    assert p.returncode == ExitCode.child_process_error
    assert not os.path.exists(no_outpdf)
    assert "ERROR" in err
    print(out)
    print(err)


@pytest.mark.parametrize('renderer', RENDERERS)
@pytest.mark.slow
def test_tesseract_image_too_big(
    renderer, spoof_tesseract_big_image_error, resources, outpdf
):
    check_ocrmypdf(
        resources / 'hugemono.pdf',
        outpdf,
        '-r',
        '--pdf-renderer',
        renderer,
        '--max-image-mpixels',
        '0',
        env=spoof_tesseract_big_image_error,
    )


def test_algo4(resources, spoof_tesseract_noop, outpdf):
    p, _, _ = run_ocrmypdf(
        resources / 'encrypted_algo4.pdf', outpdf, env=spoof_tesseract_noop
    )
    assert p.returncode == ExitCode.encrypted_pdf


def test_jbig2_passthrough(spoof_tesseract_cache, resources, outpdf):
    out = check_ocrmypdf(
        resources / 'jbig2.pdf',
        outpdf,
        '--output-type',
        'pdf',
        '--pdf-renderer',
        'hocr',
        env=spoof_tesseract_cache,
    )
    out_pageinfo = PdfInfo(out)
    assert out_pageinfo[0].images[0].enc == Encoding.jbig2


def test_masks(spoof_tesseract_noop, resources, outpdf):
    assert (
        ocrmypdf.ocr(
            resources / 'masks.pdf', outpdf, tesseract_env=spoof_tesseract_noop
        )
        == ExitCode.ok
    )


def test_linearized_pdf_and_indirect_object(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(resources / 'epson.pdf', outpdf, env=spoof_tesseract_noop)


def test_very_high_dpi(spoof_tesseract_cache, resources, outpdf):
    "Checks for a Decimal quantize error with high DPI, etc"
    check_ocrmypdf(resources / '2400dpi.pdf', outpdf, env=spoof_tesseract_cache)
    pdfinfo = PdfInfo(outpdf)

    image = pdfinfo[0].images[0]
    assert isclose(image.xres, image.yres)
    assert isclose(image.xres, 2400)


def test_overlay(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'overlay.pdf', outpdf, '--skip-text', env=spoof_tesseract_noop
    )


def test_destination_not_writable(spoof_tesseract_noop, resources, outdir):
    if os.name != 'nt' and (os.getuid() == 0 or os.geteuid() == 0):
        pytest.xfail(reason="root can write to anything")
    protected_file = outdir / 'protected.pdf'
    protected_file.touch()
    protected_file.chmod(0o400)  # Read-only
    p, out, err = run_ocrmypdf(
        resources / 'jbig2.pdf', protected_file, env=spoof_tesseract_noop
    )
    assert p.returncode == ExitCode.file_access_error, "Expected error"


def test_tesseract_config_valid(resources, outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write(
            '''\
load_system_dawg 0
language_model_penalty_non_dict_word 0
language_model_penalty_non_freq_dict_word 0
'''
        )

    check_ocrmypdf(
        resources / '3small.pdf',
        outdir / 'out.pdf',
        '--tesseract-config',
        cfg_file,
        '--pages',
        '1',
    )


@pytest.mark.slow  # This test sometimes times out in CI
@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_config_invalid(renderer, resources, outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write(
            '''\
THIS FILE IS INVALID
'''
        )

    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf',
        outdir / 'out.pdf',
        '--pdf-renderer',
        renderer,
        '--tesseract-config',
        cfg_file,
    )
    assert (
        "parameter not found" in err.lower()
        or "error occurred while parsing" in err.lower()
    ), "No error message"
    assert p.returncode == ExitCode.invalid_config


@pytest.mark.skipif(not tesseract.has_user_words(), reason='not functional until 4.1.0')
def test_user_words_ocr(resources, outdir):
    # Does not actually test if --user-words causes output to differ
    word_list = outdir / 'wordlist.txt'
    sidecar_after = outdir / 'sidecar.txt'

    with word_list.open('w') as f:
        f.write('cromulent\n')  # a perfectly cromulent word

    check_ocrmypdf(
        resources / 'crom.png',
        outdir / 'out.pdf',
        '--image-dpi',
        150,
        '--sidecar',
        sidecar_after,
        '--user-words',
        word_list,
    )


def test_form_xobject(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'formxobject.pdf', outpdf, '--force-ocr', env=spoof_tesseract_noop
    )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_pagesize_consistency(renderer, resources, outpdf):

    first_page_dimensions = pytest.helpers.first_page_dimensions

    infile = resources / '3small.pdf'

    before_dims = first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        renderer,
        '--clean' if pytest.helpers.have_unpaper() else None,
        '--deskew',
        '--remove-background',
        '--clean-final' if pytest.helpers.have_unpaper() else None,
        '--pages',
        '1',
    )

    after_dims = first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0], rel_tol=1e-4)
    assert isclose(before_dims[1], after_dims[1], rel_tol=1e-4)


def test_skip_big_with_no_images(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'blank.pdf',
        outpdf,
        '--skip-big',
        '5',
        '--force-ocr',
        env=spoof_tesseract_noop,
    )


@pytest.mark.skipif(
    '8.0.0' <= qpdf.version() <= '8.0.1',
    reason="qpdf regression on pages with no contents",
)
def test_no_contents(spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'no_contents.pdf', outpdf, '--force-ocr', env=spoof_tesseract_noop
    )


@pytest.mark.parametrize(
    'image', ['baiona.png', 'baiona_gray.png', 'baiona_alpha.png', 'congress.jpg']
)
def test_compression_preserved(
    spoof_tesseract_noop, ocrmypdf_exec, resources, image, outpdf
):
    input_file = str(resources / image)
    output_file = str(outpdf)

    im = Image.open(input_file)
    # Runs: ocrmypdf - output.pdf < testfile
    with open(input_file, 'rb') as input_stream:
        p_args = ocrmypdf_exec + [
            '--optimize',
            '0',
            '--image-dpi',
            '150',
            '--output-type',
            'pdf',
            '-',
            output_file,
        ]
        p = run(
            p_args,
            stdout=PIPE,
            stderr=PIPE,
            stdin=input_stream,
            universal_newlines=True,
            env=spoof_tesseract_noop,
        )

        if im.mode in ('RGBA', 'LA'):
            # If alpha image is input, expect an error
            assert p.returncode != ExitCode.ok and 'alpha' in p.stderr
            return

        assert p.returncode == ExitCode.ok, p.stderr

    pdfinfo = PdfInfo(output_file)

    pdfimage = pdfinfo[0].images[0]

    if input_file.endswith('.png'):
        assert pdfimage.enc != Encoding.jpeg, "Lossless compression changed to lossy!"
    elif input_file.endswith('.jpg'):
        assert pdfimage.enc == Encoding.jpeg, "Lossy compression changed to lossless!"
    if im.mode.startswith('RGB') or im.mode.startswith('BGR'):
        assert pdfimage.color == Colorspace.rgb, "Colorspace changed"
    elif im.mode.startswith('L'):
        assert pdfimage.color == Colorspace.gray, "Colorspace changed"
    im.close()


@pytest.mark.parametrize(
    'image,compression',
    [
        ('baiona.png', 'jpeg'),
        ('baiona_gray.png', 'lossless'),
        ('congress.jpg', 'lossless'),
    ],
)
def test_compression_changed(
    spoof_tesseract_noop, ocrmypdf_exec, resources, image, compression, outpdf
):
    input_file = str(resources / image)
    output_file = str(outpdf)

    im = Image.open(input_file)

    # Runs: ocrmypdf - output.pdf < testfile
    with open(input_file, 'rb') as input_stream:
        p_args = ocrmypdf_exec + [
            '--image-dpi',
            '150',
            '--output-type',
            'pdfa',
            '--optimize',
            '0',
            '--pdfa-image-compression',
            compression,
            '-',
            output_file,
        ]
        p = run(
            p_args,
            stdout=PIPE,
            stderr=PIPE,
            stdin=input_stream,
            universal_newlines=True,
            env=spoof_tesseract_noop,
        )
        assert p.returncode == ExitCode.ok, p.stderr

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
        assert pdfimage.color == Colorspace.rgb, "Colorspace changed"
    elif im.mode.startswith('L'):
        assert pdfimage.color == Colorspace.gray, "Colorspace changed"
    im.close()


def test_sidecar_pagecount(spoof_tesseract_cache, resources, outpdf):
    sidecar = outpdf.with_suffix('.txt')
    check_ocrmypdf(
        resources / '3small.pdf',
        outpdf,
        '--skip-text',
        '--sidecar',
        sidecar,
        env=spoof_tesseract_cache,
    )

    pdfinfo = PdfInfo(resources / '3small.pdf')
    num_pages = len(pdfinfo)

    with open(sidecar, 'r', encoding='utf-8') as f:
        ocr_text = f.read()

    # There should a formfeed between each pair of pages, so the count of
    # formfeeds is the page count less one
    assert (
        ocr_text.count('\f') == num_pages - 1
    ), "Sidecar page count does not match PDF page count"


def test_sidecar_nonempty(spoof_tesseract_cache, resources, outpdf):
    sidecar = outpdf.with_suffix('.txt')
    check_ocrmypdf(
        resources / 'ccitt.pdf', outpdf, '--sidecar', sidecar, env=spoof_tesseract_cache
    )

    with open(sidecar, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    assert 'the' in ocr_text


@pytest.mark.parametrize('pdfa_level', ['1', '2', '3'])
def test_pdfa_n(spoof_tesseract_cache, pdfa_level, resources, outpdf):
    if pdfa_level == '3' and ghostscript.version() < '9.19':
        pytest.xfail(reason='Ghostscript >= 9.19 required')

    check_ocrmypdf(
        resources / 'ccitt.pdf',
        outpdf,
        '--output-type',
        'pdfa-' + pdfa_level,
        env=spoof_tesseract_cache,
    )

    pdfa_info = file_claims_pdfa(outpdf)
    assert pdfa_info['conformance'] == f'PDF/A-{pdfa_level}B'


@pytest.mark.skipif(
    PIL.__version__ < '5.0.0', reason="Pillow < 5.0.0 doesn't raise the exception"
)
@pytest.mark.slow
def test_decompression_bomb(resources, outpdf):
    p, out, err = run_ocrmypdf(resources / 'hugemono.pdf', outpdf)
    assert 'decompression bomb' in err

    p, out, err = run_ocrmypdf(
        resources / 'hugemono.pdf', outpdf, '--max-image-mpixels', '2000'
    )
    assert p.returncode == 0


def test_text_curves(spoof_tesseract_noop, resources, outpdf):
    with patch('ocrmypdf._pipeline.VECTOR_PAGE_DPI', 100):
        check_ocrmypdf(resources / 'vector.pdf', outpdf, env=spoof_tesseract_noop)

        info = PdfInfo(outpdf)
        assert len(info.pages[0].images) == 0, "added images to the vector PDF"

        check_ocrmypdf(
            resources / 'vector.pdf', outpdf, '--force-ocr', env=spoof_tesseract_noop
        )

        info = PdfInfo(outpdf)
        assert len(info.pages[0].images) != 0, "force did not rasterize"


def test_output_is_dir(spoof_tesseract_noop, resources, outdir):
    p, out, err = run_ocrmypdf(
        resources / 'trivial.pdf', outdir, '--force-ocr', env=spoof_tesseract_noop
    )
    assert p.returncode == ExitCode.file_access_error
    assert 'is not a writable file' in err


@pytest.mark.skipif(os.name == 'nt', reason="symlink needs admin permissions")
def test_output_is_symlink(spoof_tesseract_noop, resources, outdir):
    sym = Path(outdir / 'this_is_a_symlink')
    sym.symlink_to(outdir / 'out.pdf')
    p, out, err = run_ocrmypdf(
        resources / 'trivial.pdf', sym, '--force-ocr', env=spoof_tesseract_noop
    )
    assert p.returncode == ExitCode.ok, err
    assert (outdir / 'out.pdf').stat().st_size > 0, 'target file not created'


def test_livecycle(resources, no_outpdf):
    p, _, err = run_ocrmypdf(resources / 'livecycle.pdf', no_outpdf)

    assert p.returncode == ExitCode.input_file, err


def test_version_check():
    from ocrmypdf.exec import get_version

    with pytest.raises(MissingDependencyError):
        get_version('NOT_FOUND_UNLIKELY_ON_PATH')

    with pytest.raises(MissingDependencyError):
        get_version('sh', version_arg='-c')

    with pytest.raises(MissingDependencyError):
        get_version('echo')


@pytest.mark.parametrize(
    'threshold, optimize, output_type, expected',
    [
        [1.0, 0, 'pdfa', False],
        [1.0, 0, 'pdf', False],
        [0.0, 0, 'pdfa', True],
        [0.0, 0, 'pdf', True],
        [1.0, 1, 'pdfa', False],
        [1.0, 1, 'pdf', False],
        [0.0, 1, 'pdfa', True],
        [0.0, 1, 'pdf', True],
    ],
)
def test_fast_web_view(
    spoof_tesseract_noop, resources, outpdf, threshold, optimize, output_type, expected
):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--fast-web-view',
        threshold,
        '--optimize',
        optimize,
        '--output-type',
        output_type,
        env=spoof_tesseract_noop,
    )
    with pikepdf.open(outpdf) as pdf:
        assert pdf.is_linearized == expected


def test_image_dpi_not_image(caplog, spoof_tesseract_noop, resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--image-dpi',
        '100',
        env=spoof_tesseract_noop,
    )
    assert '--image-dpi is being ignored' in caplog.text
