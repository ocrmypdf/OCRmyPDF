# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Runtime patches for defects in fpdf2 that damage the OCR text layer.

fpdf2 writes every entry of a font's ToUnicode CMap in a single
``beginbfchar``/``endbfchar`` block, and for CFF CID-keyed fonts (such as the
Noto Sans CJK OpenType fonts) every entry of the font's Encoding CMap in a
single ``begincidchar``/``endcidchar`` block. The CMap specification (ISO
32000-2 section 9.10.3, via the Adobe CMap and CIDFont Files Specification)
allows at most 100 entries per block. Ghostscript 9.56.0 through 10.04.x
reject an oversized block with a syntax error and drop the whole CMap when
writing PDF/A. A dropped ToUnicode CMap makes text extraction return raw
glyph ids instead of characters; a dropped Encoding CMap also makes the
wrong glyphs render (https://github.com/py-pdf/fpdf2/issues/1952). Any page
with more than 100 distinct glyphs is affected, which is nearly every page of
prose.

fpdf2 2.8.9 splits the ToUnicode blocks (py-pdf/fpdf2#1954) but not the
Encoding CMap of CFF CID-keyed fonts, so this patch stays in place for every
fpdf2 release.

Rather than rewriting fpdf2's font serializer, which is one very long
method, we intercept the ToUnicode content stream at the point fpdf2 registers
it as a PDF object and split its blocks to the permitted size.
"""

from __future__ import annotations

import logging
import re
import zlib
from typing import Any

from fpdf.output import OutputProducer
from fpdf.syntax import PDFContentStream
from packaging.version import Version

log = logging.getLogger(__name__)

# Maximum number of entries in one begin*/end* CMap block, per the spec.
CMAP_BLOCK_LIMIT = 100

# First fpdf2 release that splits every CMap block itself, once one exists.
# While this is None, every fpdf2 version is patched. fpdf2 2.8.9 does not
# qualify: it splits ToUnicode bfchar blocks but not the Encoding cidchar
# block of CFF CID-keyed fonts.
FPDF2_CMAP_BLOCKS_FIXED: Version | None = None

_CMAP_PREFIX = b'/CIDInit /ProcSet findresource begin'

# One begin*/end* block: declared count, block kind, and body of one entry per
# line. Bodies are hex strings and integers, never nested, so a non-greedy
# match up to the matching end operator is safe.
_BLOCK_RE = re.compile(
    rb'(?P<count>\d+) begin(?P<kind>bfchar|bfrange|cidchar|cidrange)\n'
    rb'(?P<body>.*?)end(?P=kind)\n',
    flags=re.DOTALL,
)

_PATCH_MARKER = '_ocrmypdf_cmap_blocks_patch'


def split_cmap_blocks(cmap: bytes) -> bytes:
    """Split oversized mapping blocks in a CMap into blocks of at most 100 entries.

    CMaps whose blocks are already within the limit are returned unchanged.
    Content that is not a CMap is returned unchanged.
    """
    if not cmap.startswith(_CMAP_PREFIX):
        return cmap

    def rewrite(match: re.Match[bytes]) -> bytes:
        kind = match.group('kind')
        entries = [line for line in match.group('body').split(b'\n') if line]
        if len(entries) <= CMAP_BLOCK_LIMIT:
            return match.group(0)
        blocks = []
        for start in range(0, len(entries), CMAP_BLOCK_LIMIT):
            chunk = entries[start : start + CMAP_BLOCK_LIMIT]
            blocks.append(
                b'%d begin%s\n%s\nend%s\n' % (len(chunk), kind, b'\n'.join(chunk), kind)
            )
        return b''.join(blocks)

    return _BLOCK_RE.sub(rewrite, cmap)


def fpdf2_needs_cmap_patch() -> bool:
    """Does the installed fpdf2 emit CMap blocks larger than the spec permits?"""
    if FPDF2_CMAP_BLOCKS_FIXED is None:
        return True
    from fpdf import __version__

    return Version(__version__) < FPDF2_CMAP_BLOCKS_FIXED


def _fix_content_stream(pdf_obj: PDFContentStream) -> None:
    filter_ = getattr(pdf_obj, 'filter', None)
    contents = pdf_obj._contents
    compressed = filter_ is not None
    if compressed:
        if str(filter_) != '/FlateDecode':
            return
        contents = zlib.decompress(contents)
    if not contents.startswith(_CMAP_PREFIX):
        return
    fixed = split_cmap_blocks(contents)
    if fixed == contents:
        return
    if compressed:
        fixed = zlib.compress(fixed, level=pdf_obj._COMPRESSION_LEVEL)
    pdf_obj._contents = fixed
    pdf_obj.length = len(fixed)


def install_fpdf2_patches() -> None:
    """Install OCRmyPDF's fpdf2 patches. Safe to call more than once."""
    if not fpdf2_needs_cmap_patch():
        return
    original = OutputProducer._add_pdf_obj
    if getattr(original, _PATCH_MARKER, False):
        return

    def _add_pdf_obj(self: OutputProducer, pdf_obj: Any, *args: Any, **kwargs: Any):
        if isinstance(pdf_obj, PDFContentStream):
            _fix_content_stream(pdf_obj)
        return original(self, pdf_obj, *args, **kwargs)

    setattr(_add_pdf_obj, _PATCH_MARKER, True)
    OutputProducer._add_pdf_obj = _add_pdf_obj  # type: ignore[method-assign]
    log.debug("Installed fpdf2 ToUnicode CMap block-splitting patch")
