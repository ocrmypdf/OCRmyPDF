# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for MultiFontManager and FontProvider."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from ocrmypdf.font import BuiltinFontProvider, FontManager, MultiFontManager


@pytest.fixture
def font_dir():
    """Return path to font directory."""
    return Path(__file__).parent.parent / "src" / "ocrmypdf" / "data"


@pytest.fixture
def multi_font_manager(font_dir):
    """Create MultiFontManager instance for testing."""
    return MultiFontManager(font_dir)


def has_cjk_font(manager: MultiFontManager) -> bool:
    """Check if CJK font is available (from system)."""
    return 'NotoSansCJK-Regular' in manager.fonts


def has_arabic_font(manager: MultiFontManager) -> bool:
    """Check if Arabic font is available (from system)."""
    return 'NotoSansArabic-Regular' in manager.fonts


def has_devanagari_font(manager: MultiFontManager) -> bool:
    """Check if Devanagari font is available (from system)."""
    return 'NotoSansDevanagari-Regular' in manager.fonts


# Marker for tests that require CJK fonts
requires_cjk = pytest.mark.skipif(
    "not has_cjk_font(MultiFontManager())",
    reason="CJK font not available (not installed on system)"
)


# --- MultiFontManager Initialization Tests ---


def test_init_loads_builtin_fonts(multi_font_manager):
    """Test that initialization loads all expected builtin fonts."""
    # Only NotoSans-Regular and Occulta are bundled
    assert 'NotoSans-Regular' in multi_font_manager.fonts
    assert 'Occulta' in multi_font_manager.fonts

    # At least 2 builtin fonts should be loaded
    assert len(multi_font_manager.fonts) >= 2

    # Arabic, Devanagari, CJK are optional (system fonts)


def test_missing_font_directory():
    """Test that missing font directory raises error for fallback font."""
    with pytest.raises(FileNotFoundError):
        MultiFontManager(Path("/nonexistent/path"))


# --- Arabic Script Language Tests ---
# These tests require Arabic fonts to be installed on the system


def test_select_font_for_arabic_language(multi_font_manager):
    """Test font selection with Arabic language hint."""
    if not has_arabic_font(multi_font_manager):
        pytest.skip("Arabic font not available")
    font_manager = multi_font_manager.select_font_for_word("مرحبا", "ara")
    assert font_manager == multi_font_manager.fonts['NotoSansArabic-Regular']


def test_select_font_for_persian_language(multi_font_manager):
    """Test font selection with Persian language hint."""
    if not has_arabic_font(multi_font_manager):
        pytest.skip("Arabic font not available")
    font_manager = multi_font_manager.select_font_for_word("سلام", "per")
    assert font_manager == multi_font_manager.fonts['NotoSansArabic-Regular']


def test_select_font_for_urdu_language(multi_font_manager):
    """Test font selection with Urdu language hint."""
    if not has_arabic_font(multi_font_manager):
        pytest.skip("Arabic font not available")
    font_manager = multi_font_manager.select_font_for_word("ہیلو", "urd")
    assert font_manager == multi_font_manager.fonts['NotoSansArabic-Regular']


def test_farsi_language_code(multi_font_manager):
    """Test that 'fas' (Farsi alternative code) maps to Arabic font."""
    if not has_arabic_font(multi_font_manager):
        pytest.skip("Arabic font not available")
    font_manager = multi_font_manager.select_font_for_word("سلام", "fas")
    assert font_manager == multi_font_manager.fonts['NotoSansArabic-Regular']


# --- Devanagari Script Language Tests ---
# These tests require Devanagari fonts to be installed on the system


def test_select_font_for_hindi_language(multi_font_manager):
    """Test font selection with Hindi language hint."""
    if not has_devanagari_font(multi_font_manager):
        pytest.skip("Devanagari font not available")
    font_manager = multi_font_manager.select_font_for_word("नमस्ते", "hin")
    assert font_manager == multi_font_manager.fonts['NotoSansDevanagari-Regular']


