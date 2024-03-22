# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Utilities for PDF/A production and confirmation with Ghostspcript."""

from __future__ import annotations

import base64
from collections.abc import Iterator
from importlib.resources import files as package_files
from pathlib import Path

import pikepdf

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
        valid_part_conforms = {'1A', '1B', '2A', '2B', '2U', '3A', '3B', '3U'}
        conformance = f'PDF/A-{pdfmeta.pdfa_status}'
        pdfa_dict: dict[str, str | bool] = {}
        if pdfmeta.pdfa_status in valid_part_conforms:
            pdfa_dict['pass'] = True
            pdfa_dict['output'] = 'pdfa'
        pdfa_dict['conformance'] = conformance
    return pdfa_dict
