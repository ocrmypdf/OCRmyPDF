# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF page processing pipeline functions."""

from __future__ import annotations

import datetime as dt
import logging
import warnings
from pathlib import Path
from typing import Any

import pikepdf
from pikepdf import Dictionary, Name, Pdf, XmpTypeWarning
from pikepdf import __version__ as PIKEPDF_VERSION
from pikepdf.models.metadata import PdfMetadata, decode_pdf_date, encode_pdf_date

from ocrmypdf._defaults import PROGRAM_NAME
from ocrmypdf._jobcontext import PdfContext
from ocrmypdf._version import __version__ as OCRMYPF_VERSION
from ocrmypdf.languages import iso_639_2_from_3

log = logging.getLogger(__name__)


def _attach_local_time_zone(naive: dt.datetime) -> dt.datetime | None:
    """Return *naive* with the local time zone attached, or None on failure.

    ``astimezone()`` interprets a naive datetime as local time. Some platforms
    cannot convert dates outside the range of the C library's time functions,
    such as dates before 1970 on Windows.
    """
    try:
        return naive.astimezone()
    except (ValueError, OverflowError, OSError):
        return None


def _utc_offset_label(when: dt.datetime) -> str:
    """Return the UTC offset of an aware datetime as text, e.g. ``UTC-08:00``."""
    offset = when.strftime('%z')
    return f'UTC{offset[:3]}:{offset[3:5]}'


def assume_local_time_zone(pdf_date: str) -> tuple[str, bool]:
    """Attach the local time zone to a PDF date string that has none.

    PDF dates may omit the time zone, in which case their relation to UTC is
    unknown. PDF/A validators disagree on how to interpret such dates, so we
    assume the date is local time on this machine.

    Args:
        pdf_date: A PDF date string, such as ``D:20160119123847``.

    Returns:
        The date string, with the local time zone attached if it had none,
        and True if it was changed. Strings that are not PDF dates, or already
        have a time zone, are returned unchanged.
    """
    try:
        parsed = decode_pdf_date(pdf_date)
    except (ValueError, TypeError):
        return pdf_date, False
    if parsed.tzinfo is not None:
        return pdf_date, False
    zoned = _attach_local_time_zone(parsed)
    if zoned is None:
        return pdf_date, False
    return encode_pdf_date(zoned), True


def get_docinfo(base_pdf: Pdf, context: PdfContext) -> dict[str, str]:
    """Read the document info and store it in a dictionary."""
    options = context.options

    def from_document_info(key):
        try:
            s = base_pdf.docinfo[key]
            return str(s)
        except (KeyError, TypeError):
            return ''

    pdfmark = {
        k: from_document_info(k)
        for k in ('/Title', '/Author', '/Keywords', '/Subject', '/CreationDate')
    }
    pdfmark['/CreationDate'], zone_assumed = assume_local_time_zone(
        pdfmark['/CreationDate']
    )
    if zone_assumed:
        created = decode_pdf_date(pdfmark['/CreationDate'])
        log.warning(
            "The input's creation date has no time zone; assumed the local "
            "time zone (%s). If the document was created elsewhere, run with "
            "the TZ environment variable set to that zone, e.g. "
            "TZ=Europe/Berlin.",
            _utc_offset_label(created),
        )
    if options.title:
        pdfmark['/Title'] = options.title
    if options.author:
        pdfmark['/Author'] = options.author
    if options.keywords:
        pdfmark['/Keywords'] = options.keywords
    if options.subject:
        pdfmark['/Subject'] = options.subject

    creator_tag = context.plugin_manager.get_ocr_engine(options=options).creator_tag(
        options
    )

    pdfmark['/Creator'] = f'{PROGRAM_NAME} {OCRMYPF_VERSION} / {creator_tag}'
    pdfmark['/Producer'] = f'pikepdf {PIKEPDF_VERSION}'
    pdfmark['/ModDate'] = encode_pdf_date(dt.datetime.now(dt.UTC))
    return pdfmark


