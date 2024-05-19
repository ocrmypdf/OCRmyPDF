# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF page processing pipeline functions."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pikepdf import Dictionary, Name, Pdf
from pikepdf import __version__ as PIKEPDF_VERSION
from pikepdf.models.metadata import PdfMetadata, encode_pdf_date

from ocrmypdf._jobcontext import PdfContext
from ocrmypdf._version import PROGRAM_NAME
from ocrmypdf._version import __version__ as OCRMYPF_VERSION
from ocrmypdf.languages import iso_639_2_from_3

log = logging.getLogger(__name__)


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
    if options.title:
        pdfmark['/Title'] = options.title
    if options.author:
        pdfmark['/Author'] = options.author
    if options.keywords:
        pdfmark['/Keywords'] = options.keywords
    if options.subject:
        pdfmark['/Subject'] = options.subject

    creator_tag = context.plugin_manager.hook.get_ocr_engine().creator_tag(options)

    pdfmark['/Creator'] = f'{PROGRAM_NAME} {OCRMYPF_VERSION} / {creator_tag}'
    pdfmark['/Producer'] = f'pikepdf {PIKEPDF_VERSION}'
    pdfmark['/ModDate'] = encode_pdf_date(datetime.now(timezone.utc))
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
            if isinstance(v, str) and b'\x00' in bytes(v):
                pdf.docinfo[k] = bytes(v).replace(b'\x00', b'')
                modified = True
    except TypeError:
        # TypeError can also be raised if dictionary items are unexpected types
        log.error("File contains a malformed DocumentInfo block - continuing anyway.")
    return modified


def should_linearize(working_file: Path, context: PdfContext) -> bool:
    """Determine whether the PDF should be linearized.

    For smaller files, linearization is not worth the effort.
    """
    filesize = os.stat(working_file).st_size
    if filesize > (context.options.fast_web_view * 1_000_000):
        return True
    return False


def _fix_metadata(meta_original: PdfMetadata, meta_pdf: PdfMetadata):
    # If xmp:CreateDate is missing, set it to the modify date to
    # ensure consistency with Ghostscript.
    if 'xmp:CreateDate' not in meta_pdf:
        meta_pdf['xmp:CreateDate'] = meta_pdf.get('xmp:ModifyDate', '')
    if meta_pdf.get('dc:title') == 'Untitled':
        # Ghostscript likes to set title to Untitled if omitted from input.
        # Reverse this, because PDF/A TechNote 0003:Metadata in PDF/A-1
        # and the XMP Spec do not make this recommendation.
        if 'dc:title' not in meta_original:
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


class MetadataProgress:
    def __init__(self, progressbar_class):
        self.progressbar_class = progressbar_class
        self.progressbar = self.progressbar_class(
            total=100, desc="Linearizing", unit='%'
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
    working_file: Path, context: PdfContext, pdf_save_settings: dict[str, Any]
) -> Path:
    """Fix certain metadata fields whether PDF or PDF/A.

    Override some of Ghostscript's metadata choices.

    Also report on metadata in the input file that was not retained during
    conversion.
    """
    output_file = context.get_path('metafix.pdf')
    options = context.options

    pbar_class = context.plugin_manager.hook.get_progressbar_class()
    with (
        Pdf.open(context.origin) as original,
        Pdf.open(working_file) as pdf,
        MetadataProgress(pbar_class) as pbar,
    ):
        docinfo = get_docinfo(original, context)
        with (
            original.open_metadata(
                set_pikepdf_as_editor=False, update_docinfo=False, strict=False
            ) as meta_original,
            pdf.open_metadata() as meta_pdf,
        ):
            meta_pdf.load_from_docinfo(
                docinfo, delete_missing=False, raise_failure=False
            )
            _fix_metadata(meta_original, meta_pdf)
            _unset_empty_metadata(meta_original, options)
            _unset_empty_metadata(meta_pdf, options)
            meta_missing = set(meta_original.keys()) - set(meta_pdf.keys())
            report_on_metadata(options, meta_missing)

        _set_language(pdf, options.languages)
        pdf.save(output_file, progress=pbar, **pdf_save_settings)

    return output_file
