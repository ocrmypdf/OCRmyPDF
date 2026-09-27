# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import os
import re
from io import BytesIO

import pikepdf
import pytest
from pikepdf import Name
from pikepdf.pdfa import validate_written

from ocrmypdf.exceptions import ExitCode, MissingDependencyError
from ocrmypdf.pdfa import (
    add_simple_font_tounicode,
    file_claims_pdfa,
    find_nonembedded_cid_fonts,
    find_nonembedded_fonts,
    has_embedded_fonts,
    is_standard14_font,
)

from .conftest import check_ocrmypdf, run_ocrmypdf_api


def _make_cid_font(
    pdf: pikepdf.Pdf, *, embedded: bool, basefont: str | pikepdf.Object
) -> pikepdf.Object:
    """Build a Type0/CID font object, optionally embedding glyph data."""
    if isinstance(basefont, str):
        basefont = Name(basefont)
    descriptor = pikepdf.Dictionary(
        Type=Name.FontDescriptor, FontName=basefont, Flags=4
    )
    if embedded:
        # The actual bytes do not matter; only the presence of FontFile2 marks
        # the CID font as embedded.
        descriptor.FontFile2 = pdf.make_stream(b'\x00\x01\x00\x00 fake font program')
    cidfont = pdf.make_indirect(
        pikepdf.Dictionary(
            Type=Name.Font,
            Subtype=Name.CIDFontType2,
            BaseFont=basefont,
            FontDescriptor=descriptor,
            CIDSystemInfo=pikepdf.Dictionary(
                Registry='Adobe', Ordering='Identity', Supplement=0
            ),
        )
    )
    return pdf.make_indirect(
        pikepdf.Dictionary(
            Type=Name.Font,
            Subtype=Name.Type0,
            BaseFont=basefont,
            Encoding=Name.Identity_H,
            DescendantFonts=pikepdf.Array([cidfont]),
        )
    )


def _write_cid_font_pdf(path, *, embedded: bool, basefont='/ABCDEF+TestCID'):
    with pikepdf.new() as pdf:
        page = pdf.add_blank_page()
        font = _make_cid_font(pdf, embedded=embedded, basefont=basefont)
        page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F0=font))
        pdf.save(path)