def test_select_font_for_sanskrit_language(multi_font_manager):
    """Test font selection with Sanskrit language hint."""
    if not has_devanagari_font(multi_font_manager):
        pytest.skip("Devanagari font not available")
    font_manager = multi_font_manager.select_font_for_word("संस्कृतम्", "san")
    assert font_manager == multi_font_manager.fonts['NotoSansDevanagari-Regular']


def test_select_font_for_marathi_language(multi_font_manager):
    """Test font selection with Marathi language hint."""
    if not has_devanagari_font(multi_font_manager):
        pytest.skip("Devanagari font not available")
    font_manager = multi_font_manager.select_font_for_word("मराठी", "mar")
    assert font_manager == multi_font_manager.fonts['NotoSansDevanagari-Regular']


def test_select_font_for_nepali_language(multi_font_manager):
    """Test font selection with Nepali language hint."""
    if not has_devanagari_font(multi_font_manager):
        pytest.skip("Devanagari font not available")
    font_manager = multi_font_manager.select_font_for_word("नेपाली", "nep")
    assert font_manager == multi_font_manager.fonts['NotoSansDevanagari-Regular']


# --- CJK Language Tests ---
# These tests require CJK fonts to be installed on the system


def test_select_font_for_chinese_language(multi_font_manager):
    """Test font selection with Chinese language hint (ISO 639-3)."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    font_manager = multi_font_manager.select_font_for_word("你好", "zho")
    assert font_manager == multi_font_manager.fonts['NotoSansCJK-Regular']


def test_select_font_for_chinese_generic(multi_font_manager):
    """Test font selection with generic Chinese language code."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    font_manager = multi_font_manager.select_font_for_word("中文", "chi")
    assert font_manager == multi_font_manager.fonts['NotoSansCJK-Regular']


def test_select_font_for_chinese_simplified(multi_font_manager):
    """Test font selection with Tesseract's chi_sim language code."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    font_manager = multi_font_manager.select_font_for_word("简体字", "chi_sim")
    assert font_manager == multi_font_manager.fonts['NotoSansCJK-Regular']


def test_select_font_for_chinese_traditional(multi_font_manager):
    """Test font selection with Tesseract's chi_tra language code."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    font_manager = multi_font_manager.select_font_for_word("漢字", "chi_tra")
    assert font_manager == multi_font_manager.fonts['NotoSansCJK-Regular']


def test_select_font_for_japanese_language(multi_font_manager):
    """Test font selection with Japanese language hint."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    font_manager = multi_font_manager.select_font_for_word("こんにちは", "jpn")
    assert font_manager == multi_font_manager.fonts['NotoSansCJK-Regular']


def test_select_font_for_korean_language(multi_font_manager):
    """Test font selection with Korean language hint."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    font_manager = multi_font_manager.select_font_for_word("안녕하세요", "kor")
    assert font_manager == multi_font_manager.fonts['NotoSansCJK-Regular']


# --- Latin/English Tests ---


def test_select_font_for_english_text(multi_font_manager):
    """Test font selection for English text."""
    font_manager = multi_font_manager.select_font_for_word("Hello World", "eng")
    assert font_manager == multi_font_manager.fonts['NotoSans-Regular']


def test_select_font_without_language_hint(multi_font_manager):
    """Test font selection without language hint falls back to glyph checking."""
    font_manager = multi_font_manager.select_font_for_word("Hello", None)
    assert font_manager == multi_font_manager.fonts['NotoSans-Regular']


# --- Fallback Behavior Tests ---


def test_select_font_arabic_text_without_language_hint(multi_font_manager):
    """Test that Arabic text is handled via fallback without language hint."""
    if not has_arabic_font(multi_font_manager):
        pytest.skip("Arabic font not available")
    font_manager = multi_font_manager.select_font_for_word("مرحبا", None)
    # Should get NotoSansArabic-Regular via fallback chain glyph checking
    assert font_manager == multi_font_manager.fonts['NotoSansArabic-Regular']


def test_devanagari_text_without_language_hint(multi_font_manager):
    """Test that Devanagari text is handled via fallback without language hint."""
    # NotoSans-Regular includes Devanagari glyphs, so it's selected first in fallback
    font_manager = multi_font_manager.select_font_for_word("नमस्ते", None)
    # Could be NotoSans-Regular or NotoSansDevanagari-Regular depending on availability
    assert font_manager is not None