def report_on_metadata(options, missing):
    if not missing:
        return
    if options.output_type.startswith('pdfa'):
        log.warning(
            "Some input metadata could not be copied because it is not "
            "permitted in PDF/A. You may wish to examine the output "
            "PDF's XMP metadata."
        )
        log.debug("The following metadata fields were not copied: %r", missing)
    else:
        log.error(
            "Some input metadata could not be copied."
            "You may wish to examine the output PDF's XMP metadata."
        )
        log.info("The following metadata fields were not copied: %r", missing)


def repair_docinfo_nuls(pdf):
    """If the DocumentInfo block contains NUL characters, remove them.

    If the DocumentInfo block is malformed, log an error and continue.
    """
    modified = False
    try:
        if not isinstance(pdf.docinfo, Dictionary):
            raise TypeError("DocumentInfo is not a dictionary")
        for k, v in pdf.docinfo.items():
            raw = pikepdf.as_bytes(v)
            if raw is not None and b'\x00' in raw:
                pdf.docinfo[k] = raw.replace(b'\x00', b'')
                modified = True
    except (TypeError, UnicodeDecodeError):
        # TypeError: DocumentInfo is not a dictionary, or its items are
        # unexpected types.
        # UnicodeDecodeError: a DocumentInfo key or value contains bytes that
        # are not valid PDFDocEncoding/UTF-16, e.g. a Latin-1 /Name key such as
        # /Saks#e5r. Older pikepdf raised while iterating such a block (#1540).
        log.error("File contains a malformed DocumentInfo block - continuing anyway.")
    return modified


def should_linearize(working_file: Path, context: PdfContext) -> bool:
    """Determine whether the PDF should be linearized.

    For smaller files, linearization is not worth the effort.
    """
    filesize = working_file.stat().st_size
    return filesize > (context.options.fast_web_view * 1_000_000)


# DocInfo entries whose XMP equivalent is a language alternative
_DOCINFO_LANGALT = {'/Title': 'dc:title', '/Subject': 'dc:description'}


def _docinfo_to_copy(docinfo: dict[str, str], meta: PdfMetadata) -> dict[str, str]:
    """Return the DocInfo entries that should be copied to XMP.

    Empty entries are the input's missing ones, so they are not copied, which
    would replace a value that is only in XMP with an empty one. A title or
    subject equal to the XMP default is not copied either, to keep the
    translations in the language alternative.
    """
    to_copy = {}
    for key, value in docinfo.items():
        if not value:
            continue
        xmp_key = _DOCINFO_LANGALT.get(key)
        if xmp_key is not None and meta.get(xmp_key) == value:
            continue
        to_copy[key] = value
    return to_copy


# XMP properties that describe this file rather than the document, and are
# written afresh for the output, so they are never copied from the input.
_XMP_REGENERATED_PROPERTIES = frozenset(
    {
        '{http://ns.adobe.com/xap/1.0/}MetadataDate',
        '{http://ns.adobe.com/xap/1.0/}ModifyDate',
        '{http://ns.adobe.com/xap/1.0/}CreatorTool',
        '{http://ns.adobe.com/pdf/1.3/}Producer',
        '{http://ns.adobe.com/pdf/1.3/}PDFVersion',
        '{http://purl.org/dc/elements/1.1/}format',
        '{http://ns.adobe.com/xap/1.0/mm/}DocumentID',
        '{http://ns.adobe.com/xap/1.0/mm/}InstanceID',
        '{http://ns.adobe.com/xap/1.0/mm/}VersionID',
        '{http://ns.adobe.com/xap/1.0/mm/}RenditionClass',
    }
)