class TestFindNonembeddedCidFonts:
    def test_blank_page_reports_nothing(self, tmp_path):
        path = tmp_path / 'blank.pdf'
        with pikepdf.new() as pdf:
            pdf.add_blank_page()
            pdf.save(path)
        with pikepdf.open(path) as pdf:
            assert find_nonembedded_cid_fonts(pdf) == set()

    def test_detects_nonembedded_cid_font(self, tmp_path):
        path = tmp_path / 'nonembedded.pdf'
        _write_cid_font_pdf(path, embedded=False)
        with pikepdf.open(path) as pdf:
            assert find_nonembedded_cid_fonts(pdf) == {'ABCDEF+TestCID'}

    def test_ignores_embedded_cid_font(self, tmp_path):
        path = tmp_path / 'embedded.pdf'
        _write_cid_font_pdf(path, embedded=True)
        with pikepdf.open(path) as pdf:
            assert find_nonembedded_cid_fonts(pdf) == set()

    def test_detects_nonembedded_cid_font_in_form_xobject(self, tmp_path):
        path = tmp_path / 'xobject.pdf'
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            font = _make_cid_font(pdf, embedded=False, basefont='/ZZZ+Hidden')
            form = pdf.make_stream(
                b'',
                Type=Name.XObject,
                Subtype=Name.Form,
                BBox=pikepdf.Array([0, 0, 1, 1]),
                Resources=pikepdf.Dictionary(Font=pikepdf.Dictionary(F0=font)),
            )
            page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Fm0=form))
            pdf.save(path)
        with pikepdf.open(path) as pdf:
            assert find_nonembedded_cid_fonts(pdf) == {'ZZZ+Hidden'}

    def test_non_dictionary_font_and_xobject_resources_are_ignored(self, tmp_path):
        # A malformed PDF may carry a /Font or /XObject resource that is not a
        # dictionary (an array, a name, an empty value). Scanning must skip it
        # rather than raise when iterating its values (regression test for the
        # crash reported in issue #1713).
        path = tmp_path / 'malformed_resources.pdf'
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            page.Resources = pikepdf.Dictionary(
                Font=pikepdf.Array([]),
                XObject=pikepdf.Array([]),
            )
            pdf.save(path)
        with pikepdf.open(path) as pdf:
            assert find_nonembedded_cid_fonts(pdf) == set()

    def test_non_utf8_font_name_is_reported(self, tmp_path):
        # PDF name objects are byte sequences with no mandated encoding.
        # Chinese PDFs commonly carry FounderType font names encoded in GBK
        # (here 方正大黑 = b7 bd d5 fd b4 f3 ba da), which is not valid UTF-8,
        # so stringifying the Name raises UnicodeDecodeError (issue #1727).
        # The font must still be reported -- in hex-escaped PDF syntax form --
        # so that PDF/A conversion is refused instead of crashing.
        path = tmp_path / 'gbk_name.pdf'
        gbk_name = pikepdf.Object.parse(b'/#b7#bd#d5#fd#b4#f3#ba#da_GBK+ZEFSzV-12')
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            font = _make_cid_font(pdf, embedded=False, basefont=gbk_name)
            page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F0=font))
            pdf.save(path)
        with pikepdf.open(path) as pdf:
            assert find_nonembedded_cid_fonts(pdf) == {
                '#b7#bd#d5#fd#b4#f3#ba#da_GBK+ZEFSzV-12'
            }

    def test_non_dictionary_font_descriptor_is_reported(self, tmp_path):
        # A Type0 font whose descendant carries a non-dictionary /FontDescriptor
        # has no embedded glyph data, so it must be reported -- not crash. This
        # is the same malformed-resource bug class as #1713, one level deeper:
        # `key in descriptor` raises ValueError on a non-dictionary.
        path = tmp_path / 'bad_descriptor.pdf'
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            cidfont = pdf.make_indirect(
                pikepdf.Dictionary(
                    Type=Name.Font,
                    Subtype=Name.CIDFontType2,
                    BaseFont=Name('/BOGUS+CID'),
                    FontDescriptor=Name.NotADictionary,
                )
            )
            type0 = pdf.make_indirect(
                pikepdf.Dictionary(
                    Type=Name.Font,
                    Subtype=Name.Type0,
                    BaseFont=Name('/BOGUS+CID'),
                    Encoding=Name.Identity_H,
                    DescendantFonts=pikepdf.Array([cidfont]),
                )
            )
            page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F0=type0))
            pdf.save(path)
        with pikepdf.open(path) as pdf:
            assert find_nonembedded_cid_fonts(pdf) == {'BOGUS+CID'}


@pytest.fixture
def nonembedded_cid_pdf(tmp_path):
    """A PDF with a real, non-embedded CID (CJK) text layer, as Acrobat produces."""
    reportlab = pytest.importorskip('reportlab')
    del reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas

    path = tmp_path / 'cjk_nonembedded.pdf'
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))  # Adobe-GB1, not embedded
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont('STSong-Light', 24)
    c.drawString(60, 650, '你好世界')
    c.showPage()
    c.save()
    # Sanity check that we built the structure under test.
    with pikepdf.open(path) as pdf:
        assert find_nonembedded_cid_fonts(pdf)
    return path


def test_pdfa_rejects_nonembedded_cid_font(nonembedded_cid_pdf, outpdf):
    """Explicit PDF/A on a non-embedded CID layer must error, not corrupt it."""
    exitcode = run_ocrmypdf_api(
        nonembedded_cid_pdf,
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--skip-text',
        '--output-type',
        'pdfa',
    )
    assert exitcode == ExitCode.input_file
    assert not outpdf.exists() or outpdf.stat().st_size == 0


def test_auto_downgrades_nonembedded_cid_font_to_pdf(nonembedded_cid_pdf, outpdf):
    """Auto mode preserves the text layer by outputting a regular PDF."""
    check_ocrmypdf(
        nonembedded_cid_pdf,
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--skip-text',
        '--output-type',
        'auto',
    )
    # Not PDF/A, and the original non-embedded layer survived untouched.
    assert not file_claims_pdfa(outpdf)['pass']
    with pikepdf.open(outpdf) as pdf:
        assert find_nonembedded_cid_fonts(pdf)


def test_auto_falls_back_to_ghostscript_for_pdfa(
    resources, outpdf, no_speculative_pdfa
):
    """Auto mode produces PDF/A via Ghostscript when the cheap path can't."""
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--output-type',
        'auto',
    )
    assert file_claims_pdfa(outpdf)['pass']


def test_auto_outputs_pdf_when_ghostscript_unavailable(
    resources, outpdf, monkeypatch, no_speculative_pdfa
):
    """If speculative PDF/A fails and there is no Ghostscript, output a plain PDF."""
    monkeypatch.setattr('ocrmypdf._exec.ghostscript.available', lambda: False)
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--output-type',
        'auto',
    )
    assert not file_claims_pdfa(outpdf)['pass']