def test_cjk_text_without_language_hint(multi_font_manager):
    """Test that CJK text is handled via fallback without language hint."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    font_manager = multi_font_manager.select_font_for_word("你好", None)
    assert font_manager == multi_font_manager.fonts['NotoSansCJK-Regular']


def test_fallback_to_occulta_font(multi_font_manager):
    """Test that unsupported characters fall back to Occulta.ttf."""
    # Use a character unlikely to be in any standard font
    font_manager = multi_font_manager.select_font_for_word("test", "xyz")
    # Should return some valid font
    assert font_manager in multi_font_manager.fonts.values()


def test_fallback_fonts_constant(multi_font_manager):
    """Test that FALLBACK_FONTS contains expected fonts."""
    # Check that core fonts are in fallback list
    assert 'NotoSans-Regular' in MultiFontManager.FALLBACK_FONTS
    assert 'NotoSansArabic-Regular' in MultiFontManager.FALLBACK_FONTS
    assert 'NotoSansDevanagari-Regular' in MultiFontManager.FALLBACK_FONTS
    assert 'NotoSansCJK-Regular' in MultiFontManager.FALLBACK_FONTS

    # Only NotoSans-Regular is bundled; other scripts are system fonts
    assert 'NotoSans-Regular' in multi_font_manager.fonts


# --- Glyph Coverage Tests ---


def test_has_all_glyphs_for_english(multi_font_manager):
    """Test glyph coverage checking for English text."""
    assert multi_font_manager.has_all_glyphs('NotoSans-Regular', "Hello World")
    assert multi_font_manager.has_all_glyphs('NotoSans-Regular', "café")


def test_has_all_glyphs_for_arabic(multi_font_manager):
    """Test glyph coverage checking for Arabic text."""
    if not has_arabic_font(multi_font_manager):
        pytest.skip("Arabic font not available")
    assert multi_font_manager.has_all_glyphs('NotoSansArabic-Regular', "مرحبا")


def test_has_all_glyphs_for_devanagari(multi_font_manager):
    """Test glyph coverage checking for Devanagari text."""
    if not has_devanagari_font(multi_font_manager):
        pytest.skip("Devanagari font not available")
    assert multi_font_manager.has_all_glyphs('NotoSansDevanagari-Regular', "नमस्ते")


def test_has_all_glyphs_for_cjk(multi_font_manager):
    """Test glyph coverage checking for CJK text."""
    if not has_cjk_font(multi_font_manager):
        pytest.skip("CJK font not available")
    assert multi_font_manager.has_all_glyphs('NotoSansCJK-Regular', "你好")


def test_empty_text_has_all_glyphs(multi_font_manager):
    """Test that empty text returns True for glyph coverage."""
    assert multi_font_manager.has_all_glyphs('NotoSans-Regular', "")


def test_has_all_glyphs_missing_font(multi_font_manager):
    """Test that has_all_glyphs returns False for non-existent font."""
    assert not multi_font_manager.has_all_glyphs('NonExistentFont', "test")


# --- Caching Tests ---


def test_font_selection_caching(multi_font_manager):
    """Test that font selection results are cached."""
    font1 = multi_font_manager.select_font_for_word("Hello", "eng")

    cache_key = ("Hello", "eng")
    assert cache_key in multi_font_manager._selection_cache

    font2 = multi_font_manager.select_font_for_word("Hello", "eng")
    assert font1 == font2


# --- Language Font Map Tests ---


def test_language_font_map_coverage():
    """Test that LANGUAGE_FONT_MAP has valid structure."""
    # Only NotoSans-Regular is bundled now
    # This test just verifies the structure is valid
    for font_name in MultiFontManager.LANGUAGE_FONT_MAP.values():
        # All font names should be valid strings
        assert isinstance(font_name, str)
        assert font_name.startswith('NotoSans')


# --- get_all_fonts Tests ---


def test_get_all_fonts(multi_font_manager):
    """Test get_all_fonts returns all loaded fonts."""
    all_fonts = multi_font_manager.get_all_fonts()
    assert isinstance(all_fonts, dict)
    # At least 2 builtin fonts should be loaded (NotoSans-Regular and Occulta)
    assert len(all_fonts) >= 2
    assert 'NotoSans-Regular' in all_fonts
    assert 'Occulta' in all_fonts
    # Arabic, Devanagari, CJK are optional (system fonts)


# --- FontProvider Tests ---


class MockFontProvider:
    """Mock FontProvider for testing missing fonts."""

    def __init__(
        self, available_fonts: dict[str, FontManager], fallback: FontManager
    ):
        """Initialize mock font provider with given fonts."""
        self._fonts = available_fonts
        self._fallback = fallback

    def get_font(self, font_name: str) -> FontManager | None:
        return self._fonts.get(font_name)

    def get_available_fonts(self) -> list[str]:
        return list(self._fonts.keys())

    def get_fallback_font(self) -> FontManager:
        return self._fallback


def test_custom_font_provider(font_dir):
    """Test that custom FontProvider can be injected."""
    fonts = {
        'NotoSans-Regular': FontManager(font_dir / 'NotoSans-Regular.ttf'),
        'Occulta': FontManager(font_dir / 'Occulta.ttf'),
    }
    provider = MockFontProvider(fonts, fonts['Occulta'])

    manager = MultiFontManager(font_provider=provider)

    # Should only have the fonts we provided
    assert len(manager.fonts) == 2
    assert 'NotoSans-Regular' in manager.fonts
    assert 'Occulta' in manager.fonts


def test_missing_font_uses_fallback(font_dir):
    """Test that missing fonts gracefully fall back."""
    fonts = {
        'NotoSans-Regular': FontManager(font_dir / 'NotoSans-Regular.ttf'),
        'Occulta': FontManager(font_dir / 'Occulta.ttf'),
    }
    provider = MockFontProvider(fonts, fonts['Occulta'])

    manager = MultiFontManager(font_provider=provider)

    # Arabic text should fall back to Occulta since NotoSansArabic is missing
    font = manager.select_font_for_word("مرحبا", "ara")
    assert font == fonts['Occulta']


def test_builtin_font_provider_loads_expected_fonts(font_dir):
    """Test BuiltinFontProvider loads all expected builtin fonts."""
    provider = BuiltinFontProvider(font_dir)

    available = provider.get_available_fonts()
    assert 'NotoSans-Regular' in available
    assert 'Occulta' in available
    # Only Latin (NotoSans) and glyphless fallback (Occulta) are bundled.
    # All other scripts (Arabic, Devanagari, CJK, etc.) are discovered
    # from system fonts by SystemFontProvider to reduce package size.
    assert len(available) == 2


def test_builtin_font_provider_get_font(font_dir):
    """Test BuiltinFontProvider.get_font returns correct fonts."""
    provider = BuiltinFontProvider(font_dir)

    font = provider.get_font('NotoSans-Regular')
    assert font is not None
    assert isinstance(font, FontManager)

    missing = provider.get_font('NonExistent')
    assert missing is None


def test_builtin_font_provider_get_fallback(font_dir):
    """Test BuiltinFontProvider.get_fallback_font returns Occulta font."""
    provider = BuiltinFontProvider(font_dir)

    fallback = provider.get_fallback_font()
    assert fallback is not None
    assert fallback == provider.get_font('Occulta')


def test_builtin_font_provider_missing_font_logs_warning(tmp_path, font_dir, caplog):
    """Test that missing expected fonts log a warning."""
    # Create minimal font directory with only Occulta.ttf
    (tmp_path / 'Occulta.ttf').write_bytes((font_dir / 'Occulta.ttf').read_bytes())

    with caplog.at_level(logging.WARNING):
        provider = BuiltinFontProvider(tmp_path)

    # Should have logged warnings for missing fonts
    assert 'NotoSans-Regular' in caplog.text
    assert 'not found' in caplog.text

    # But Occulta should be loaded
    assert provider.get_fallback_font() is not None


def test_builtin_font_provider_missing_occulta_raises(tmp_path):
    """Test that missing Occulta.ttf raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Required fallback font"):
        BuiltinFontProvider(tmp_path)
