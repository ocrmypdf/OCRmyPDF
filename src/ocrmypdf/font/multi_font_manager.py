# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Multi-font management for PDF rendering.

Provides automatic font selection for multilingual documents based on
language hints and glyph coverage analysis.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ocrmypdf.font.font_manager import FontManager
from ocrmypdf.font.font_provider import (
    BuiltinFontProvider,
    ChainedFontProvider,
    FontProvider,
)
from ocrmypdf.font.system_font_provider import SystemFontProvider

log = logging.getLogger(__name__)


class MultiFontManager:
    """Manages multiple fonts with automatic selection and fallback.

    This class orchestrates multiple FontManager instances to provide
    word-level font selection for multilingual documents. It uses a hybrid
    approach combining language hints from hOCR with glyph coverage analysis.

    Font selection strategy:
    1. Try language-preferred font (if language hint available)
    2. Try fallback fonts in order by glyph coverage
    3. Fall back to Occulta.ttf (glyphless fallback)
    """

    # Language to font mapping
    # Keys are ISO 639-2/3 codes or Tesseract language codes
    LANGUAGE_FONT_MAP = {
        # Arabic script
        'ara': 'NotoSansArabic-Regular',  # Arabic
        'per': 'NotoSansArabic-Regular',  # Persian (uses Arabic script)
        'fas': 'NotoSansArabic-Regular',  # Farsi (alternative code for Persian)
        'urd': 'NotoSansArabic-Regular',  # Urdu (uses Arabic script)
        'pus': 'NotoSansArabic-Regular',  # Pashto
        'kur': 'NotoSansArabic-Regular',  # Kurdish (Arabic script variant)
        # Devanagari script
        'hin': 'NotoSansDevanagari-Regular',  # Hindi
        'san': 'NotoSansDevanagari-Regular',  # Sanskrit
        'mar': 'NotoSansDevanagari-Regular',  # Marathi
        'nep': 'NotoSansDevanagari-Regular',  # Nepali
        'kok': 'NotoSansDevanagari-Regular',  # Konkani
        'bho': 'NotoSansDevanagari-Regular',  # Bhojpuri
        'mai': 'NotoSansDevanagari-Regular',  # Maithili
        # CJK
        'chi': 'NotoSansCJK-Regular',  # Chinese (generic)
        'zho': 'NotoSansCJK-Regular',  # Chinese (ISO 639-3)
        'chi_sim': 'NotoSansCJK-Regular',  # Chinese Simplified (Tesseract)
        'chi_tra': 'NotoSansCJK-Regular',  # Chinese Traditional (Tesseract)
        'jpn': 'NotoSansCJK-Regular',  # Japanese
        'kor': 'NotoSansCJK-Regular',  # Korean
        # Thai
        'tha': 'NotoSansThai-Regular',  # Thai
        # Hebrew
        'heb': 'NotoSansHebrew-Regular',  # Hebrew
        'yid': 'NotoSansHebrew-Regular',  # Yiddish (uses Hebrew script)
        # Bengali script
        'ben': 'NotoSansBengali-Regular',  # Bengali
        'asm': 'NotoSansBengali-Regular',  # Assamese (uses Bengali script)
        # Tamil
        'tam': 'NotoSansTamil-Regular',  # Tamil
        # Gujarati
        'guj': 'NotoSansGujarati-Regular',  # Gujarati
        # Telugu
        'tel': 'NotoSansTelugu-Regular',  # Telugu
        # Kannada
        'kan': 'NotoSansKannada-Regular',  # Kannada
        # Malayalam
        'mal': 'NotoSansMalayalam-Regular',  # Malayalam
        # Myanmar (Burmese)
        'mya': 'NotoSansMyanmar-Regular',  # Myanmar
        # Khmer (Cambodian)
        'khm': 'NotoSansKhmer-Regular',  # Khmer
        # Lao
        'lao': 'NotoSansLao-Regular',  # Lao
        # Georgian
        'kat': 'NotoSansGeorgian-Regular',  # Georgian
        'geo': 'NotoSansGeorgian-Regular',  # Georgian (alternative)
        # Armenian
        'hye': 'NotoSansArmenian-Regular',  # Armenian
        'arm': 'NotoSansArmenian-Regular',  # Armenian (alternative)
        # Ethiopic
        'amh': 'NotoSansEthiopic-Regular',  # Amharic
        'tir': 'NotoSansEthiopic-Regular',  # Tigrinya
        # Sinhala
        'sin': 'NotoSansSinhala-Regular',  # Sinhala
        # Gurmukhi (Punjabi)
        'pan': 'NotoSansGurmukhi-Regular',  # Punjabi
        'pnb': 'NotoSansGurmukhi-Regular',  # Western Punjabi
        # Oriya
        'ori': 'NotoSansOriya-Regular',  # Oriya
        'ory': 'NotoSansOriya-Regular',  # Oriya (alternative)
        # Tibetan
        'bod': 'NotoSansTibetan-Regular',  # Tibetan
        'tib': 'NotoSansTibetan-Regular',  # Tibetan (alternative)
    }

    # Ordered fallback chain for fonts (after language-preferred font)
    # Order matters: most common scripts first for faster matching
    FALLBACK_FONTS = [
        'NotoSans-Regular',  # Latin, Greek, Cyrillic
        'NotoSansArabic-Regular',
        'NotoSansDevanagari-Regular',
        'NotoSansCJK-Regular',
        'NotoSansThai-Regular',
        'NotoSansHebrew-Regular',
        'NotoSansBengali-Regular',
        'NotoSansTamil-Regular',
        'NotoSansGujarati-Regular',
        'NotoSansTelugu-Regular',
        'NotoSansKannada-Regular',
        'NotoSansMalayalam-Regular',
        'NotoSansMyanmar-Regular',
        'NotoSansKhmer-Regular',
        'NotoSansLao-Regular',
        'NotoSansGeorgian-Regular',
        'NotoSansArmenian-Regular',
        'NotoSansEthiopic-Regular',
        'NotoSansSinhala-Regular',
        'NotoSansGurmukhi-Regular',
        'NotoSansOriya-Regular',
        'NotoSansTibetan-Regular',
    ]

    def __init__(
        self,
        font_dir: Path | None = None,
        *,
        font_provider: FontProvider | None = None,
    ):
        """Initialize multi-font manager.

        Args:
            font_dir: Directory containing font files. If font_provider is
                      not specified, this is passed to BuiltinFontProvider.
            font_provider: Provider for loading fonts. If None, uses a
                           ChainedFontProvider that tries builtin fonts first,
                           then searches system fonts.
        """
        if font_provider is not None:
            self.font_provider = font_provider
        else:
            # Use chained provider: try builtin fonts first, then system fonts
            self.font_provider = ChainedFontProvider(
                [
                    BuiltinFontProvider(font_dir),
                    SystemFontProvider(),
                ]
            )

        # Font selection cache: (word_text, language) -> font_name
        self._selection_cache: dict[tuple[str, str | None], str] = {}
        # Track whether we've warned about missing fonts (warn once per script)
        self._warned_scripts: set[str] = set()

    @property
    def fonts(self) -> dict[str, FontManager]:
        """Get all loaded fonts (backward compatibility)."""
        return self.get_all_fonts()

    def _try_font(
        self, font_name: str, word_text: str, cache_key: tuple[str, str | None]
    ) -> FontManager | None:
        """Try to use a font for the given word.

        Args:
            font_name: Name of font to try
            word_text: Text content to check
            cache_key: Cache key for storing successful result

        Returns:
            FontManager if font exists and has all glyphs, None otherwise
        """
        font = self.font_provider.get_font(font_name)
        if font is None:
            return None
        if self._has_all_glyphs(font, word_text):
            self._selection_cache[cache_key] = font_name
            return font
        return None

    def select_font_for_word(
        self, word_text: str, line_language: str | None
    ) -> FontManager:
        """Select appropriate font for a word.

        Uses a hybrid approach:
        1. Language-based selection (if language hint available)
        2. Ordered fallback through available fonts by glyph coverage
        3. Final fallback to Occulta.ttf (glyphless)

        Args:
            word_text: The text content of the word
            line_language: Language code from hOCR (e.g., 'ara', 'eng')

        Returns:
            FontManager instance to use for rendering this word
        """
        cache_key = (word_text, line_language)
        if cache_key in self._selection_cache:
            cached_name = self._selection_cache[cache_key]
            font = self.font_provider.get_font(cached_name)
            if font:
                return font

        tried_fonts: set[str] = set()

        # Phase 1: Try language-preferred font
        if line_language and line_language in self.LANGUAGE_FONT_MAP:
            preferred = self.LANGUAGE_FONT_MAP[line_language]
            tried_fonts.add(preferred)
            if result := self._try_font(preferred, word_text, cache_key):
                return result

        # Phase 2: Try fallback fonts in order
        for font_name in self.FALLBACK_FONTS:
            if font_name in tried_fonts:
                continue
            if result := self._try_font(font_name, word_text, cache_key):
                return result

        # Phase 3: Glyphless fallback (always succeeds)
        # Warn if we're falling back for non-ASCII text (likely missing font)
        self._warn_missing_font(word_text, line_language)
        self._selection_cache[cache_key] = 'Occulta'
        return self.font_provider.get_fallback_font()

    def _warn_missing_font(self, word_text: str, line_language: str | None) -> None:
        """Warn user about missing font for non-Latin text.

        Only warns once per language/script to avoid log spam.
        """
        # Determine a key for deduplication (language or 'non-ascii')
        warn_key = line_language if line_language else 'unknown'

        # Only warn for non-ASCII text and only once per key
        if warn_key in self._warned_scripts:
            return

        # Check if text contains non-ASCII characters
        if not any(ord(c) > 127 for c in word_text):
            return

        self._warned_scripts.add(warn_key)

        if line_language and line_language in self.LANGUAGE_FONT_MAP:
            font_name = self.LANGUAGE_FONT_MAP[line_language]
            log.warning(
                "No font found with glyphs for '%s' text. "
                "Install %s for better rendering. "
                "See https://fonts.google.com/noto",
                line_language,
                font_name,
            )
        else:
            log.warning(
                "No font found with glyphs for some text. "
                "Install Noto fonts for better rendering. "
                "See https://fonts.google.com/noto"
            )

    def _has_all_glyphs(self, font: FontManager, text: str) -> bool:
        """Check if a font has glyphs for all characters in text.

        Args:
            font: FontManager instance to check
            text: Text to verify coverage for

        Returns:
            True if font has real glyphs for all characters (not .notdef)
        """
        if not text:
            return True

        hb_font = font.get_hb_font()

        for char in text:
            codepoint = ord(char)
            glyph_id = hb_font.get_nominal_glyph(codepoint)
            if glyph_id is None or glyph_id == 0:  # 0 = .notdef glyph
                return False

        return True

    def has_font(self, font_name: str) -> bool:
        """Check if a named font is available.

        Args:
            font_name: Name of font to check

        Returns:
            True if font is available
        """
        return self.font_provider.get_font(font_name) is not None

    def has_all_glyphs(self, font_name: str, text: str) -> bool:
        """Check if a named font has glyphs for all characters in text.

        Args:
            font_name: Name of font to check
            text: Text to verify coverage for

        Returns:
            True if font has real glyphs for all characters (not .notdef)
        """
        font = self.font_provider.get_font(font_name)
        if font is None:
            return False
        return self._has_all_glyphs(font, text)

    def get_all_fonts(self) -> dict[str, FontManager]:
        """Get all loaded font managers.

        Returns:
            Dictionary mapping font names to FontManager instances
        """
        result = {}
        for name in self.font_provider.get_available_fonts():
            font = self.font_provider.get_font(name)
            if font is not None:
                result[name] = font
        return result
