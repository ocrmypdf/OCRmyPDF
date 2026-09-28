# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""The file OCRmyPDF emits as PDF/A is the file pikepdf's validator checks.

Speculative PDF/A conversion is followed by the metadata fixup and the
optimizer, which both rewrite the file. These tests check that the metadata
fixup keeps a speculative candidate valid, and that the final file is
validated, with the usual fallbacks if it is not.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import pikepdf
import pytest
from pikepdf import Name
from pikepdf.pdfa import Finding, validate_written

from ocrmypdf._jobcontext import PdfContext
from ocrmypdf._metadata import metadata_fixup
from ocrmypdf.api import setup_plugin_infrastructure
from ocrmypdf.cli import get_options_and_plugins
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.pdfa import (
    file_claims_pdfa,
    get_pdf_save_settings,
    output_type_to_flavour,
    speculative_pdfa_conversion,
)

from .conftest import assert_verapdf_agrees, check_ocrmypdf, run_ocrmypdf_api

SPECULATIVE_OK = 'Speculative PDF/A conversion succeeded'
FINAL_DENIED = 'output was not used after metadata and optimization'

DC = 'http://purl.org/dc/elements/1.1/'
RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'


def _langalt_items(packet: bytes, prop: str) -> set[tuple[str | None, str]]:
    """Return the (language, text) items of a language alternative in XMP."""
    root = ET.fromstring(packet)
    return {
        (li.get(XML_LANG), li.text or '')
        for element in root.iter(f'{{{DC}}}{prop}')
        for li in element.iter(f'{{{RDF}}}li')
    }


ORIGINAL_XMP = b"""<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title><rdf:Alt>
<rdf:li xml:lang="x-default">English title</rdf:li>
<rdf:li xml:lang="fr">Titre</rdf:li>
</rdf:Alt></dc:title>
<dc:creator><rdf:Seq><rdf:li>XMP Only Author</rdf:li></rdf:Seq></dc:creator>
</rdf:Description>
<rdf:Description rdf:about="uuid:0f3a9b3e-1111-2222-3333-444455556666"
  xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:description><rdf:Alt>
<rdf:li xml:lang="x-default">About another resource</rdf:li>
</rdf:Alt></dc:description>
</rdf:Description>
</rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


@pytest.fixture
def original_with_xmp_only_author(resources, tmp_path) -> Path:
    """An input whose author is only in XMP, with a multi-language title."""
    path = tmp_path / 'original.pdf'
    with pikepdf.open(resources / 'graph.pdf') as pdf:
        pdf.Root.Metadata = pdf.make_stream(
            ORIGINAL_XMP, Type=Name.Metadata, Subtype=Name.XML
        )
        for key in list(pdf.docinfo.keys()):
            del pdf.docinfo[key]
        pdf.docinfo[Name.Title] = 'English title'
        pdf.save(path)
    return path


def _metadata_fixup(original: Path, working: Path, output_type: str, work: Path):
    options, _pm = get_options_and_plugins(
        ['--output-type', output_type, str(original), 'out.pdf']
    )
    plugin_manager = setup_plugin_infrastructure([])
    context = PdfContext(options, work, original, None, plugin_manager)
    return metadata_fixup(
        working_file=working,
        context=context,
        pdf_save_settings=get_pdf_save_settings(output_type),
        pdfa_output_type=output_type if output_type.startswith('pdfa') else None,
    )


@pytest.mark.parametrize('output_type', ['pdfa-1', 'pdfa-2', 'pdfa-3'])
def test_metadata_fixup_keeps_speculative_candidate_valid(
    original_with_xmp_only_author, tmp_path, output_type
):
    flavour = output_type_to_flavour(output_type)
    candidate = tmp_path / 'candidate.pdf'
    report = speculative_pdfa_conversion(
        original_with_xmp_only_author, candidate, output_type
    )
    assert report.verdict == 'pass'

    final = _metadata_fixup(
        original_with_xmp_only_author, candidate, output_type, tmp_path
    )

    report = validate_written(final, flavour)
    assert report.verdict == 'pass', report.summary()
    assert_verapdf_agrees(final, str(flavour.value))
    with pikepdf.open(final) as pdf:
        packet = pdf.Root.Metadata.read_bytes()
        assert _langalt_items(packet, 'title') == {
            ('x-default', 'English title'),
            ('fr', 'Titre'),
        }
        # Saving the original gave both Descriptions the same rdf:about, so
        # both describe the document and both are kept
        assert _langalt_items(packet, 'description') == {
            ('x-default', 'About another resource')
        }
        assert pdf.open_metadata().get('dc:creator') == ['XMP Only Author']
        assert str(pdf.docinfo[Name.Author]) == 'XMP Only Author'
        assert str(pdf.docinfo[Name.Title]) == 'English title'
    assert file_claims_pdfa(final)['conformance'] == f'PDF/A-{flavour.value}'


def test_metadata_fixup_empty_docinfo_does_not_erase_xmp(
    original_with_xmp_only_author, tmp_path
):
    """Outside PDF/A, a missing /Author does not erase the working file's."""
    working = tmp_path / 'working.pdf'
    with pikepdf.open(original_with_xmp_only_author) as pdf:
        pdf.save(working)
    final = _metadata_fixup(original_with_xmp_only_author, working, 'pdf', tmp_path)
    with pikepdf.open(final) as pdf:
        meta = pdf.open_metadata()
        assert meta.get('dc:creator') == ['XMP Only Author']
        assert 'pdfaid:part' not in meta


