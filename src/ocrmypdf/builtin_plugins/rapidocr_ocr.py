# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Built-in plugin implementing OCR with RapidOCR.

RapidOCR runs PaddleOCR's PP-OCR detection, line orientation and recognition
models on ONNX Runtime. It is an optional dependency, installed with
``uv tool install 'ocrmypdf[rapidocr]'``, and is imported only when this
engine is selected.

Usage:
    ocrmypdf --ocr-engine rapidocr input.pdf output.pdf

The bundled PP-OCRv6 recognition model reads Chinese, Japanese, English and
about fifty Latin-script languages. Other scripts (Korean, Cyrillic, Arabic,
Devanagari, Thai, Greek, Tamil, Telugu, Georgian) use separate models that
RapidOCR downloads from ModelScope the first time they are needed, into its
own package directory, or into --rapidocr-model-dir (or
$OCRMYPDF_RAPIDOCR_MODEL_DIR) if given. RapidOCR loads one recognition model
at a time, so ``-l`` may only combine languages that the same model reads.

RapidOCR does not measure page orientation or skew. This engine measures
skew from the angle of the detected text lines. For orientation, the shape
of the line boxes shows whether the page is sideways, and PaddlePaddle's
PP-LCNet_x1_0_doc_ori page orientation model (Apache-2.0), downloaded on
first use, says which way; an upside down reading, or a sideways one the
model is unsure of, is confirmed by recognizing the longest lines both ways
up. Without the model, orientation is judged by recognition alone, which is
slower.

RapidOCR's own text line angle classifier is never used. On documents it
turns long Latin lines and nearly every Cyrillic line upside down, and
recognition then returns junk with confident scores. Page orientation is
corrected by --rotate-pages instead; a line that is upside down on an
otherwise upright page is recognized poorly.
"""

from __future__ import annotations

import hashlib
import html
import logging
import os
import sys
import tempfile
import threading
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from math import atan2, degrees, hypot
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, BinaryIO

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

#: Environment variable naming the directory to keep models in, used when
#: --rapidocr-model-dir is not given.
MODEL_DIR_ENV = 'OCRMYPDF_RAPIDOCR_MODEL_DIR'

#: Where the baseline sits in a detection box, as a fraction of the box height
#: above its bottom edge. Detection boxes are padded around the glyphs; this
#: was measured on 300 dpi Latin text.
BASELINE_FRACTION = 0.25
#: Height from the bottom of the descenders to the top of the ascenders, and
#: descender depth, as fractions of the detection box height.
TEXT_HEIGHT_FRACTION = 0.75
DESCENDER_FRACTION = 0.15

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


def _model_dir_from_env() -> Path | None:
    value = os.environ.get(MODEL_DIR_ENV)
    return Path(value) if value else None


class RapidOcrOptions(BaseModel):
    """Options specific to the RapidOCR engine."""

    max_side_len: Annotated[
        int,
        Field(
            ge=32,
            description="Downscale images whose longer side exceeds this many pixels",
        ),
    ] = DEFAULT_MAX_SIDE_LEN

    model_dir: Annotated[
        Path | None,
        Field(
            default_factory=_model_dir_from_env,
            description=(
                "Directory to keep RapidOCR's models and the page orientation "
                "model in, instead of RapidOCR's package directory"
            ),
        ),
    ]

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
        group.add_argument(
            f'--{namespace}-model-dir',
            type=Path,
            metavar='DIR',
            default=None,
            dest=f'{namespace}_model_dir',
            help=(
                "Keep RapidOCR's models, and the page orientation model, in this "
                "directory instead of RapidOCR's package directory. Models found "
                "missing are downloaded into it. Useful when the package "
                "directory is read-only, or to share models between "
                f"installations. Defaults to ${MODEL_DIR_ENV} if set."
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


@dataclass(frozen=True, slots=True)
class _ReadingEdges:
    """Corners of a line quad as seen by a reader of the line."""

    start_top: Point
    start_bottom: Point
    end_top: Point
    end_bottom: Point


def _reading_edges(quad: list[Point], textangle: float | None) -> _ReadingEdges:
    """Corners of a line quad in reading order, whatever the line's orientation."""
    tl, tr, br, bl = quad
    if textangle == 270:  # reads downward
        return _ReadingEdges(tr, tl, br, bl)
    return _ReadingEdges(tl, bl, tr, br)


@dataclass(frozen=True, slots=True)
class _WordQuad:
    """A word, its recognition score, and its quad in image pixels."""

    text: str
    score: float
    quad: list[Point]


# --------------------------------------------------------------------------
# Conversion to OcrElement


