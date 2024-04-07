# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import datetime
import warnings
from datetime import timezone
from shutil import copyfile

import pikepdf
import pytest
from packaging.version import Version
from pikepdf.models.metadata import decode_pdf_date

from ocrmypdf._exec import ghostscript
from ocrmypdf._jobcontext import PdfContext
from ocrmypdf._metadata import metadata_fixup
from ocrmypdf._pipeline import convert_to_pdfa
from ocrmypdf._plugin_manager import get_parser_options_plugins, get_plugin_manager
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.pdfa import file_claims_pdfa, generate_pdfa_ps
from ocrmypdf.pdfinfo import PdfInfo

from .conftest import check_ocrmypdf, run_ocrmypdf, run_ocrmypdf_api


@pytest.mark.parametrize("output_type", ['pdfa', 'pdf'])
def test_preserve_docinfo(output_type, resources, outpdf):
    output = check_ocrmypdf(
        resources / 'graph.pdf',
        outpdf,
        '--output-type',
        output_type,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )
    with (
        pikepdf.open(resources / 'graph.pdf') as pdf_before,
        pikepdf.open(output) as pdf_after,
    ):
        for key in ('/Title', '/Author'):
            assert pdf_before.docinfo[key] == pdf_after.docinfo[key]
        pdfa_info = file_claims_pdfa(str(output))
        assert pdfa_info['output'] == output_type


