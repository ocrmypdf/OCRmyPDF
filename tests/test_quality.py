# © 2020 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import pytest

import ocrmypdf.quality as qual


def test_quality_measurement():
    oqd = qual.OcrQualityDictionary(
        wordlist=["words", "words", "quick", "brown", "fox", "dog", "lazy"]
    )
    assert len(oqd.dictionary) == 6  # 6 unique

    assert (
        oqd.measure_words_matched("The quick brown fox jumps quickly over the lazy dog")
        == 0.5
    )
    assert oqd.measure_words_matched("12345 10% _f  7fox -brown   | words") == 1.0

    assert oqd.measure_words_matched("quick quick quick") == 1.0
