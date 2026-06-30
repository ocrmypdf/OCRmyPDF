# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os

import pikepdf
import pytest
from pikepdf import Name

from ocrmypdf.exceptions import ExitCode, MissingDependencyError
from ocrmypdf.pdfa import file_claims_pdfa, find_nonembedded_cid_fonts

from .conftest import check_ocrmypdf, run_ocrmypdf_api


def _make_cid_font(
    pdf: pikepdf.Pdf, *, embedded: bool, basefont: str
) -> pikepdf.Object:
    """Build a Type0/CID font object, optionally embedding glyph data."""
    descriptor = pikepdf.Dictionary(
        Type=Name.FontDescriptor, FontName=Name(basefont), Flags=4
    )
    if embedded:
        # The actual bytes do not matter; only the presence of FontFile2 marks
        # the CID font as embedded.
        descriptor.FontFile2 = pdf.make_stream(b'\x00\x01\x00\x00 fake font program')
    cidfont = pdf.make_indirect(
        pikepdf.Dictionary(
            Type=Name.Font,
            Subtype=Name.CIDFontType2,
            BaseFont=Name(basefont),
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
            BaseFont=Name(basefont),
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


def test_auto_falls_back_to_ghostscript_for_pdfa(resources, outpdf, monkeypatch):
    """Auto mode produces PDF/A via Ghostscript when the cheap path can't."""
    # Force the speculative (veraPDF) path off so the fallback is exercised.
    monkeypatch.setattr('ocrmypdf._exec.verapdf.available', lambda: False)
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--output-type',
        'auto',
    )
    assert file_claims_pdfa(outpdf)['pass']


def test_auto_outputs_pdf_when_ghostscript_unavailable(resources, outpdf, monkeypatch):
    """With neither veraPDF nor Ghostscript, auto outputs a plain PDF."""
    monkeypatch.setattr('ocrmypdf._exec.verapdf.available', lambda: False)
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
    resources, outpdf, monkeypatch
):
    """If Ghostscript produces non-PDF/A output, auto keeps a plain PDF (no error)."""
    monkeypatch.setattr('ocrmypdf._exec.verapdf.available', lambda: False)
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


def test_auto_degrades_when_ghostscript_raises(resources, outpdf, monkeypatch):
    """A Ghostscript conversion exception in auto mode degrades to plain PDF."""
    from ocrmypdf.exceptions import ColorConversionNeededError

    monkeypatch.setattr('ocrmypdf._exec.verapdf.available', lambda: False)

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
