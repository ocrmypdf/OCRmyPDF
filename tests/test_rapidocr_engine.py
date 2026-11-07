# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for the RapidOCR engine plugin.

Most tests feed canned RapidOCR output to the conversion functions and need no
model. Tests that run the models are skipped when rapidocr is not installed.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import threading
from math import atan2, cos, degrees, radians, sin
from pathlib import Path

import pytest

from ocrmypdf.builtin_plugins import rapidocr_ocr
from ocrmypdf.builtin_plugins.rapidocr_ocr import (
    RecModel,
    estimate_skew_angle,
    ocr_tree_to_hocr,
    ocr_tree_to_text,
    orientation_crops,
    orientation_from_scores,
    rapidocr_to_ocr_tree,
    rec_model_for_languages,
    select_orientation_lines,
)
from ocrmypdf.exceptions import BadArgsError, MissingDependencyError
from ocrmypdf.hocrtransform import HocrParser, OcrClass

have_rapidocr = importlib.util.find_spec('rapidocr') is not None
needs_rapidocr = pytest.mark.skipif(not have_rapidocr, reason="rapidocr not installed")


def rect(left, top, right, bottom):
    """A quad, clockwise from top-left, for an axis-aligned rectangle."""
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


def rotated_quad(cx, cy, length, height, angle_deg):
    """A quad for a line centred on (cx, cy) whose baseline descends by angle_deg.

    Image coordinates: y increases downward, so a positive angle means the
    line runs downhill to the right.
    """
    a = radians(angle_deg)
    ux, uy = cos(a), sin(a)  # along the line
    vx, vy = -sin(a), cos(a)  # down, perpendicular to the line
    hl, hh = length / 2, height / 2
    return [
        [cx - hl * ux - hh * vx, cy - hl * uy - hh * vy],  # TL
        [cx + hl * ux - hh * vx, cy + hl * uy - hh * vy],  # TR
        [cx + hl * ux + hh * vx, cy + hl * uy + hh * vy],  # BR
        [cx - hl * ux + hh * vx, cy - hl * uy + hh * vy],  # BL
    ]


def convert(boxes, txts, word_results=None, *, language='eng', image=None):
    scores = tuple(0.9 for _ in txts)
    return rapidocr_to_ocr_tree(
        boxes,
        txts,
        scores,
        word_results,
        width=2550,
        height=3300,
        dpi=300,
        language=language,
        image=image,
    )


def ink_page(lines, slope=0.0, descenders=True):
    """A white page with a dark band for each (left, right, top, baseline).

    Each band is inked in two of every three columns from top to baseline,
    like capitals and x-height letters, with sparse descenders below the
    baseline.
    """
    import numpy as np

    image = np.full((3300, 2550), 255, dtype=np.uint8)
    for left, right, top, baseline in lines:
        for x in range(left, right):
            dy = round(slope * (x - left))
            if x % 3:
                image[top + dy : baseline + dy, x] = 0
            if descenders and x % 10 == 0:
                image[baseline + dy : baseline + dy + 8, x] = 0
    return image


HORIZONTAL_BOXES = [
    rect(343.6, 374.2, 2194.7, 422.5),
    rect(343.6, 424.1, 1997.2, 472.4),
]
HORIZONTAL_TXTS = ("The LinnSequencer is", "extremely powerful")
HORIZONTAL_WORDS = (
    (
        ('The', 0.99, rect(354, 374, 411, 422)),
        ('LinnSequencer', 0.99, rect(426, 374, 676, 422)),
        ('is', 0.99, rect(683, 374, 716, 422)),
    ),
    (
        ('extremely', 0.99, rect(346, 424, 508, 472)),
        ('powerful', 0.99, rect(523, 424, 685, 472)),
    ),
)


