# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Built-in plugin implementing OCR with RapidOCR.

RapidOCR runs PaddleOCR's PP-OCR detection, line orientation and recognition
models on ONNX Runtime. It is an optional dependency, installed with
``pip install ocrmypdf[rapidocr]``, and is imported only when this engine is
selected.

Usage:
    ocrmypdf --ocr-engine rapidocr input.pdf output.pdf

The bundled PP-OCRv6 recognition model reads Chinese, Japanese, English and
about fifty Latin-script languages. Other scripts (Korean, Cyrillic, Arabic,
Devanagari, Thai, Greek, Tamil, Telugu, Georgian) use separate models that
RapidOCR downloads from ModelScope the first time they are needed, into its
own package directory. RapidOCR loads one recognition model at a time, so
``-l`` may only combine languages that the same model reads.

RapidOCR does not measure page orientation or skew. This engine derives both
from the detected text line boxes: skew from the angle of long lines, and
orientation from the shape of the boxes combined with how confidently the
longest lines are recognized either way up.

RapidOCR's own text line angle classifier is never used. On documents it
turns long Latin lines and nearly every Cyrillic line upside down, and
recognition then returns junk with confident scores. Page orientation is
corrected by --rotate-pages instead; a line that is upside down on an
otherwise upright page is recognized poorly.
"""

from __future__ import annotations

import html
import logging
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from math import atan2, degrees, hypot
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from PIL import Image
from pydantic import BaseModel, Field

from ocrmypdf import hookimpl
from ocrmypdf.cli import numeric
from ocrmypdf.exceptions import BadArgsError, MissingDependencyError
from ocrmypdf.hocrtransform import Baseline, BoundingBox, OcrClass, OcrElement
from ocrmypdf.pluginspec import OcrEngine, OrientationConfidence

if TYPE_CHECKING:
    from ocrmypdf._options import OcrOptions

log = logging.getLogger(__name__)

DEFAULT_MAX_SIDE_LEN = 2000

#: Where the baseline sits in a detection box, as a fraction of the box height
#: above its bottom edge. Detection boxes are padded around the glyphs; this
#: was measured on 300 dpi Latin text.
BASELINE_FRACTION = 0.25
#: Height from the bottom of the descenders to the top of the ascenders, as
#: a fraction of the detection box height.
TEXT_HEIGHT_FRACTION = 0.75

#: Least gap between words, as a fraction of the line's box height, so that
#: the space the renderer adds after each word does not overlap the next.
WORD_GAP_FRACTION = 0.25

#: Lines at least this many times longer than they are high are taken for
#: prose, which is stacked into paragraphs; shorter ones may be table cells.
WIDE_LINE_ASPECT = 8.0

#: Ink measurement: least contrast between paper and ink in a line's box,
#: and the width of the column strips its profile is gathered in.
INK_MIN_CONTRAST = 40
INK_STRIP_WIDTH = 50

#: RapidOCR turns a crop to read it when it is this much taller than wide.
VERTICAL_ASPECT = 1.5

#: Text line evidence for skew and orientation: boxes at least this many times
#: longer than they are thick.
LINE_ASPECT = 3.0

#: Orientation is judged by recognizing this many of the longest lines both
#: ways up, and needs at least ORIENTATION_MIN_LINES of them.
ORIENTATION_LINES = 10
ORIENTATION_MIN_LINES = 3
#: Line crops longer than this many times their thickness are trimmed to
#: their middle, to bound recognition cost.
ORIENTATION_MAX_ASPECT = 25


# --------------------------------------------------------------------------
# Options


class RapidOcrOptions(BaseModel):
    """Options specific to the RapidOCR engine."""

    max_side_len: Annotated[
        int,
        Field(
            ge=32,
            description="Downscale images whose longer side exceeds this many pixels",
        ),
    ] = DEFAULT_MAX_SIDE_LEN

    @classmethod
    def add_arguments_to_parser(cls, parser, namespace: str = 'rapidocr'):
        """Add RapidOCR-specific arguments to the argument parser."""
        group = parser.add_argument_group(
            "RapidOCR", "Advanced control of the RapidOCR engine"
        )
        group.add_argument(
            f'--{namespace}-max-side-len',
            type=numeric(int, 32),
            metavar='PIXELS',
            default=DEFAULT_MAX_SIDE_LEN,
            dest=f'{namespace}_max_side_len',
            help=(
                "RapidOCR downscales page images whose longer side exceeds this "
                "many pixels before detecting text. The default of 2000 reduces "
                "a 300 dpi Letter page to about 180 dpi. Larger values may "
                "recognize small print better, at the cost of speed."
            ),
        )


# --------------------------------------------------------------------------
# Languages


@dataclass(frozen=True, slots=True)
class RecModel:
    """A RapidOCR recognition model, as RapidOCR's configuration names it."""

    ocr_version: str
    model_type: str
    lang_type: str


_PPOCR_V6 = RecModel('PP-OCRv6', 'small', 'ch')

# Tesseract language codes read by the bundled multilingual PP-OCRv6 model
_V6_CODES = (
    'eng chi_sim chi_tra jpn afr aze bos cat ces cym dan deu est eus fin '
    'fra gle glg hrv hun ind isl ita kmr lat lav lit ltz mlt mri msa nld '
    'nor oci pol por que ron slk slv spa sqi srp_latn swa swe tgl tur uzb '
    'vie '
)
_V6_LANGUAGES = frozenset(_V6_CODES.split())


def _v5(lang_type: str) -> RecModel:
    return RecModel('PP-OCRv5', 'mobile', lang_type)


