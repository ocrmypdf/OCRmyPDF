# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Utilities for PDF/A production and confirmation with Ghostscript."""

from __future__ import annotations

import base64
import logging
from collections.abc import Iterator
from importlib.resources import files as package_files
from pathlib import Path

import pikepdf
from pikepdf import Array, Dictionary, Name, Pdf, Stream

log = logging.getLogger(__name__)

SRGB_ICC_PROFILE_NAME = 'sRGB.icc'


def _postscript_objdef(
    alias: str,
    dictionary: dict[str, str],
    *,
    stream_name: str | None = None,
    stream_data: bytes | None = None,
) -> Iterator[str]:
    assert (stream_name is None) == (stream_data is None)

    objtype = '/stream' if stream_name else '/dict'

    if stream_name:
        assert stream_data is not None
        a85_data = base64.a85encode(stream_data, adobe=True).decode('ascii')
        yield f'{stream_name} ' + a85_data
        yield 'def'

    if alias != '{Catalog}':  # Catalog needs no definition
        yield f'[/_objdef {alias} /type {objtype} /OBJ pdfmark'

    yield f'[{alias} <<'
    for key, val in dictionary.items():
        yield f'  {key} {val}'
    yield '>> /PUT pdfmark'

    if stream_name:
        yield f'[{alias} {stream_name[1:]} /PUT pdfmark'


def _make_postscript(icc_name: str, icc_data: bytes, colors: int) -> Iterator[str]:
    yield '%!'
    yield from _postscript_objdef(
        '{icc_PDFA}',  # Not an f-string
        {'/N': str(colors)},
        stream_name='/ICCProfile',
        stream_data=icc_data,
    )
    yield ''
    yield from _postscript_objdef(
        '{OutputIntent_PDFA}',
        {
            '/Type': '/OutputIntent',
            '/S': '/GTS_PDFA1',
            '/DestOutputProfile': '{icc_PDFA}',
            '/OutputConditionIdentifier': f'({icc_name})',  # Only f-string
        },
    )
    yield ''
    yield from _postscript_objdef(
        '{Catalog}', {'/OutputIntents': '[ {OutputIntent_PDFA} ]'}
    )


def generate_pdfa_ps(target_filename: Path, icc: str = 'sRGB'):
    """Create a Postscript PDFMARK file for Ghostscript PDF/A conversion.

    pdfmark is an extension to the Postscript language that describes some PDF
    features like bookmarks and annotations. It was originally specified Adobe
    Distiller, for Postscript to PDF conversion.

    Ghostscript uses pdfmark for PDF to PDF/A conversion as well. To use Ghostscript
    to create a PDF/A, we need to create a pdfmark file with the necessary metadata.

    This function takes care of the many version-specific bugs and peculiarities in
    Ghostscript's handling of pdfmark.

    The only information we put in specifies that we want the file to be a
    PDF/A, and we want to Ghostscript to convert objects to the sRGB colorspace
    if it runs into any object that it decides must be converted.

    Arguments:
        target_filename: filename to save
        icc: ICC identifier such as 'sRGB'
    References:
        Adobe PDFMARK Reference:
        https://opensource.adobe.com/dc-acrobat-sdk-docs/library/pdfmark/
    """
    if icc != 'sRGB':
        raise NotImplementedError("Only supporting sRGB")

    bytes_icc_profile = (
        package_files('ocrmypdf.data') / SRGB_ICC_PROFILE_NAME
    ).read_bytes()
    postscript = '\n'.join(_make_postscript(icc, bytes_icc_profile, 3))

    # We should have encoded everything to pure ASCII by this point, and
    # to be safe, only allow ASCII in PostScript
    Path(target_filename).write_text(postscript, encoding='ascii')
    return target_filename


def file_claims_pdfa(filename: Path):
    """Determines if the file claims to be PDF/A compliant.

    This only checks if the XMP metadata contains a PDF/A marker. It does not
    do full PDF/A validation.
    """
    with pikepdf.open(filename) as pdf:
        pdfmeta = pdf.open_metadata()
        if not pdfmeta.pdfa_status:
            return {
                'pass': False,
                'output': 'pdf',
                'conformance': 'No PDF/A metadata in XMP',
            }
        valid_part_conforms = {'1a', '1b', '2a', '2b', '2u', '3a', '3b', '3u'}
        # Raw value in XMP metadata returned by pikepdf is uppercase, but ISO
        # uses lower case for conformance levels.
        pdfa_status_iso = pdfmeta.pdfa_status.lower()
        conformance = f'PDF/A-{pdfa_status_iso}'
        pdfa_dict: dict[str, str | bool] = {}
        if pdfa_status_iso in valid_part_conforms:
            pdfa_dict['pass'] = True
            pdfa_dict['output'] = 'pdfa'
        pdfa_dict['conformance'] = conformance
    return pdfa_dict


