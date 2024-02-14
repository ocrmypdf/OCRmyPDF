# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os
import shutil
import sys
from math import isclose
from pathlib import Path
from subprocess import run
from unittest.mock import patch

import pikepdf
import pytest
from PIL import Image

import ocrmypdf
from ocrmypdf._exec import tesseract
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
def test_maximum_options(renderer, output_type, multipage, outpdf):
    check_ocrmypdf(
        multipage,
        outpdf,
        '-d',
        '-ci' if have_unpaper() else None,
        '-f',
        '-k',
        '--oversample',
        '300',
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


@pytest.mark.skipif(
    tesseract.version() >= tesseract.TesseractVersion('5'),
    reason="tess 5 tries harder to find its files",
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
    exitcode = run_ocrmypdf_api(
        resources / 'blank.pdf',
        no_outpdf,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert exitcode == ExitCode.child_process_error
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
    with pytest.raises(MissingDependencyError):
        run_ocrmypdf_api(resources / 'francais.pdf', outpdf, '-l', 'klz')


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


def test_tesseract_oem(resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--tesseract-oem',
        '1',
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )


@pytest.mark.parametrize('value', ['auto', 'otsu', 'adaptive-otsu', 'sauvola'])
def test_tesseract_thresholding(value, resources, outpdf):
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--tesseract-thresholding',
        value,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )


@pytest.mark.parametrize('value', ['abcxyz'])
def test_tesseract_thresholding_invalid(value, resources, no_outpdf):
    with pytest.raises(SystemExit, match='2'):
        run_ocrmypdf_api(
            resources / 'trivial.pdf',
            no_outpdf,
            '--tesseract-thresholding',
            value,
            '--plugin',
            'tests/plugins/tesseract_cache.py',
        )


@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_crash(renderer, resources, no_outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'ccitt.pdf',
        no_outpdf,
        '-v',
        '1',
        '--pdf-renderer',
        renderer,
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert exitcode == ExitCode.child_process_error
    assert not no_outpdf.exists()
    assert "SubprocessOutputError" in caplog.text


def test_tesseract_crash_autorotate(resources, no_outpdf, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'ccitt.pdf',
        no_outpdf,
        '-r',
        '--plugin',
        'tests/plugins/tesseract_crash.py',
    )
    assert exitcode == ExitCode.child_process_error
    assert not no_outpdf.exists()
    assert "uncaught exception" in caplog.text


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


@pytest.mark.parametrize('encryption_level', [2, 3, 4, 6])
def test_encrypted(resources, outpdf, encryption_level, caplog):
    if os.name == 'darwin' and sys.version_info >= (3, 12) and encryption_level <= 4:
        # Error is: RuntimeError: unable to load openssl legacy provider
        # pikepdf obtains encryption from qpdf, which gets it from openssl among other
        # providers.
        # Error message itself comes from here:
        # https://github.com/qpdf/qpdf/blob/da3eae39c8e5261196bbc1b460e5b556c6836dbf/libqpdf/QPDFCrypto_openssl.cc#L56
        # Somehow pikepdf + Python 3.12 + macOS does not have this problem, despite
        # using Homebrew's qpdf. Possibly the difference is that pikepdf's Python 3.12
        # comes from cibuildwheel, and our macOS Python 3.12 comes from GitHub Actions
        # setup-python. It may be necessary to build a custom qpdf for macOS.
        # In any case, OCRmyPDF doesn't support loading encrypted files at all, it
        # just complains about encryption, and it's using pikepdf to generate encrypted
        # files for testing.
        pytest.skip("GitHub Python 3.12 on macOS does not have openssl legacy support")
    encryption = pikepdf.models.encryption.Encryption(
        owner='ocrmypdf',
        user='ocrmypdf',
        R=encryption_level,
        aes=(encryption_level >= 4),
        metadata=(encryption_level == 6),
    )

    with pikepdf.open(resources / 'jbig2.pdf') as pdf:
        pdf.save(outpdf, encryption=encryption)

    exitcode = run_ocrmypdf_api(
        outpdf,
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.encrypted_pdf
    assert 'encryption must be removed' in caplog.text


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
    """Checks for a Decimal quantize error with high DPI, etc."""
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


@pytest.fixture
def protected_file(outdir):
    protected_file = outdir / 'protected.pdf'
    protected_file.touch()
    protected_file.chmod(0o400)  # Read-only
    yield protected_file


@pytest.mark.skipif(
    os.name == 'nt' or os.geteuid() == 0, reason="root can write to anything"
)
def test_destination_not_writable(resources, protected_file):
    exitcode = run_ocrmypdf_api(
        resources / 'jbig2.pdf',
        protected_file,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.file_access_error


@pytest.fixture
def valid_tess_config(outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write(
            '''\
load_system_dawg 0
language_model_penalty_non_dict_word 0
language_model_penalty_non_freq_dict_word 0
'''
        )
    yield cfg_file


def test_tesseract_config_valid(resources, valid_tess_config, outpdf):
    check_ocrmypdf(
        resources / '3small.pdf',
        outpdf,
        '--tesseract-config',
        valid_tess_config,
        '--pages',
        '1',
    )


@pytest.fixture
def invalid_tess_config(outdir):
    cfg_file = outdir / 'test.cfg'
    with cfg_file.open('w') as f:
        f.write(
            '''\
THIS FILE IS INVALID
'''
        )
    yield cfg_file


@pytest.mark.slow  # This test sometimes times out in CI
@pytest.mark.parametrize('renderer', RENDERERS)
def test_tesseract_config_invalid(renderer, resources, invalid_tess_config, outpdf):
    p = run_ocrmypdf(
        resources / 'ccitt.pdf',
        outpdf,
        '--pdf-renderer',
        renderer,
        '--tesseract-config',
        invalid_tess_config,
    )
    assert (
        "parameter not found" in p.stderr.lower()
        or "error occurred while parsing" in p.stderr.lower()
    ), "No error message"
    assert p.returncode == ExitCode.invalid_config


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
        # '--remove-background',
        '--clean-final' if have_unpaper() else None,
        '-k',
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


def test_no_contents(resources, outpdf):
    check_ocrmypdf(
        resources / 'no_contents.pdf',
        outpdf,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )


@pytest.mark.parametrize(
    'image', ['baiona.png', 'baiona_gray.png', 'baiona_alpha.png', 'baiona_color.jpg']
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
            capture_output=True,
            stdin=input_stream,
            text=True,
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
        ('baiona_color.jpg', 'lossless'),
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
            capture_output=True,
            stdin=input_stream,
            text=True,
            check=False,
        )
        assert p.returncode == ExitCode.ok, p.stderr

    pdfinfo = PdfInfo(output_file)

    pdfimage = pdfinfo[0].images[0]

    if compression == "jpeg":
        assert pdfimage.enc == Encoding.jpeg
    else:
        if image.endswith('jpg'):
            # Ghostscript JPEG passthrough - no issue
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

    with open(sidecar, encoding='utf-8') as f:
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

    with open(sidecar, encoding='utf-8') as f:
        ocr_text = f.read()
    assert 'the' in ocr_text


@pytest.mark.parametrize('pdfa_level', ['1', '2', '3'])
def test_pdfa_n(pdfa_level, resources, outpdf):
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


def test_decompression_bomb_error(resources, outpdf, caplog):
    run_ocrmypdf_api(resources / 'hugemono.pdf', outpdf)
    assert 'decompression bomb' in caplog.text
    assert 'max-image-mpixels' in caplog.text


@pytest.mark.slow
def test_decompression_bomb_succeeds(resources, outpdf):
    exitcode = run_ocrmypdf_api(
        resources / 'hugemono.pdf', outpdf, '--max-image-mpixels', '2000'
    )
    assert exitcode == 0


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


def test_text_curves_force(resources, outpdf):
    with patch('ocrmypdf._pipeline.VECTOR_PAGE_DPI', 100):
        check_ocrmypdf(
            resources / 'vector.pdf',
            outpdf,
            '--force-ocr',
            '--plugin',
            'tests/plugins/tesseract_noop.py',
        )

        info = PdfInfo(outpdf)
        assert len(info.pages[0].images) != 0, "force did not rasterize"


def test_output_is_dir(resources, outdir, caplog):
    exitcode = run_ocrmypdf_api(
        resources / 'trivial.pdf',
        outdir,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.file_access_error
    assert 'is not a writable file' in caplog.text


@pytest.mark.skipif(os.name == 'nt', reason="symlink needs admin permissions")
def test_output_is_symlink(resources, outdir):
    sym = Path(outdir / 'this_is_a_symlink')
    sym.symlink_to(outdir / 'out.pdf')
    exitcode = run_ocrmypdf_api(
        resources / 'trivial.pdf',
        sym,
        '--force-ocr',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.ok
    assert (outdir / 'out.pdf').stat().st_size > 0, 'target file not created'


def test_livecycle(resources, no_outpdf, caplog):
    exitcode = run_ocrmypdf_api(resources / 'livecycle.pdf', no_outpdf)

    assert exitcode == ExitCode.input_file, caplog.text


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


def test_outputtype_none_bad_setup(resources, outpdf):
    p = run_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--output-type=none',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert p.returncode == ExitCode.bad_args
    assert 'Set the output file to' in p.stderr


def test_outputtype_none(resources, outtxt):
    exitcode = run_ocrmypdf_api(
        resources / 'trivial.pdf',
        '-',
        '--output-type=none',
        '--sidecar',
        outtxt,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    assert exitcode == ExitCode.ok
    assert outtxt.exists()


@pytest.fixture
def graph_bad_icc(resources, outdir):
    synth_input_file = outdir / 'graph-bad-icc.pdf'
    with pikepdf.open(resources / 'graph.pdf') as pdf:
        icc = pdf.make_stream(
            b'invalid icc profile', N=3, Alternate=pikepdf.Name.DeviceRGB
        )
        pdf.pages[0].Resources.XObject['/Im0'].ColorSpace = pikepdf.Array(
            [pikepdf.Name.ICCBased, icc]
        )
        pdf.save(synth_input_file)
        yield synth_input_file


def test_corrupt_icc(graph_bad_icc, outpdf, caplog):
    result = run_ocrmypdf_api(graph_bad_icc, outpdf)
    assert result == ExitCode.ok
    assert any(
        'corrupt or unreadable ICC profile' in rec.message for rec in caplog.records
    )