_OTHER_LANGUAGES: dict[str, RecModel] = {
    'kor': _v5('korean'),
    'rus': _v5('eslav'),
    'ukr': _v5('eslav'),
    'bel': _v5('eslav'),
    'bul': _v5('cyrillic'),
    'mkd': _v5('cyrillic'),
    'srp': _v5('cyrillic'),
    'kaz': _v5('cyrillic'),
    'kir': _v5('cyrillic'),
    'mon': _v5('cyrillic'),
    'tgk': _v5('cyrillic'),
    'tat': _v5('cyrillic'),
    'uzb_cyrl': _v5('cyrillic'),
    'ara': _v5('arabic'),
    'fas': _v5('arabic'),
    'urd': _v5('arabic'),
    'uig': _v5('arabic'),
    'hin': _v5('devanagari'),
    'mar': _v5('devanagari'),
    'nep': _v5('devanagari'),
    'san': _v5('devanagari'),
    'tha': _v5('th'),
    'ell': _v5('el'),
    'tam': _v5('ta'),
    'tel': _v5('te'),
    'kat': RecModel('PP-OCRv4', 'mobile', 'ka'),
}

_LANGUAGE_MODELS: dict[str, RecModel] = {
    **dict.fromkeys(_V6_LANGUAGES, _PPOCR_V6),
    **_OTHER_LANGUAGES,
}


def rec_model_for_languages(languages: Sequence[str]) -> RecModel:
    """Choose the recognition model that reads all of the given languages.

    English is accepted alongside any other language, since every RapidOCR
    recognition model reads basic Latin text. The East Slavic model is
    replaced by the general Cyrillic model when other Cyrillic languages are
    requested too.

    Raises:
        BadArgsError: A language is unsupported, or the languages need
            different recognition models.
    """
    unsupported = [lang for lang in languages if lang not in _LANGUAGE_MODELS]
    if unsupported:
        raise BadArgsError(
            f"RapidOCR does not support these languages: {', '.join(unsupported)}"
        )
    models = {_LANGUAGE_MODELS[lang] for lang in languages if lang != 'eng'}
    if {_v5('eslav'), _v5('cyrillic')} <= models:
        models.discard(_v5('eslav'))
    if not models:
        return _PPOCR_V6
    if len(models) > 1:
        raise BadArgsError(
            "RapidOCR uses one recognition model at a time, and these languages "
            f"need different models: {', '.join(languages)}. "
            "Choose languages of a single script, or use --ocr-engine tesseract."
        )
    return models.pop()


# --------------------------------------------------------------------------
# Geometry helpers

Point = tuple[float, float]
Quad = Sequence[Sequence[float]]


def _as_quad(quad: Quad) -> list[Point]:
    return [(float(p[0]), float(p[1])) for p in quad]


def _dist(a: Point, b: Point) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def _quad_dims(quad: list[Point]) -> tuple[float, float]:
    """Width and height of a quad as RapidOCR measures them for cropping."""
    tl, tr, br, bl = quad
    return max(_dist(tl, tr), _dist(bl, br)), max(_dist(tl, bl), _dist(tr, br))


def _is_vertical(quad: list[Point]) -> bool:
    width, height = _quad_dims(quad)
    return width <= 0 or height / width >= VERTICAL_ASPECT


def _hull(points: Sequence[Point], width: float, height: float) -> BoundingBox:
    """Axis-aligned bounding box of points, clamped to the page."""
    xs = [min(max(p[0], 0.0), width) for p in points]
    ys = [min(max(p[1], 0.0), height) for p in points]
    return BoundingBox(left=min(xs), top=min(ys), right=max(xs), bottom=max(ys))


def _lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _reading_edges(
    quad: list[Point], textangle: float | None
) -> tuple[Point, Point, Point, Point]:
    """Corners of a line quad in reading order.

    Returns (start_top, start_bottom, end_top, end_bottom) as seen by a
    reader of the line, whatever the line's orientation on the page.
    """
    tl, tr, br, bl = quad
    if textangle == 270:  # reads downward
        return tr, tl, br, bl
    return tl, bl, tr, br


# --------------------------------------------------------------------------
# Conversion to OcrElement


def _words_from_text(
    text: str, quad: list[Point], textangle: float | None
) -> list[tuple[str, list[Point]]]:
    """Estimate word quads by dividing a line in proportion to character counts."""
    tokens = text.split()
    if not tokens:
        return []
    start_top, start_bottom, end_top, end_bottom = _reading_edges(quad, textangle)
    total = sum(len(t) for t in tokens) + len(tokens) - 1
    words = []
    pos = 0
    for token in tokens:
        t0, t1 = pos / total, (pos + len(token)) / total
        words.append(
            (
                token,
                [
                    _lerp(start_top, end_top, t0),
                    _lerp(start_top, end_top, t1),
                    _lerp(start_bottom, end_bottom, t1),
                    _lerp(start_bottom, end_bottom, t0),
                ],
            )
        )
        pos += len(token) + 1
    return words


def _is_cjk_char(char: str) -> bool:
    """Roughly: is this a character of a script written without spaces?"""
    return ord(char) >= 0x2E80


def _separate_words(
    word_quads: list[tuple[str, float, list[Point]]], min_gap: float
) -> list[tuple[str, float, list[Point]]]:
    """Pull back the right edge of words that touch the next word.

    RapidOCR estimates word boxes by dividing the line between its
    characters, so neighbouring words can touch. The renderer follows each
    word with a space; when the next word starts before that space ends,
    text extractors join the two words. Only horizontal, left-to-right lines
    are adjusted, and never between characters of scripts written without
    spaces.
    """
    result = list(word_quads)
    for i in range(len(result) - 1):
        text, score, quad = result[i]
        next_text, _, next_quad = result[i + 1]
        if not text or not next_text:
            continue
        if _is_cjk_char(text[-1]) or _is_cjk_char(next_text[0]):
            continue
        right = max(quad[1][0], quad[2][0])
        left = min(quad[0][0], quad[3][0])
        next_left = min(next_quad[0][0], next_quad[3][0])
        shift = right - (next_left - min_gap)
        if shift <= 0 or right - shift < left + 0.5 * (right - left):
            continue
        tl, tr, br, bl = quad
        result[i] = (
            text,
            score,
            [tl, (tr[0] - shift, tr[1]), (br[0] - shift, br[1]), bl],
        )
    return result