def test_auto_degrades_when_ghostscript_cannot_make_pdfa(
    resources, outpdf, no_speculative_pdfa
):
    """If Ghostscript produces non-PDF/A output, auto keeps a plain PDF (no error)."""
    exitcode = run_ocrmypdf_api(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_pdfa_failure.py',
        '--output-type',
        'auto',
    )
    assert exitcode == ExitCode.ok
    assert outpdf.exists()
    assert not file_claims_pdfa(outpdf)['pass']


def test_auto_degrades_when_ghostscript_raises(
    resources, outpdf, monkeypatch, no_speculative_pdfa
):
    """A Ghostscript conversion exception in auto mode degrades to plain PDF."""
    from ocrmypdf.exceptions import ColorConversionNeededError

    monkeypatch.setattr('ocrmypdf._exec.ghostscript.available', lambda: True)

    def boom(*args, **kwargs):
        raise ColorConversionNeededError()

    monkeypatch.setattr('ocrmypdf._pipeline.convert_to_pdfa', boom)
    exitcode = run_ocrmypdf_api(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--output-type',
        'auto',
    )
    assert exitcode == ExitCode.ok
    assert outpdf.exists()
    assert not file_claims_pdfa(outpdf)['pass']


@pytest.mark.parametrize('optimize', (0, 3))
@pytest.mark.parametrize('pdfa_level', (1, 2, 3))
def test_pdfa(resources, outpdf, optimize, pdfa_level):
    try:
        check_ocrmypdf(
            resources / 'francais.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            f'--output-type=pdfa-{pdfa_level}',
            f'--optimize={optimize}',
        )
    except MissingDependencyError as e:
        if 'pngquant' in str(e) and optimize in (2, 3) and os.name == 'nt':
            pytest.xfail("pngquant currently not available on Windows")
    if pdfa_level in (2, 3):
        # PDF/A-2 allows ObjStm
        assert b'/ObjStm' in outpdf.read_bytes()
    elif pdfa_level == 1:
        # PDF/A-1 might allow ObjStm, but Acrobat does not approve it, so
        # we don't use it
        assert b'/ObjStm' not in outpdf.read_bytes()

    with pikepdf.open(outpdf) as pdf, pdf.open_metadata() as m:
        assert m.pdfa_status == f'{pdfa_level}B'


def test_auto_force_ocr_output_is_valid_pdfa(resources, outpdf, monkeypatch):
    """Auto mode makes the force-ocr rebuild PDF/A without Ghostscript."""

    def no_ghostscript(*args, **kwargs):
        raise AssertionError('Ghostscript fallback should not be needed')

    monkeypatch.setattr('ocrmypdf._pipeline._ghostscript_pdfa_fallback', no_ghostscript)
    check_ocrmypdf(
        resources / 'trivial.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--force-ocr',
        '--output-type',
        'auto',
    )
    assert file_claims_pdfa(outpdf)['pass']
    with pikepdf.open(outpdf) as pdf:
        assert '/OutputIntents' in pdf.Root
    report = validate_written(outpdf, '2b')
    assert report.verdict == 'pass', report.summary()


def test_auto_pdfa_without_ghostscript(resources, outpdf, monkeypatch):
    """Without Ghostscript, auto still yields PDF/A if the validator approves."""
    monkeypatch.setattr('ocrmypdf._exec.ghostscript.available', lambda: False)
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--output-type',
        'auto',
    )
    assert file_claims_pdfa(outpdf)['pass']
    report = validate_written(outpdf, '2b')
    assert report.verdict == 'pass', report.summary()


SPECULATIVE_OK = 'Speculative PDF/A conversion succeeded'
GS_ONLY_OPTIONS = [
    pytest.param(('--pdfa-image-compression', 'jpeg'), id='image-compression'),
    pytest.param(('--ghostscript-jpeg-quality', '60'), id='jpeg-quality'),
    pytest.param(('--ghostscript-jpeg-maxdpi', '150'), id='jpeg-maxdpi'),
    pytest.param(('--color-conversion-strategy', 'CMYK'), id='color-cmyk'),
    pytest.param(('--color-conversion-strategy', 'Gray'), id='color-gray'),
    pytest.param(
        ('--color-conversion-strategy', 'UseDeviceIndependentColor'),
        id='color-device-independent',
    ),
]