def _run(input_file: Path, output_file: Path, *args):
    return run_ocrmypdf_api(
        input_file,
        output_file,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        *args,
    )


@pytest.fixture
def deny_final_validation(monkeypatch):
    """Approve the speculative candidate as usual, but deny every later file.

    ``pikepdf.pdfa.save`` validates the candidate with its own reference to
    ``validate_written``, so only OCRmyPDF's validation of the final file is
    denied.
    """
    import pikepdf.pdfa

    real_validate = pikepdf.pdfa.validate_written
    denied: list[Path] = []

    def deny(path, flavour, *args, **kwargs):
        report = real_validate(path, flavour, *args, **kwargs)
        report.findings.append(Finding('pikepdf:test', str(path), "denied by the test"))
        denied.append(Path(path))
        return report

    monkeypatch.setattr(pikepdf.pdfa, 'validate_written', deny)
    return denied


@pytest.fixture
def ghostscript_calls(monkeypatch):
    """Record the inputs of Ghostscript PDF/A conversions."""
    from ocrmypdf import _pipeline

    calls: list[Path] = []
    real_convert = _pipeline.convert_to_pdfa

    def spy(input_pdf, *args, **kwargs):
        calls.append(Path(input_pdf))
        return real_convert(input_pdf, *args, **kwargs)

    monkeypatch.setattr(_pipeline, 'convert_to_pdfa', spy)
    return calls


@pytest.fixture
def copying_safe_symlink(monkeypatch):
    """Make ``optimize``'s ``safe_symlink`` copy instead of linking.

    This mimics Windows, where ``safe_symlink`` always copies files rather
    than symlinking them, so the optimizer's output path is a real file
    after the first pass, not a symlink.
    """
    import os
    import shutil

    from ocrmypdf import optimize as optimize_module

    def copying(input_file, soft_link_name):
        # Same overwrite guard as the real safe_symlink: refuse to clobber
        # a real (non-symlink) file left by an earlier pass.
        link_path = Path(soft_link_name)
        if os.path.lexists(link_path):
            if not link_path.is_symlink():
                raise FileExistsError(f"{link_path} exists and is not a link")
            link_path.unlink()
        shutil.copyfile(input_file, link_path)

    monkeypatch.setattr(optimize_module, 'safe_symlink', copying)


@pytest.mark.parametrize('output_type', ['pdfa-1', 'pdfa-2'])
def test_final_denial_falls_back_to_ghostscript_with_copying_symlink(
    resources,
    outpdf,
    caplog,
    deny_final_validation,
    ghostscript_calls,
    copying_safe_symlink,
    output_type,
):
    """The Ghostscript-fallback optimize pass must not collide with the first.

    On Windows, ``safe_symlink`` always copies (never symlinks), so the
    first optimizer pass leaves a real file at the shared 'optimize.pdf'
    intermediate path. When final validation of the speculative candidate
    is denied and the pipeline falls back to Ghostscript, a second optimize
    pass runs and must not crash trying to write to that same path
    (``FileExistsError: ... exists and is not a link``, see #1808-style
    Windows CI failures).
    """
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        exitcode = _run(
            resources / 'francais.pdf', outpdf, '--output-type', output_type
        )
    assert exitcode == ExitCode.ok
    assert FINAL_DENIED in caplog.text
    assert len(ghostscript_calls) == 1
    assert file_claims_pdfa(outpdf)['pass']


@pytest.mark.parametrize('output_type', ['pdfa-1', 'pdfa-2'])
def test_final_denial_falls_back_to_ghostscript(
    resources, outpdf, caplog, deny_final_validation, ghostscript_calls, output_type
):
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        exitcode = _run(
            resources / 'francais.pdf', outpdf, '--output-type', output_type
        )
    assert exitcode == ExitCode.ok
    assert SPECULATIVE_OK in caplog.text
    assert FINAL_DENIED in caplog.text
    assert 'denied by the test' in caplog.text
    assert len(deny_final_validation) == 1
    # Ghostscript converted the file speculative conversion started from
    assert len(ghostscript_calls) == 1
    assert ghostscript_calls[0].name != 'speculative_pdfa.pdf'
    assert file_claims_pdfa(outpdf)['pass']


def test_final_denial_with_internal_backend_fails(
    resources, outpdf, caplog, deny_final_validation, ghostscript_calls
):
    exitcode = _run(
        resources / 'francais.pdf',
        outpdf,
        '--output-type',
        'pdfa-2',
        '--pdfa-backend',
        'internal',
    )
    assert exitcode == ExitCode.pdfa_conversion_failed
    assert '--pdfa-backend internal could not produce PDF/A' in caplog.text
    assert 'denied by the test' in caplog.text
    assert ghostscript_calls == []