def _words_from_text(
    text: str, score: float, quad: list[Point], textangle: float | None
) -> list[_WordQuad]:
    """Estimate word quads by dividing a line in proportion to character counts.

    Each word is given the line's score.
    """
    tokens = text.split()
    if not tokens:
        return []
    edges = _reading_edges(quad, textangle)
    total = sum(len(t) for t in tokens) + len(tokens) - 1
    words = []
    pos = 0
    for token in tokens:
        t0, t1 = pos / total, (pos + len(token)) / total
        words.append(
            _WordQuad(
                token,
                score,
                [
                    _lerp(edges.start_top, edges.end_top, t0),
                    _lerp(edges.start_top, edges.end_top, t1),
                    _lerp(edges.start_bottom, edges.end_bottom, t1),
                    _lerp(edges.start_bottom, edges.end_bottom, t0),
                ],
            )
        )
        pos += len(token) + 1
    return words


def _is_cjk_char(char: str) -> bool:
    """Roughly: is this a character of a script written without spaces?"""
    return ord(char) >= 0x2E80


def _separate_words(word_quads: list[_WordQuad], min_gap: float) -> list[_WordQuad]:
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
        word, following = result[i], result[i + 1]
        if not word.text or not following.text:
            continue
        if _is_cjk_char(word.text[-1]) or _is_cjk_char(following.text[0]):
            continue
        quad, next_quad = word.quad, following.quad
        right = max(quad[1][0], quad[2][0])
        left = min(quad[0][0], quad[3][0])
        next_left = min(next_quad[0][0], next_quad[3][0])
        shift = right - (next_left - min_gap)
        if shift <= 0 or right - shift < left + 0.5 * (right - left):
            continue
        tl, tr, br, bl = quad
        result[i] = _WordQuad(
            word.text,
            word.score,
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


@dataclass(frozen=True, slots=True)
class _InkMetrics:
    """Where a line's ink lies, as y coordinates in image pixels."""

    top: float
    baseline: float
    bottom: float


def _ink_metrics(
    image: Any, quad: list[Point], left: float, slope: float
) -> _InkMetrics | None:
    """Measure where a line's ink lies inside its padded detection box.

    Dark pixels are counted along the line's slope, one strip of columns at
    a time, to give a profile across the line. The run of inked rows around
    its densely inked core spans the tallest glyphs and the descenders; the
    last densely inked row is the baseline, since descenders are sparse.

    Returns:
        The ink's top, baseline and bottom where the line crosses x = left,
        or None if the box holds no clear line of ink.
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
    return _InkMetrics(float(ink_top), float(baseline), float(ink_bottom))


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
    rise = slope * bbox.width
    line.bbox = BoundingBox(
        left=bbox.left,
        top=max(0.0, ink.top + min(0.0, rise)),
        right=bbox.right,
        bottom=min(height, ink.bottom + max(0.0, rise)),
    )
    line.baseline = Baseline(slope=slope, intercept=ink.baseline - line.bbox.bottom)
    line.x_size = ink.bottom - ink.top
    line.x_descenders = ink.bottom - ink.baseline


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
    x_size = x_descenders = None
    if textangle is None:
        dx = br[0] - bl[0]
        slope = (br[1] - bl[1]) / dx if dx > 0 else 0.0
        # hOCR: y = slope * (x - bbox.left) + bbox.bottom + intercept
        y_at_left = bl[1] - BASELINE_FRACTION * thickness
        y_at_left += slope * (bbox.left - bl[0])
        baseline = Baseline(slope=slope, intercept=y_at_left - bbox.bottom)
        # The box height overstates the text size of a sloped line by its
        # rise; these metrics, across the line, let the renderer cap it.
        x_size = TEXT_HEIGHT_FRACTION * thickness
        x_descenders = DESCENDER_FRACTION * thickness

    if words:
        word_quads = [
            _WordQuad(str(word_text), float(word_score), _as_quad(word_quad))
            for word_text, word_score, word_quad in words
        ]
    else:
        word_quads = _words_from_text(text, score, quad, textangle)

    if textangle is None:
        word_quads = _separate_words(word_quads, WORD_GAP_FRACTION * thickness)

    children = [
        OcrElement(
            ocr_class=OcrClass.WORD,
            bbox=_hull(word.quad, width, height),
            poly=word.quad,
            text=word.text,
            confidence=word.score,
            language=language,
        )
        for word in word_quads
        if word.text.strip()
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
        x_size=x_size,
        x_descenders=x_descenders,
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


@dataclass(frozen=True, slots=True)
class _Column:
    """Units whose horizontal extents overlap, and the extent they span."""

    left: float
    right: float
    units: list[list[OcrElement]]


@dataclass(frozen=True, slots=True)
class _Band:
    """Units side by side across the page, and the lowest bottom among them."""

    bottom: float
    units: list[list[OcrElement]]


def _unit_extent(unit: list[OcrElement]) -> tuple[float, float]:
    boxes = [ln.bbox for ln in unit if ln.bbox is not None]
    return min(b.left for b in boxes), max(b.right for b in boxes)


def _columns(units: list[list[OcrElement]]) -> list[_Column]:
    """Group units whose horizontal extents overlap into columns."""
    columns: list[_Column] = []
    for unit in sorted(units, key=lambda u: _unit_extent(u)[0]):
        left, right = _unit_extent(unit)
        if columns and left < columns[-1].right:
            last = columns[-1]
            last.units.append(unit)
            columns[-1] = _Column(last.left, max(last.right, right), last.units)
        else:
            columns.append(_Column(left, right, [unit]))
    return columns


def _columns_match(a: list[_Column], b: list[_Column]) -> bool:
    """Whether two bands have the same columns of prose."""
    return len(a) == len(b) > 1 and all(
        min(ca.right, cb.right) > max(ca.left, cb.left)
        for ca, cb in zip(a, b, strict=True)
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
    bands: list[_Band] = []
    for unit in units:
        bottom = max(ln.bbox.bottom for ln in unit if ln.bbox is not None)
        if bands and _centre_y(unit[0]) < bands[-1].bottom:
            last = bands[-1]
            last.units.append(unit)
            bands[-1] = _Band(max(last.bottom, bottom), last.units)
        else:
            bands.append(_Band(bottom, [unit]))
    # Bands of prose columns that line up, with paragraph breaks between
    # them, are one stretch of columns.
    merged: list[list[list[OcrElement]]] = []
    previous: list[_Column] | None = None
    for band in bands:
        members = band.units
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
        for column in _columns(members):
            if all(len(unit) == 1 for unit in column.units):
                singles.extend(column.units)
                continue
            blocks.extend(_split_rows(singles))
            singles = []
            blocks.extend(sorted(column.units, key=lambda u: _centre_y(u[0])))
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
            if line.x_size is not None and line.x_descenders is not None:
                title += (
                    f'; x_size {line.x_size:.1f}; x_descenders {line.x_descenders:.1f}'
                )
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


@dataclass(frozen=True, slots=True)
class _LineShape:
    """A detection box that is long enough to be a line of text."""

    quad: list[Point]
    length: float
    vertical: bool


def _line_shape(raw: Quad) -> _LineShape | None:
    """Describe a box, if it is long enough to be a line."""
    quad = _as_quad(raw)
    width, height = _quad_dims(quad)
    long, short = max(width, height), min(width, height)
    if short <= 0 or long < LINE_ASPECT * short:
        return None
    return _LineShape(quad, long, height > width)


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
        if shape is None or shape.vertical:
            continue
        tl, tr, br, bl = shape.quad
        dx = (tr[0] - tl[0]) + (br[0] - bl[0])
        dy = (tr[1] - tl[1]) + (br[1] - bl[1])
        angle = degrees(atan2(dy, dx))
        if abs(angle) < 30:
            angles.append((angle, shape.length))
    if not angles:
        return 0.0
    return _weighted_median(angles)


@dataclass(frozen=True, slots=True)
class OrientationLines:
    """The lines chosen to judge page orientation by.

    Attributes:
        vertical: Whether the page's lines run vertically.
        indices: Indices of the chosen quads, longest first.
        axis_share: The winning axis's share of the line direction vote.
    """

    vertical: bool
    indices: list[int]
    axis_share: float


def select_orientation_lines(
    quads: Sequence[Quad] | None, n: int = ORIENTATION_LINES
) -> OrientationLines | None:
    """Choose the lines to judge page orientation by.

    Boxes vote, weighted by area, on whether lines run horizontally or
    vertically. The longest lines along the winning axis are chosen.

    Returns:
        The chosen lines, or None if there are too few lines to judge.
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
            candidates[shape.vertical].append((shape.length, index))
    total = votes[False] + votes[True]
    if total <= 0:
        return None
    vertical = votes[True] > votes[False]
    chosen = sorted(candidates[vertical], reverse=True)[:n]
    if len(chosen) < ORIENTATION_MIN_LINES:
        return None
    return OrientationLines(
        vertical, [index for _length, index in chosen], votes[vertical] / total
    )


@dataclass(frozen=True, slots=True)
class OrientationCrops:
    """A line crop, turned both candidate ways up.

    Attributes:
        upright: Upright if the page orientation is 0 or 90.
        turned: Upright if the page orientation is 180 or 270.
    """

    upright: Any
    turned: Any


def orientation_crops(image: Any, quad: Quad, vertical: bool) -> OrientationCrops:
    """Crop a line from an image array, turned both candidate ways up.

    Horizontal lines are returned as they are and turned over. Vertical lines
    are turned a quarter turn counterclockwise (upright if the line reads
    downward) and clockwise (upright if it reads upward). Long lines are
    trimmed to their middle.

    Returns:
        Both crops, as image arrays.
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
        return OrientationCrops(np.rot90(crop, 1), np.rot90(crop, -1))
    if w > ORIENTATION_MAX_ASPECT * h:
        start = (w - ORIENTATION_MAX_ASPECT * h) // 2
        crop = crop[:, start : start + ORIENTATION_MAX_ASPECT * h]
    return OrientationCrops(crop, np.rot90(crop, 2))


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
# Page orientation model


@dataclass(frozen=True, slots=True)
class ModelFile:
    """A model file that is downloaded when first needed."""

    filename: str
    url: str
    size: int
    sha256: str


#: PP-LCNet_x1_0_doc_ori, PaddlePaddle's four-class document orientation
#: classifier from PaddleClas, exported to ONNX. Apache-2.0 licensed.
ORIENTATION_MODEL = ModelFile(
    filename='PP-LCNet_x1_0_doc_ori.onnx',
    url=(
        'https://huggingface.co/PaddlePaddle/PP-LCNet_x1_0_doc_ori_onnx/resolve/'
        '7330ab7039123e46af2dc03154b9969aa412c61d/inference.onnx'
    ),
    size=6_788_069,
    sha256='af9a0a4f317ff0709ce752067807f819cb15d883f8ecad89f28df1c6ee2d9c92',
)
#: The model's classes, in order: how far the page is turned clockwise, as
#: its inference.yml labels them. That is also Tesseract OSD's "Orientation
#: in degrees", which OrientationConfidence.angle follows.
ORIENTATION_MODEL_CLASSES = (0, 90, 180, 270)
#: PaddleClas preprocessing for the model: shorter side resized to 256
#: pixels, then a centred square of 224 pixels, normalised with ImageNet's
#: channel means and standard deviations.
ORIENTATION_RESIZE_SHORT = 256
ORIENTATION_CROP = 224
_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD = (0.229, 0.224, 0.225)

#: Seconds to wait for the model download to respond.
DOWNLOAD_TIMEOUT = 30

#: The model must give the orientation it names at least this probability;
#: chance among its four classes is 0.25.
MIN_MODEL_PROBABILITY = 0.5
#: Below this probability, a sideways reading is confirmed by recognition.
SURE_MODEL_PROBABILITY = 0.75
#: Line boxes decide whether text runs along the page or across it. The
#: winning direction needs at least this much line length, in multiples of
#: the page's longer side, and this many times the length of the other.
MIN_AXIS_WEIGHT = 1.0
MIN_AXIS_RATIO = 2.0
#: Confidence of a page on which the line boxes and the model fully agree.
MAX_MODEL_CONFIDENCE = 30.0


@dataclass(frozen=True, slots=True)
class ModelOrientation:
    """The page orientation model's answer.

    Attributes:
        angle: How far the page content is turned clockwise (0, 90, 180, 270).
        probability: The probability the model gives that angle.
    """

    angle: int
    probability: float


@dataclass(frozen=True, slots=True)
class AxisVotes:
    """Length of the text lines that run along the page, and across it.

    Each is the sum of the lengths of line boxes, in multiples of the page
    image's longer side.
    """

    along: float
    sideways: float


class PageAxis(Enum):
    """Which way a page's text lines run, as their boxes show."""

    ALONG = 'along'
    SIDEWAYS = 'sideways'
    UNCLEAR = 'unclear'


def axis_votes(quads: Sequence[Quad] | None, size: tuple[int, int]) -> AxisVotes:
    """Measure the text lines that run along the page and across it.

    Boxes at least VERTICAL_ASPECT times longer than they are thick vote,
    weighted by their length; a box's shape is measured, not judged, so this
    reliably tells a sideways page from one that is upright or upside down.
    """
    along = sideways = 0.0
    for raw in quads if quads is not None else ():
        width, height = _quad_dims(_as_quad(raw))
        if width >= VERTICAL_ASPECT * height:
            along += width
        elif height >= VERTICAL_ASPECT * width:
            sideways += height
    scale = max(size) or 1
    return AxisVotes(along=along / scale, sideways=sideways / scale)


def page_axis(votes: AxisVotes) -> PageAxis:
    """Decide which way a page's text lines run, if the votes are clear."""
    if votes.sideways >= MIN_AXIS_WEIGHT and (
        votes.sideways >= MIN_AXIS_RATIO * votes.along
    ):
        return PageAxis.SIDEWAYS
    if (
        votes.along >= MIN_AXIS_WEIGHT
        and votes.along >= MIN_AXIS_RATIO * votes.sideways
    ):
        return PageAxis.ALONG
    return PageAxis.UNCLEAR


def _axis_angles(axis: PageAxis) -> tuple[int, ...]:
    if axis is PageAxis.SIDEWAYS:
        return (90, 270)
    if axis is PageAxis.ALONG:
        return (0, 180)
    return ()


def needs_recognition(votes: AxisVotes, direction: ModelOrientation) -> bool:
    """Whether the model's reading must be confirmed by recognition.

    An upside down reading always must be, and a sideways one if the model
    is not sure of it.
    """
    return (
        direction.angle in _axis_angles(page_axis(votes))
        and direction.probability >= MIN_MODEL_PROBABILITY
        and (
            direction.angle == 180
            or (direction.angle != 0 and direction.probability < SURE_MODEL_PROBABILITY)
        )
    )


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def combine_orientation(
    votes: AxisVotes,
    direction: ModelOrientation,
    recognition: OrientationConfidence | None = None,
) -> OrientationConfidence:
    """Decide page orientation from the line boxes and the orientation model.

    The model reads the whole page at 224 pixels square. Alone, it turns
    upright maps, charts and covers, so it never decides on its own: the
    line boxes say whether the page is sideways, and the model which way.

    - Lines run across the page, and the model says 90 or 270: the page is
      turned that way.
    - Lines run along the page, and the model says 0: the page is upright.
    - Lines run along the page, and the model says 180: the page is upside
      down only if recognition, which compares how well the longest lines
      read either way up, agrees.
    - Anything else, including an unsure model (probability below 0.5) or
      lines that run both ways, is not acted on: confidence is 0.

    Confidence is put on the scale of Tesseract's OSD, so that OCRmyPDF's
    default --rotate-pages-threshold of 14 keeps its meaning. It is 30 times
    two factors: the model's certainty, its probability rescaled from chance
    (0.25) to 1, and the winning direction's share of the line length
    rescaled from a tie (0.5) to 0.75 or more. On text pages the model's
    probability is about 0.92 and nearly all lines run one way, so agreement
    lands at about 27; a probability under 0.6, or lines split 2 to 1, keeps
    it under 14.

    Where recognition was consulted (see :func:`needs_recognition`) and
    agrees, the model's certainty is replaced by recognition's, its own
    confidence over 20, if that is higher. So a sideways page that the model
    is unsure of, such as a dense table of small figures, is still turned
    when recognition agrees. If recognition disagrees, confidence is 0.

    Args:
        votes: Line lengths along the page and across it.
        direction: The orientation model's answer.
        recognition: The recognition comparison, if consulted.

    Returns:
        How far the page content is turned clockwise, and confidence.
    """
    no_decision = OrientationConfidence(angle=0, confidence=0.0)
    axis = page_axis(votes)
    if (
        direction.angle not in _axis_angles(axis)
        or direction.probability < MIN_MODEL_PROBABILITY
    ):
        return no_decision
    certainty = _clamp((direction.probability - 0.25) / 0.75)
    if needs_recognition(votes, direction):
        if recognition is None or recognition.angle != direction.angle:
            return no_decision
        certainty = max(certainty, _clamp(recognition.confidence / 20))
    share = max(votes.along, votes.sideways) / (votes.along + votes.sideways)
    confidence = MAX_MODEL_CONFIDENCE * certainty * _clamp((share - 0.5) * 4)
    return OrientationConfidence(angle=direction.angle, confidence=confidence)


def orientation_model_input(image: Image.Image) -> Any:
    """Prepare a page image for the orientation model.

    Returns:
        A float32 array of shape (1, 3, 224, 224).
    """
    import numpy as np

    rgb = image.convert('RGB')
    width, height = rgb.size
    scale = ORIENTATION_RESIZE_SHORT / min(width, height)
    resized = rgb.resize(
        (max(1, round(width * scale)), max(1, round(height * scale))),
        Image.Resampling.LANCZOS,
        reducing_gap=3.0,
    )
    left = (resized.width - ORIENTATION_CROP) // 2
    top = (resized.height - ORIENTATION_CROP) // 2
    cropped = resized.crop((left, top, left + ORIENTATION_CROP, top + ORIENTATION_CROP))
    pixels = np.asarray(cropped, dtype=np.float32) / 255.0
    mean = np.array(_IMAGENET_MEAN, dtype=np.float32)
    std = np.array(_IMAGENET_STD, dtype=np.float32)
    return ((pixels - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)


class DocOrientationModel:
    """The page orientation model, on ONNX Runtime."""

    def __init__(self, model_path: Path | None = None, *, session: Any = None):
        """Load the model from a file, or wrap an existing ONNX session."""
        if session is None:
            import onnxruntime as ort

            session_options = ort.SessionOptions()
            session_options.log_severity_level = 3
            # OCRmyPDF runs one worker per core already
            session_options.intra_op_num_threads = 1
            session_options.inter_op_num_threads = 1
            session = ort.InferenceSession(
                str(model_path), session_options, providers=['CPUExecutionProvider']
            )
        self._session = session
        self._input_name = session.get_inputs()[0].name

    def __call__(self, image: Image.Image) -> ModelOrientation:
        """Classify a page image. The model's output is already softmaxed."""
        import numpy as np

        output = self._session.run(
            None, {self._input_name: orientation_model_input(image)}
        )[0]
        probabilities = np.asarray(output, dtype=np.float64).reshape(-1)
        best = int(np.argmax(probabilities))
        return ModelOrientation(
            angle=ORIENTATION_MODEL_CLASSES[best],
            probability=float(probabilities[best]),
        )


def _user_cache_dir() -> Path:
    """OCRmyPDF's directory in the user's cache."""
    if sys.platform == 'win32' and (local := os.environ.get('LOCALAPPDATA')):
        return Path(local) / 'ocrmypdf' / 'Cache'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Caches' / 'ocrmypdf'
    xdg = os.environ.get('XDG_CACHE_HOME')
    return (Path(xdg) if xdg else Path.home() / '.cache') / 'ocrmypdf'


def orientation_model_dirs(model_dir: Path | None = None) -> list[Path]:
    """Where the orientation model is looked for, and stored, in that order.

    It is kept with RapidOCR's models, in model_dir if given, or in the user's
    cache if that directory cannot be written.
    """
    models_dir = model_dir if model_dir is not None else rapidocr_models_dir()
    dirs = [models_dir] if models_dir is not None else []
    return [*dirs, _user_cache_dir()]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _is_intact(path: Path, model: ModelFile) -> bool:
    try:
        return path.stat().st_size == model.size and _sha256(path) == model.sha256
    except OSError:
        return False


def find_orientation_model(model_dir: Path | None = None) -> Path | None:
    """Find a verified copy of the orientation model, if one is stored."""
    for directory in orientation_model_dirs(model_dir):
        path = directory / ORIENTATION_MODEL.filename
        if _is_intact(path, ORIENTATION_MODEL):
            return path
    return None


def _urlopen(url: str, timeout: float) -> Any:
    return urllib.request.urlopen(url, timeout=timeout)


def _download(model: ModelFile, out: BinaryIO, timeout: float) -> None:
    """Download a model file, and check its size and checksum."""
    digest = hashlib.sha256()
    size = 0
    try:
        with _urlopen(model.url, timeout) as response:
            while chunk := response.read(1 << 16):
                size += len(chunk)
                if size > model.size:
                    break
                digest.update(chunk)
                out.write(chunk)
    except OSError as e:  # including URLError, HTTPError and timeouts
        raise MissingDependencyError(
            f"Could not download the page orientation model from {model.url}: {e}"
        ) from e
    if size != model.size or digest.hexdigest() != model.sha256:
        raise MissingDependencyError(
            f"The page orientation model downloaded from {model.url} does not "
            "match its expected size and checksum."
        )


def download_orientation_model(
    model_dir: Path | None = None, *, timeout: float = DOWNLOAD_TIMEOUT
) -> Path:
    """Return the orientation model's path, downloading it if necessary.

    The download is checked against the model's size and SHA-256 checksum,
    and stored under a temporary name until complete, so that no damaged or
    partial file is ever found under the model's name.

    Raises:
        MissingDependencyError: The model could not be downloaded or stored.
    """
    found = find_orientation_model(model_dir)
    if found is not None:
        return found
    model = ORIENTATION_MODEL
    dirs = orientation_model_dirs(model_dir)
    for directory in dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(
                prefix=f'.{model.filename}.', suffix='.part', dir=directory
            )
        except OSError:
            continue  # not writable; try the next directory
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, 'wb') as out:
                _download(model, out, timeout)
            # Temporary files are private; the model is not
            temp.chmod(0o644)
            target = directory / model.filename
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
        log.info(f"Downloaded the page orientation model to {target}")
        return target
    raise MissingDependencyError(
        "Could not store the page orientation model in any of: "
        + ', '.join(str(d) for d in dirs)
    )


#: The orientation model's path once found or downloaded, or None if it could
#: not be had, by model directory. Shared by all threads.
_orientation_model_paths: dict[Path | None, Path | None] = {}
_orientation_model_lock = threading.Lock()


def _orientation_model_path(model_dir: Path | None = None) -> Path | None:
    """Find or download the orientation model, once per process."""
    with _orientation_model_lock:
        if model_dir not in _orientation_model_paths:
            try:
                path = download_orientation_model(model_dir)
            except MissingDependencyError as e:
                log.warning(
                    f"{e} Judging page orientation by recognizing text instead, "
                    f"which is slower. To download the model in advance, run: "
                    f"{DOWNLOAD_COMMAND}"
                )
                path = None
            _orientation_model_paths[model_dir] = path
        return _orientation_model_paths[model_dir]


def _orientation_model(model_dir: Path | None = None) -> DocOrientationModel | None:
    """Return the current thread's orientation model, or None if unavailable."""
    models: dict[Path, DocOrientationModel] | None = getattr(
        _thread_engines, 'orientation_models', None
    )
    if models is None:
        models = _thread_engines.orientation_models = {}
    path = _orientation_model_path(model_dir)
    if path is None:
        return None
    if path not in models:
        models[path] = DocOrientationModel(path)
    return models[path]


# --------------------------------------------------------------------------
# RapidOCR engine


DOWNLOAD_COMMAND = 'python -m ocrmypdf.builtin_plugins.rapidocr_ocr download'

INSTALL_HINT = (
    "Install them with: uv tool install 'ocrmypdf[rapidocr]' "
    "(or, in a virtual environment, uv pip install 'ocrmypdf[rapidocr]' or "
    "pip install 'ocrmypdf[rapidocr]')"
)


def _import_rapidocr():
    try:
        import onnxruntime  # noqa: F401
        import rapidocr
    except ImportError as e:
        raise MissingDependencyError(
            "The RapidOCR engine requires the rapidocr and onnxruntime packages. "
            + INSTALL_HINT
        ) from e
    return rapidocr


def _model_load_errors() -> tuple[type[BaseException], ...]:
    """Exceptions that mean a model could not be downloaded or loaded.

    RapidOCR raises its own exception for HTTP errors, OSError for network
    and file system errors, and ONNX Runtime raises its own exceptions,
    which derive only from Exception, for damaged model files.
    """
    errors: list[type[BaseException]] = [OSError]
    try:
        from rapidocr.utils.download_file import DownloadFileException

        errors.append(DownloadFileException)
    except ImportError:
        pass
    try:
        from onnxruntime.capi import onnxruntime_pybind11_state as ort_state

        errors += [ort_state.Fail, ort_state.InvalidProtobuf, ort_state.NoSuchFile]
    except ImportError:
        pass
    return tuple(errors)


def rapidocr_models_dir() -> Path | None:
    """Where RapidOCR keeps its models, or None if it is not installed."""
    import importlib.util

    spec = importlib.util.find_spec('rapidocr')
    if spec is None or spec.origin is None:
        return None
    return Path(spec.origin).parent / 'models'


@dataclass(frozen=True, slots=True)
class _EngineConfig:
    """What a RapidOCR instance is configured for."""

    max_side_len: int
    rec: RecModel
    model_dir: Path | None = None

    def rapidocr_params(self, rapidocr: Any) -> dict[str, Any]:
        """RapidOCR's ``params`` for this configuration."""
        params = {
            'Global.log_level': 'error',
            'Global.max_side_len': self.max_side_len,
            'Global.return_word_box': True,
            'Global.use_cls': False,
            # OCRmyPDF runs one worker per core already
            'EngineConfig.onnxruntime.intra_op_num_threads': 1,
            'EngineConfig.onnxruntime.inter_op_num_threads': 1,
            'Rec.ocr_version': rapidocr.OCRVersion(self.rec.ocr_version),
            'Rec.model_type': rapidocr.ModelType(self.rec.model_type),
            'Rec.lang_type': rapidocr.LangRec(self.rec.lang_type),
        }
        if self.model_dir is not None:
            params['Global.model_root_dir'] = str(self.model_dir)
        return params


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
    engine = rapidocr.RapidOCR(params=config.rapidocr_params(rapidocr))
    # RapidOCR loads its models when first used, downloading any that are not
    # bundled. Load them now, so that a failed download is reported here.
    try:
        engine._load_det_model()
        engine._load_rec_model()
    except _model_load_errors() as e:
        rec = config.rec
        if config.model_dir is None:
            missing = (
                "Models other than the bundled one download on first use "
                f"into {rapidocr_models_dir()}"
            )
        else:
            missing = f"Models download on first use into {config.model_dir}"
        raise MissingDependencyError(
            f"RapidOCR could not load its {rec.ocr_version} {rec.lang_type} "
            f"recognition model: {e}. {missing}, which needs network access "
            "and a writable directory. To download them in advance, run: "
            f"{DOWNLOAD_COMMAND} LANGUAGE"
        ) from e
    return engine


def _engine_for(options: OcrOptions) -> Any:
    return _get_engine(
        _EngineConfig(
            max_side_len=options.rapidocr.max_side_len,
            rec=rec_model_for_languages(options.languages),
            model_dir=options.rapidocr.model_dir,
        )
    )


@dataclass(frozen=True, slots=True)
class _PageImage:
    """A page image ready for RapidOCR, and its resolution."""

    image: Image.Image
    dpi: float


def _load_image(input_file: Path) -> _PageImage:
    with Image.open(input_file) as im:
        dpi_info = im.info.get('dpi', (300, 300))
        dpi = float(dpi_info[0] if isinstance(dpi_info, tuple) else dpi_info)
        if im.mode in ('1', 'L', 'I', 'I;16', 'F'):
            loaded = im.convert('L')
        else:
            loaded = im.convert('RGB')
    return _PageImage(loaded, dpi)


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


def _orientation_by_recognition(
    engine: Any, image: Image.Image, quads: Any
) -> OrientationConfidence:
    """Judge orientation by recognizing the longest lines both ways up."""
    import numpy as np

    selected = select_orientation_lines(quads)
    if selected is None:
        return OrientationConfidence(angle=0, confidence=0.0)
    array = np.asarray(image.convert('RGB'))[:, :, ::-1]  # RapidOCR wants BGR
    crops = [
        orientation_crops(array, quads[i], selected.vertical) for i in selected.indices
    ]
    crops = [c for c in crops if c.upright.size]
    if len(crops) < ORIENTATION_MIN_LINES:
        return OrientationConfidence(angle=0, confidence=0.0)
    upright = _mean_rec_score(engine, [c.upright for c in crops])
    turned = _mean_rec_score(engine, [c.turned for c in crops])
    return orientation_from_scores(
        selected.vertical, upright, turned, selected.axis_share
    )


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
        image = _load_image(input_file).image
        engine = _engine_for(options)
        quads = _boxes(_run(engine, image, rec=False))
        votes = axis_votes(quads, image.size)
        if page_axis(votes) is PageAxis.UNCLEAR:
            log.debug(f"Orientation: {votes}; too few lines, or lines both ways")
            return OrientationConfidence(angle=0, confidence=0.0)
        model = _orientation_model(options.rapidocr.model_dir)
        if model is None:
            return _orientation_by_recognition(engine, image, quads)
        direction = model(image)
        recognition = None
        if needs_recognition(votes, direction):
            recognition = _orientation_by_recognition(engine, image, quads)
        result = combine_orientation(votes, direction, recognition)
        log.debug(f"Orientation: {votes}, {direction}, {recognition} -> {result}")
        return result

    @staticmethod
    def get_deskew(input_file: Path, options: OcrOptions) -> float:
        image = _load_image(input_file).image
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

        loaded = _load_image(input_file)
        image = loaded.image
        result = _run(_engine_for(options), image, rec=True)
        boxes = _boxes(result)
        page = rapidocr_to_ocr_tree(
            boxes,
            tuple(result.txts) if boxes is not None else None,
            tuple(float(s) for s in result.scores) if boxes is not None else None,
            result.word_results if boxes is not None else None,
            width=image.width,
            height=image.height,
            dpi=loaded.dpi,
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
    model_dir = options.rapidocr.model_dir
    if model_dir is not None and model_dir.exists() and not model_dir.is_dir():
        raise BadArgsError(f"--rapidocr-model-dir {model_dir} is not a directory.")


@hookimpl
def get_ocr_engine(options):
    """Return RapidOcrEngine when --ocr-engine rapidocr is selected."""
    if options is not None and _selected(options):
        return RapidOcrEngine()
    return None


# --------------------------------------------------------------------------
# Downloading models in advance


def download_models(languages: Sequence[str], model_dir: Path | None = None) -> None:
    """Download the orientation model, and the models for the given languages.

    Languages read by the bundled recognition model need nothing more. A
    model_dir starts empty, though, so without languages, the bundled models
    are fetched into it.
    """
    print(f"Page orientation model: {download_orientation_model(model_dir)}")
    if model_dir is not None and not languages:
        languages = ['eng']
    for lang in languages:
        rec = rec_model_for_languages([lang])
        _create_engine(_EngineConfig(DEFAULT_MAX_SIDE_LEN, rec, model_dir))
        print(
            f"{lang}: {rec.ocr_version} {rec.lang_type} recognition model "
            f"in {model_dir or rapidocr_models_dir()}"
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Download RapidOCR models in advance."""
    import argparse

    parser = argparse.ArgumentParser(
        prog=DOWNLOAD_COMMAND.removesuffix(' download'),
        description=(
            "Download models for OCRmyPDF's RapidOCR engine in advance, instead "
            "of on first use, for example while building a container image."
        ),
    )
    commands = parser.add_subparsers(dest='command', required=True)
    download = commands.add_parser(
        'download',
        help="Download the page orientation model and recognition models",
        description=(
            "Download the page orientation model, and the recognition models "
            "for the given languages, into RapidOCR's model directory, or the "
            "one given by --model-dir."
        ),
    )
    download.add_argument(
        '--model-dir',
        type=Path,
        metavar='DIR',
        default=_model_dir_from_env(),
        help=(
            "Download into this directory instead of RapidOCR's, for use with "
            f"ocrmypdf --rapidocr-model-dir. Defaults to ${MODEL_DIR_ENV} if set."
        ),
    )
    download.add_argument(
        'languages',
        nargs='*',
        metavar='LANGUAGE',
        help=(
            "Languages to download recognition models for, as given to -l, "
            "such as kor or rus+ukr. Languages read by the bundled model, "
            "including English, Chinese, Japanese and most Latin-script "
            "languages, need no download."
        ),
    )
    args = parser.parse_args(argv)
    languages = [lang for arg in args.languages for lang in arg.split('+') if lang]
    try:
        download_models(languages, args.model_dir)
    except (BadArgsError, MissingDependencyError) as e:
        print(e, file=sys.stderr)
        return e.exit_code
    return 0


if __name__ == '__main__':
    sys.exit(main())