def _squash(text: str) -> str:
    return ''.join(text.split())


def _align_word_results(
    txts: Sequence[str], word_results: Sequence[Any] | None
) -> list[Sequence[Any] | None]:
    """Match RapidOCR's word results to their lines.

    RapidOCR omits lines that have no word boxes from its word results, so
    when there are fewer word results than lines, match them up by text.
    """
    if not word_results:
        return [None] * len(txts)
    if len(word_results) == len(txts):
        return list(word_results)
    aligned: list[Sequence[Any] | None] = []
    j = 0
    for txt in txts:
        if j < len(word_results) and _squash(
            ''.join(str(w[0]) for w in word_results[j])
        ) == _squash(txt):
            aligned.append(word_results[j])
            j += 1
        else:
            aligned.append(None)
    return aligned


def _line_textangle(quad: list[Point]) -> float | None:
    """Rotation of a line's text, counterclockwise in degrees (hOCR textangle).

    RapidOCR turns vertical crops a quarter turn counterclockwise before
    reading them, so it reads vertical lines downward.
    """
    return 270 if _is_vertical(quad) else None


def _ink_metrics(
    image: Any, quad: list[Point], left: float, slope: float
) -> tuple[float, float, float] | None:
    """Measure where a line's ink lies inside its padded detection box.

    Dark pixels are counted along the line's slope, one strip of columns at
    a time, to give a profile across the line. The run of inked rows around
    its densely inked core spans the tallest glyphs and the descenders; the
    last densely inked row is the baseline, since descenders are sparse.

    Returns:
        (top, baseline, bottom) where the line crosses x = left, or None if
        the box holds no clear line of ink.
    """
    import numpy as np

    img_h, img_w = image.shape[:2]
    offsets = [p[1] - slope * (p[0] - left) for p in quad]
    p_min, p_max = int(min(offsets)), int(max(offsets)) + 1
    x_start = max(0, int(min(p[0] for p in quad)))
    x_end = min(img_w, int(max(p[0] for p in quad)) + 1)
    rows = p_max - p_min
    if rows < 4 or x_end - x_start < 4:
        return None
    y_low = max(0, int(min(p[1] for p in quad)))
    y_high = min(img_h, int(max(p[1] for p in quad)) + 1)
    region = image[y_low:y_high, x_start:x_end]
    lo, hi = np.percentile(region, (5, 95))
    if hi - lo < INK_MIN_CONTRAST:
        return None
    threshold = (lo + hi) / 2

    profile = np.zeros(rows, dtype=np.int64)
    for x0 in range(x_start, x_end, INK_STRIP_WIDTH):
        x1 = min(x_end, x0 + INK_STRIP_WIDTH)
        shift = round(p_min + slope * ((x0 + x1) / 2 - left))
        top, bottom = max(0, shift), min(img_h, shift + rows)
        if bottom <= top:
            continue
        strip = image[top:bottom, x0:x1] < threshold
        profile[top - shift : bottom - shift] += strip.sum(axis=1)

    peak = int(profile.max())
    if peak == 0 or peak > 0.9 * (x_end - x_start):
        return None  # blank, or a ruled line
    # The ink of this line is the run of inked rows around its densely inked
    # core. Padded boxes reach into the neighbouring lines, whose descenders
    # or ascenders are separated from this line's ink by blank rows.
    dense = np.nonzero(profile >= 0.3 * peak)[0]
    inked = profile > 0.02 * peak
    first, last = int(dense[0]), int(dense[-1])
    while first > 0 and inked[first - 1]:
        first -= 1
    while last < rows - 1 and inked[last + 1]:
        last += 1
    ink_top, ink_bottom = p_min + first, p_min + last + 1
    baseline = p_min + dense[-1] + 1
    if ink_bottom - ink_top < 0.25 * rows:
        return None
    return float(ink_top), float(baseline), float(ink_bottom)


def _fit_to_ink(line: OcrElement, image: Any, height: float) -> None:
    """Fit a horizontal line's box and baseline to its ink.

    The renderer sizes text from the line box. Padded detection boxes size it
    so large that text extractors merge the lines of neighbouring table rows
    into one block, and read tables column by column.
    """
    if line.textangle is not None or line.baseline is None or not line.poly:
        return
    assert line.bbox is not None
    bbox, slope = line.bbox, line.baseline.slope
    ink = _ink_metrics(image, line.poly, bbox.left, slope)
    if ink is None:
        return
    ink_top, ink_baseline, ink_bottom = ink
    rise = slope * bbox.width
    line.bbox = BoundingBox(
        left=bbox.left,
        top=max(0.0, ink_top + min(0.0, rise)),
        right=bbox.right,
        bottom=min(height, ink_bottom + max(0.0, rise)),
    )
    line.baseline = Baseline(slope=slope, intercept=ink_baseline - line.bbox.bottom)