def test_final_denial_in_auto_uses_ghostscript(
    resources, outpdf, caplog, deny_final_validation, ghostscript_calls
):
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        exitcode = _run(resources / 'francais.pdf', outpdf, '--output-type', 'auto')
    assert exitcode == ExitCode.ok
    assert FINAL_DENIED in caplog.text
    assert 'Auto mode: produced PDF/A via Ghostscript' in caplog.text
    assert len(ghostscript_calls) == 1
    assert file_claims_pdfa(outpdf)['pass']


def test_final_denial_in_auto_without_ghostscript_outputs_pdf(
    resources, outpdf, caplog, deny_final_validation, ghostscript_calls
):
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        exitcode = _run(
            resources / 'francais.pdf',
            outpdf,
            '--output-type',
            'auto',
            '--pdfa-backend',
            'internal',
        )
    assert exitcode == ExitCode.ok
    assert FINAL_DENIED in caplog.text
    assert 'outputting regular PDF' in caplog.text
    assert 'Output file is a PDF (auto mode)' in caplog.text
    assert ghostscript_calls == []
    assert not file_claims_pdfa(outpdf)['pass']


def test_final_file_is_validated(resources, outpdf, caplog, monkeypatch):
    """The emitted file, not an intermediate, is the last one validated.

    The speculative candidate is validated inside ``pikepdf.pdfa.save``,
    before it is moved into place; OCRmyPDF validates only the final file.
    """
    import pikepdf.pdfa

    real_validate = pikepdf.pdfa.validate_written
    validated: list[tuple[str, bytes]] = []

    def recording_validate(path, flavour, *args, **kwargs):
        validated.append((Path(path).name, Path(path).read_bytes()))
        return real_validate(path, flavour, *args, **kwargs)

    monkeypatch.setattr(pikepdf.pdfa, 'validate_written', recording_validate)
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        exitcode = _run(
            resources / 'francais.pdf', outpdf, '--output-type', 'pdfa-2', '-O1'
        )
    assert exitcode == ExitCode.ok
    assert SPECULATIVE_OK in caplog.text
    assert [name for name, _ in validated] == ['optimize.pdf']
    assert outpdf.read_bytes() == validated[-1][1]


E2E_INPUTS = ['francais.pdf', 'graph.pdf', 'ccitt.pdf', 'link.pdf']


def _assert_final_output_valid(outpdf: Path, output_type: str, log_text: str):
    assert SPECULATIVE_OK in log_text
    assert FINAL_DENIED not in log_text
    flavour = output_type_to_flavour(output_type)
    report = validate_written(outpdf, flavour)
    assert report.verdict == 'pass', report.summary()
    assert_verapdf_agrees(outpdf, str(flavour.value))


@pytest.mark.parametrize('output_type', ['pdfa', 'pdfa-1'])
@pytest.mark.parametrize('in_pdf', E2E_INPUTS)
def test_final_output_passes_validation(resources, outpdf, caplog, in_pdf, output_type):
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        check_ocrmypdf(
            resources / in_pdf,
            outpdf,
            '--skip-text',
            '-l',
            'eng',
            '--output-type',
            output_type,
            '--plugin',
            'tests/plugins/tesseract_cache.py',
        )
    _assert_final_output_valid(outpdf, output_type, caplog.text)


@pytest.mark.parametrize('output_type', ['pdfa', 'pdfa-1'])
def test_final_output_with_input_metadata_passes_validation(
    resources, outpdf, caplog, output_type
):
    """meta.pdf carries DocInfo and XMP that the metadata fixup copies."""
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        exitcode = _run(resources / 'meta.pdf', outpdf, '--output-type', output_type)
    assert exitcode == ExitCode.ok
    _assert_final_output_valid(outpdf, output_type, caplog.text)


def test_final_denial_in_auto_with_undeclared_ghostscript_output_is_pdf(
    resources, outpdf, caplog, deny_final_validation, monkeypatch
):
    """If Ghostscript does not declare PDF/A either, auto reports a regular PDF."""

    def ghostscript_without_pdfa(input_pdf, context):
        return input_pdf

    monkeypatch.setattr(
        'ocrmypdf._pipeline._pdfa_without_speculation', ghostscript_without_pdfa
    )
    from ocrmypdf.builtin_plugins import optimize as optimize_plugin

    optimizer_output_types: list[str] = []
    real_settings = optimize_plugin.get_pdf_save_settings

    def recording_settings(output_type):
        optimizer_output_types.append(output_type)
        return real_settings(output_type)

    monkeypatch.setattr(optimize_plugin, 'get_pdf_save_settings', recording_settings)
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        exitcode = _run(resources / 'francais.pdf', outpdf, '--output-type', 'auto')
    assert exitcode == ExitCode.ok
    assert FINAL_DENIED in caplog.text
    assert 'Output file is a PDF (auto mode)' in caplog.text
    assert not file_claims_pdfa(outpdf)['pass']
    # The speculative candidate was optimized as PDF/A; the regular PDF that
    # is output was optimized as a regular PDF
    assert optimizer_output_types == ['pdfa', 'pdf']