def _load_srgb_icc_profile() -> bytes:
    """Load the sRGB ICC profile from package data."""
    return (package_files('ocrmypdf.data') / SRGB_ICC_PROFILE_NAME).read_bytes()


def _pdfa_part_conformance(output_type: str) -> tuple[str, str]:
    """Extract PDF/A part and conformance from output_type.

    Args:
        output_type: One of 'pdfa', 'pdfa-1', 'pdfa-2', 'pdfa-3'

    Returns:
        Tuple of (part, conformance) e.g., ('2', 'B')
    """
    mapping = {
        'pdfa': ('2', 'B'),
        'pdfa-1': ('1', 'B'),
        'pdfa-2': ('2', 'B'),
        'pdfa-3': ('3', 'B'),
    }
    return mapping.get(output_type, ('2', 'B'))


def add_pdfa_metadata(pdf: Pdf, part: str, conformance: str) -> None:
    """Add PDF/A XMP metadata declaration to a PDF.

    Args:
        pdf: An open pikepdf.Pdf object
        part: PDF/A part number ('1', '2', or '3')
        conformance: Conformance level ('A', 'B', or 'U')
    """
    with pdf.open_metadata() as meta:
        meta['pdfaid:part'] = part
        meta['pdfaid:conformance'] = conformance


def add_srgb_output_intent(pdf: Pdf) -> None:
    """Add sRGB ICC profile as OutputIntent to PDF catalog.

    This creates the required PDF/A OutputIntent structure with:
    - An ICC profile stream containing sRGB profile
    - An OutputIntent dictionary pointing to that profile
    - Updates the Catalog's OutputIntents array

    Args:
        pdf: An open pikepdf.Pdf object
    """
    icc_data = _load_srgb_icc_profile()

    # Create ICC profile stream
    icc_stream = Stream(pdf, icc_data)
    icc_stream[Name.N] = 3  # RGB has 3 components

    # Create OutputIntent dictionary
    output_intent = Dictionary({
        '/Type': Name.OutputIntent,
        '/S': Name('/GTS_PDFA1'),
        '/OutputConditionIdentifier': 'sRGB',
        '/DestOutputProfile': icc_stream,
    })

    # Add to catalog's OutputIntents array
    if Name.OutputIntents not in pdf.Root:
        pdf.Root[Name.OutputIntents] = Array([])

    # Check if sRGB OutputIntent already exists
    for intent in pdf.Root.OutputIntents:  # type: ignore[attr-defined]
        if str(intent.get(Name.OutputConditionIdentifier)) == 'sRGB':
            log.debug('sRGB OutputIntent already exists, skipping')
            return

    pdf.Root.OutputIntents.append(output_intent)


def speculative_pdfa_conversion(
    input_file: Path,
    output_file: Path,
    output_type: str,
) -> Path:
    """Attempt to convert a PDF to PDF/A by adding required structures.

    This function creates a copy of the input PDF and adds:
    1. sRGB ICC profile as OutputIntent
    2. XMP metadata declaring PDF/A conformance

    This approach works for PDFs that are already mostly PDF/A compliant
    but lack the formal declarations. It does NOT perform color conversion,
    font embedding, or other transformations that Ghostscript does.

    Args:
        input_file: Path to input PDF
        output_file: Path where output PDF should be written
        output_type: One of 'pdfa', 'pdfa-1', 'pdfa-2', 'pdfa-3'

    Returns:
        Path to the output file

    Raises:
        pikepdf.PdfError: If the PDF cannot be opened or modified
    """
    part, conformance = _pdfa_part_conformance(output_type)

    with Pdf.open(input_file) as pdf:
        add_srgb_output_intent(pdf)
        add_pdfa_metadata(pdf, part, conformance)

        pdf.save(output_file)

    log.debug('Speculative PDF/A conversion complete: %s', output_file)
    return output_file