# Namespaces of conformance claims and PDF/A extension schemas, which are
# declared for the output by the PDF/A conversion if they apply to it.
_XMP_REGENERATED_NAMESPACES = frozenset(
    {
        'http://www.aiim.org/pdfa/ns/id/',
        'http://www.aiim.org/pdfua/ns/id/',
        'http://www.aiim.org/pdfa/ns/extension/',
        'http://www.aiim.org/pdfa/ns/schema#',
        'http://www.aiim.org/pdfa/ns/property#',
        'http://www.aiim.org/pdfa/ns/type#',
        'http://www.aiim.org/pdfa/ns/field#',
    }
)


def _is_regenerated_xmp_property(key: str) -> bool:
    if key in _XMP_REGENERATED_PROPERTIES:
        return True
    namespace = key[1:].partition('}')[0]
    return namespace in _XMP_REGENERATED_NAMESPACES


def _open_xmp(pdf: Pdf) -> PdfMetadata:
    """Open the XMP metadata of a PDF for reading, tolerating malformed XMP."""
    return pdf.open_metadata(
        set_pikepdf_as_editor=False, update_docinfo=False, strict=False
    )


def _xmp_keys(pdf: Pdf) -> set[str]:
    """Return the Clark names of the top-level XMP properties of a PDF.

    Properties are read from every rdf:Description, whatever its rdf:about.
    """
    return {key for key in _open_xmp(pdf) if key.startswith('{')}


def _copy_missing_xmp(original: Pdf, pdf: Pdf, excluded: set[str]) -> None:
    """Copy XMP properties that are in *original* but missing from *pdf*.

    Ghostscript writes the XMP of a PDF/A from DocInfo alone, dropping
    properties that have no DocInfo equivalent, such as dc:contributor. The
    properties are copied with their whole value: every language of a
    language alternative, array order, structures and qualifiers. Properties
    that are not permitted in PDF/A are removed afterwards, when PDF/A is
    declared again.

    Args:
        original: The input PDF.
        pdf: The PDF whose XMP is to receive the properties.
        excluded: Clark names of properties not to copy.
    """
    source = _open_xmp(original)
    keys = [
        key
        for key in source
        if key.startswith('{') and not _is_regenerated_xmp_property(key)
    ]
    with (
        warnings.catch_warnings(),
        _open_xmp(pdf) as meta,
    ):
        # The input's XMP is copied as it is, whatever its structure;
        # declaring PDF/A later removes or repairs what PDF/A does not permit
        warnings.simplefilter('ignore', XmpTypeWarning)
        meta.copy_properties(source, keys, exclude=excluded)


# The title Ghostscript writes to the XMP of a PDF/A whose input has none;
# Ghostscript 10.08 encloses it in single quotes
_GHOSTSCRIPT_UNTITLED = frozenset({'Untitled', "'Untitled'"})


def _fix_metadata(meta_original: PdfMetadata, meta_pdf: PdfMetadata):
    # If xmp:CreateDate is missing, set it to the modify date to
    # ensure consistency with Ghostscript.
    if 'xmp:CreateDate' not in meta_pdf:
        meta_pdf['xmp:CreateDate'] = meta_pdf.get('xmp:ModifyDate', '')
    if meta_pdf.get('dc:title') in _GHOSTSCRIPT_UNTITLED and (
        'dc:title' not in meta_original
    ):
        # Ghostscript likes to set title to Untitled if omitted from input.
        # Reverse this, because PDF/A TechNote 0003:Metadata in PDF/A-1
        # and the XMP Spec do not make this recommendation.
        del meta_pdf['dc:title']


def _unset_empty_metadata(meta: PdfMetadata, options):
    """Unset metadata fields that were explicitly set to empty strings.

    If the user explicitly specified an empty string for any of the
    following, they should be unset and not reported as missing in
    the output pdf. Note that some metadata fields use differing names
    between PDF/A and PDF.
    """
    if options.title == '' and 'dc:title' in meta:
        del meta['dc:title']  # PDF/A and PDF
    if options.author == '':
        if 'dc:creator' in meta:
            del meta['dc:creator']  # PDF/A (Not xmp:CreatorTool)
        if 'pdf:Author' in meta:
            del meta['pdf:Author']  # PDF
    if options.subject == '':
        if 'dc:description' in meta:
            del meta['dc:description']  # PDF/A
        if 'dc:subject' in meta:
            del meta['dc:subject']  # PDF
    if options.keywords == '' and 'pdf:Keywords' in meta:
        del meta['pdf:Keywords']  # PDF/A and PDF