class TestConversion:
    def test_page(self):
        page = convert(HORIZONTAL_BOXES, HORIZONTAL_TXTS, HORIZONTAL_WORDS)
        assert page.ocr_class == OcrClass.PAGE
        assert page.dpi == 300
        assert (page.bbox.right, page.bbox.bottom) == (2550, 3300)

    def test_horizontal_lines(self):
        page = convert(HORIZONTAL_BOXES, HORIZONTAL_TXTS, HORIZONTAL_WORDS)
        lines = page.lines
        assert len(lines) == 2
        line = lines[0]
        assert line.bbox.left == pytest.approx(343.6)
        assert line.bbox.bottom == pytest.approx(422.5)
        assert line.textangle is None
        assert line.baseline.slope == pytest.approx(0.0)
        # The detection box is padded around the glyphs, so the baseline sits
        # a little above its bottom edge (hOCR intercepts are negative).
        assert -0.4 * line.bbox.height < line.baseline.intercept < 0
        assert line.poly == [tuple(p) for p in HORIZONTAL_BOXES[0]]
        assert line.language == 'eng'
        assert line.confidence == pytest.approx(0.9)
        assert [w.text for w in line.words] == ['The', 'LinnSequencer', 'is']
        assert line.words[1].bbox.left == 426
        assert line.words[1].confidence == pytest.approx(0.99)

    def test_every_line_is_inside_a_paragraph(self):
        # The renderer only draws lines directly under a paragraph once any
        # paragraph exists.
        page = convert(HORIZONTAL_BOXES, HORIZONTAL_TXTS, HORIZONTAL_WORDS)
        assert all(child.ocr_class == OcrClass.PARAGRAPH for child in page.children)
        assert sum(len(p.children) for p in page.paragraphs) == 2

    def test_adjacent_lines_share_a_paragraph(self):
        page = convert(HORIZONTAL_BOXES, HORIZONTAL_TXTS, HORIZONTAL_WORDS)
        assert len(page.paragraphs) == 1

    def test_two_columns_become_separate_paragraphs_in_column_order(self):
        # RapidOCR sorts lines by y then x, interleaving the lines of two
        # columns. Paragraphs follow each column.
        boxes = [
            rect(100, 100, 1000, 140),
            rect(1300, 100, 2200, 140),
            rect(100, 150, 1000, 190),
            rect(1300, 150, 2200, 190),
        ]
        txts = ('left one', 'right one', 'left two', 'right two')
        page = convert(boxes, txts)
        assert [
            [ln.get_text_recursive() for ln in p.children] for p in page.paragraphs
        ] == [
            ['left one', 'left two'],
            ['right one', 'right two'],
        ]
        assert ocr_tree_to_text(page) == "left one\nleft two\n\nright one\nright two\n"

    def test_overlapping_detection_boxes_stay_in_order(self):
        # Detection boxes are padded and can overlap the line above by more
        # than half their height. Measured on a 300 dpi Russian page.
        boxes = [
            rect(227, 699, 2324, 775),
            rect(222, 742, 2323, 830),
            rect(224, 790, 2311, 878),
            rect(224, 883, 2319, 961),
        ]
        txts = ('one', 'two', 'three', 'four')
        page = convert(boxes, txts)
        assert ocr_tree_to_text(page) == "one\ntwo\nthree\nfour\n"

    @staticmethod
    def table(top, rows=5, cols=6):
        boxes, txts = [], []
        for r in range(rows):
            for c in range(cols):
                left, y = 100 + 300 * c, top + 50 * r
                boxes.append(rect(left, y, left + 150, y + 42))
                txts.append(f'r{r}c{c}')
        return boxes, txts

    def test_table_reads_row_by_row(self):
        boxes, txts = self.table(100)
        page = convert(boxes, txts)
        # One line per cell in the text layer, grouped by row
        assert len(page.lines) == 30
        assert len(page.paragraphs) == 5
        expected = ''.join(
            ' '.join(f'r{r}c{c}' for c in range(6)) + '\n' for r in range(5)
        )
        assert ocr_tree_to_text(page) == expected

    def test_table_rows_in_order_when_lines_arrive_shuffled(self):
        boxes, txts = self.table(100)
        order = sorted(range(30), key=lambda i: (i % 6, i // 6))  # by column
        page = convert([boxes[i] for i in order], tuple(txts[i] for i in order))
        assert ocr_tree_to_text(page).splitlines()[1] == 'r1c0 r1c1 r1c2 r1c3 r1c4 r1c5'

    def test_header_above_table(self):
        header = [rect(100, 100, 1700, 142), rect(100, 150, 1500, 192)]
        caption = [rect(100, 250, 1200, 292)]  # left-aligned with column 0
        boxes, txts = self.table(300)
        page = convert(
            header + caption + boxes,
            ('header one', 'header two', 'Description of the samples', *txts),
        )
        lines = ocr_tree_to_text(page).split('\n')
        assert lines[:4] == [
            'header one',
            'header two',
            '',
            'Description of the samples',
        ]
        assert lines[4] == 'r0c0 r0c1 r0c2 r0c3 r0c4 r0c5'
        assert lines[8] == 'r4c0 r4c1 r4c2 r4c3 r4c4 r4c5'

    def test_two_column_prose_with_short_last_lines(self):
        boxes = []
        txts = []
        for n in range(4):
            boxes.append(rect(100, 100 + 50 * n, 1000 if n < 3 else 300, 142 + 50 * n))
            txts.append(f'left {n}')
            boxes.append(rect(1300, 100 + 50 * n, 2200, 142 + 50 * n))
            txts.append(f'right {n}')
        boxes.append(rect(1300, 300, 1500, 342))
        txts.append('right end')
        page = convert(boxes, tuple(txts))
        assert ocr_tree_to_text(page) == (
            "left 0\nleft 1\nleft 2\nleft 3\n\n"
            "right 0\nright 1\nright 2\nright 3\nright end\n"
        )

    def test_two_column_prose_with_paragraph_gaps(self):
        # Paragraphs in the two columns end at about the same height; the
        # columns must still be read one after the other.
        def paragraph(name, left, top, n):
            return [
                (rect(left, top + 50 * i, left + 900, top + 42 + 50 * i), f'{name}{i}')
                for i in range(n)
            ]

        lines = (
            paragraph('a', 100, 100, 3)
            + paragraph('b', 100, 300, 3)
            + paragraph('c', 1300, 100, 3)
            + paragraph('d', 1300, 300, 4)
        )
        lines.sort(key=lambda item: (item[0][0][1], item[0][0][0]))
        page = convert([b for b, _ in lines], tuple(t for _, t in lines))
        assert ocr_tree_to_text(page) == (
            "a0\na1\na2\n\nb0\nb1\nb2\n\nc0\nc1\nc2\n\nd0\nd1\nd2\nd3\n"
        )

    def test_table_with_a_wide_column(self):
        # Long descriptions stack like prose, but their neighbours on each row
        # are table cells, so the table is still read by rows.
        boxes, txts = [], []
        for r in range(5):
            y = 100 + 50 * r
            for left, right, text in (
                (100, 250, f'code{r}'),
                (300, 1300, f'description number {r}'),
                (1400, 1480, f'{r}'),
                (1600, 1750, f'{r}.00'),
            ):
                boxes.append(rect(left, y, right, y + 42))
                txts.append(text)
        page = convert(boxes, tuple(txts))
        assert ocr_tree_to_text(page).splitlines() == [
            f'code{r} description number {r} {r} {r}.00' for r in range(5)
        ]

    def test_paragraph_beside_key_value_pairs(self):
        boxes = [rect(100, 100 + 50 * i, 1000, 142 + 50 * i) for i in range(4)] + [
            rect(1300, 100, 1500, 142),
            rect(1700, 100, 1900, 142),
            rect(1300, 150, 1500, 192),
            rect(1700, 150, 1900, 192),
        ]
        txts = ('p0', 'p1', 'p2', 'p3', 'Date', '14/03', 'Due', '13/04')
        page = convert(boxes, txts)
        assert ocr_tree_to_text(page) == "p0\np1\np2\np3\n\nDate 14/03\nDue 13/04\n"

    def test_skewed_line_baseline(self):
        quad = rotated_quad(1200, 1000, 1800, 50, 2.0)
        page = convert([quad], ("skewed text line",))
        (line,) = page.lines
        assert line.baseline.slope == pytest.approx(0.0349, abs=1e-3)
        # The baseline (y = slope * (x - left) + bottom + intercept) runs
        # parallel to the quad's bottom edge, a quarter of its height above it.
        bl, br = quad[3], quad[2]
        for x, y_edge in (bl, br):
            y = line.baseline.slope * (x - line.bbox.left)
            y += line.bbox.bottom + line.baseline.intercept
            assert y_edge - 0.3 * 50 < y < y_edge
        assert line.bbox.height > 50 + 1800 * sin(radians(2.0)) - 1

    def test_rising_line_baseline(self):
        quad = rotated_quad(1200, 1000, 1800, 50, -2.0)
        page = convert([quad], ("rising text line",))
        (line,) = page.lines
        assert line.baseline.slope == pytest.approx(-0.0349, abs=1e-3)
        x, y_edge = quad[3]
        y = line.baseline.slope * (x - line.bbox.left)
        y += line.bbox.bottom + line.baseline.intercept
        assert y_edge - 0.3 * 50 < y < y_edge

    def test_vertical_line_reads_downward(self):
        boxes = [rect(1488, 304, 1556, 970)]
        words = (
            (
                ('这', 1.0, rect(1487, 314, 1555, 369)),
                ('是', 1.0, rect(1487, 369, 1555, 424)),
            ),
        )
        page = convert(boxes, ("这是",), words, language='chi_sim')
        (line,) = page.lines
        assert line.textangle == 270
        assert [w.text for w in line.words] == ['这', '是']
        assert line.language == 'chi_sim'

    def test_cjk_per_character_words(self):
        boxes = [rect(95, 108, 777, 167)]
        words = (
            (
                ('我', 1.0, rect(107, 108, 148, 168)),
                ('们', 1.0, rect(148, 108, 189, 168)),
                ('可', 1.0, rect(195, 108, 238, 168)),
            ),
        )
        page = convert(boxes, ("我们可",), words, language='chi_sim')
        (line,) = page.lines
        assert [w.text for w in line.words] == ['我', '们', '可']
        assert line.textangle is None
        assert ocr_tree_to_text(page) == "我们可\n"

    def test_abutting_words_are_separated(self):
        # RapidOCR's word boxes divide the line between its words, so
        # neighbours can touch. The renderer appends a space to each word;
        # unless the boxes leave room for it, extractors join the words.
        boxes = [rect(343, 479, 1000, 529)]
        words = (
            (
                ('is', 0.99, rect(595, 479, 635, 529)),
                ('similar', 0.99, rect(636, 479, 776, 529)),
                ('to', 0.99, rect(800, 479, 840, 529)),
            ),
        )
        page = convert(boxes, ("is similar to",), words)
        is_, similar, to = page.lines[0].words
        assert similar.bbox.left - is_.bbox.right >= 0.2 * 50
        assert is_.bbox.left == 595
        assert similar.bbox.left == 636
        # Words already apart are left alone
        assert similar.bbox.right == 776

    def test_abutting_cjk_characters_are_not_separated(self):
        boxes = [rect(95, 108, 777, 167)]
        words = (
            (
                ('我', 1.0, rect(107, 108, 148, 168)),
                ('们', 1.0, rect(148, 108, 189, 168)),
            ),
        )
        page = convert(boxes, ("我们",), words, language='chi_sim')
        assert page.lines[0].words[0].bbox.right == 148

    def test_empty_page(self):
        page = convert(None, ())
        assert page.children == []
        assert page.bbox.right == 2550
        assert ocr_tree_to_text(page) == ""

    def test_missing_word_results_split_on_spaces(self):
        boxes = [rect(100, 100, 1100, 150)]
        page = convert(boxes, ("aaaa bbbbb",), None)
        (line,) = page.lines
        first, second = line.words
        assert (first.text, second.text) == ('aaaa', 'bbbbb')
        assert first.bbox.left == pytest.approx(100)
        assert second.bbox.right == pytest.approx(1100)
        assert first.bbox.right < second.bbox.left
        # Widths are proportional to character counts
        assert first.bbox.width / second.bbox.width == pytest.approx(4 / 5)

    def test_missing_word_results_for_one_line_keeps_others_aligned(self):
        # RapidOCR drops lines without word boxes from word_results, so it
        # can be shorter than txts.
        page = convert(HORIZONTAL_BOXES, HORIZONTAL_TXTS, (HORIZONTAL_WORDS[1],))
        first, second = page.lines
        assert [w.text for w in first.words] == ['The', 'LinnSequencer', 'is']
        assert first.words[0].bbox.left == pytest.approx(343.6)  # estimated
        assert second.words[0].bbox.left == 346  # from RapidOCR

    def test_boxes_clamped_to_page(self):
        page = convert([rect(-5, -3, 2560, 40)], ("edge",))
        (line,) = page.lines
        assert line.bbox.left == 0 and line.bbox.top == 0
        assert line.bbox.right == 2550


class TestInkMetrics:
    """Line metrics are measured from the ink inside the padded box."""

    def test_flat_line(self):
        image = ink_page([(110, 1090, 112, 140)])
        page = convert([rect(100, 100, 1100, 158)], ("ink",), image=image)
        (line,) = page.lines
        assert line.bbox.top == pytest.approx(112, abs=1)
        assert line.bbox.bottom == pytest.approx(148, abs=1)
        baseline = line.bbox.bottom + line.baseline.intercept
        assert baseline == pytest.approx(140, abs=1)

    def test_skewed_line(self):
        slope = 0.02
        image = ink_page([(110, 1090, 112, 140)], slope=slope)
        quad = [[100, 100], [1100, 120], [1100, 178], [100, 158]]
        page = convert([quad], ("ink",), image=image)
        (line,) = page.lines
        assert line.baseline.slope == pytest.approx(slope, abs=1e-3)
        left_baseline = line.bbox.bottom + line.baseline.intercept
        assert left_baseline == pytest.approx(140 - 10 * slope, abs=1.5)
        # The ink is 36 pixels high, and rises 20 pixels along the line
        assert line.bbox.height == pytest.approx(36 + 1000 * slope, abs=1.5)

    def test_ignores_neighbouring_lines(self):
        # The padded box reaches into the descenders of the line above and
        # the ascenders of the line below.
        image = ink_page([(110, 1090, 112, 140)])
        image[100:104, 200:1000:10] = 0
        image[154:158, 300:900:12] = 0
        page = convert([rect(100, 98, 1100, 160)], ("ink",), image=image)
        (line,) = page.lines
        assert line.bbox.top == pytest.approx(112, abs=1)
        assert line.bbox.bottom == pytest.approx(148, abs=1)

    def test_blank_box_keeps_estimate(self):
        import numpy as np

        image = np.full((3300, 2550), 255, dtype=np.uint8)
        page = convert([rect(100, 100, 1100, 158)], ("ink",), image=image)
        assert page.lines[0].bbox.top == 100

    def test_table_rows_survive_pdftotext(self, tmp_path, pdftotext):
        # With padded detection boxes, each cell's text was sized so large
        # that pdftotext merged the cells of each column into a block, and
        # read the table column by column.
        boxes, txts, ink = [], [], []
        for r in range(5):
            for c in range(6):
                left, y = 100 + 300 * c, 100 + 37 * r
                boxes.append(rect(left, y, left + 120, y + 42))
                txts.append(f'r{r}c{c}')
                ink.append((left + 5, left + 115, y + 9, y + 31))
        page = convert(boxes, tuple(txts), image=ink_page(ink, descenders=False))
        text = pdftotext(TestRendering.render(page, tmp_path))
        words = text.split()
        assert words.index('r0c5') < words.index('r1c0')


class TestHocr:
    def test_round_trip(self, tmp_path):
        quad = rotated_quad(1200, 1000, 1800, 50, 2.0)
        boxes = [*HORIZONTAL_BOXES, quad, rect(1488, 304, 1556, 970)]
        txts = (*HORIZONTAL_TXTS, "skewed <line> & more", "这是")
        page = convert(boxes, txts, None)
        hocr = tmp_path / 'page.hocr'
        hocr.write_text(ocr_tree_to_hocr(page), encoding='utf-8')
        parsed = HocrParser(hocr).parse()
        assert parsed.bbox.right == 2550
        lines = parsed.lines
        assert [ln.get_text_recursive() for ln in lines] == [
            ln.get_text_recursive() for ln in page.lines
        ]
        by_text = {ln.get_text_recursive(): ln for ln in lines}
        original = {ln.get_text_recursive(): ln for ln in page.lines}
        skewed = by_text["skewed <line> & more"]
        assert skewed.baseline.slope == pytest.approx(0.0349, abs=1e-3)
        assert skewed.baseline.intercept == round(
            original["skewed <line> & more"].baseline.intercept
        )
        assert by_text["这是"].textangle == 270
        assert lines[0].words[0].confidence == pytest.approx(0.9)

    def test_empty_page(self, tmp_path):
        hocr = tmp_path / 'page.hocr'
        hocr.write_text(ocr_tree_to_hocr(convert(None, ())), encoding='utf-8')
        assert HocrParser(hocr).parse().children == []


class TestSkew:
    @pytest.mark.parametrize('angle', [-4.0, -1.5, 0.0, 0.7, 3.0])
    def test_long_lines(self, angle):
        quads = [rotated_quad(1200, 300 + 60 * i, 1800, 45, angle) for i in range(10)]
        assert estimate_skew_angle(quads) == pytest.approx(angle, abs=0.05)

    def test_sign_matches_pil_rotate(self):
        # A line running downhill to the right has been turned clockwise.
        # PIL's Image.rotate() turns counterclockwise for positive angles,
        # so the correction is positive.
        quad = rotated_quad(1200, 300, 1800, 45, 2.0)
        (tl, tr, _, _) = quad
        assert degrees(atan2(tr[1] - tl[1], tr[0] - tl[0])) > 0
        assert estimate_skew_angle([quad]) > 0

    def test_ignores_short_and_vertical_boxes(self):
        lines = [rotated_quad(1200, 300 + 60 * i, 1800, 45, 1.0) for i in range(5)]
        noise = [rotated_quad(500, 2000 + 60 * i, 80, 45, 30.0) for i in range(20)]
        vertical = [rect(100 + 70 * i, 500, 150 + 70 * i, 1800) for i in range(20)]
        assert estimate_skew_angle(lines + noise + vertical) == pytest.approx(
            1.0, abs=0.05
        )

    def test_weighted_by_length(self):
        long_lines = [rotated_quad(1200, 300 + 60 * i, 1800, 45, 1.0) for i in range(3)]
        shortish = [rotated_quad(600, 1000 + 60 * i, 400, 45, -2.0) for i in range(4)]
        assert estimate_skew_angle(long_lines + shortish) == pytest.approx(
            1.0, abs=0.05
        )

    def test_no_text(self):
        assert estimate_skew_angle(None) == 0.0
        assert estimate_skew_angle([]) == 0.0


class TestOrientation:
    @staticmethod
    def page(vertical, n=20):
        if vertical:
            return [rect(200 + 60 * i, 300, 245 + 60 * i, 2000) for i in range(n)]
        return [rect(300, 200 + 60 * i, 2000, 245 + 60 * i) for i in range(n)]

    def test_selects_longest_lines_of_dominant_axis(self):
        quads = self.page(False, 15) + [rect(300, 2000, 600, 2045)] + self.page(True, 2)
        vertical, indices, axis_share = select_orientation_lines(quads, n=10)
        assert not vertical
        assert len(indices) == 10
        assert 15 not in indices  # short line
        assert axis_share > 0.75

    def test_selects_vertical(self):
        vertical, indices, _ = select_orientation_lines(self.page(True), n=10)
        assert vertical
        assert len(indices) == 10

    def test_too_few_lines(self):
        assert select_orientation_lines(self.page(False, 2)) is None
        assert select_orientation_lines(None) is None
        assert select_orientation_lines([]) is None

    def test_crops(self):
        import numpy as np

        image = np.zeros((100, 200, 3), dtype=np.uint8)
        image[10:20, 20:120] = 255
        image[10:20, 20, 0] = 7  # mark the left end of the line
        upright, turned = orientation_crops(image, rect(20, 10, 120, 20), False)
        assert upright.shape[:2] == turned.shape[:2]
        assert upright.shape[1] > upright.shape[0]
        assert (turned == upright[::-1, ::-1]).all()

    def test_vertical_crops_are_turned_horizontal(self):
        import numpy as np

        image = np.zeros((300, 100, 3), dtype=np.uint8)
        image[50, 40, 0] = 7  # top of a line reading downward
        downward, upward = orientation_crops(image, rect(40, 50, 50, 250), True)
        assert downward.shape[1] > downward.shape[0]
        assert upward.shape[1] > upward.shape[0]
        # Turned a quarter turn counterclockwise, a line that reads downward
        # starts at the left
        assert downward[:, :3, 0].max() == 7
        assert upward[:, -3:, 0].max() == 7

    @pytest.mark.parametrize(
        'vertical, upright_wins, angle',
        [
            (False, True, 0),
            (False, False, 180),
            # Lines read top to bottom: the content is turned 90 degrees
            # clockwise. Tesseract OSD reports this as "Orientation in
            # degrees: 90", which is what OCRmyPDF expects.
            (True, True, 90),
            (True, False, 270),
        ],
    )
    def test_angle(self, vertical, upright_wins, angle):
        a, b = (0.9, 0.55) if upright_wins else (0.55, 0.9)
        result = orientation_from_scores(vertical, a, b)
        assert result.angle == angle
        assert result.confidence == pytest.approx(35)

    def test_confidence_scale(self):
        # Benchmark margins on correctly oriented pages were 0.27 to 0.50;
        # OCRmyPDF's default threshold of 14 needs a margin of 0.14.
        assert orientation_from_scores(False, 0.80, 0.53).confidence == pytest.approx(
            27
        )
        assert orientation_from_scores(False, 0.60, 0.55).confidence < 14
        assert orientation_from_scores(False, 1.0, 0.0).confidence == 50

    def test_mixed_axes_lowers_confidence(self):
        assert orientation_from_scores(False, 0.9, 0.5, axis_share=0.55).confidence < 14
        assert orientation_from_scores(False, 0.9, 0.5, axis_share=0.9).confidence == (
            pytest.approx(40)
        )


class TestLanguages:
    def test_default_model_for_latin_and_cjk(self):
        default = rec_model_for_languages(['eng'])
        assert default.ocr_version == 'PP-OCRv6'
        assert (
            rec_model_for_languages(['eng', 'deu', 'fra', 'chi_sim', 'jpn']) == default
        )

    @pytest.mark.parametrize(
        'lang, rec_lang',
        [
            ('kor', 'korean'),
            ('rus', 'eslav'),
            ('bul', 'cyrillic'),
            ('ara', 'arabic'),
            ('hin', 'devanagari'),
            ('tha', 'th'),
            ('ell', 'el'),
        ],
    )
    def test_other_scripts(self, lang, rec_lang):
        model = rec_model_for_languages([lang])
        assert model.lang_type == rec_lang
        # English is understood by every recognition model
        assert rec_model_for_languages([lang, 'eng']) == model

    def test_mixed_families_rejected(self):
        with pytest.raises(BadArgsError, match="RapidOCR"):
            rec_model_for_languages(['kor', 'rus'])
        with pytest.raises(BadArgsError):
            rec_model_for_languages(['deu', 'ara'])

    def test_unsupported_language(self):
        with pytest.raises(BadArgsError):
            rec_model_for_languages(['xyz'])

    def test_languages_lists_tesseract_codes(self):
        langs = rapidocr_ocr.RapidOcrEngine.languages(None)
        assert {'eng', 'deu', 'chi_sim', 'jpn', 'kor', 'rus', 'ara'} <= langs

    def test_rec_model_is_hashable(self):
        assert isinstance(rec_model_for_languages(['eng']), RecModel)
        hash(rec_model_for_languages(['eng']))


class TestMissingDependency:
    def test_clean_error_when_not_installed(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def no_rapidocr(name, *args, **kwargs):
            if name == 'rapidocr' or name.startswith('rapidocr.'):
                raise ImportError(name)
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, '__import__', no_rapidocr)
        with pytest.raises(MissingDependencyError, match=r"ocrmypdf\[rapidocr\]"):
            rapidocr_ocr._import_rapidocr()


class TestCheckOptions:
    @staticmethod
    def options(*args):
        from ocrmypdf.cli import get_options_and_plugins

        options, _ = get_options_and_plugins(
            args=['--ocr-engine', 'rapidocr', *args, 'in.pdf', 'out.pdf']
        )
        return options

    @needs_rapidocr
    def test_sandwich_rejected(self):
        with pytest.raises(BadArgsError, match="sandwich"):
            rapidocr_ocr.check_options(self.options('--pdf-renderer', 'sandwich'))

    @needs_rapidocr
    def test_mixed_languages_rejected(self):
        with pytest.raises(BadArgsError):
            rapidocr_ocr.check_options(self.options('-l', 'kor+ara'))

    def test_max_side_len_option(self):
        assert self.options().rapidocr.max_side_len == 2000
        assert (
            self.options('--rapidocr-max-side-len', '4000').rapidocr.max_side_len
            == 4000
        )

    def test_other_engines_not_checked(self):
        from ocrmypdf.cli import get_options_and_plugins

        options, _ = get_options_and_plugins(
            args=['--pdf-renderer', 'sandwich', '-l', 'kor+ara', 'in.pdf', 'out.pdf']
        )
        rapidocr_ocr.check_options(options)


@pytest.fixture
def pdftotext():
    if shutil.which('pdftotext') is None:
        pytest.skip("pdftotext not available")

    def extract(pdf: Path, *args) -> str:
        return subprocess.check_output(
            ['pdftotext', '-enc', 'UTF-8', *args, str(pdf), '-'], text=True
        )

    return extract


class TestRendering:
    """The converted tree places text where the fpdf2 renderer expects it."""

    @staticmethod
    def render(page, tmp_path):
        from ocrmypdf.font import MultiFontManager
        from ocrmypdf.fpdf_renderer import Fpdf2PdfRenderer

        out = tmp_path / 'page.pdf'
        Fpdf2PdfRenderer(
            page=page,
            dpi=300,
            multi_font_manager=MultiFontManager(),
            invisible_text=True,
        ).render(out)
        return out

    @staticmethod
    def word_boxes(xhtml):
        return [
            (float(m[1]), float(m[2]), float(m[3]), float(m[4]), m[5])
            for m in re.finditer(
                r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                r'yMax="([\d.]+)">([^<]*)</word>',
                xhtml,
            )
        ]

    def test_skewed_line_follows_quad(self, tmp_path, pdftotext):
        quad = rotated_quad(1275, 1000, 1800, 50, 2.0)
        page = convert([quad], ("alpha beta gamma delta",))
        boxes = self.word_boxes(pdftotext(self.render(page, tmp_path), '-bbox'))
        assert [b[4] for b in boxes] == ['alpha', 'beta', 'gamma', 'delta']
        # Downhill to the right, in points (72/300 of a pixel)
        assert boxes[-1][3] - boxes[0][3] > 0.8 * 1350 * sin(radians(2)) * 72 / 300

    def test_vertical_line_reads_in_order(self, tmp_path, pdftotext):
        page = convert([rect(400, 840, 450, 1600)], ("one two three",))
        text = pdftotext(self.render(page, tmp_path))
        assert text.split() == ['one', 'two', 'three']


@needs_rapidocr
class TestEngine:
    """Run the RapidOCR models."""

    @pytest.fixture
    def no_tesseract(self, monkeypatch):
        from ocrmypdf._exec import tesseract

        def missing(*args, **kwargs):
            raise FileNotFoundError('tesseract')

        for name in (
            'version',
            'get_languages',
            'has_thresholding',
            'get_orientation',
            'get_deskew',
            'generate_hocr',
            'generate_pdf',
        ):
            monkeypatch.setattr(tesseract, name, missing)

    def test_linn(self, resources, outpdf, no_tesseract, pdftotext):
        from .conftest import check_ocrmypdf

        check_ocrmypdf(
            resources / 'linn.pdf',
            outpdf,
            '--ocr-engine',
            'rapidocr',
            '--output-type',
            'pdf',
            '--force-ocr',
        )
        text = pdftotext(outpdf)
        assert 'LinnSequencer' in text

    def test_rotate_pages(self, resources, outdir, no_tesseract):
        from .conftest import check_ocrmypdf
        from .test_rotation import compare_images_monochrome

        out = check_ocrmypdf(
            resources / 'cardinal.pdf',
            outdir / 'out.pdf',
            '--ocr-engine',
            'rapidocr',
            '--rotate-pages',
            '--output-type',
            'pdf',
        )
        for n in range(1, 5):
            cmp = compare_images_monochrome(
                outdir,
                reference_pdf=resources / 'cardinal.pdf',
                reference_pageno=1,
                test_pdf=out,
                test_pageno=n,
            )
            assert cmp > 0.95, f"page {n} not upright"

    def test_deskew(self, resources, outdir, no_tesseract, pdftotext):
        from .conftest import check_ocrmypdf

        out = check_ocrmypdf(
            resources / 'skew.pdf',
            outdir / 'out.pdf',
            '--ocr-engine',
            'rapidocr',
            '--deskew',
            '--output-type',
            'pdf',
        )
        deskewed_angle = rapidocr_ocr.RapidOcrEngine.get_deskew(
            _rasterize(out, outdir / 'deskewed.png'), _options()
        )
        original_angle = rapidocr_ocr.RapidOcrEngine.get_deskew(
            _rasterize(resources / 'skew.pdf', outdir / 'skewed.png'), _options()
        )
        assert abs(original_angle) > 1.5  # Tesseract measures 1.9 degrees
        assert abs(deskewed_angle) < 0.5
        assert pdftotext(out).strip()


def _options(*args):
    from ocrmypdf.cli import get_options_and_plugins

    options, _ = get_options_and_plugins(
        args=['--ocr-engine', 'rapidocr', *args, 'in.pdf', 'out.pdf']
    )
    return options


def _rasterize(pdf: Path, png: Path) -> Path:
    from ocrmypdf._exec import ghostscript
    from ocrmypdf.helpers import Resolution
    from ocrmypdf.pluginspec import GhostscriptRasterDevice

    ghostscript.rasterize_pdf(
        pdf,
        png,
        raster_device=GhostscriptRasterDevice.PNGGRAY,
        raster_dpi=Resolution(150, 150),
        pageno=1,
        rotation=0,
    )
    return png


class _RecordingOcr:
    """Stands in for a RapidOCR instance, recording how it is called."""

    def __init__(self):
        self.calls = []

    def __call__(self, image, **kwargs):
        self.calls.append(kwargs)
        return type('Empty', (), {'boxes': None})()


_ENGINE_CONFIG = rapidocr_ocr._EngineConfig(2000, rec_model_for_languages(['rus']))


class _FakeRapidOCR:
    """Stands in for rapidocr.RapidOCR."""

    created: list[dict] = []
    barrier: threading.Barrier | None = None

    def __init__(self, params):
        self.created.append(params)

    def __call__(self, image, **kwargs):
        if self.barrier is not None:
            # Two engines working at once both reach the barrier; engines
            # that take turns time out.
            self.barrier.wait(timeout=5)
        return type('Empty', (), {'boxes': None})()


@pytest.fixture
def fake_rapidocr(monkeypatch):
    """Replace the rapidocr module, and forget engines made so far."""
    _FakeRapidOCR.created = []
    _FakeRapidOCR.barrier = None
    fake_module = type(
        'rapidocr',
        (),
        {
            'RapidOCR': _FakeRapidOCR,
            'OCRVersion': str,
            'ModelType': str,
            'LangRec': str,
        },
    )
    monkeypatch.setattr(rapidocr_ocr, '_import_rapidocr', lambda: fake_module)
    monkeypatch.setattr(rapidocr_ocr, '_thread_engines', threading.local())
    return _FakeRapidOCR


class TestEnginePerThread:
    """OCRmyPDF's worker threads must each have their own engine.

    One engine shared by all threads makes them take turns.
    """

    def test_reused_within_a_thread(self, fake_rapidocr):
        first = rapidocr_ocr._get_engine(_ENGINE_CONFIG)
        assert rapidocr_ocr._get_engine(_ENGINE_CONFIG) is first
        assert len(fake_rapidocr.created) == 1

    def test_distinct_between_threads(self, fake_rapidocr):
        from concurrent.futures import ThreadPoolExecutor

        barrier = threading.Barrier(2)

        def engine_id():
            engine = rapidocr_ocr._get_engine(_ENGINE_CONFIG)
            barrier.wait(timeout=5)  # keep both threads alive together
            return id(engine)

        with ThreadPoolExecutor(2) as pool:
            ids = list(pool.map(lambda _: engine_id(), range(2)))
        assert ids[0] != ids[1]
        assert len(fake_rapidocr.created) == 2

    def test_threads_run_at_once(self, fake_rapidocr, tmp_path):
        from concurrent.futures import ThreadPoolExecutor

        from PIL import Image

        image = tmp_path / 'page.png'
        Image.new('L', (200, 100), 255).save(image, dpi=(300, 300))
        fake_rapidocr.barrier = threading.Barrier(2)
        options = _options()
        with ThreadPoolExecutor(2) as pool:
            results = list(
                pool.map(
                    lambda _: rapidocr_ocr.RapidOcrEngine.generate_ocr(image, options),
                    range(2),
                )
            )
        assert len(results) == 2


class TestAngleClassifierDisabled:
    """RapidOCR's text line angle classifier must not run.

    On documents it turns long Latin lines and nearly all Cyrillic lines
    upside down, and recognition then returns junk with confident scores.
    """

    def test_engine_constructed_without_classifier(self, fake_rapidocr):
        rapidocr_ocr._get_engine(_ENGINE_CONFIG)
        assert fake_rapidocr.created[0]['Global.use_cls'] is False

    @pytest.mark.parametrize(
        'method', ['generate_ocr', 'get_deskew', 'get_orientation']
    )
    def test_never_called_with_classifier(self, monkeypatch, tmp_path, method):
        from PIL import Image

        image = tmp_path / 'page.png'
        Image.new('L', (200, 100), 255).save(image, dpi=(300, 300))
        ocr = _RecordingOcr()
        monkeypatch.setattr(rapidocr_ocr, '_engine_for', lambda options: ocr)
        getattr(rapidocr_ocr.RapidOcrEngine, method)(image, _options())
        assert ocr.calls
        assert all(call.get('use_cls') is False for call in ocr.calls)


RUSSIAN_LINES = [
    "Старая железнодорожная станция стоит на краю посёлка уже больше ста лет.",
    "Её построили в тысяча девятьсот восьмом году, когда через эти места",
    "прокладывали новую линию, и с тех пор здание почти не изменилось.",
    "Когда-то здесь останавливались все поезда, идущие на восток. На перроне",
    "продавали горячие пирожки, молоко и яблоки, а в зале ожидания было шумно.",
]


@pytest.fixture
def cyrillic_page(tmp_path):
    """A 200 dpi page of full-width Russian lines."""
    from PIL import Image, ImageDraw, ImageFont

    try:
        font_file = subprocess.check_output(
            ['fc-match', '-f', '%{file}', 'DejaVu Serif:lang=ru'], text=True
        )
        font = ImageFont.truetype(font_file, 34)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("no font with Cyrillic glyphs")
    image = Image.new('L', (1700, 600), 255)
    draw = ImageDraw.Draw(image)
    for n, line in enumerate(RUSSIAN_LINES):
        draw.text((60, 60 + 95 * n), line, font=font, fill=0)
    path = tmp_path / 'ru.png'
    image.save(path, dpi=(200, 200))
    return path


def _words(text):
    return re.findall(r'\w+', text.lower())


@needs_rapidocr
class TestCyrillic:
    def test_recognized(self, cyrillic_page):
        options = _options('-l', 'rus')
        _page, text = rapidocr_ocr.RapidOcrEngine.generate_ocr(cyrillic_page, options)
        expected = _words(' '.join(RUSSIAN_LINES))
        found = set(_words(text))
        missing = [w for w in expected if w not in found]
        assert len(missing) <= 0.05 * len(expected), text

    @pytest.mark.parametrize('turn', [0, 90, 180, 270])
    def test_orientation(self, cyrillic_page, tmp_path, turn):
        from PIL import Image

        turned = tmp_path / f'turned{turn}.png'
        with Image.open(cyrillic_page) as im:
            # PIL turns counterclockwise; Tesseract's "Orientation in degrees"
            # for content turned counterclockwise by 90 is 270.
            im.rotate(turn, expand=True).save(turned)
        result = rapidocr_ocr.RapidOcrEngine.get_orientation(
            turned, _options('-l', 'rus')
        )
        assert result.angle == (360 - turn) % 360
        assert result.confidence >= 14
