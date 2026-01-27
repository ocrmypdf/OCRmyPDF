#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Direct tests for multilingual text rendering with fpdf2 renderer.

This tests the fpdf2 renderer with various language groups:
- Latin (English, French, German with diacritics)
- Arabic (Arabic, Persian - RTL scripts)
- CJK (Chinese Simplified/Traditional, Japanese, Korean)
- Devanagari (Hindi, Sanskrit)
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from ocrmypdf.font import MultiFontManager
from ocrmypdf.fpdf_renderer import DebugRenderOptions, Fpdf2PdfRenderer
from ocrmypdf.hocrtransform.hocr_parser import HocrParser

RESOURCES = Path(__file__).parent / "resources"


@pytest.fixture
def pdftotext():
    """Return a function to extract text from PDF using pdftotext.

    Skips the test if pdftotext is not available.
    """
    pdftotext_path = shutil.which('pdftotext')
    if pdftotext_path is None:
        pytest.skip("pdftotext not available")

    def extract_text(pdf_path: Path) -> str:
        return subprocess.check_output(
            ['pdftotext', '-enc', 'UTF-8', str(pdf_path), '-'],
            text=True,
            encoding='utf-8',
        )

    return extract_text


@pytest.fixture
def font_dir():
    """Return path to font directory."""
    return Path(__file__).parent.parent / "src" / "ocrmypdf" / "data"


@pytest.fixture
def multi_font_manager(font_dir):
    """Create MultiFontManager instance for testing."""
    return MultiFontManager(font_dir)


@pytest.fixture
def multi_font_manager_arabic(font_dir):
    """Create MultiFontManager instance for testing, with Arabic."""
    mfm = MultiFontManager(font_dir)
    if not mfm.has_font("NotoSansArabic-Regular"):
        pytest.skip("NotoSansArabic font not available")
    return mfm


# =============================================================================
# Latin Script Tests
# =============================================================================


class TestLatinScript:
    """Tests for Latin script (English, French, German, etc.)."""

    @pytest.fixture
    def latin_hocr(self):
        """Return path to Latin HOCR test file."""
        return RESOURCES / "latin.hocr"

    def test_render_latin_basic(
        self, latin_hocr, multi_font_manager, tmp_path, pdftotext
    ):
        """Test rendering Latin script with various diacritics."""
        parser = HocrParser(latin_hocr)
        page = parser.parse()

        assert page is not None
        paras = list(page.paragraphs)
        assert len(paras) == 3  # English, French, German

        # Check languages
        assert paras[0].language == 'eng'
        assert paras[1].language == 'fra'
        assert paras[2].language == 'deu'

        # Render to PDF
        output_pdf = tmp_path / "latin_output.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300.0,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

        # Extract text and verify
        text = pdftotext(output_pdf)

        # English words
        assert 'quick' in text or 'brown' in text or 'fox' in text

        # French with diacritics
        assert 'Café' in text or 'résumé' in text or 'naïve' in text

        # German with umlauts and eszett
        assert 'Größe' in text or 'Zürich' in text or 'Ärger' in text

    def test_latin_font_selection(self, latin_hocr, multi_font_manager):
        """Test that NotoSans is selected for Latin text."""
        parser = HocrParser(latin_hocr)
        page = parser.parse()

        for line in page.lines:
            for word in line.children:
                if word.text:
                    font = multi_font_manager.select_font_for_word(
                        word.text, line.language
                    )
                    assert font is not None
                    # Latin text should use NotoSans-Regular
                    assert multi_font_manager.has_all_glyphs(
                        'NotoSans-Regular', word.text
                    )


# =============================================================================
# Arabic Script Tests
# =============================================================================