def _set_language(pdf: Pdf, languages: list[str]):
    """Set the language of the PDF."""
    if Name.Lang in pdf.Root or not languages:
        return  # Already set or can't change
    primary_language_iso639_3 = languages[0]
    if not primary_language_iso639_3:
        return
    iso639_2 = iso_639_2_from_3(primary_language_iso639_3)
    if not iso639_2:
        return
    pdf.Root.Lang = iso639_2


class PikepdfProgress:
    """Adapt a progress bar class to pikepdf's percent-complete callback."""

    def __init__(self, progressbar_class, enable: bool = True, *, desc: str):
        self.progressbar_class = progressbar_class
        self.progressbar = self.progressbar_class(
            total=100, desc=desc, unit='%', disable=not enable
        )

    def __enter__(self):
        self.progressbar.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.progressbar.__exit__(exc_type, exc_value, traceback)

    def __call__(self, percent: int):
        if not self.progressbar_class:
            return
        self.progressbar.update(completed=percent)


def metadata_fixup(
    working_file: Path,
    context: PdfContext,
    pdf_save_settings: dict[str, Any],
    *,
    pdfa_output_type: str | None = None,
) -> Path:
    """Fix certain metadata fields whether PDF or PDF/A.

    Override some of Ghostscript's metadata choices.

    Also report on metadata in the input file that was not retained during
    conversion.

    Args:
        working_file: The PDF to fix.
        context: The PDF context.
        pdf_save_settings: Settings for saving the fixed PDF.
        pdfa_output_type: If the working file is PDF/A, the PDF/A output type
            ('pdfa', 'pdfa-1', 'pdfa-2' or 'pdfa-3') it conforms to. PDF/A
            is then declared again with `pikepdf.pdfa.prepare`, which
            rewrites the XMP packet in the canonical form pikepdf's validator
            accepts and sets DocInfo to agree with it.
    """
    output_file = context.get_path('metafix.pdf')
    options = context.options

    pbar_class = context.plugin_manager.get_progressbar_class()
    with (
        Pdf.open(context.origin, conversion_mode='explicit') as original,
        Pdf.open(working_file, conversion_mode='explicit') as pdf,
        PikepdfProgress(pbar_class, options.progress_bar, desc="Linearizing") as pbar,
    ):
        docinfo = get_docinfo(original, context)
        with (
            original.open_metadata(
                set_pikepdf_as_editor=False, update_docinfo=False, strict=False
            ) as meta_original,
            pdf.open_metadata() as meta_pdf,
        ):
            meta_pdf.load_from_docinfo(
                _docinfo_to_copy(docinfo, meta_pdf),
                delete_missing=False,
                raise_failure=False,
            )
            _fix_metadata(meta_original, meta_pdf)
            keys_before_unset = set(meta_original.keys())
            _unset_empty_metadata(meta_original, options)
            _unset_empty_metadata(meta_pdf, options)
            unset_keys = keys_before_unset - set(meta_original.keys())

        _set_language(pdf, options.languages)
        if pdfa_output_type is not None:
            from ocrmypdf.pdfa import prepare_pdfa

            _copy_missing_xmp(original, pdf, excluded=unset_keys)
            prepare_pdfa(pdf, pdfa_output_type)
        meta_missing = {
            key
            for key in _xmp_keys(original) - _xmp_keys(pdf) - unset_keys
            if not _is_regenerated_xmp_property(key)
        }
        report_on_metadata(options, meta_missing)
        pdf.save(output_file, **(pdf_save_settings | {'progress': pbar}))

    return output_file
