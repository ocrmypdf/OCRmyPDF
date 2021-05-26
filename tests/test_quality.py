# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import pytest

from ocrmypdf import quality as qual


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