def _gs_option_label(gs_args):
    """Name an option as the backend messages do, with the value if it matters."""
    if gs_args[0] == '--color-conversion-strategy':
        return ' '.join(gs_args)
    return gs_args[0]


def _options(*args):
    from ocrmypdf.cli import get_options_and_plugins

    return get_options_and_plugins([*args, 'a.pdf', 'b.pdf'])


def _coordinate(options, plugin_manager):
    from ocrmypdf._validation_coordinator import ValidationCoordinator

    ValidationCoordinator(plugin_manager).validate_all_options(options)


def _forbid_ghostscript_pdfa(monkeypatch):
    def no_ghostscript(*args, **kwargs):
        raise AssertionError('Ghostscript must not be used for PDF/A')

    monkeypatch.setattr('ocrmypdf._pipeline.convert_to_pdfa', no_ghostscript)
    monkeypatch.setattr('ocrmypdf._pipeline._ghostscript_pdfa_fallback', no_ghostscript)


@pytest.mark.parametrize('backend', ['auto', 'ghostscript', 'internal'])
def test_pdfa_backend_parsed(backend):
    options, _pm = _options('--pdfa-backend', backend)
    assert options.pdfa_backend == backend


def test_pdfa_backend_default():
    options, _pm = _options()
    assert options.pdfa_backend == 'auto'


def test_pdfa_backend_rejects_unknown_value():
    from ocrmypdf._options import OcrOptions

    with pytest.raises(ValueError, match='pdfa_backend'):
        OcrOptions(input_file='a.pdf', output_file='b.pdf', pdfa_backend='acrobat')


@pytest.mark.parametrize('gs_args', GS_ONLY_OPTIONS)
def test_internal_backend_rejects_ghostscript_options(gs_args):
    from ocrmypdf.exceptions import BadArgsError

    options, pm = _options('--pdfa-backend', 'internal', *gs_args)
    with pytest.raises(
        BadArgsError,
        match=f"{_gs_option_label(gs_args)} has no effect with --pdfa-backend internal",
    ):
        _coordinate(options, pm)


@pytest.mark.parametrize('gs_args', GS_ONLY_OPTIONS)
@pytest.mark.parametrize('output_type', ['auto', 'pdfa-2'])
def test_auto_backend_switches_to_ghostscript(gs_args, output_type, caplog):
    options, pm = _options('--output-type', output_type, *gs_args)
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        _coordinate(options, pm)
    assert options.pdfa_backend == 'ghostscript'
    assert (
        f"{_gs_option_label(gs_args)} requires Ghostscript; using --pdfa-backend "
        "ghostscript" in caplog.text
    )


@pytest.mark.parametrize('strategy', ['LeaveColorUnchanged', 'RGB'])
@pytest.mark.parametrize('backend', ['auto', 'internal'])
def test_internal_path_color_strategies_keep_backend(strategy, backend, caplog):
    options, pm = _options(
        '--output-type',
        'pdfa',
        '--pdfa-backend',
        backend,
        '--color-conversion-strategy',
        strategy,
    )
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        _coordinate(options, pm)
    assert options.pdfa_backend == backend
    assert 'requires Ghostscript' not in caplog.text


def test_image_compression_applies_to_auto_output(caplog):
    options, pm = _options('--output-type', 'auto', '--pdfa-image-compression', 'jpeg')
    with caplog.at_level(logging.WARNING, logger='ocrmypdf'):
        _coordinate(options, pm)
    assert 'only applies' not in caplog.text


def test_auto_backend_stays_auto_without_ghostscript_options():
    options, pm = _options('--pdfa-image-compression', 'auto')
    _coordinate(options, pm)
    assert options.pdfa_backend == 'auto'


def test_ghostscript_backend_requires_ghostscript(monkeypatch):
    from ocrmypdf.builtin_plugins import ghostscript as gs_plugin

    monkeypatch.setattr('ocrmypdf._exec.ghostscript.version', _raise_file_not_found)
    options, _pm = _options('--output-type', 'auto', '--pdfa-backend', 'ghostscript')
    with pytest.raises(MissingDependencyError):
        gs_plugin.check_options(options)
    # The default backend does not need Ghostscript for --output-type auto
    options, _pm = _options('--output-type', 'auto')
    gs_plugin.check_options(options)


def test_internal_backend_does_not_require_ghostscript(monkeypatch):
    from ocrmypdf.builtin_plugins import ghostscript as gs_plugin

    monkeypatch.setattr('ocrmypdf._exec.ghostscript.version', _raise_file_not_found)
    options, _pm = _options('--output-type', 'pdfa', '--pdfa-backend', 'internal')
    gs_plugin.check_options(options)
    assert options.output_type == 'pdfa-2'