def _make_line(
    quad: list[Point],
    text: str,
    score: float,
    words: Sequence[Any] | None,
    width: float,
    height: float,
    language: str | None,
) -> OcrElement:
    bbox = _hull(quad, width, height)
    textangle = _line_textangle(quad)
    tl, tr, br, bl = quad
    thickness = (_dist(tl, bl) + _dist(tr, br)) / 2

    baseline = None
    if textangle is None:
        dx = br[0] - bl[0]
        slope = (br[1] - bl[1]) / dx if dx > 0 else 0.0
        # hOCR: y = slope * (x - bbox.left) + bbox.bottom + intercept
        y_at_left = bl[1] - BASELINE_FRACTION * thickness
        y_at_left += slope * (bbox.left - bl[0])
        baseline = Baseline(slope=slope, intercept=y_at_left - bbox.bottom)

    if words:
        word_quads = [
            (str(word_text), float(word_score), _as_quad(word_quad))
            for word_text, word_score, word_quad in words
        ]
    else:
        word_quads = [
            (word_text, score, points)
            for word_text, points in _words_from_text(text, quad, textangle)
        ]

    if textangle is None:
        word_quads = _separate_words(word_quads, WORD_GAP_FRACTION * thickness)

    children = [
        OcrElement(
            ocr_class=OcrClass.WORD,
            bbox=_hull(points, width, height),
            poly=points,
            text=word_text,
            confidence=word_score,
            language=language,
        )
        for word_text, word_score, points in word_quads
        if word_text.strip()
    ]
    return OcrElement(
        ocr_class=OcrClass.LINE,
        bbox=bbox,
        poly=quad,
        text=text,
        confidence=score,
        baseline=baseline,
        textangle=textangle,
        language=language,
        children=children,
    )


def _thickness(line: OcrElement) -> float:
    """Height of a line's detection box, perpendicular to the line."""
    if line.poly and len(line.poly) == 4:
        tl, tr, br, bl = line.poly
        return (_dist(tl, bl) + _dist(tr, br)) / 2
    assert line.bbox is not None
    return min(line.bbox.width, line.bbox.height)


def _text_height(line: OcrElement) -> float:
    """Estimated text height of a line, from its detection box."""
    return TEXT_HEIGHT_FRACTION * _thickness(line)


def _centre_y(line: OcrElement) -> float:
    assert line.bbox is not None
    return (line.bbox.top + line.bbox.bottom) / 2


def _is_wide(line: OcrElement) -> bool:
    """Whether a horizontal line is long enough to be a line of prose.

    Table cells are short; lines of running text are long.
    """
    assert line.bbox is not None
    return line.textangle is None and line.bbox.width >= WIDE_LINE_ASPECT * (
        _thickness(line)
    )


def _same_row(a: OcrElement, b: OcrElement) -> bool:
    return abs(_centre_y(a) - _centre_y(b)) < 0.4 * _thickness(a)


def _is_table_cell(line: OcrElement, lines: list[OcrElement]) -> bool:
    """Whether a line has a short line beside it on its row."""
    assert line.bbox is not None
    for other in lines:
        if other is line or other.textangle is not None or _is_wide(other):
            continue
        assert other.bbox is not None
        apart = other.bbox.left >= line.bbox.right or other.bbox.right <= line.bbox.left
        if apart and _same_row(line, other):
            return True
    return False


def _is_tabular(paragraph: list[OcrElement], lines: list[OcrElement]) -> bool:
    """Whether most lines of a paragraph have short cells beside them."""
    cells = sum(_is_table_cell(line, lines) for line in paragraph)
    return 2 * cells > len(paragraph)


def _line_pitch(paragraph: list[OcrElement], line: OcrElement) -> float | None:
    """How far a horizontal line sits below the paragraph's last line.

    Returns the distance between the lines' centres, if the line could
    continue the paragraph: it is a normal line pitch below, overlaps it
    horizontally, and is of similar size. Otherwise returns None.
    """
    last = paragraph[-1]
    if last.textangle is not None or line.textangle is not None:
        return None
    assert last.bbox is not None and line.bbox is not None
    a, b = last.bbox, line.bbox
    # Detection boxes are padded and can overlap their neighbours, so compare
    # centres, scaled by the lines' text size rather than their hulls.
    ha = _text_height(last)
    hb = _text_height(line)
    pitch = (b.top + b.bottom - a.top - a.bottom) / 2
    overlap = min(a.right, b.right) - max(a.left, b.left)
    if (
        0.4 * ha < pitch < 2.0 * ha
        and overlap > 0.5 * min(a.width, b.width)
        and 0.7 < hb / ha < 1.4
        and abs(a.left - b.left) < 2.0 * ha + 0.5 * a.width
    ):
        return pitch
    return None


def _stack_paragraphs(lines: list[OcrElement]) -> list[list[OcrElement]]:
    """Stack lines of prose into paragraphs.

    A line joins the paragraph whose last line lies nearest above it, so
    paragraphs follow columns. Only long lines are stacked. A short line may
    end a paragraph whose left edge it shares, unless it is a table cell;
    every other short line is a paragraph of its own.
    """
    paragraphs: list[list[OcrElement]] = []
    for line in lines:
        wide = _is_wide(line)
        if wide or not _is_table_cell(line, lines):
            pitches = [
                (pitch, n)
                for n, paragraph in enumerate(paragraphs)
                if _is_wide(paragraph[-1])
                and (pitch := _line_pitch(paragraph, line)) is not None
                and (wide or _left_aligned(paragraph[-1], line))
            ]
            if pitches:
                paragraphs[min(pitches)[1]].append(line)
                continue
        paragraphs.append([line])
    return paragraphs


def _left_aligned(a: OcrElement, b: OcrElement) -> bool:
    assert a.bbox is not None and b.bbox is not None
    return abs(a.bbox.left - b.bbox.left) < _text_height(a)


def _split_rows(units: list[list[OcrElement]]) -> list[list[OcrElement]]:
    """Split single lines into rows, each read left to right."""
    rows: list[list[OcrElement]] = []
    for line in sorted((u[0] for u in units), key=_centre_y):
        if rows and _same_row(rows[-1][0], line):
            rows[-1].append(line)
        else:
            rows.append([line])
    return [sorted(row, key=lambda ln: ln.bbox.left if ln.bbox else 0) for row in rows]


Column = tuple[float, float, list[list[OcrElement]]]