@pytest.mark.parametrize("output_type", ['pdfa', 'pdf'])
def test_override_metadata(output_type, resources, outpdf, caplog):
    input_file = resources / 'c02-22.pdf'
    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'

    exitcode = run_ocrmypdf_api(
        input_file,
        outpdf,
        '--title',
        german,
        '--author',
        chinese,
        '--output-type',
        output_type,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    assert exitcode == ExitCode.ok, caplog.text

    with pikepdf.open(input_file) as before, pikepdf.open(outpdf) as after:
        assert after.docinfo.Title == german, after.docinfo
        assert after.docinfo.Author == chinese, after.docinfo
        assert after.docinfo.get('/Keywords', '') == ''

        before_date = decode_pdf_date(str(before.docinfo.CreationDate))
        after_date = decode_pdf_date(str(after.docinfo.CreationDate))
        assert before_date == after_date

        pdfa_info = file_claims_pdfa(outpdf)
        assert pdfa_info['output'] == output_type


@pytest.mark.parametrize('output_type', ['pdfa', 'pdf', 'pdfa-1', 'pdfa-2', 'pdfa-3'])
@pytest.mark.parametrize('field', ['title', 'author', 'subject', 'keywords'])
def test_unset_metadata(output_type, field, resources, outpdf, caplog):
    input_file = resources / 'meta.pdf'

    # magic strings contained in the input pdf metadata
    meta = {
        'title': b'NFY5f7Ft2DWMkxLhXwxvFf7eWR2KeK3vEDcd',
        'author': b'yXaryipxyRk9dVjWjSSaVaNCKeLRgEVzPRMp',
        'subject': b't49vimctvnuH7ZeAjAkv52ACvWFjcnm5MPJr',
        'keywords': b's9EeALwUg7urA7fnnhm5EtUyC54sW2WPUzqh',
    }

    exitcode = run_ocrmypdf_api(
        input_file,
        outpdf,
        f'--{field}',
        '',
        '--output-type',
        output_type,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    assert exitcode == ExitCode.ok, caplog.text

    # We mainly want to ensure that when '' is passed, the corresponding
    # metadata is unset in the output pdf. Since metedata is not compressed,
    # the best way to gaurentee the metadata of interest didn't carry
    # forward is to just check to ensure the corresponding magic string
    # isn't contained anywhere in the output pdf. We'll also check to ensure
    # it's in the input pdf and that any values not unset are still in the
    # output pdf.
    with open(input_file, 'rb') as before, open(outpdf, 'rb') as after:
        before_data = before.read()
        after_data = after.read()

    for k, v in meta.items():
        assert v in before_data
        if k == field:
            assert v not in after_data
        else:
            assert v in after_data


def test_high_unicode(resources, no_outpdf):
    # Ghostscript doesn't support high Unicode, so neither do we, to be
    # safe
    input_file = resources / 'c02-22.pdf'
    high_unicode = 'U+1030C is: 𐌌'

    p = run_ocrmypdf(
        input_file,
        no_outpdf,
        '--subject',
        high_unicode,
        '--output-type',
        'pdfa',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    assert p.returncode == ExitCode.bad_args, p.stderr


@pytest.mark.parametrize('ocr_option', ['--skip-text', '--force-ocr'])
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_bookmarks_preserved(output_type, ocr_option, resources, outpdf):
    fitz = pytest.importorskip('fitz')
    input_file = resources / 'toc.pdf'
    before_toc = fitz.Document(str(input_file)).get_toc()

    check_ocrmypdf(
        input_file,
        outpdf,
        ocr_option,
        '--output-type',
        output_type,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    after_toc = fitz.Document(str(outpdf)).get_toc()
    print(before_toc)
    print(after_toc)
    assert before_toc == after_toc


def seconds_between_dates(date1, date2):
    return (date2 - date1).total_seconds()


@pytest.mark.parametrize('infile', ['trivial.pdf', 'jbig2.pdf'])
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_creation_date_preserved(output_type, resources, infile, outpdf):
    input_file = resources / infile

    check_ocrmypdf(
        input_file,
        outpdf,
        '--output-type',
        output_type,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    with pikepdf.open(input_file) as pdf_before, pikepdf.open(outpdf) as pdf_after:
        before = pdf_before.trailer.get('/Info', {})
        after = pdf_after.trailer.get('/Info', {})

        if not before:
            assert after.get('/CreationDate', '') != ''
        else:
            # We expect that the creation date stayed the same
            date_before = decode_pdf_date(str(before['/CreationDate']))
            date_after = decode_pdf_date(str(after['/CreationDate']))
            assert seconds_between_dates(date_before, date_after) < 1000

        # We expect that the modified date is quite recent
        date_after = decode_pdf_date(str(after['/ModDate']))
        assert (
            seconds_between_dates(date_after, datetime.datetime.now(timezone.utc))
            < 1000
        )


@pytest.fixture
def libxmp_file_to_dict():
    try:
        with warnings.catch_warnings():
            # libxmp imports distutils.Version, which is deprecated
            warnings.filterwarnings(
                "ignore",
                category=DeprecationWarning,
                message=r".*distutils Version classes are deprecated.*",
            )
            from libxmp.utils import (
                file_to_dict,  # pylint: disable=import-outside-toplevel
            )
    except Exception:  # pylint: disable=broad-except
        pytest.skip("libxmp not available or libexempi3 not installed")
    return file_to_dict


@pytest.mark.parametrize(
    'test_file,output_type',
    [
        ('graph.pdf', 'pdf'),  # PDF with full metadata
        ('graph.pdf', 'pdfa'),  # PDF/A with full metadata
        ('overlay.pdf', 'pdfa'),  # /Title()
        ('3small.pdf', 'pdfa'),
    ],
)
def test_xml_metadata_preserved(
    libxmp_file_to_dict, test_file, output_type, resources, outpdf
):
    input_file = resources / test_file

    before = libxmp_file_to_dict(str(input_file))

    check_ocrmypdf(
        input_file,
        outpdf,
        '--output-type',
        output_type,
        '--skip-text',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    after = libxmp_file_to_dict(str(outpdf))

    equal_properties = [
        'dc:contributor',
        'dc:coverage',
        'dc:creator',
        'dc:description',
        'dc:format',
        'dc:identifier',
        'dc:language',
        'dc:publisher',
        'dc:relation',
        'dc:rights',
        'dc:source',
        'dc:subject',
        'dc:title',
        'dc:type',
        'pdf:keywords',
    ]
    acquired_properties = ['dc:format']

    # Cleanup messy data structure
    # Top level is key-value mapping of namespaces to keys under namespace,
    # so we put everything in the same namespace
    def unify_namespaces(xmpdict):
        for entries in xmpdict.values():
            yield from entries

    # Now we have a list of (key, value, {infodict}). We don't care about
    # infodict. Just flatten to keys and values
    def keyval_from_tuple(list_of_tuples):
        for k, v, *_ in list_of_tuples:
            yield k, v

    before = dict(keyval_from_tuple(unify_namespaces(before)))
    after = dict(keyval_from_tuple(unify_namespaces(after)))

    for prop in equal_properties:
        if prop in before:
            assert prop in after, f'{prop} dropped from xmp'
            assert before[prop] == after[prop]

        # libxmp presents multivalued entries (e.g. dc:title) as:
        # 'dc:title': '' <- there's a title
        # 'dc:title[1]: 'The Title' <- the actual title
        # 'dc:title[1]/?xml:lang': 'x-default' <- language info
        propidx = f'{prop}[1]'
        if propidx in before:
            assert (
                after.get(propidx) == before[propidx]
                or after.get(prop) == before[propidx]
            )

        if prop in after and prop not in before:
            assert prop in acquired_properties, (
                f"acquired unexpected property {prop} with value "
                f"{after.get(propidx) or after.get(prop)}"
            )


def test_kodak_toc(resources, outpdf):
    check_ocrmypdf(
        resources / 'kcs.pdf',
        outpdf,
        '--output-type',
        'pdf',
        '--plugin',
        'tests/plugins/tesseract_noop.py',
    )

    with pikepdf.open(outpdf) as p:
        if pikepdf.Name.First in p.Root.Outlines:
            assert isinstance(p.Root.Outlines.First, pikepdf.Dictionary)


def test_metadata_fixup_warning(resources, outdir, caplog):
    _parser, options, _pm = get_parser_options_plugins(
        ['--output-type', 'pdfa-2', 'graph.pdf', 'out.pdf']
    )

    copyfile(resources / 'graph.pdf', outdir / 'graph.pdf')

    context = PdfContext(
        options, outdir, outdir / 'graph.pdf', None, get_plugin_manager([])
    )
    metadata_fixup(
        working_file=outdir / 'graph.pdf', context=context, pdf_save_settings={}
    )
    for record in caplog.records:
        assert record.levelname != 'WARNING', "Unexpected warning"

    # Now add some metadata that will not be copyable
    with pikepdf.open(outdir / 'graph.pdf') as graph:
        with graph.open_metadata() as meta:
            meta['prism2:publicationName'] = 'OCRmyPDF Test'
        graph.save(outdir / 'graph_mod.pdf')

    context = PdfContext(
        options, outdir, outdir / 'graph_mod.pdf', None, get_plugin_manager([])
    )
    metadata_fixup(
        working_file=outdir / 'graph.pdf', context=context, pdf_save_settings={}
    )
    assert any(record.levelname == 'WARNING' for record in caplog.records)


XMP_MAGIC = b'W5M0MpCehiHzreSzNTczkc9d'


def test_prevent_gs_invalid_xml(resources, outdir):
    generate_pdfa_ps(outdir / 'pdfa.ps')

    # Inject a string with a trailing nul character into the DocumentInfo
    # dictionary of this PDF, as often occurs in practice.
    with pikepdf.open(resources / 'trivial.pdf') as pdf:
        pdf.Root.DocumentInfo = pikepdf.Dictionary(
            Title=b'String with trailing nul\x00'
        )
        pdf.save(outdir / 'layers.rendered.pdf', fix_metadata_version=False)

    _, options, _ = get_parser_options_plugins(
        args=[
            '-j',
            '1',
            '--output-type',
            'pdfa-2',
            'a.pdf',
            'b.pdf',
        ]
    )
    pdfinfo = PdfInfo(outdir / 'layers.rendered.pdf')
    context = PdfContext(
        options, outdir, outdir / 'layers.rendered.pdf', pdfinfo, get_plugin_manager([])
    )

    convert_to_pdfa(
        str(outdir / 'layers.rendered.pdf'), str(outdir / 'pdfa.ps'), context
    )

    contents = (outdir / 'pdfa.pdf').read_bytes()
    # Since the XML may be invalid, we scan instead of actually feeding it
    # to a parser.

    xmp_start = contents.find(XMP_MAGIC)
    xmp_end = contents.rfind(b'<?xpacket end', xmp_start)
    assert 0 < xmp_start < xmp_end
    # Ensure we did not carry the nul forward.
    assert contents.find(b'&#0;', xmp_start, xmp_end) == -1, "found escaped nul"
    assert contents.find(b'\x00', xmp_start, xmp_end) == -1


@pytest.mark.xfail(
    ghostscript.version() >= Version('10.01.2'),
    reason=(
        "Ghostscript now exits with an error on invalid DocumentInfo, defeating "
        "this test.",
    ),
)
def test_malformed_docinfo(caplog, resources, outdir):
    generate_pdfa_ps(outdir / 'pdfa.ps')

    with pikepdf.open(resources / 'trivial.pdf') as pdf:
        pdf.trailer.Info = pikepdf.Stream(pdf, b"<xml></xml>")
        pdf.save(outdir / 'layers.rendered.pdf', fix_metadata_version=False)

    _, options, _ = get_parser_options_plugins(
        args=[
            '-j',
            '1',
            '--output-type',
            'pdfa-2',
            'a.pdf',
            'b.pdf',
        ]
    )
    pdfinfo = PdfInfo(outdir / 'layers.rendered.pdf')
    context = PdfContext(
        options, outdir, outdir / 'layers.rendered.pdf', pdfinfo, get_plugin_manager([])
    )

    convert_to_pdfa(
        str(outdir / 'layers.rendered.pdf'), str(outdir / 'pdfa.ps'), context
    )

    print(caplog.records)
    assert any(
        'malformed DocumentInfo block' in record.message for record in caplog.records
    )
