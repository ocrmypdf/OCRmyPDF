# © 2015-19 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


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
from ocrmypdf._exec import ghostscript, tesseract
from ocrmypdf.exceptions import ExitCode, MissingDependencyError
from ocrmypdf.pdfa import file_claims_pdfa
from ocrmypdf.pdfinfo import Colorspace, Encoding, PdfInfo
from ocrmypdf.subprocess import get_version

from .conftest import (
    check_ocrmypdf,
    first_page_dimensions,
    have_unpaper,
    is_macos,
    run_ocrmypdf,
    run_ocrmypdf_api,
    running_in_docker,
)

# pylint: disable=redefined-outer-name


RENDERERS = ['hocr', 'sandwich']


def test_quick(resources, outpdf):
    check_ocrmypdf(
        resources / 'ccitt.pdf', outpdf, '--plugin', 'tests/plugins/tesseract_cache.py'
    )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_oversample(renderer, resources, outpdf):
    oversampled_pdf = check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--oversample',
        '350',
        '-f',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    pdfinfo = PdfInfo(oversampled_pdf)

    print(pdfinfo[0].dpi.x)
    assert abs(pdfinfo[0].dpi.x - 350) < 1


def test_repeat_ocr(resources, no_outpdf):
    result = run_ocrmypdf_api(resources / 'graph_ocred.pdf', no_outpdf)
    assert result == ExitCode.already_done_ocr