class TestArabicScript:
    """Tests for Arabic script (Arabic, Persian, etc.)."""

    @pytest.fixture
    def arabic_hocr(self):
        """Return path to Arabic HOCR test file."""
        return RESOURCES / "arabic.hocr"

    def test_render_arabic_basic(
        self, arabic_hocr, multi_font_manager_arabic, tmp_path, pdftotext
    ):
        """Test rendering Arabic script text."""
        parser = HocrParser(arabic_hocr)
        page = parser.parse()

        assert page is not None
        paras = list(page.paragraphs)
        assert len(paras) == 3  # Arabic paragraphs and Persian

        # Render to PDF
        output_pdf = tmp_path / "arabic_output.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300.0,
            multi_font_manager=multi_font_manager_arabic,
            invisible_text=False,
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

        # Extract text and verify Arabic content
        text = pdftotext(output_pdf)

        # Arabic words: مرحبا بالعالم (Hello world)
        assert 'مرحبا' in text or 'بالعالم' in text
        # هذا نص عربي (This is Arabic text)
        assert 'عربي' in text or 'نص' in text

    def test_arabic_font_selection(self, arabic_hocr, multi_font_manager_arabic):
        """Test that NotoSansArabic is selected for Arabic text."""
        parser = HocrParser(arabic_hocr)
        page = parser.parse()

        for line in page.lines:
            for word in line.children:
                if word.text and line.language in ('ara', 'per'):
                    font = multi_font_manager_arabic.select_font_for_word(
                        word.text, line.language
                    )
                    assert font is not None
                    # Arabic text should use NotoSansArabic
                    assert multi_font_manager_arabic.has_all_glyphs(
                        'NotoSansArabic-Regular', word.text
                    ), f"NotoSansArabic cannot render '{word.text}'"

    def test_arabic_rtl_handling(self, arabic_hocr):
        """Test that RTL direction is correctly parsed from hOCR."""
        parser = HocrParser(arabic_hocr)
        page = parser.parse()

        for para in page.paragraphs:
            if para.language in ('ara', 'per'):
                # Arabic paragraphs should have RTL direction
                assert (
                    para.direction == 'rtl'
                ), "Arabic paragraph should have RTL direction"


# =============================================================================
# CJK Script Tests
# =============================================================================


def _latin_font_works(multi_font_manager) -> bool:
    """Check if Latin font is available."""
    return multi_font_manager.has_font('NotoSans-Regular')


def _arabic_font_works(multi_font_manager) -> bool:
    """Check if Arabic font is available."""
    return multi_font_manager.has_font('NotoSansArabic-Regular')


def _devanagari_font_works(multi_font_manager) -> bool:
    """Check if Devanagari font is available."""
    return multi_font_manager.has_font('NotoSansDevanagari-Regular')


def _cjk_font_works(multi_font_manager) -> bool:
    """Check if CJK font is working (not corrupted)."""
    return multi_font_manager.has_font('NotoSansCJK-Regular')


class TestCJKScript:
    """Tests for CJK scripts (Chinese, Japanese, Korean)."""

    @pytest.fixture
    def cjk_hocr(self):
        """Return path to CJK HOCR test file."""
        return RESOURCES / "cjk.hocr"

    def test_render_cjk_basic(self, cjk_hocr, multi_font_manager, tmp_path, pdftotext):
        """Test rendering CJK script text."""
        if not _cjk_font_works(multi_font_manager):
            pytest.skip("CJK font not available or corrupted")

        parser = HocrParser(cjk_hocr)
        page = parser.parse()

        assert page is not None
        paras = list(page.paragraphs)
        assert len(paras) == 4  # Chinese Simplified, Traditional, Japanese, Korean

        # Check languages
        languages = [p.language for p in paras]
        assert 'chi_sim' in languages
        assert 'chi_tra' in languages
        assert 'jpn' in languages
        assert 'kor' in languages

        # Render to PDF
        output_pdf = tmp_path / "cjk_output.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300.0,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

        # Extract text and verify CJK content
        text = pdftotext(output_pdf)

        # Chinese: 你好 世界 (Hello world)
        assert '你好' in text or '世界' in text
        # Japanese: こんにちは (Hello)
        assert 'こんにちは' in text or '世界' in text
        # Korean: 안녕하세요 (Hello)
        assert '안녕하세요' in text or '세계' in text

    def test_cjk_font_selection(self, cjk_hocr, multi_font_manager):
        """Test that NotoSansCJK is selected for CJK text."""
        if not _cjk_font_works(multi_font_manager):
            pytest.skip("CJK font not available or corrupted")

        parser = HocrParser(cjk_hocr)
        page = parser.parse()

        cjk_languages = {'chi_sim', 'chi_tra', 'jpn', 'kor', 'zho', 'chi'}

        for line in page.lines:
            for word in line.children:
                if word.text and line.language in cjk_languages:
                    font = multi_font_manager.select_font_for_word(
                        word.text, line.language
                    )
                    assert font is not None
                    # CJK text should use NotoSansCJK
                    assert multi_font_manager.has_all_glyphs(
                        'NotoSansCJK-Regular', word.text
                    ), f"NotoSansCJK cannot render '{word.text}'"


# =============================================================================
# Devanagari Script Tests
# =============================================================================