def _raise_file_not_found(*args, **kwargs):
    raise FileNotFoundError('gs')


def test_internal_backend_denial_fails(resources, outpdf, caplog, monkeypatch):
    """blank.pdf has /OCProperties, which pikepdf's validator does not check."""
    _forbid_ghostscript_pdfa(monkeypatch)
    exitcode = run_ocrmypdf_api(
        resources / 'blank.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--output-type',
        'pdfa',
        '--pdfa-backend',
        'internal',
    )
    assert exitcode == ExitCode.pdfa_conversion_failed
    assert 'optional content (/OCProperties) is not supported' in caplog.text
    assert 'PDF/A-2b: not_checked' in caplog.text
    assert '--pdfa-backend internal' in caplog.text


def test_internal_backend_denial_in_auto_outputs_pdf(
    resources, outpdf, caplog, monkeypatch
):
    _forbid_ghostscript_pdfa(monkeypatch)
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        check_ocrmypdf(
            resources / 'blank.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '--output-type',
            'auto',
            '--pdfa-backend',
            'internal',
        )
    assert not file_claims_pdfa(outpdf)['pass']
    assert 'outputting regular PDF' in caplog.text
    # A construct the validator does not check is reported as such, not as
    # a violation
    assert "construct(s) pikepdf's validator does not check" in caplog.text


def test_internal_backend_success(resources, outpdf, caplog, monkeypatch):
    _forbid_ghostscript_pdfa(monkeypatch)
    monkeypatch.setattr('ocrmypdf._exec.ghostscript.available', lambda: False)
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        check_ocrmypdf(
            resources / 'francais.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '--output-type',
            'pdfa-2',
            '--pdfa-backend',
            'internal',
        )
    assert SPECULATIVE_OK in caplog.text
    assert file_claims_pdfa(outpdf)['pass']


@pytest.mark.parametrize('output_type', ['pdfa', 'auto'])
def test_ghostscript_backend_skips_speculative(resources, outpdf, caplog, output_type):
    with caplog.at_level(logging.DEBUG, logger='ocrmypdf'):
        check_ocrmypdf(
            resources / 'francais.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '--output-type',
            output_type,
            '--pdfa-backend',
            'ghostscript',
        )
    assert 'Speculative PDF/A' not in caplog.text
    assert file_claims_pdfa(outpdf)['pass']


def test_auto_backend_with_ghostscript_jpeg_quality(resources, outpdf, caplog):
    with caplog.at_level(logging.DEBUG, logger='ocrmypdf'):
        check_ocrmypdf(
            resources / 'francais.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '--output-type',
            'pdfa',
            '--ghostscript-jpeg-quality',
            '60',
        )
    assert (
        "--ghostscript-jpeg-quality requires Ghostscript; using --pdfa-backend "
        "ghostscript" in caplog.text
    )
    assert 'Speculative PDF/A' not in caplog.text
    assert file_claims_pdfa(outpdf)['pass']


def test_pdfa_backend_api_kwarg(resources, outpdf, monkeypatch):
    import ocrmypdf
    from ocrmypdf.exceptions import PdfaConversionFailedError

    _forbid_ghostscript_pdfa(monkeypatch)
    with pytest.raises(PdfaConversionFailedError, match='/OCProperties'):
        ocrmypdf.ocr(
            resources / 'blank.pdf',
            outpdf,
            output_type='pdfa',
            pdfa_backend='internal',
            plugins=['tests/plugins/tesseract_noop.py'],
            progress_bar=False,
        )


def test_rgb_color_strategy_internal_backend(resources, outpdf, caplog, monkeypatch):
    _forbid_ghostscript_pdfa(monkeypatch)
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        check_ocrmypdf(
            resources / 'francais.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '--output-type',
            'pdfa',
            '--pdfa-backend',
            'internal',
            '--color-conversion-strategy',
            'RGB',
        )
    assert SPECULATIVE_OK in caplog.text
    assert file_claims_pdfa(outpdf)['pass']


def test_rgb_color_strategy_api_takes_speculative_path(
    resources, outpdf, caplog, monkeypatch
):
    """paperless-ngx passes color_conversion_strategy='RGB' on every PDF/A job."""
    import ocrmypdf

    _forbid_ghostscript_pdfa(monkeypatch)
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        ocrmypdf.ocr(
            resources / 'francais.pdf',
            outpdf,
            output_type='pdfa',
            color_conversion_strategy='RGB',
            plugins=['tests/plugins/tesseract_noop.py'],
            progress_bar=False,
        )
    assert SPECULATIVE_OK in caplog.text
    assert file_claims_pdfa(outpdf)['pass']


