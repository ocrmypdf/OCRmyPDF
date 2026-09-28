# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Utilities for PDF/A production, with pikepdf or Ghostscript."""

from __future__ import annotations

import base64
import logging
from collections.abc import Iterator
from contextlib import suppress
from importlib.resources import files as package_files
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pikepdf
from pikepdf import Name, NamePath, Object, Pdf

if TYPE_CHECKING:
    from pikepdf.pdfa import Flavour, PrepareResult, Report

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
    with pikepdf.open(filename, conversion_mode='explicit') as pdf:
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


def _cid_font_is_embedded(type0_font: Object) -> bool:
    """Return True if a Type0 font's CID descendant carries embedded glyphs."""
    for descendant in type0_font.get(Name.DescendantFonts, []):
        # A malformed PDF may store a non-dictionary here; `key in descriptor`
        # raises on those, so get_dict reduces anything that is not a
        # dictionary to None before we probe it.
        descriptor = descendant.get_dict(Name.FontDescriptor)
        if descriptor is not None and any(
            key in descriptor for key in (Name.FontFile, Name.FontFile2, Name.FontFile3)
        ):
            return True
    return False


def find_nonembedded_cid_fonts(pdf: Pdf) -> set[str]:
    """Find CID-keyed (Type0) fonts that lack embedded glyph data.

    PDF/A requires every font to be embedded. When Ghostscript converts a PDF
    to PDF/A it must substitute and embed a replacement for any non-embedded
    font. For CID-keyed fonts -- which is how CJK text is encoded, including the
    OCR text layers produced by Adobe Acrobat -- this substitution routinely
    corrupts the character-to-Unicode mapping, silently destroying the
    searchable text. Detecting these fonts lets the caller refuse PDF/A
    conversion rather than emit corrupted output.

    Simple (non-CID) non-embedded fonts are not reported: Ghostscript
    substitutes standard encodings for them without corrupting the text, and
    they are far too common to treat as conversion blockers.

    Args:
        pdf: An open ``pikepdf.Pdf`` to scan.

    Returns:
        The set of ``BaseFont`` names of non-embedded CID fonts found.
    """
    found: set[str] = set()
    for font in _iter_fonts(pdf):
        try:
            if font.get(Name.Subtype) == Name.Type0 and not _cid_font_is_embedded(font):
                found.add(_font_basename(font))
        except (AttributeError, TypeError, KeyError):
            continue
    return found


def _iter_fonts(pdf: Pdf) -> Iterator[Object]:
    """Yield the font dictionaries used by pages, forms and annotations."""

    def fonts_in(container: Object, depth: int = 0) -> Iterator[Object]:
        if depth > 10:
            return
        # A well-formed PDF stores dictionaries under /Resources, /Font and
        # /XObject, but a malformed one (common in OCR workloads) may store an
        # array, a name, or another non-dictionary object. get_dict reduces
        # every one of those to "no fonts" rather than let the scan crash
        # (issue #1713).
        for font in (container.get_dict(NamePath.Resources.Font) or {}).values():
            if isinstance(font, pikepdf.Dictionary):
                yield font
        for xobj in (container.get_dict(NamePath.Resources.XObject) or {}).values():
            if isinstance(xobj, pikepdf.Stream) and xobj.get(Name.Subtype) == Name.Form:
                yield from fonts_in(xobj, depth + 1)

    def appearance_streams(page: Object) -> Iterator[Object]:
        annots = page.get(Name.Annots)
        if not isinstance(annots, pikepdf.Array):
            return
        for annot in annots:
            if not isinstance(annot, pikepdf.Dictionary):
                continue
            appearances = annot.get_dict(Name.AP)
            if appearances is None:
                continue
            for appearance in appearances.values():
                if isinstance(appearance, pikepdf.Stream):
                    yield appearance
                elif isinstance(appearance, pikepdf.Dictionary):
                    # Appearance subdictionary keyed by state, e.g. /On /Off
                    for state in appearance.as_dict().values():
                        if isinstance(state, pikepdf.Stream):
                            yield state

    for page in pdf.pages:
        yield from fonts_in(page.obj)
        for appearance in appearance_streams(page.obj):
            yield from fonts_in(appearance)
    # Default resources for form fields, which a viewer may use to regenerate
    # their appearances
    for font in (pdf.Root.get_dict(NamePath.AcroForm.DR.Font) or {}).values():
        if isinstance(font, pikepdf.Dictionary):
            yield font