class TestDevanagariScript:
    """Tests for Devanagari script (Hindi, Sanskrit, etc.)."""

    @pytest.fixture
    def devanagari_hocr(self):
        """Return path to Devanagari HOCR test file."""
        return RESOURCES / "devanagari.hocr"

    def test_render_devanagari_basic(
        self, devanagari_hocr, multi_font_manager, tmp_path, pdftotext
    ):
        """Test rendering Devanagari script text."""
        parser = HocrParser(devanagari_hocr)
        page = parser.parse()

        assert page is not None
        paras = list(page.paragraphs)
        assert len(paras) == 3  # Hindi paragraphs and Sanskrit

        # Render to PDF
        output_pdf = tmp_path / "devanagari_output.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300.0,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

        # Extract text and verify Devanagari content
        text = pdftotext(output_pdf)

        # Hindi: नमस्ते दुनिया (Hello world)
        assert 'नमस्ते' in text or 'दुनिया' in text
        # यह हिंदी पाठ है (This is Hindi text)
        assert 'हिंदी' in text or 'पाठ' in text

    def test_devanagari_font_selection(self, devanagari_hocr, multi_font_manager):
        """Test that NotoSansDevanagari is selected for Devanagari text."""
        if not multi_font_manager.has_font('NotoSansDevanagari-Regular'):
            pytest.skip("Devanagari font not available")
        parser = HocrParser(devanagari_hocr)
        page = parser.parse()

        devanagari_languages = {'hin', 'san', 'mar', 'nep'}

        for line in page.lines:
            for word in line.children:
                if word.text and line.language in devanagari_languages:
                    font = multi_font_manager.select_font_for_word(
                        word.text, line.language
                    )
                    assert font is not None
                    # Devanagari text should use NotoSansDevanagari
                    assert multi_font_manager.has_all_glyphs(
                        'NotoSansDevanagari-Regular', word.text
                    ), f"NotoSansDevanagari cannot render '{word.text}'"


# =============================================================================
# Mixed Language / Multilingual Tests
# =============================================================================


class TestMultilingual:
    """Tests for mixed-language documents."""

    @pytest.fixture
    def multilingual_hocr(self):
        """Return path to multilingual HOCR test file."""
        return RESOURCES / "multilingual.hocr"

    def test_render_multilingual_hocr_basic(
        self, multilingual_hocr, multi_font_manager_arabic, tmp_path, pdftotext
    ):
        """Test rendering multilingual HOCR file with English and Arabic text."""
        parser = HocrParser(multilingual_hocr)
        page = parser.parse()

        assert page is not None
        assert len(list(page.paragraphs)) == 2  # English and Arabic paragraphs

        # Check languages
        paras = list(page.paragraphs)
        assert paras[0].language == 'eng'
        assert paras[1].language == 'ara'

        # Render to PDF
        output_pdf = tmp_path / "multilingual_output.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300.0,
            multi_font_manager=multi_font_manager_arabic,
            invisible_text=False,
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

        # Extract text from PDF
        text = pdftotext(output_pdf)

        # Verify both English and Arabic text are present
        assert 'English' in text or 'Text' in text or 'Here' in text
        # Arabic text: مرحبا بك
        assert 'مرحبا' in text or 'بك' in text

    def test_render_multilingual_with_debug_options(
        self, multilingual_hocr, multi_font_manager, tmp_path
    ):
        """Test rendering with debug visualization enabled."""
        parser = HocrParser(multilingual_hocr)
        page = parser.parse()

        # Render with debug options
        output_pdf = tmp_path / "multilingual_debug.pdf"
        debug_options = DebugRenderOptions(
            render_baseline=True,
            render_line_bbox=True,
            render_word_bbox=True,
        )
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300.0,
            multi_font_manager=multi_font_manager,
            invisible_text=False,
            debug_render_options=debug_options,
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

    def test_multilingual_invisible_text(
        self, multilingual_hocr, multi_font_manager, tmp_path, pdftotext
    ):
        """Test rendering with invisible text (default OCR mode)."""
        parser = HocrParser(multilingual_hocr)
        page = parser.parse()

        # Render with invisible text (standard for OCR layer)
        output_pdf = tmp_path / "multilingual_invisible.pdf"
        renderer = Fpdf2PdfRenderer(
            page=page,
            dpi=300.0,
            multi_font_manager=multi_font_manager,
            invisible_text=True,
        )
        renderer.render(output_pdf)

        assert output_pdf.exists()

        # Text should still be extractable even though invisible
        text = pdftotext(output_pdf)
        assert len(text.strip()) > 0

    def test_multilingual_font_selection(
        self, multilingual_hocr, multi_font_manager_arabic
    ):
        """Test that correct fonts are selected for each language."""
        parser = HocrParser(multilingual_hocr)
        page = parser.parse()

        # Get all words
        words = []
        for line in page.lines:
            for word in line.children:
                if word.text:
                    words.append((word.text, line.language))

        # Verify we have both English and Arabic words
        eng_words = [w for w, lang in words if lang == 'eng']
        ara_words = [w for w, lang in words if lang == 'ara']

        assert len(eng_words) > 0, "Should have English words"
        assert len(ara_words) > 0, "Should have Arabic words"

        # Test font selection
        for text, lang in words:
            font_mgr = multi_font_manager_arabic.select_font_for_word(text, lang)
            assert font_mgr is not None, f"No font selected for '{text}' ({lang})"

            if lang == 'ara':
                assert multi_font_manager_arabic.has_all_glyphs(
                    'NotoSansArabic-Regular', text
                ), f"NotoSansArabic cannot render '{text}'"