def _unit_extent(unit: list[OcrElement]) -> tuple[float, float]:
    boxes = [ln.bbox for ln in unit if ln.bbox is not None]
    return min(b.left for b in boxes), max(b.right for b in boxes)


def _columns(units: list[list[OcrElement]]) -> list[Column]:
    """Group units whose horizontal extents overlap into columns."""
    columns: list[Column] = []
    for unit in sorted(units, key=lambda u: _unit_extent(u)[0]):
        left, right = _unit_extent(unit)
        if columns and left < columns[-1][1]:
            column_left, column_right, members = columns[-1]
            members.append(unit)
            columns[-1] = (column_left, max(column_right, right), members)
        else:
            columns.append((left, right, [unit]))
    return columns


def _columns_match(a: list[Column], b: list[Column]) -> bool:
    """Whether two bands have the same columns of prose."""
    return len(a) == len(b) > 1 and all(
        min(ra, rb) > max(la, lb) for (la, ra, _), (lb, rb, _) in zip(a, b, strict=True)
    )


def _layout_blocks(lines: list[OcrElement]) -> list[list[OcrElement]]:
    """Arrange lines into blocks in reading order.

    Prose is stacked into paragraphs that follow its columns. The page is
    then cut into horizontal bands: a unit (paragraph or single line) joins
    the band above if its first line is centred above the band's bottom, so
    a band holds side-by-side columns of prose, or one row of a table.

    A band holding a paragraph of several lines is read column by column.
    Any other band is read row by row, each row a block of its cells from
    left to right, as a reader would read a table.
    """
    stacked = _stack_paragraphs(
        sorted(lines, key=lambda ln: ln.bbox.top if ln.bbox else 0)
    )
    # Long table cells stack like prose; when their rows hold short cells
    # too, they are a table column, and are read by rows instead.
    units: list[list[OcrElement]] = []
    for paragraph in stacked:
        if len(paragraph) > 1 and _is_tabular(paragraph, lines):
            units.extend([line] for line in paragraph)
        else:
            units.append(paragraph)
    units.sort(key=lambda u: u[0].bbox.top if u[0].bbox else 0)
    bands: list[tuple[float, list[list[OcrElement]]]] = []
    for unit in units:
        bottom = max(ln.bbox.bottom for ln in unit if ln.bbox is not None)
        if bands and _centre_y(unit[0]) < bands[-1][0]:
            band_bottom, members = bands[-1]
            members.append(unit)
            bands[-1] = (max(band_bottom, bottom), members)
        else:
            bands.append((bottom, [unit]))
    # Bands of prose columns that line up, with paragraph breaks between
    # them, are one stretch of columns.
    merged: list[list[list[OcrElement]]] = []
    previous: list[Column] | None = None
    for _bottom, members in bands:
        columns = _columns(members) if any(len(unit) > 1 for unit in members) else None
        if columns and previous and _columns_match(previous, columns):
            merged[-1].extend(members)
            previous = _columns(merged[-1])
        else:
            merged.append(members)
            previous = columns
    blocks: list[list[OcrElement]] = []
    for members in merged:
        if not any(len(unit) > 1 for unit in members):
            blocks.extend(_split_rows(members))
            continue
        # Read column by column, except that neighbouring columns of single
        # lines, such as labels and their values, are read by rows.
        singles: list[list[OcrElement]] = []
        for _left, _right, column in _columns(members):
            if all(len(unit) == 1 for unit in column):
                singles.extend(column)
                continue
            blocks.extend(_split_rows(singles))
            singles = []
            blocks.extend(sorted(column, key=lambda u: _centre_y(u[0])))
        blocks.extend(_split_rows(singles))
    return blocks


def rapidocr_to_ocr_tree(
    boxes: Sequence[Quad] | None,
    txts: Sequence[str] | None,
    scores: Sequence[float] | None,
    word_results: Sequence[Any] | None,
    width: float,
    height: float,
    dpi: float,
    language: str | None,
    *,
    page_number: int = 0,
    image: Any = None,
) -> OcrElement:
    """Convert RapidOCR output for one page into an OcrElement tree.

    Args:
        boxes: Line quads, clockwise from top left, in image pixels.
        txts: Line texts.
        scores: Line confidences, 0 to 1.
        word_results: For each line, a sequence of (text, score, quad) word
            results, as RapidOCR returns with ``return_word_box=True``. It may
            be missing, or lack entries for some lines; their word boxes are
            then estimated from the line.
        width: Image width in pixels.
        height: Image height in pixels.
        dpi: Image resolution.
        language: Tesseract language code to tag text with, for font choice.
        page_number: Page number to record.
        image: The page image as a greyscale array, if available. The ink of
            each horizontal line is then measured to fit its box and
            baseline to the glyphs; otherwise they are estimated from the
            padded detection box.

    Returns:
        A page containing paragraphs of lines of words.
    """
    page = OcrElement(
        ocr_class=OcrClass.PAGE,
        bbox=BoundingBox(left=0, top=0, right=width, bottom=height),
        dpi=float(dpi),
        page_number=page_number,
        language=language,
    )
    if boxes is None or txts is None or len(boxes) == 0:
        return page
    if scores is None:
        scores = [1.0] * len(txts)
    aligned_words = _align_word_results(txts, word_results)

    lines = [
        _make_line(
            _as_quad(quad),
            str(text),
            float(score),
            words,
            width,
            height,
            language,
        )
        for quad, text, score, words in zip(
            boxes, txts, scores, aligned_words, strict=True
        )
        if str(text).strip()
    ]
    blocks = _layout_blocks(lines)
    if image is not None:
        # After layout, which relies on the detection boxes' consistent size
        for line in lines:
            _fit_to_ink(line, image, height)
    for group in blocks:
        corners = [
            corner
            for ln in group
            if (b := ln.bbox) is not None
            for corner in ((b.left, b.top), (b.right, b.bottom))
        ]
        page.children.append(
            OcrElement(
                ocr_class=OcrClass.PARAGRAPH,
                bbox=_hull(corners, width, height),
                language=language,
                children=group,
            )
        )
    return page