def _font_basename(font: Object) -> str:
    """Return a font's /BaseFont as text, without the leading slash."""
    name = font.get(Name.BaseFont, Name('/(unnamed)'))
    try:
        basefont = str(name)
    except UnicodeDecodeError:
        # Name objects are byte sequences with no mandated encoding; e.g. CJK
        # foundry font names are often GBK, which is not valid UTF-8 (issue
        # #1727). Fall back to the hex-escaped PDF syntax form. Do not skip the
        # font: it is still non-embedded and must be reported.
        basefont = name.unparse().decode('ascii', 'replace')
    return basefont.lstrip('/')


def _font_is_embedded(font: Object) -> bool:
    """Return True if a font carries its own glyphs."""
    subtype = font.get(Name.Subtype)
    if subtype == Name.Type3:
        return True  # Glyphs are content streams in the font itself
    if subtype == Name.Type0:
        return _cid_font_is_embedded(font)
    descriptor = font.get_dict(Name.FontDescriptor)
    return descriptor is not None and any(
        key in descriptor for key in (Name.FontFile, Name.FontFile2, Name.FontFile3)
    )


def find_nonembedded_fonts(pdf: Pdf) -> set[str]:
    """Find all fonts, simple or CID-keyed, that lack embedded glyph data.

    PDF/A requires every font to be embedded, so Ghostscript substitutes and
    embeds a replacement for each font reported here.

    Args:
        pdf: An open ``pikepdf.Pdf`` to scan.

    Returns:
        The set of ``BaseFont`` names of non-embedded fonts found.
    """
    found: set[str] = set()
    for font in _iter_fonts(pdf):
        try:
            if not _font_is_embedded(font):
                found.add(_font_basename(font))
        except (AttributeError, TypeError, KeyError, ValueError):
            continue
    return found


_SIMPLE_FONT_SUBTYPES = (Name.Type1, Name.MMType1, Name.TrueType)
_SYMBOLIC_FLAG = 1 << 2
_BFCHAR_BLOCK_SIZE = 100  # Ghostscript 9.56 to 10.04 drop larger blocks


def _as_int(obj: object) -> int | None:
    """Return a PDF integer as int, whether or not pikepdf converted it."""
    if isinstance(obj, (int, pikepdf.Integer)) and not isinstance(obj, bool):
        return int(obj)
    return None


def _simple_font_unicode_map(font: pikepdf.Dictionary) -> dict[int, str]:
    """Map a simple font's character codes to Unicode using its /Encoding.

    This is what PDF viewers do to extract text from a font without a
    /ToUnicode CMap: look up the glyph name that the encoding assigns to each
    code. Codes whose meaning depends on the font program's built-in encoding
    are left unmapped.
    """
    from pdfminer.encodingdb import EncodingDB, name2unicode

    encoding = font.get(Name.Encoding)
    if isinstance(encoding, Name):
        base: Object | None = encoding
        differences: Object = pikepdf.Array()
    elif isinstance(encoding, pikepdf.Dictionary):
        base = encoding.get(Name.BaseEncoding)
        differences = encoding.get(Name.Differences, pikepdf.Array())
    else:
        return {}

    mapping: dict[int, str] = {}
    if base is None:
        # With no base encoding, a nonsymbolic TrueType font, or a
        # nonsymbolic Type 1 font that is not embedded, starts from
        # StandardEncoding. Any other font starts from its built-in encoding.
        descriptor = font.get_dict(Name.FontDescriptor)
        flags = _as_int(descriptor.get(Name.Flags, 0)) if descriptor else 0
        embedded = descriptor is not None and any(
            key in descriptor for key in (Name.FontFile, Name.FontFile3)
        )
        symbolic = flags is None or bool(flags & _SYMBOLIC_FLAG)
        if not symbolic and (font.get(Name.Subtype) == Name.TrueType or not embedded):
            mapping.update(EncodingDB.encodings['StandardEncoding'])
    elif isinstance(base, Name):
        mapping.update(EncodingDB.encodings.get(str(base)[1:], {}))

    if isinstance(differences, pikepdf.Array):
        code = 0
        for item in differences:
            if (number := _as_int(item)) is not None:
                code = number
            elif isinstance(item, Name):
                mapping.pop(code, None)
                with suppress(KeyError, ValueError, UnicodeDecodeError):
                    mapping[code] = name2unicode(str(item)[1:])
                code += 1
    return {code: text for code, text in mapping.items() if 0 <= code <= 0xFF}