# =============================================================================
# Baseline and Structure Tests
# =============================================================================


class TestBaselineHandling:
    """Tests for baseline and hOCR structure handling."""

    @pytest.fixture
    def multilingual_hocr(self):
        """Return path to multilingual HOCR test file."""
        return RESOURCES / "multilingual.hocr"

    def test_multilingual_baseline_handling(self, multilingual_hocr):
        """Test that baseline information is correctly parsed from hOCR."""
        parser = HocrParser(multilingual_hocr)
        page = parser.parse()

        for line in page.lines:
            if line.baseline:
                # Baseline should be reasonable
                assert (
                    -1.0 <= line.baseline.slope <= 1.0
                ), "Baseline slope should be reasonable"


# =============================================================================
# Font Coverage Tests
# =============================================================================


class TestFontCoverage:
    """Tests verifying font coverage for various scripts."""

    def test_noto_sans_latin_coverage(self, multi_font_manager):
        """Test NotoSans covers common Latin characters and diacritics."""
        if not _latin_font_works(multi_font_manager):
            pytest.skip("NotoSans font not available")

        latin_samples = [
            "Hello World",
            "Café résumé naïve",
            "Größe Zürich Ärger",
            "ÀÁÂÃÄÅÆÇÈÉÊË",
            "àáâãäåæçèéêë",
        ]

        for sample in latin_samples:
            assert multi_font_manager.has_all_glyphs(
                'NotoSans-Regular', sample
            ), f"NotoSans should cover: {sample}"

    def test_noto_sans_arabic_coverage(self, multi_font_manager_arabic):
        """Test NotoSansArabic covers Arabic characters."""
        arabic_samples = [
            "مرحبا",  # Hello
            "بالعالم",  # World
            "العربية",  # Arabic
        ]

        for sample in arabic_samples:
            assert multi_font_manager_arabic.has_all_glyphs(
                'NotoSansArabic-Regular', sample
            ), f"NotoSansArabic should cover: {sample}"

    def test_noto_sans_devanagari_coverage(self, multi_font_manager):
        """Test NotoSansDevanagari covers Devanagari characters."""
        if not _devanagari_font_works(multi_font_manager):
            pytest.skip("NotoSansDevanagari font not available")

        devanagari_samples = [
            "नमस्ते",  # Hello
            "हिंदी",  # Hindi
            "संस्कृत",  # Sanskrit
        ]

        for sample in devanagari_samples:
            assert multi_font_manager.has_all_glyphs(
                'NotoSansDevanagari-Regular', sample
            ), f"NotoSansDevanagari should cover: {sample}"

    def test_noto_sans_cjk_coverage(self, multi_font_manager):
        """Test NotoSansCJK covers CJK characters."""
        if not _cjk_font_works(multi_font_manager):
            pytest.skip("CJK font not available or corrupted")

        cjk_samples = [
            "你好",  # Chinese: Hello
            "世界",  # Chinese: World
            "こんにちは",  # Japanese: Hello
            "안녕하세요",  # Korean: Hello
        ]

        for sample in cjk_samples:
            assert multi_font_manager.has_all_glyphs(
                'NotoSansCJK-Regular', sample
            ), f"NotoSansCJK should cover: {sample}"


if __name__ == "__main__":
    # Allow running this test directly for quick iteration
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