def test_failed_speculative_conversion_logs_repairs(
    resources, outpdf, caplog, monkeypatch
):
    """What pikepdf repaired is logged even when the result is not approved."""
    _forbid_ghostscript_pdfa(monkeypatch)
    with caplog.at_level(logging.DEBUG, logger='ocrmypdf'):
        check_ocrmypdf(
            resources / 'blank.pdf',
            outpdf,
            '--plugin',
            'tests/plugins/tesseract_noop.py',
            '--output-type',
            'auto',
            '--pdfa-backend',
            'internal',
        )
    assert 'Declared PDF/A conformance in the XMP metadata' in caplog.text
    assert "construct(s) pikepdf's validator does not check" in caplog.text


def _page_text(path) -> str:
    """Extract text without whitespace, which depends on inexact glyph widths."""
    from pdfminer.high_level import extract_text

    return ''.join(extract_text(path).split())


def _make_simple_truetype_font(
    pdf: pikepdf.Pdf, *, flags: int, encoding: pikepdf.Object
) -> pikepdf.Object:
    """Build an embedded simple TrueType font with no /ToUnicode."""
    from importlib.resources import files

    font_data = (files('ocrmypdf.data') / 'NotoSans-Regular.ttf').read_bytes()
    descriptor = pikepdf.Dictionary(
        Type=Name.FontDescriptor,
        FontName=Name('/ABCDEF+NotoSans'),
        Flags=flags,
        FontBBox=[-600, -300, 2600, 1100],
        ItalicAngle=0,
        Ascent=1069,
        Descent=-293,
        CapHeight=714,
        StemV=80,
        FontFile2=pdf.make_stream(font_data),
    )
    return pdf.make_indirect(
        pikepdf.Dictionary(
            Type=Name.Font,
            Subtype=Name.TrueType,
            BaseFont=Name('/ABCDEF+NotoSans'),
            FirstChar=1,
            LastChar=255,
            Widths=[600] * 255,
            FontDescriptor=descriptor,
            Encoding=encoding,
        )
    )


def _differences(*glyphs: str) -> pikepdf.Dictionary:
    return pikepdf.Dictionary(
        Type=Name.Encoding,
        Differences=[1, *(Name('/' + glyph) for glyph in glyphs)],
    )


def _write_simple_font_pdf(path, *, flags: int) -> None:
    """Text drawn with glyph names only, as in issue #1297."""
    with pikepdf.new() as pdf:
        page = pdf.add_blank_page(page_size=(300, 100))
        font = _make_simple_truetype_font(
            pdf,
            flags=flags,
            encoding=_differences(
                'G', 'r', 'adieresis', 'space', 'afii10017', 'afii10066'
            ),
        )
        page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
        page.Contents = pdf.make_stream(b'BT /F1 24 Tf 20 40 Td <010203040506> Tj ET')
        pdf.save(path)


@pytest.mark.parametrize('flags', [4, 32], ids=['symbolic', 'nonsymbolic'])
def test_ghostscript_pdfa_keeps_glyph_name_text(tmp_path, outpdf, flags):
    # Ghostscript rewrites simple TrueType fonts as CID fonts for PDF/A and
    # loses the Unicode meaning of their glyph names (issue #1297).
    input_pdf = tmp_path / 'glyph_names.pdf'
    _write_simple_font_pdf(input_pdf, flags=flags)
    assert _page_text(input_pdf) == 'GräАб'

    check_ocrmypdf(
        input_pdf,
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--skip-text',
        '--output-type',
        'pdfa',
        '--pdfa-backend',
        'ghostscript',
    )
    assert file_claims_pdfa(outpdf)['pass']
    assert _page_text(outpdf) == 'GräАб'


def _tounicode_map(font: pikepdf.Object) -> dict[int, str]:
    cmap = font.ToUnicode.read_bytes().decode('ascii')
    mapping = {}
    for count, block in re.findall(r'(\d+) beginbfchar\n(.*?)endbfchar', cmap, re.S):
        entries = re.findall(r'<([0-9A-F]{2})> <([0-9A-F]+)>', block)
        assert len(entries) == int(count) <= 100
        mapping.update(
            (int(code, 16), bytes.fromhex(text).decode('utf-16-be'))
            for code, text in entries
        )
    return mapping