def test_force_ocr(resources, outpdf):
    out = check_ocrmypdf(
        resources / 'graph_ocred.pdf',
        outpdf,
        '-f',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(out)
    assert pdfinfo[0].has_text


def test_skip_ocr(resources, outpdf):
    out = check_ocrmypdf(
        resources / 'graph_ocred.pdf',
        outpdf,
        '-s',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(out)
    assert pdfinfo[0].has_text


def test_redo_ocr(resources, outpdf):
    in_ = resources / 'graph_ocred.pdf'
    before = PdfInfo(in_, detailed_analysis=True)
    out = outpdf
    out = check_ocrmypdf(in_, out, '--redo-ocr')
    after = PdfInfo(out, detailed_analysis=True)
    assert before[0].has_text and after[0].has_text
    assert (
        before[0].get_textareas() != after[0].get_textareas()
    ), "Expected text to be different after re-OCR"


def test_argsfile(resources, outdir):
    path_argsfile = outdir / 'test_argsfile.txt'
    with open(str(path_argsfile), 'w') as argsfile:
        print(
            '--title',
            'ArgsFile Test',
            '--author',
            'Test Cases',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            sep='\n',
            end='\n',
            file=argsfile,
        )
    check_ocrmypdf(
        resources / 'graph.pdf', path_argsfile, '@' + str(outdir / 'test_argsfile.txt')
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


def test_skip_big(resources, outpdf):
    out = check_ocrmypdf(
        resources / 'jbig2.pdf',
        outpdf,
        '--skip-big',
        '1',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(out)
    assert not pdfinfo[0].has_text


@pytest.mark.parametrize('renderer', RENDERERS)
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_maximum_options(renderer, output_type, resources, outpdf):
    check_ocrmypdf(
        resources / 'multipage.pdf',
        outpdf,
        '-d',
        '-ci' if have_unpaper() else None,
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
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )


def test_tesseract_missing_tessdata(monkeypatch, resources, no_outpdf, tmpdir):
    monkeypatch.setenv("TESSDATA_PREFIX", os.fspath(tmpdir))
    with pytest.raises(MissingDependencyError):
        run_ocrmypdf_api(resources / 'graph.pdf', no_outpdf, '-v', '1', '--skip-text')


def test_invalid_input_pdf(resources, no_outpdf):
    result = run_ocrmypdf_api(resources / 'invalid.pdf', no_outpdf)
    assert result == ExitCode.input_file


def test_blank_input_pdf(resources, outpdf):
    result = run_ocrmypdf_api(resources / 'blank.pdf', outpdf)
    assert result == ExitCode.ok


def test_force_ocr_on_pdf_with_no_images(resources, no_outpdf):
    # As a correctness test, make sure that --force-ocr on a PDF with no
    # content still triggers tesseract. If tesseract crashes, then it was
    # called.
    p, _, _ = run_ocrmypdf(
        resources / 'blank.pdf',
        no_outpdf,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert p.returncode == ExitCode.child_process_error
    assert not no_outpdf.exists()


@pytest.mark.skipif(
    is_macos(),
    reason="takes too long to install language packs in macOS homebrew",
)
def test_german(resources, outdir):
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
            '--plugin',
            'tests/plugins/tesseract_cache.py',
        )
    except MissingDependencyError:
        if 'deu' not in tesseract.get_languages():
            pytest.xfail(reason="tesseract-deu language pack not installed")
        raise


def test_klingon(resources, outpdf):
    p, _, _ = run_ocrmypdf(resources / 'francais.pdf', outpdf, '-l', 'klz')
    assert p.returncode == ExitCode.missing_dependency


def test_missing_docinfo(resources, outpdf):
    result = run_ocrmypdf_api(
        resources / 'missing_docinfo.pdf',
        outpdf,
        '-l',
        'eng',
        '--skip-text',
        '--plugin',
        Path('tests/plugins/tesseract_noop.py'),
    )
    assert result == ExitCode.ok


def test_uppercase_extension(resources, outdir):
    shutil.copy(str(resources / "skew.pdf"), str(outdir / "UPPERCASE.PDF"))

    check_ocrmypdf(
        outdir / "UPPERCASE.PDF",
        outdir / "UPPERCASE_OUT.PDF",
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


def test_input_file_not_found(caplog, no_outpdf):
    input_file = "does not exist.pdf"
    result = run_ocrmypdf_api(input_file, no_outpdf)
    assert result == ExitCode.input_file
    assert input_file in caplog.text


@pytest.mark.skipif(os.name == 'nt' or running_in_docker(), reason="chmod")
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
def test_pagesegmode(renderer, resources, outpdf):
    check_ocrmypdf(
        resources / 'skew.pdf',
        outpdf,
        '--tesseract-pagesegmode',
        '7',
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_crash(renderer, resources, no_outpdf):
    p, _, err = run_ocrmypdf(
        resources / 'ccitt.pdf',
        no_outpdf,
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert p.returncode == ExitCode.child_process_error
    assert not no_outpdf.exists()
    assert "SubprocessOutputError" in err


def test_tesseract_crash_autorotate(resources, no_outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'ccitt.pdf',
        no_outpdf,
        '-r',
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert p.returncode == ExitCode.child_process_error
    assert not no_outpdf.exists()
    assert "uncaught exception" in err
    print(out)
    print(err)


@pytest.mark.parametrize('renderer', RENDERERS)
@pytest.mark.slow
def test_tesseract_image_too_big(renderer, resources, outpdf):
    check_ocrmypdf(
        resources / 'hugemono.pdf',
        outpdf,
        '-r',
        '--pdf-renderer',
        renderer,
        '--max-image-mpixels',
        '0',
        '--plugin',
        'tests/plugins/tesseract_big_image_error.py',
    )


def test_algo4(resources, outpdf):
    p, _, _ = run_ocrmypdf(
        resources / 'encrypted_algo4.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == ExitCode.encrypted_pdf


def test_jbig2_passthrough(resources, outpdf):
    out = check_ocrmypdf(
        resources / 'jbig2.pdf',
        outpdf,
        '--output-type',
        'pdf',
        '--pdf-renderer',
        'hocr',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    out_pageinfo = PdfInfo(out)
    assert out_pageinfo[0].images[0].enc == Encoding.jbig2


def test_masks(resources, outpdf):
    assert (
        ocrmypdf.ocr(
            resources / 'masks.pdf', outpdf, plugins=['tests/plugins/tesseract_noop.py']
        )
        == ExitCode.ok
    )


def test_linearized_pdf_and_indirect_object(resources, outpdf):
    check_ocrmypdf(
        resources / 'epson.pdf', outpdf, '--plugin', 'tests/plugins/tesseract_noop.py'
    )


def test_very_high_dpi(resources, outpdf):
    "Checks for a Decimal quantize error with high DPI, etc"
    check_ocrmypdf(
        resources / '2400dpi.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )
    pdfinfo = PdfInfo(outpdf)

    image = pdfinfo[0].images[0]
    assert isclose(image.dpi.x, image.dpi.y)
    assert isclose(image.dpi.x, 2400)


def test_overlay(resources, outpdf):
    check_ocrmypdf(
        resources / 'overlay.pdf',
        outpdf,
        '--skip-text',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


def test_destination_not_writable(resources, outdir):
    if os.name != 'nt' and (os.getuid() == 0 or os.geteuid() == 0):
        pytest.xfail(reason="root can write to anything")
    protected_file = outdir / 'protected.pdf'
    protected_file.touch()
    protected_file.chmod(0o400)  # Read-only
    p, _out, _err = run_ocrmypdf(
        resources / 'jbig2.pdf',
        protected_file,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
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

    p, _out, err = run_ocrmypdf(
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


def test_form_xobject(resources, outpdf):
    check_ocrmypdf(
        resources / 'formxobject.pdf',
        outpdf,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_pagesize_consistency(renderer, resources, outpdf):
    infile = resources / '3small.pdf'

    before_dims = first_page_dimensions(infile)

    check_ocrmypdf(
        infile,
        outpdf,
        '--pdf-renderer',
        renderer,
        '--clean' if have_unpaper() else None,
        '--deskew',
        '--remove-background',
        '--clean-final' if have_unpaper() else None,
        '--pages',
        '1',
    )

    after_dims = first_page_dimensions(outpdf)

    assert isclose(before_dims[0], after_dims[0], rel_tol=1e-4)
    assert isclose(before_dims[1], after_dims[1], rel_tol=1e-4)


def test_skip_big_with_no_images(resources, outpdf):
    check_ocrmypdf(
        resources / 'blank.pdf',
        outpdf,
        '--skip-big',
        '5',
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@pytest.mark.skipif(
    '8.0.0' <= pikepdf.__libqpdf_version__ <= '8.0.1',
    reason="libqpdf regression on pages with no contents",
)
def test_no_contents(resources, outpdf):
    check_ocrmypdf(
        resources / 'no_contents.pdf',
        outpdf,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@pytest.mark.parametrize(
    'image', ['baiona.png', 'baiona_gray.png', 'baiona_alpha.png', 'congress.jpg']
)
def test_compression_preserved(ocrmypdf_exec, resources, image, outpdf):
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
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '-',
            output_file,
        ]
        p = run(
            p_args,
            stdout=PIPE,
            stderr=PIPE,
            stdin=input_stream,
            universal_newlines=True,  # When dropping support for Python 3.6 change to text=
            check=False,
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
def test_compression_changed(ocrmypdf_exec, resources, image, compression, outpdf):
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
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '-',
            output_file,
        ]
        p = run(
            p_args,
            stdout=PIPE,
            stderr=PIPE,
            stdin=input_stream,
            universal_newlines=True,  # When dropping support for Python 3.6 change to text=
            check=False,
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


def test_sidecar_pagecount(resources, outpdf):
    sidecar = outpdf.with_suffix('.txt')
    check_ocrmypdf(
        resources / '3small.pdf',
        outpdf,
        '--skip-text',
        '--sidecar',
        sidecar,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
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


def test_sidecar_nonempty(resources, outpdf):
    sidecar = outpdf.with_suffix('.txt')
    check_ocrmypdf(
        resources / 'ccitt.pdf',
        outpdf,
        '--sidecar',
        sidecar,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    with open(sidecar, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    assert 'the' in ocr_text


@pytest.mark.parametrize('pdfa_level', ['1', '2', '3'])
def test_pdfa_n(pdfa_level, resources, outpdf):
    if pdfa_level == '3' and ghostscript.version() < '9.19':
        pytest.xfail(reason='Ghostscript >= 9.19 required')

    check_ocrmypdf(
        resources / 'ccitt.pdf',
        outpdf,
        '--output-type',
        'pdfa-' + pdfa_level,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )

    pdfa_info = file_claims_pdfa(outpdf)
    assert pdfa_info['conformance'] == f'PDF/A-{pdfa_level}B'


@pytest.mark.skipif(
    PIL.__version__ < '5.0.0', reason="Pillow < 5.0.0 doesn't raise the exception"
)
@pytest.mark.slow
def test_decompression_bomb(resources, outpdf):
    p, _out, err = run_ocrmypdf(resources / 'hugemono.pdf', outpdf)
    assert 'decompression bomb' in err

    p, _out, err = run_ocrmypdf(
        resources / 'hugemono.pdf', outpdf, '--max-image-mpixels', '2000'
    )
    assert p.returncode == 0


def test_text_curves(resources, outpdf):
    with patch('ocrmypdf._pipeline.VECTOR_PAGE_DPI', 100):
        check_ocrmypdf(
            resources / 'vector.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

        info = PdfInfo(outpdf)
        assert len(info.pages[0].images) == 0, "added images to the vector PDF"

        check_ocrmypdf(
            resources / 'vector.pdf',
            outpdf,
            '--force-ocr',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

        info = PdfInfo(outpdf)
        assert len(info.pages[0].images) != 0, "force did not rasterize"


def test_output_is_dir(resources, outdir):
    p, _out, err = run_ocrmypdf(
        resources / 'trivial.pdf',
        outdir,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == ExitCode.file_access_error
    assert 'is not a writable file' in err


@pytest.mark.skipif(os.name == 'nt', reason="symlink needs admin permissions")
def test_output_is_symlink(resources, outdir):
    sym = Path(outdir / 'this_is_a_symlink')
    sym.symlink_to(outdir / 'out.pdf')
    p, _out, err = run_ocrmypdf(
        resources / 'trivial.pdf',
        sym,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == ExitCode.ok, err
    assert (outdir / 'out.pdf').stat().st_size > 0, 'target file not created'


def test_livecycle(resources, no_outpdf):
    p, _, err = run_ocrmypdf(resources / 'livecycle.pdf', no_outpdf)

    assert p.returncode == ExitCode.input_file, err


def test_version_check():
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
def test_fast_web_view(resources, outpdf, threshold, optimize, output_type, expected):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--fast-web-view',
        threshold,
        '--optimize',
        optimize,
        '--output-type',
        output_type,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    with pikepdf.open(outpdf) as pdf:
        assert pdf.is_linearized == expected


def test_image_dpi_not_image(caplog, resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--image-dpi',
        '100',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert '--image-dpi is being ignored' in caplog.text


def test_image_dpi_threshold(resources, outpdf):
    check_ocrmypdf(
        resources / 'typewriter.png',
        outpdf,
        '--threshold',
        '--image-dpi=170',
        '--output-type=pdf',
        '--optimize=0',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert outpdf.exists()