def _is_row(paragraph: OcrElement) -> bool:
    """Whether a paragraph's lines are cells side by side on one row."""
    lines = paragraph.children
    return len(lines) > 1 and all(
        _same_row(a, b)
        and a.bbox is not None
        and b.bbox is not None
        and b.bbox.left >= a.bbox.left
        for a, b in zip(lines, lines[1:], strict=False)
    )


def ocr_tree_to_text(page: OcrElement) -> str:
    """Plain text of a page.

    The lines of a paragraph go on separate lines, with a blank line between
    paragraphs. The cells of a table row go on one line, separated by spaces,
    and rows of single lines follow each other without blank lines.
    """
    out: list[str] = []
    previous_single = False
    for paragraph in page.paragraphs:
        texts = [line.get_text_recursive() for line in paragraph.children]
        single = len(texts) == 1 or _is_row(paragraph)
        if out:
            out.append('\n' if single and previous_single else '\n\n')
        out.append(' '.join(texts) if single else '\n'.join(texts))
        previous_single = single
    return ''.join(out) + '\n' if out else ''


# --------------------------------------------------------------------------
# hOCR output


def _bbox_title(bbox: BoundingBox | None) -> str:
    if bbox is None:
        return ''
    return (
        f'bbox {round(bbox.left)} {round(bbox.top)} '
        f'{round(bbox.right)} {round(bbox.bottom)}'
    )


def ocr_tree_to_hocr(page: OcrElement) -> str:
    """Serialize a page from :func:`rapidocr_to_ocr_tree` as hOCR."""
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"',
        '    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">',
        '<head>',
        '<title></title>',
        '<meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>',
        "<meta name='ocr-system' content='OCRmyPDF RapidOCR engine'/>",
        "<meta name='ocr-capabilities' content='ocr_page ocr_par ocr_line "
        "ocrx_word ocrp_wconf'/>",
        '</head>',
        '<body>',
    ]
    page_no = page.page_number or 0
    out.append(
        f"<div class='ocr_page' id='page_{page_no + 1}' "
        f"title='{_bbox_title(page.bbox)}; ppageno {page_no}'>"
    )
    n_line = n_word = 0
    for n_par, paragraph in enumerate(page.paragraphs, start=1):
        lang = f" lang='{paragraph.language}'" if paragraph.language else ''
        out.append(
            f"<p class='ocr_par' id='par_{page_no + 1}_{n_par}'{lang} "
            f"title='{_bbox_title(paragraph.bbox)}'>"
        )
        for line in paragraph.children:
            n_line += 1
            title = _bbox_title(line.bbox)
            if line.baseline is not None:
                title += (
                    f'; baseline {line.baseline.slope:.4f} '
                    f'{round(line.baseline.intercept)}'
                )
            if line.textangle is not None:
                title += f'; textangle {line.textangle:g}'
            out.append(
                f"<span class='ocr_line' id='line_{page_no + 1}_{n_line}' "
                f"title='{title}'>"
            )
            for word in line.children:
                n_word += 1
                conf = round(100 * (word.confidence or 0.0))
                out.append(
                    f"<span class='ocrx_word' id='word_{page_no + 1}_{n_word}' "
                    f"title='{_bbox_title(word.bbox)}; x_wconf {conf}'>"
                    f'{html.escape(word.text, quote=False)}</span>'
                )
            out.append('</span>')
        out.append('</p>')
    out += ['</div>', '</body>', '</html>', '']
    return '\n'.join(out)


# --------------------------------------------------------------------------
# Skew and orientation


def _line_shape(raw: Quad) -> tuple[list[Point], float, bool] | None:
    """Return (quad, length, vertical) if a box is long enough to be a line."""
    quad = _as_quad(raw)
    width, height = _quad_dims(quad)
    long, short = max(width, height), min(width, height)
    if short <= 0 or long < LINE_ASPECT * short:
        return None
    return quad, long, height > width


def _weighted_median(values: list[tuple[float, float]]) -> float:
    values.sort()
    half = sum(w for _, w in values) / 2
    running = 0.0
    for value, weight in values:
        running += weight
        if running >= half:
            return value
    return values[-1][0]


def estimate_skew_angle(quads: Sequence[Quad] | None) -> float:
    """Estimate page skew from detected line quads.

    Takes the length-weighted median angle of long horizontal lines.

    Returns:
        The counterclockwise rotation in degrees that straightens the page,
        as PIL's ``Image.rotate()`` expects: positive when lines run downhill
        to the right. 0.0 if there are no usable lines.
    """
    angles = []
    for raw in quads if quads is not None else ():
        shape = _line_shape(raw)
        if shape is None or shape[2]:
            continue
        quad, length, _vertical = shape
        tl, tr, br, bl = quad
        dx = (tr[0] - tl[0]) + (br[0] - bl[0])
        dy = (tr[1] - tl[1]) + (br[1] - bl[1])
        angle = degrees(atan2(dy, dx))
        if abs(angle) < 30:
            angles.append((angle, length))
    if not angles:
        return 0.0
    return _weighted_median(angles)


