# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Confirm that every stream in a finished PDF can be decoded.

Each stream is checked in the way that is cheapest for its filters, instead of
decoding everything to full resolution. By the time the output is checked,
pikepdf has already opened and saved the file several times, and obsolete
filters have been rewritten as Flate, so only a few filter chains need
dedicated handling.
"""

from __future__ import annotations

import io
import logging
import warnings
import zlib
from collections.abc import Callable

import pikepdf
from pikepdf import PdfImage
from pikepdf.models.image import UnsupportedImageTypeError
from PIL import Image
from PIL.Jpeg2KImagePlugin import Jpeg2KImageFile

log = logging.getLogger(__name__)

_CHUNK = 1 << 16

# Lossless filters that qpdf decodes itself, for chains without a dedicated check
_QPDF_LOSSLESS = frozenset(
    {
        '/FlateDecode',
        '/LZWDecode',
        '/ASCIIHexDecode',
        '/ASCII85Decode',
        '/RunLengthDecode',
    }
)


def _filters(stream: pikepdf.Stream) -> list[str]:
    filter_ = stream.get(pikepdf.Name.Filter)
    if filter_ is None:
        return []
    if isinstance(filter_, pikepdf.Array):
        return [str(f) for f in filter_]
    return [str(filter_)]


def _inflate(data: bytes, *, keep: bool) -> bytes:
    """Inflate *data* in chunks, keeping the output only if asked to.

    Raises:
        zlib.error: If the data is corrupt or ends before the zlib stream does.
    """
    decompressor = zlib.decompressobj()
    kept = []
    view = memoryview(data)
    for start in range(0, len(view), _CHUNK):
        out = decompressor.decompress(view[start : start + _CHUNK])
        if keep:
            kept.append(out)
    kept.append(decompressor.flush())
    if not decompressor.eof:
        raise zlib.error("compressed data ends before the end of the stream")
    return b''.join(kept) if keep else b''


def _check_jpeg(data: bytes) -> None:
    """Decode the JPEG at 1/8 scale.

    Draft mode still reads all of the entropy-coded data, so truncation and
    structural damage are found, but skips most of the inverse DCT.
    """
    with Image.open(io.BytesIO(data)) as im:
        im.draft(im.mode, (max(1, im.width // 8), max(1, im.height // 8)))
        im.load()


def _check_jpx(data: bytes) -> None:
    """Decode the JPEG 2000 image at reduced resolution.

    A codestream with fewer resolution levels than the reduction cannot be
    decoded reduced, so it is decoded at full resolution before being called
    damaged.
    """
    try:
        with Image.open(io.BytesIO(data)) as im:
            if not isinstance(im, Jpeg2KImageFile):
                raise ValueError("JPXDecode stream is not JPEG 2000 data")
            im.reduce = 5
            im.load()
    except OSError:
        with Image.open(io.BytesIO(data)) as im:
            im.load()


def _check_bilevel(stream: pikepdf.Stream) -> None:
    """Decode a CCITT or JBIG2 image with pikepdf's helpers."""
    try:
        PdfImage(stream).as_pil_image().load()
    except (pikepdf.DependencyError, UnsupportedImageTypeError) as e:
        log.debug("Could not check image %r: %s", stream.objgen, e)


def _check_stream(stream: pikepdf.Stream) -> None:
    filters = _filters(stream)
    if not filters:
        return
    if filters == ['/FlateDecode']:
        _inflate(stream.read_raw_bytes(), keep=False)
    elif filters == ['/DCTDecode']:
        _check_jpeg(stream.read_raw_bytes())
    elif filters == ['/FlateDecode', '/DCTDecode']:
        _check_jpeg(_inflate(stream.read_raw_bytes(), keep=True))
    elif filters == ['/JPXDecode']:
        _check_jpx(stream.read_raw_bytes())
    elif filters in (['/CCITTFaxDecode'], ['/JBIG2Decode']):
        _check_bilevel(stream)
    elif _QPDF_LOSSLESS.issuperset(filters):
        stream.read_bytes(pikepdf.StreamDecodeLevel.specialized)
    else:
        log.debug("Not checking stream %r with filters %s", stream.objgen, filters)


def check_streams(
    pdf: pikepdf.Pdf, progress: Callable[[int], None] | None = None
) -> list[str]:
    """Confirm that every stream in *pdf* can be decoded.

    Args:
        pdf: The PDF to check.
        progress: Called with the percentage of objects checked so far.

    Returns:
        A description of each stream that could not be decoded.
    """
    problems = []
    objects = list(pdf.objects)
    last_percent = -1
    for n, obj in enumerate(objects, start=1):
        if isinstance(obj, pikepdf.Stream):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', Image.DecompressionBombWarning)
                    _check_stream(obj)
            except Image.DecompressionBombError as e:
                log.debug("Not checking image %r: %s", obj.objgen, e)
            except (OSError, ValueError, zlib.error, pikepdf.PdfError) as e:
                num, gen = obj.objgen
                problems.append(
                    f"ERROR: stream {num} {gen} R ({', '.join(_filters(obj))}) "
                    f"could not be decoded: {e}"
                )
        percent = n * 100 // len(objects)
        if progress and percent != last_percent:
            progress(percent)
            last_percent = percent
    if progress and last_percent != 100:
        progress(100)
    return problems
