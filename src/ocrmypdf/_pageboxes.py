# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-FileCopyrightText: 2025 ajdlinux
# SPDX-License-Identifier: MPL-2.0

"""Validate and repair malformed page-boundary boxes.

A page's boundary boxes (``/MediaBox``, ``/CropBox``, ``/TrimBox``, ``/ArtBox``,
``/BleedBox``) are sometimes malformed in ways that PDF readers tolerate but
that crash or corrupt downstream processing. This module normalizes them in
place following the PDF 2.0 specification (ISO 32000-2:2020):

- **Non-decimal coordinates** (§7.3.3): a coordinate written in exponential
  notation is invalid PDF number syntax and is stored by qpdf/pikepdf as a
  string. We coerce it back to a number (issue #1398).
- **Reversed corners** (§7.9.5): a rectangle is "a pair of diagonally opposite
  corners"; ``[llx lly urx ury]`` is only the typical order. We normalize to
  ``[min_x, min_y, max_x, max_y]`` (issue #1526).
- **Sub-box outside the MediaBox** (§14.11.2): "If the bounds of the crop,
  trim, bleed or art box extends outside of the bounds of the media box, a
  processor shall treat the box as its intersection with the media box." We
  clamp to that intersection, or discard the sub-box (so it inherits the
  MediaBox) when the intersection is empty (issue #1400).

A rectangle is treated as empty when its width or height is ``<= 0``; PDF 2.0
permits zero-dimension rectangles and defines no minimum page size, so no other
size floor is imposed.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import pikepdf
from pikepdf import Name

log = logging.getLogger(__name__)

_SUBBOXES = ('CropBox', 'TrimBox', 'ArtBox', 'BleedBox')


@dataclass(frozen=True, slots=True)
class BoxRepair:
    """A single change made to a page box.

    Attributes:
        box: The box name, e.g. ``"CropBox"``.
        kind: One of ``"reordered"`` (reversed corners normalized; lossless),
            ``"recoded"`` (non-numeric/exponential coordinate coerced),
            ``"clamped"`` (sub-box clamped to the MediaBox), ``"discarded"``
            (sub-box removed because its MediaBox intersection was empty), or
            ``"degenerate_mediabox"`` (MediaBox has zero width or height).
    """

    box: str
    kind: str


@dataclass(frozen=True, slots=True)
class BoxRepairMessage:
    """A log message describing a repair made on one or more pages."""

    level: int
    text: str


@dataclass(frozen=True, slots=True)
class _ParsedBox:
    """A box array coerced to floats with its corners in standard order.

    Attributes:
        values: The normalized ``[min_x, min_y, max_x, max_y]``.
        recoded: True if any element needed string/exponential coercion.
        reordered: True if the corners were given in non-standard order.
    """

    values: list[float]
    recoded: bool
    reordered: bool


@dataclass(frozen=True, slots=True)
class _KindMessage:
    """Log severity and message template ({box} is substituted) for a repair."""

    level: int
    template: str


def _read_box(values: Sequence) -> _ParsedBox | None:
    """Coerce a box array to floats and normalize corner order.

    Returns None if the array is not four finite numbers.
    """
    if len(values) != 4:
        return None
    nums: list[float] = []
    recoded = False
    for v in values:
        try:
            n = float(v)
        except (TypeError, ValueError):
            try:
                n = float(str(v))
            except (TypeError, ValueError):
                return None
            recoded = True
        if not math.isfinite(n):
            return None
        nums.append(n)
    x0, y0, x1, y1 = nums
    normalized = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
    return _ParsedBox(normalized, recoded, reordered=normalized != nums)


def coerce_box(values: Iterable) -> list[float]:
    """Return box values coerced to floats with corner order normalized.

    Robust against exponential/string coordinates and reversed corners, so
    callers that only need to read a box (e.g. dimension calculations) do not
    crash on malformed input. Falls back to best-effort per-element coercion if
    the array is not four numbers.
    """
    values = list(values)
    result = _read_box(values)
    if result is not None:
        return result.values
    coerced = []
    for v in values:
        try:
            coerced.append(float(v))
        except (TypeError, ValueError):
            coerced.append(float(str(v)))
    return coerced


def _is_empty(box: Sequence[float]) -> bool:
    """A rectangle is empty when its width or height is non-positive."""
    return (box[2] - box[0]) <= 0 or (box[3] - box[1]) <= 0


def repair_page_boxes(page: pikepdf.Page) -> list[BoxRepair]:
    """Validate and repair the boundary boxes of a single page, in place.

    Returns the list of changes made (empty if the page was already valid).
    Only boxes that actually change are written back, so valid pages are left
    untouched. Performs no logging or I/O.
    """
    repairs: list[BoxRepair] = []

    # MediaBox is the reference rectangle; read it inheritance-aware.
    mediabox: list[float] | None = None
    try:
        mb_result = _read_box(list(page.mediabox.as_list()))
    except (AttributeError, KeyError, RuntimeError):
        mb_result = None
    if mb_result is not None:
        mediabox = mb_result.values
        if mb_result.reordered:
            repairs.append(BoxRepair('MediaBox', 'reordered'))
        if mb_result.recoded:
            repairs.append(BoxRepair('MediaBox', 'recoded'))
        if mb_result.recoded or mb_result.reordered:
            page.obj.MediaBox = pikepdf.Array(mediabox)
        if _is_empty(mediabox):
            repairs.append(BoxRepair('MediaBox', 'degenerate_mediabox'))
            mediabox = None  # don't clamp against a degenerate reference

    for box in _SUBBOXES:
        name = Name('/' + box)
        if name not in page.obj:
            continue
        try:
            sub_result = _read_box(list(page.obj[name]))
        except (TypeError, RuntimeError):
            continue
        if sub_result is None:
            continue
        values = sub_result.values
        if sub_result.reordered:
            repairs.append(BoxRepair(box, 'reordered'))
        if sub_result.recoded:
            repairs.append(BoxRepair(box, 'recoded'))
        if sub_result.recoded or sub_result.reordered:
            page.obj[name] = pikepdf.Array(values)

        if mediabox is None:
            continue
        intersection = [
            max(values[0], mediabox[0]),
            max(values[1], mediabox[1]),
            min(values[2], mediabox[2]),
            min(values[3], mediabox[3]),
        ]
        if _is_empty(intersection):
            del page.obj[name]
            repairs.append(BoxRepair(box, 'discarded'))
        elif intersection != values:
            page.obj[name] = pikepdf.Array(intersection)
            repairs.append(BoxRepair(box, 'clamped'))

    return repairs


_KIND_MESSAGES: dict[str, _KindMessage] = {
    'discarded': _KindMessage(
        logging.WARNING,
        '{box} lies outside the MediaBox and was discarded; '
        'the full page will be shown',
    ),
    'clamped': _KindMessage(
        logging.WARNING,
        '{box} extended beyond the MediaBox and was clamped to it',
    ),
    'recoded': _KindMessage(
        logging.WARNING,
        '{box} used invalid (e.g. exponential) coordinates, which were reinterpreted',
    ),
    'degenerate_mediabox': _KindMessage(
        logging.WARNING,
        'MediaBox has zero width or height and could not be repaired; '
        'output may be invalid',
    ),
    'reordered': _KindMessage(
        logging.DEBUG,
        '{box} corners were reversed and have been normalized',
    ),
}

# Kinds that change page appearance and warrant manual review of the output.
_INSPECT_KINDS = frozenset({'discarded', 'clamped', 'recoded'})
_INSPECT = ' Please visually inspect the output PDF.'


def _format_pages(pagenos: Iterable[int]) -> str:
    """Format 0-based page numbers as a compact 1-based range string."""
    nums = sorted(p + 1 for p in pagenos)
    ranges: list[tuple[int, int]] = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append((start, prev))
        start = prev = n
    ranges.append((start, prev))
    return ', '.join(f'{a}' if a == b else f'{a}-{b}' for a, b in ranges)


def summarize_box_repairs(
    repairs_by_page: Mapping[int, Sequence[BoxRepair]],
) -> list[BoxRepairMessage]:
    """Aggregate per-page repairs into log messages.

    Repairs are grouped by ``(kind, box)`` so a defect shared across many pages
    yields a single message listing the affected pages, rather than one message
    per page.
    """
    groups: dict[tuple[str, str], set[int]] = {}
    for pageno, repairs in repairs_by_page.items():
        for repair in repairs:
            groups.setdefault((repair.kind, repair.box), set()).add(pageno)

    messages: list[BoxRepairMessage] = []
    for (kind, box), pages in sorted(groups.items()):
        kind_message = _KIND_MESSAGES[kind]
        text = (
            f'Page(s) {_format_pages(pages)}: {kind_message.template.format(box=box)}.'
        )
        if kind in _INSPECT_KINDS:
            text += _INSPECT
        messages.append(BoxRepairMessage(kind_message.level, text))
    return messages


def log_box_repairs(repairs_by_page: Mapping[int, Sequence[BoxRepair]]) -> None:
    """Emit aggregated log messages for the repairs made across all pages."""
    for message in summarize_box_repairs(repairs_by_page):
        log.log(message.level, message.text)