@pytest.fixture(params=['implicit', 'explicit'])
def add_tounicode(request):
    """Run add_simple_font_tounicode on a PDF holding a font, return its map.

    The pipeline opens PDFs with conversion_mode='explicit', where numbers are
    pikepdf objects rather than Python ints, so both modes are tested.
    """

    def run(pdf: pikepdf.Pdf, font: pikepdf.Object) -> dict[int, str] | None:
        page = pdf.add_blank_page()
        page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
        buffer = BytesIO()
        pdf.save(buffer)
        with pikepdf.open(buffer, conversion_mode=request.param) as reopened:
            add_simple_font_tounicode(reopened)
            font = reopened.pages[-1].Resources.Font.F1
            if Name.ToUnicode not in font:
                return None
            return _tounicode_map(font)

    return run


class TestAddSimpleFontToUnicode:
    def test_differences_on_symbolic_font(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_simple_truetype_font(
                pdf, flags=4, encoding=_differences('G', 'uni0416', 'f_i')
            )
            # A symbolic font's base encoding is built into the font program,
            # so only the Differences are known.
            assert add_tounicode(pdf, font) == {1: 'G', 2: 'Ж', 3: 'fi'}

    def test_differences_over_named_base_encoding(self, add_tounicode):
        with pikepdf.new() as pdf:
            encoding = _differences('Z')
            encoding.BaseEncoding = Name.WinAnsiEncoding
            font = _make_simple_truetype_font(pdf, flags=4, encoding=encoding)
            mapping = add_tounicode(pdf, font)
            assert mapping[1] == 'Z'
            assert mapping[ord('A')] == 'A'
            assert mapping[0x80] == '€'
            assert len(mapping) > 200

    def test_nonsymbolic_font_uses_standard_encoding_base(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_simple_truetype_font(pdf, flags=32, encoding=_differences('Z'))
            mapping = add_tounicode(pdf, font)
            assert mapping[1] == 'Z'
            assert mapping[ord('A')] == 'A'
            assert mapping[0x27] == '’'  # quoteright in StandardEncoding

    def test_named_encoding(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_simple_truetype_font(
                pdf, flags=32, encoding=Name.MacRomanEncoding
            )
            assert add_tounicode(pdf, font)[0x8A] == 'ä'

    def test_unknown_glyph_name_is_unmapped(self, add_tounicode):
        with pikepdf.new() as pdf:
            encoding = _differences('g123')
            encoding.BaseEncoding = Name.WinAnsiEncoding
            font = _make_simple_truetype_font(pdf, flags=4, encoding=encoding)
            mapping = add_tounicode(pdf, font)
            # The base encoding's meaning of code 1 is replaced, not kept.
            assert 1 not in mapping
            assert mapping[ord('A')] == 'A'

    def test_nothing_mappable_adds_nothing(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_simple_truetype_font(
                pdf, flags=4, encoding=_differences('g1', 'g2')
            )
            assert add_tounicode(pdf, font) is None

    def test_existing_tounicode_is_kept(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_simple_truetype_font(pdf, flags=4, encoding=_differences('A'))
            font.ToUnicode = pdf.make_stream(b'keep me')
            # The original CMap has no entries that _tounicode_map can read.
            assert add_tounicode(pdf, font) == {}

    def test_font_without_encoding_is_untouched(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_simple_truetype_font(pdf, flags=4, encoding=Name.Null)
            del font.Encoding
            assert add_tounicode(pdf, font) is None

    def test_type0_font_is_untouched(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_cid_font(pdf, embedded=True, basefont='/ABCDEF+TestCID')
            assert add_tounicode(pdf, font) is None

    def test_large_encoding_is_split_into_blocks(self, add_tounicode):
        with pikepdf.new() as pdf:
            font = _make_simple_truetype_font(
                pdf, flags=4, encoding=Name.WinAnsiEncoding
            )
            # _tounicode_map asserts that no bfchar block exceeds 100 entries,
            # which Ghostscript 9.56 to 10.04 would drop.
            assert len(add_tounicode(pdf, font)) > 200

    def test_malformed_encoding_is_ignored(self, add_tounicode):
        with pikepdf.new() as pdf:
            encoding = pikepdf.Dictionary(
                Differences=[1, Name.A, pikepdf.String('junk'), Name.B],
                BaseEncoding=pikepdf.Array([]),
            )
            font = _make_simple_truetype_font(pdf, flags=4, encoding=encoding)
            font.FontDescriptor = Name.NotADictionary
            add_tounicode(pdf, font)  # must not raise


def _make_simple_font(
    pdf: pikepdf.Pdf, basefont: str, *, embedded: bool = False
) -> pikepdf.Object:
    """Build a simple (single-byte) TrueType font, optionally embedded."""
    descriptor = pikepdf.Dictionary(
        Type=Name.FontDescriptor,
        FontName=Name(basefont),
        Flags=32,
        FontBBox=pikepdf.Array([-500, -300, 1500, 1000]),
        ItalicAngle=0,
        Ascent=750,
        Descent=-250,
        CapHeight=700,
        StemV=80,
    )
    if embedded:
        descriptor.FontFile2 = pdf.make_stream(b'\x00\x01\x00\x00 fake font program')
    return pdf.make_indirect(
        pikepdf.Dictionary(
            Type=Name.Font,
            Subtype=Name.TrueType,
            BaseFont=Name(basefont),
            FirstChar=32,
            LastChar=126,
            Widths=pikepdf.Array([600] * 95),
            Encoding=Name.WinAnsiEncoding,
            FontDescriptor=descriptor,
        )
    )


class TestFindNonembeddedFonts:
    def test_blank_page_reports_nothing(self):
        with pikepdf.new() as pdf:
            pdf.add_blank_page()
            assert find_nonembedded_fonts(pdf) == set()
            assert not has_embedded_fonts(pdf)

    def test_detects_nonembedded_simple_and_cid_fonts(self):
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            page.Resources = pikepdf.Dictionary(
                Font=pikepdf.Dictionary(
                    F0=_make_simple_font(pdf, '/Verdana,Bold'),
                    F1=_make_cid_font(pdf, embedded=False, basefont='/TestCID'),
                    F2=_make_simple_font(pdf, '/Embedded', embedded=True),
                    F3=pikepdf.Dictionary(
                        Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica
                    ),
                )
            )
            assert find_nonembedded_fonts(pdf) == {
                'Verdana,Bold',
                'TestCID',
                'Helvetica',
            }
            assert has_embedded_fonts(pdf)

    def test_nonembedded_only(self):
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            page.Resources = pikepdf.Dictionary(
                Font=pikepdf.Dictionary(F0=_make_simple_font(pdf, '/Verdana'))
            )
            assert find_nonembedded_fonts(pdf) == {'Verdana'}
            assert not has_embedded_fonts(pdf)

    def test_type3_font_counts_as_embedded(self):
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            type3 = pdf.make_indirect(
                pikepdf.Dictionary(
                    Type=Name.Font,
                    Subtype=Name.Type3,
                    FontMatrix=pikepdf.Array([0.001, 0, 0, 0.001, 0, 0]),
                    CharProcs=pikepdf.Dictionary(),
                )
            )
            page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(T0=type3))
            assert find_nonembedded_fonts(pdf) == set()
            assert has_embedded_fonts(pdf)

    def test_finds_fonts_in_annotation_appearance(self):
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page()
            appearance = pdf.make_stream(
                b'',
                Type=Name.XObject,
                Subtype=Name.Form,
                BBox=pikepdf.Array([0, 0, 1, 1]),
                Resources=pikepdf.Dictionary(
                    Font=pikepdf.Dictionary(
                        F0=_make_simple_font(pdf, '/AnnotFont', embedded=True)
                    )
                ),
            )
            annot = pikepdf.Dictionary(
                Type=Name.Annot,
                Subtype=Name.FreeText,
                Rect=pikepdf.Array([0, 0, 1, 1]),
                AP=pikepdf.Dictionary(N=appearance),
            )
            page.Annots = pdf.make_indirect(pikepdf.Array([annot]))
            assert has_embedded_fonts(pdf)

    def test_finds_fonts_in_acroform_default_resources(self):
        with pikepdf.new() as pdf:
            pdf.add_blank_page()
            pdf.Root.AcroForm = pikepdf.Dictionary(
                Fields=pikepdf.Array([]),
                DR=pikepdf.Dictionary(
                    Font=pikepdf.Dictionary(
                        Helv=_make_simple_font(pdf, '/FormFont', embedded=True)
                    )
                ),
            )
            assert has_embedded_fonts(pdf)


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        ('Helvetica', True),
        ('Times-BoldItalic', True),
        ('ABCDEF+Courier', True),
        ('ZapfDingbats', True),
        ('Arial', False),
        ('Verdana,Bold', False),
    ],
)
def test_is_standard14_font(name, expected):
    assert is_standard14_font(name) == expected
