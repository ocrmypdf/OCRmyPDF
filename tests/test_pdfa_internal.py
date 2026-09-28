# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""End-to-end tests of speculative PDF/A conversion with pikepdf.pdfa."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pikepdf
import pytest
from pikepdf.pdfa import PdfaError, validate_written

from ocrmypdf.pdfa import output_type_to_flavour, speculative_pdfa_conversion

from .conftest import assert_verapdf_agrees, check_ocrmypdf

RESOURCES = Path(__file__).parent / 'resources'

SPECULATIVE_OK = 'Speculative PDF/A conversion succeeded'

INPUTS = [
    'francais.pdf',
    'graph.pdf',
    'ccitt.pdf',
    'jbig2.pdf',
    'multipage.pdf',
    'link.pdf',
]
RENDERERS = ['fpdf2', 'sandwich']
OUTPUT_TYPES = ['pdfa-1', 'pdfa-2', 'pdfa-3']

# Candidates the validator must deny, so that Ghostscript is used instead:
# multipage.pdf has a soft-masked image, and PDF/A-1 forbids transparency.
EXPECTED_FALLBACK = {
    ('multipage.pdf', 'pdfa-1'): 'soft masks are not permitted in PDF/A-1',
}

DEFAULT_CASES = {
    ('francais.pdf', 'fpdf2', 'pdfa-1'),
    ('francais.pdf', 'sandwich', 'pdfa-2'),
    ('ccitt.pdf', 'fpdf2', 'pdfa-3'),
    ('link.pdf', 'sandwich', 'pdfa-1'),
    ('multipage.pdf', 'fpdf2', 'pdfa-1'),
}


def _matrix():
    for in_pdf in INPUTS:
        for renderer in RENDERERS:
            for output_type in OUTPUT_TYPES:
                case = (in_pdf, renderer, output_type)
                marks = () if case in DEFAULT_CASES else (pytest.mark.slow,)
                yield pytest.param(*case, marks=marks, id='-'.join(case))


def _run(input_file: Path, output_file: Path, renderer: str, output_type: str):
    return check_ocrmypdf(
        input_file,
        output_file,
        '--skip-text',
        '-l',
        'eng',
        '--pdf-renderer',
        renderer,
        '--output-type',
        output_type,
        '--plugin',
        'tests/plugins/tesseract_cache.py',
    )


@pytest.mark.parametrize('in_pdf, renderer, output_type', list(_matrix()))
def test_pipeline_speculative_pdfa(
    resources, outpdf, caplog, in_pdf, renderer, output_type
):
    with caplog.at_level(logging.DEBUG, logger='ocrmypdf'):
        _run(resources / in_pdf, outpdf, renderer, output_type)

    flavour = output_type_to_flavour(output_type)
    fallback_reason = EXPECTED_FALLBACK.get((in_pdf, output_type))
    if fallback_reason is not None:
        assert SPECULATIVE_OK not in caplog.text
        assert fallback_reason in caplog.text
        assert 'it failed validation with' in caplog.text
        return
    assert SPECULATIVE_OK in caplog.text
    report = validate_written(outpdf, flavour)
    assert report.verdict == 'pass', report.summary()
    assert_verapdf_agrees(outpdf, flavour)


def test_speculative_pdfa_does_not_need_verapdf(resources, outpdf, caplog, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr('ocrmypdf._exec.verapdf.available', lambda: False)
        with caplog.at_level(logging.INFO, logger='ocrmypdf'):
            _run(resources / 'francais.pdf', outpdf, 'fpdf2', 'pdfa-2')
    assert SPECULATIVE_OK in caplog.text


@pytest.mark.slow
@pytest.mark.parametrize('flavour', ['1b', '2b', '3b'])
@pytest.mark.parametrize(
    'in_pdf', sorted(p.name for p in RESOURCES.glob('*.pdf')), ids=str
)
def test_no_false_approvals_on_resources(in_pdf, flavour, tmp_path):
    """Whenever pikepdf approves a speculative candidate, veraPDF must agree."""
    output_type = f'pdfa-{flavour[0]}'
    candidate = tmp_path / 'candidate.pdf'
    try:
        speculative_pdfa_conversion(RESOURCES / in_pdf, candidate, output_type)
    except PdfaError:
        assert not candidate.exists()
        return
    except (pikepdf.PdfError, ValueError, KeyError, TypeError) as e:
        pytest.skip(f"speculative conversion failed: {e}")
    assert_verapdf_agrees(candidate, flavour)


@pytest.fixture(scope='module')
def one_page_ocr(resources, tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp('perf') / 'graph.pdf'
    return _run(resources / 'graph.pdf', out, 'fpdf2', 'pdf')


def test_validation_performance(one_page_ocr, tmp_path):
    """A 300-page candidate validates in a few seconds.

    This measures scaling with the number of objects. The cost of content
    streams grows with the number of text-showing operators: pages of dense
    OCR text take about 13 ms each.
    """
    merged = tmp_path / 'merged.pdf'
    sources = [pikepdf.open(one_page_ocr) for _ in range(300)]
    try:
        with pikepdf.new() as pdf:
            for source in sources:
                # Pages from separate Pdf objects are copied with all their
                # resources, so every page has its own fonts and images.
                pdf.pages.extend(source.pages)
            pdf.save(merged)
    finally:
        for source in sources:
            source.close()
    candidate = tmp_path / 'c.pdf'
    speculative_pdfa_conversion(merged, candidate, 'pdfa-2')
    with pikepdf.open(candidate) as pdf:
        assert len(pdf.pages) == 300
        assert len(pdf.objects) > 300 * 5

    start = time.perf_counter()
    report = validate_written(candidate, '2b')
    elapsed = time.perf_counter() - start
    assert report.verdict == 'pass', report.summary()
    # Locally this takes ~3 s; a pathological regression (e.g. quadratic
    # scaling in the number of objects/pages) would be many times slower,
    # not just somewhat slower. 20 s gives generous headroom for slow,
    # shared CI runners (observed 6.7 s on ubuntu-22.04/py3.13) while still
    # catching that kind of regression.
    assert elapsed < 20.0, f"validation took {elapsed:.1f} s"