def _tounicode_cmap(mapping: dict[int, str]) -> bytes:
    """Write a /ToUnicode CMap for single-byte character codes."""
    lines = [
        '/CIDInit /ProcSet findresource begin',
        '12 dict begin',
        'begincmap',
        '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
        '/CMapName /Adobe-Identity-UCS def',
        '/CMapType 2 def',
        '1 begincodespacerange',
        '<00> <FF>',
        'endcodespacerange',
    ]
    entries = sorted(mapping.items())
    for start in range(0, len(entries), _BFCHAR_BLOCK_SIZE):
        block = entries[start : start + _BFCHAR_BLOCK_SIZE]
        lines.append(f'{len(block)} beginbfchar')
        lines.extend(
            f'<{code:02X}> <{text.encode("utf-16-be").hex().upper()}>'
            for code, text in block
        )
        lines.append('endbfchar')
    lines += [
        'endcmap',
        'CMapName currentdict /CMap defineresource pop',
        'end',
        'end',
    ]
    return '\n'.join(lines).encode('ascii')


def add_simple_font_tounicode(pdf: Pdf) -> int:
    """Give simple fonts that lack /ToUnicode one derived from their /Encoding.

    Ghostscript rewrites simple TrueType fonts as CID fonts when it produces
    PDF/A. When such a font has no /ToUnicode, the text is only extractable
    through the glyph names of its /Encoding, which the rewritten font does not
    keep, so copying the text yields garbage or nothing (issue #1297).
    Ghostscript keeps a /ToUnicode, so writing out the mapping that viewers
    would derive from the glyph names preserves the text.

    Args:
        pdf: An open ``pikepdf.Pdf``, modified in place.

    Returns:
        The number of fonts that were given a /ToUnicode.
    """
    count = 0
    for obj in pdf.objects:
        if not isinstance(obj, pikepdf.Dictionary):
            continue
        try:
            if (
                obj.get(Name.Type) != Name.Font
                or obj.get(Name.Subtype) not in _SIMPLE_FONT_SUBTYPES
                or Name.ToUnicode in obj
            ):
                continue
            mapping = _simple_font_unicode_map(obj)
        except (AttributeError, TypeError, ValueError):
            continue
        if not mapping:
            continue
        obj.ToUnicode = pdf.make_stream(_tounicode_cmap(mapping))
        count += 1
    return count


def has_embedded_fonts(pdf: Pdf) -> bool:
    """Return True if any font in the PDF carries its own glyphs."""
    for font in _iter_fonts(pdf):
        try:
            if _font_is_embedded(font):
                return True
        except (AttributeError, TypeError, KeyError, ValueError):
            continue
    return False


STANDARD_14_FONTS = frozenset(
    {
        'Courier',
        'Courier-Bold',
        'Courier-BoldOblique',
        'Courier-Oblique',
        'Helvetica',
        'Helvetica-Bold',
        'Helvetica-BoldOblique',
        'Helvetica-Oblique',
        'Symbol',
        'Times-Bold',
        'Times-BoldItalic',
        'Times-Italic',
        'Times-Roman',
        'ZapfDingbats',
    }
)


def is_standard14_font(basefont: str) -> bool:
    """Return True if a font name is one of the PDF standard 14 fonts.

    Every PDF viewer and Ghostscript carry metric-compatible versions of these
    fonts, so substituting them does not change the document's appearance.
    """
    _prefix, _plus, name = basefont.rpartition('+')
    return name in STANDARD_14_FONTS


# PDF/A flavour for each --output-type that produces PDF/A. 'auto' (and any
# other value) makes PDF/A-2b, the same default as Ghostscript conversion.
_OUTPUT_TYPE_FLAVOURS = {
    'pdfa': '2b',
    'pdfa-1': '1b',
    'pdfa-2': '2b',
    'pdfa-3': '3b',
}


def output_type_to_flavour(output_type: str) -> Flavour:
    """Map an ``--output-type`` value to the PDF/A flavour it produces.

    Args:
        output_type: One of 'pdfa', 'pdfa-1', 'pdfa-2', 'pdfa-3' or 'auto'.

    Returns:
        The pikepdf PDF/A flavour; PDF/A-2b for 'auto' or an unknown value.
    """
    from pikepdf.pdfa import Flavour

    return Flavour(_OUTPUT_TYPE_FLAVOURS.get(output_type, '2b'))


def get_pdf_save_settings(output_type: str) -> dict[str, Any]:
    """Get pikepdf.Pdf.save settings for the given output type.

    For the PDF/A output types these are the complete settings pikepdf
    resolves for the flavour, with settings that would make the file
    invalid, or different from what was validated, pinned
    (`pikepdf.pdfa.resolve_save_kwargs`). Callers may change only the
    settings pikepdf leaves to the user, such as ``linearize`` and
    ``progress``.

    Args:
        output_type: 'pdf', or one of the PDF/A output types. For 'auto',
            pass the output type achieved, 'pdfa' or 'pdf'.
    """
    if output_type.startswith('pdfa'):
        from pikepdf.pdfa import resolve_save_kwargs

        return resolve_save_kwargs(
            output_type_to_flavour(output_type), compress_streams=True
        )
    return dict(
        preserve_pdfa=True,
        compress_streams=True,
        object_stream_mode=pikepdf.ObjectStreamMode.generate,
    )