def select_orientation_lines(
    quads: Sequence[Quad] | None, n: int = ORIENTATION_LINES
) -> tuple[bool, list[int], float] | None:
    """Choose the lines to judge page orientation by.

    Boxes vote, weighted by area, on whether lines run horizontally or
    vertically. The longest lines along the winning axis are chosen.

    Returns:
        (vertical, indices of the chosen quads, the winning axis's share of
        the vote), or None if there are too few lines to judge.
    """
    if quads is None:
        return None
    votes = {False: 0.0, True: 0.0}
    candidates: dict[bool, list[tuple[float, int]]] = {False: [], True: []}
    for index, raw in enumerate(quads):
        width, height = _quad_dims(_as_quad(raw))
        if width > VERTICAL_ASPECT * height:
            votes[False] += width * height
        elif height > VERTICAL_ASPECT * width:
            votes[True] += width * height
        shape = _line_shape(raw)
        if shape is not None:
            _quad, length, is_vertical = shape
            candidates[is_vertical].append((length, index))
    total = votes[False] + votes[True]
    if total <= 0:
        return None
    vertical = votes[True] > votes[False]
    chosen = sorted(candidates[vertical], reverse=True)[:n]
    if len(chosen) < ORIENTATION_MIN_LINES:
        return None
    return vertical, [index for _length, index in chosen], votes[vertical] / total


def orientation_crops(image: Any, quad: Quad, vertical: bool) -> tuple[Any, Any]:
    """Crop a line from an image array, turned both candidate ways up.

    Horizontal lines are returned as they are and turned over. Vertical lines
    are turned a quarter turn counterclockwise (upright if the line reads
    downward) and clockwise (upright if it reads upward). Long lines are
    trimmed to their middle.

    Returns:
        (upright if the page orientation is 0 or 90, upright if it is 180 or
        270), as image arrays.
    """
    import numpy as np

    points = _as_quad(quad)
    height, width = image.shape[:2]
    pad = 2
    left = max(0, int(min(p[0] for p in points)) - pad)
    top = max(0, int(min(p[1] for p in points)) - pad)
    right = min(width, int(max(p[0] for p in points) + 1) + pad)
    bottom = min(height, int(max(p[1] for p in points) + 1) + pad)
    crop = image[top:bottom, left:right]
    h, w = crop.shape[:2]
    if vertical:
        if h > ORIENTATION_MAX_ASPECT * w:
            start = (h - ORIENTATION_MAX_ASPECT * w) // 2
            crop = crop[start : start + ORIENTATION_MAX_ASPECT * w]
        return np.rot90(crop, 1), np.rot90(crop, -1)
    if w > ORIENTATION_MAX_ASPECT * h:
        start = (w - ORIENTATION_MAX_ASPECT * h) // 2
        crop = crop[:, start : start + ORIENTATION_MAX_ASPECT * h]
    return crop, np.rot90(crop, 2)


def orientation_from_scores(
    vertical: bool, upright: float, turned: float, axis_share: float = 1.0
) -> OrientationConfidence:
    """Decide page orientation from mean recognition scores both ways up.

    Args:
        vertical: Whether the page's lines run vertically.
        upright: Mean recognition score of the line crops assuming the page
            orientation is 0 (horizontal lines) or 90 (vertical lines).
        turned: The same assuming 180 or 270.
        axis_share: The winning axis's share of the line direction vote.

    Absolute scores mean little (text the wrong way up still scores 0.5 to
    0.7), but the difference does. Confidence is 100 times the difference,
    up to 50, so OCRmyPDF's default threshold of 14 needs a margin of 0.14;
    correctly oriented test pages had margins of 0.27 to 0.50. Confidence
    falls to zero as the line direction vote approaches a tie.

    Returns:
        How far the page content is turned clockwise, as Tesseract OSD's
        "Orientation in degrees" reports it (text reading downward is 90),
        and confidence.
    """
    if vertical:
        angle = 90 if upright >= turned else 270
    else:
        angle = 0 if upright >= turned else 180
    axis_factor = min(1.0, max(0.0, (axis_share - 0.5) * 4))
    confidence = min(50.0, 100.0 * abs(upright - turned)) * axis_factor
    return OrientationConfidence(angle=angle, confidence=confidence)


# --------------------------------------------------------------------------
# RapidOCR engine


def _import_rapidocr():
    try:
        import rapidocr
    except ImportError as e:
        raise MissingDependencyError(
            "The RapidOCR engine requires the rapidocr and onnxruntime packages. "
            "Install them with: pip install ocrmypdf[rapidocr]"
        ) from e
    return rapidocr


@dataclass(frozen=True, slots=True)
class _EngineConfig:
    max_side_len: int
    rec: RecModel


#: RapidOCR instances of the current thread, by configuration. A RapidOCR
#: instance keeps state between calls, so threads cannot share one; and
#: OCRmyPDF's worker threads must not take turns on one engine either. The
#: engines are released when their thread ends.
_thread_engines = threading.local()


def _get_engine(config: _EngineConfig) -> Any:
    """Return the current thread's RapidOCR instance for a configuration."""
    engines: dict[_EngineConfig, Any] | None = getattr(_thread_engines, 'engines', None)
    if engines is None:
        engines = _thread_engines.engines = {}
    if config not in engines:
        engines[config] = _create_engine(config)
    return engines[config]


def _create_engine(config: _EngineConfig) -> Any:
    rapidocr = _import_rapidocr()
    params = {
        'Global.log_level': 'error',
        'Global.max_side_len': config.max_side_len,
        'Global.return_word_box': True,
        'Global.use_cls': False,
        # OCRmyPDF runs one worker per core already
        'EngineConfig.onnxruntime.intra_op_num_threads': 1,
        'EngineConfig.onnxruntime.inter_op_num_threads': 1,
        'Rec.ocr_version': rapidocr.OCRVersion(config.rec.ocr_version),
        'Rec.model_type': rapidocr.ModelType(config.rec.model_type),
        'Rec.lang_type': rapidocr.LangRec(config.rec.lang_type),
    }
    return rapidocr.RapidOCR(params=params)


def _engine_for(options: OcrOptions) -> Any:
    return _get_engine(
        _EngineConfig(
            max_side_len=options.rapidocr.max_side_len,
            rec=rec_model_for_languages(options.languages),
        )
    )


def _load_image(input_file: Path) -> tuple[Image.Image, float]:
    with Image.open(input_file) as im:
        dpi_info = im.info.get('dpi', (300, 300))
        dpi = float(dpi_info[0] if isinstance(dpi_info, tuple) else dpi_info)
        if im.mode in ('1', 'L', 'I', 'I;16', 'F'):
            loaded = im.convert('L')
        else:
            loaded = im.convert('RGB')
    return loaded, dpi


def _run(engine: Any, image: Image.Image, *, rec: bool) -> Any:
    """Detect, and optionally recognize, text; return RapidOCR's result."""
    # RapidOCR keeps these flags between calls, so always pass all of them
    return engine(
        image,
        use_det=True,
        use_cls=False,
        use_rec=rec,
        return_word_box=rec,
    )


def _boxes(result: Any) -> Any:
    boxes = getattr(result, 'boxes', None)
    return None if boxes is None or len(boxes) == 0 else boxes


def _mean_rec_score(engine: Any, crops: list[Any]) -> float:
    """Mean recognition score of line crops (BGR image arrays)."""
    import numpy as np
    from rapidocr.ch_ppocr_rec.typings import TextRecInput

    recognizer = engine._load_rec_model()
    result = recognizer(TextRecInput(img=[np.ascontiguousarray(c) for c in crops]))
    scores = result.scores or ()
    return float(np.mean(scores)) if len(scores) else 0.0


class RapidOcrEngine(OcrEngine):
    """Implements OCR with RapidOCR."""

    @staticmethod
    def version() -> str:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version('rapidocr')
        except PackageNotFoundError:
            return "not installed"

    @staticmethod
    def creator_tag(options: OcrOptions) -> str:
        return f"OCRmyPDF fpdf2 + RapidOCR {RapidOcrEngine.version()}"

    def __str__(self) -> str:
        return f"RapidOCR {RapidOcrEngine.version()}"

    @staticmethod
    def languages(options: OcrOptions | None) -> set[str]:
        return set(_LANGUAGE_MODELS)

    @staticmethod
    def get_orientation(input_file: Path, options: OcrOptions) -> OrientationConfidence:
        import numpy as np

        image, _dpi = _load_image(input_file)
        engine = _engine_for(options)
        quads = _boxes(_run(engine, image, rec=False))
        selected = select_orientation_lines(quads)
        if selected is None:
            return OrientationConfidence(angle=0, confidence=0.0)
        vertical, indices, axis_share = selected
        array = np.asarray(image.convert('RGB'))[:, :, ::-1]  # RapidOCR wants BGR
        pairs = [orientation_crops(array, quads[i], vertical) for i in indices]
        pairs = [(a, b) for a, b in pairs if a.size]
        if len(pairs) < ORIENTATION_MIN_LINES:
            return OrientationConfidence(angle=0, confidence=0.0)
        upright = _mean_rec_score(engine, [a for a, _ in pairs])
        turned = _mean_rec_score(engine, [b for _, b in pairs])
        return orientation_from_scores(vertical, upright, turned, axis_share)

    @staticmethod
    def get_deskew(input_file: Path, options: OcrOptions) -> float:
        image, _dpi = _load_image(input_file)
        return estimate_skew_angle(_boxes(_run(_engine_for(options), image, rec=False)))

    @staticmethod
    def supports_generate_ocr() -> bool:
        return True

    @staticmethod
    def generate_ocr(
        input_file: Path,
        options: OcrOptions,
        page_number: int = 0,
    ) -> tuple[OcrElement, str]:
        import numpy as np

        image, dpi = _load_image(input_file)
        result = _run(_engine_for(options), image, rec=True)
        boxes = _boxes(result)
        page = rapidocr_to_ocr_tree(
            boxes,
            tuple(result.txts) if boxes is not None else None,
            tuple(float(s) for s in result.scores) if boxes is not None else None,
            result.word_results if boxes is not None else None,
            width=image.width,
            height=image.height,
            dpi=dpi,
            language=options.languages[0] if options.languages else None,
            page_number=page_number,
            image=np.asarray(image.convert('L')) if boxes is not None else None,
        )
        return page, ocr_tree_to_text(page)

    @staticmethod
    def generate_hocr(
        input_file: Path,
        output_hocr: Path,
        output_text: Path,
        options: OcrOptions,
    ) -> None:
        page, text = RapidOcrEngine.generate_ocr(input_file, options)
        output_hocr.write_text(ocr_tree_to_hocr(page), encoding='utf-8')
        output_text.write_text(text, encoding='utf-8')

    @staticmethod
    def generate_pdf(
        input_file: Path,
        output_pdf: Path,
        output_text: Path,
        options: OcrOptions,
    ) -> None:
        raise NotImplementedError(
            "RapidOCR cannot generate PDFs directly. "
            "Use --pdf-renderer fpdf2 instead of sandwich mode."
        )


def _selected(options) -> bool:
    return getattr(options, 'ocr_engine', 'auto') == 'rapidocr'


@hookimpl
def register_options():
    """Register RapidOCR option model."""
    return {'rapidocr': RapidOcrOptions}


@hookimpl
def add_options(parser):
    RapidOcrOptions.add_arguments_to_parser(parser)


@hookimpl
def check_options(options):
    """Check that RapidOCR is installed and can serve the requested options."""
    if not _selected(options):
        return
    _import_rapidocr()
    if options.pdf_renderer == 'sandwich':
        raise BadArgsError(
            "--pdf-renderer sandwich is not supported by --ocr-engine rapidocr. "
            "Use --pdf-renderer fpdf2."
        )
    rec_model_for_languages(options.languages)


@hookimpl
def get_ocr_engine(options):
    """Return RapidOcrEngine when --ocr-engine rapidocr is selected."""
    if options is not None and _selected(options):
        return RapidOcrEngine()
    return None