def log_prepare_result(result: PrepareResult | None) -> None:
    """Log what `pikepdf.pdfa.prepare` changed, at the level pikepdf suggests.

    Removing hidden annotations discards content the user may care about, so
    it is a warning. Other changes the reader might notice are logged at info
    level, and the rest at debug level.
    """
    if result is None:
        return
    for level, sentence in result.messages():
        log.log(logging.getLevelName(level.upper()), '%s', sentence)


def repair_annotations_for_ghostscript(pdf: Pdf, *, report_removed: bool) -> bool:
    """Make annotation flags acceptable to PDF/A before Ghostscript converts.

    Ghostscript's PDF/A conversion drops every annotation without the Print
    flag, which loses hyperlinks from files whose producer did not set /F,
    and drops hidden or non-viewable annotations, which PDF/A does not
    permit. `pikepdf.pdfa.repair_annotation_flags` sets the Print flag on
    viewable annotations and removes the others, as speculative conversion
    does.

    Args:
        pdf: Opened PDF file, modified in place.
        report_removed: Warn about removed annotations, as speculative
            conversion does. Pass False if speculative conversion of the same
            file has already reported them.

    Returns:
        True if any annotation was changed or removed.
    """
    from pikepdf.pdfa import PrepareResult, repair_annotation_flags

    result = repair_annotation_flags(pdf)
    if result.removed:
        # Describe the removal in the same words as speculative conversion
        described = PrepareResult(
            annotations_removed=result.removed,
            annotations_removed_pages=frozenset(result.removed_pages),
        )
        for _level, sentence in described.messages():
            log.log(
                logging.WARNING if report_removed else logging.DEBUG, '%s', sentence
            )
    if result.print_flags_set:
        log.debug(
            "Set the Print flag on %d annotation(s) so that PDF/A conversion "
            "keeps them",
            result.print_flags_set,
        )
    return bool(result.removed or result.print_flags_set)


def prepare_pdfa(pdf: Pdf, output_type: str) -> PrepareResult:
    """Declare PDF/A in an open PDF that is to be saved as PDF/A.

    Runs `pikepdf.pdfa.prepare`, keeping the document's output intents,
    which were installed earlier by speculative conversion or by
    Ghostscript: it rewrites the XMP packet in the canonical form pikepdf's
    validator accepts, declares PDF/A conformance, sets DocInfo to agree
    with XMP, and repeats the structural repairs, which change nothing on a
    file that was already prepared. It is safe to call again after editing
    the metadata.

    Args:
        pdf: An open pikepdf.Pdf object
        output_type: One of 'pdfa', 'pdfa-1', 'pdfa-2', 'pdfa-3'
    """
    from pikepdf.pdfa import prepare

    result = prepare(pdf, output_type_to_flavour(output_type), output_intent=None)
    log_prepare_result(result)
    return result


def speculative_pdfa_conversion(
    input_file: Path,
    output_file: Path,
    output_type: str,
) -> Report:
    """Attempt to convert a PDF to PDF/A by adding and repairing structures.

    `pikepdf.pdfa.save` replaces the output intents with an sRGB PDF/A
    intent, removes image interpolation, removes annotations that are hidden
    or not viewable and sets the Print flag on the others, adds the /CIDSet
    that PDF/A-1 requires on subset CIDFonts, rewrites the XMP packet with
    only what PDF/A permits, declares PDF/A conformance, and saves with the
    settings of the flavour. It then validates the bytes written, and moves
    them to *output_file* only if they pass.

    This works for PDFs that are already mostly PDF/A compliant but lack the
    formal declarations. It does NOT perform color conversion, font
    embedding, or other transformations that Ghostscript does.

    Args:
        input_file: Path to input PDF
        output_file: Path where output PDF should be written
        output_type: One of 'pdfa', 'pdfa-1', 'pdfa-2', 'pdfa-3'

    Returns:
        pikepdf's validation report on the file written, which passed.

    Raises:
        pikepdf.pdfa.PdfaError: If the file written did not pass validation;
            ``e.report`` explains why. *output_file* is not written.
        pikepdf.PdfError: If the PDF cannot be opened or modified
    """
    from pikepdf.pdfa import save

    flavour = output_type_to_flavour(output_type)
    with Pdf.open(input_file, conversion_mode='explicit') as pdf:
        report = save(pdf, output_file, flavour, output_intent='sRGB')
    log_prepare_result(report.prepared)

    log.debug('Speculative PDF/A conversion complete: %s', output_file)
    return report
