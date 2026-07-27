# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Multi-font management for PDF rendering.

Provides automatic font selection for multilingual documents based on
language hints and glyph coverage analysis.
"""

from __future__ import annotations

import logging
import unicodedata
from pathlib import Path

from ocrmypdf.font.font_manager import FontManager
from ocrmypdf.font.font_provider import (
    BuiltinFontProvider,
    ChainedFontProvider,
    FontProvider,
    GlyphSearchingFontProvider,
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
    3. Ask the provider for any installed font that covers the text
    4. Fall back to Occulta.ttf (glyphless fallback)
    """

    # How many uncoverable characters to name in the missing-font warning
    MAX_REPORTED_CHARS = 3

    # How many characters of a word to look up individually when composing that
    # warning; each lookup may scan every font installed on the system
    MAX_EXAMINED_CHARS = 8

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
        # CJK — prefer the family matching the document language, because the
        # modern per-language Noto fonts are region subsets (e.g. NotoSansSC
        # lacks Japanese kana). The pan-CJK super font is a shared fallback.
        'chi': 'NotoSansSC-Regular',  # Chinese (generic → Simplified)
        'zho': 'NotoSansSC-Regular',  # Chinese (ISO 639-3)
        'chi_sim': 'NotoSansSC-Regular',  # Chinese Simplified (Tesseract)
        'chi_tra': 'NotoSansTC-Regular',  # Chinese Traditional (Tesseract)
        'jpn': 'NotoSansJP-Regular',  # Japanese
        'kor': 'NotoSansKR-Regular',  # Korean
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
        # Pan-CJK super font first (full coverage), then the per-language
        # subsets so a glyph missing from one CJK family is found in another.
        'NotoSansCJK-Regular',
        'NotoSansSC-Regular',
        'NotoSansTC-Regular',
        'NotoSansHK-Regular',
        'NotoSansJP-Regular',
        'NotoSansKR-Regular',
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
        # Fonts found by glyph coverage rather than by name, tried before
        # repeating the (expensive) provider search
        self._discovered_fonts: list[str] = []

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
        3. Provider search over every installed font, by glyph coverage
        4. Final fallback to Occulta.ttf (glyphless)

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

        # Phase 2: Try fallback fonts in order, then anything a previous
        # coverage search turned up
        for font_name in [*self.FALLBACK_FONTS, *self._discovered_fonts]:
            if font_name in tried_fonts:
                continue
            tried_fonts.add(font_name)
            if result := self._try_font(font_name, word_text, cache_key):
                return result

        # Phase 3: Ask the provider to search every installed font. The named
        # families cover common scripts only, but systems ship many more (macOS
        # installs ~100 Noto faces), and those should be used before giving up
        # on rendering the text at all. See issue #1722.
        if found := self._search_font_by_coverage(word_text):
            font_name, font = found
            self._selection_cache[cache_key] = font_name
            return font

        # Phase 4: Glyphless fallback (always succeeds)
        # Warn if we're falling back for non-ASCII text (likely missing font)
        self._warn_missing_font(word_text, line_language)
        self._selection_cache[cache_key] = 'Occulta'
        return self.font_provider.get_fallback_font()

    def _search_font_by_coverage(self, text: str) -> tuple[str, FontManager] | None:
        """Search the provider for any font covering text, if it supports it.

        Args:
            text: Text the font must fully cover

        Returns:
            (font name, FontManager), or None if unsupported or nothing matched
        """
        provider = self.font_provider
        if not isinstance(provider, GlyphSearchingFontProvider):
            return None
        found = provider.find_font_with_glyphs(text)
        if found is None:
            return None
        font_name, _font = found
        if font_name not in self._discovered_fonts:
            self._discovered_fonts.append(font_name)
        return found

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

        uncoverable = self._uncoverable_characters(word_text)
        if not uncoverable:
            # Every character has a font, but no single font has them all.
            # Telling the user to install fonts would be wrong advice here.
            log.warning(
                "Text mixing scripts that no single installed font covers (%r) "
                "was added as an invisible text layer: it stays searchable and "
                "copyable, but appears blank when highlighted in a PDF viewer. "
                "Installing more fonts will not help; OCRmyPDF uses one font "
                "per word.",
                word_text,
            )
            return

        missing = self._describe_characters(uncoverable)
        if line_language and line_language in self.LANGUAGE_FONT_MAP:
            font_family = self.LANGUAGE_FONT_MAP[line_language].removesuffix('-Regular')
            log.warning(
                "No installed font has glyphs for the detected '%s' text (%s), "
                "so it was added as an invisible text layer: it stays searchable "
                "and copyable, but appears blank when highlighted in a PDF "
                "viewer. Install the %s font family (via your OS package "
                "manager or https://fonts.google.com/noto) for full rendering.",
                line_language,
                missing,
                font_family,
            )
        else:
            log.warning(
                "No installed font has glyphs for some of the detected text "
                "(%s), so it was added as an invisible text layer: it stays "
                "searchable and copyable, but appears blank when highlighted "
                "in a PDF viewer. Install a Noto font covering that script "
                "(https://fonts.google.com/noto) for full rendering.",
                missing,
            )

    def _uncoverable_characters(self, word_text: str) -> list[str]:
        """Find the characters of word_text that no installed font can render.

        Args:
            word_text: The word that fell back to glyphless rendering

        Returns:
            The distinct uncoverable characters, in order of first appearance,
            considering at most MAX_EXAMINED_CHARS of them
        """
        candidates = [
            char
            for char in dict.fromkeys(word_text)  # de-duplicate, keep order
            if not char.isspace() and not self._is_char_renderable(char)
        ]
        # The named fonts missed these, but the provider may still have a font
        # for them, so confirm before telling the user to install anything. The
        # search walks every installed font, hence the cap on how many
        # characters we are willing to look up for one warning.
        return [
            char
            for char in candidates[: self.MAX_EXAMINED_CHARS]
            if self._search_font_by_coverage(char) is None
        ]

    def _describe_characters(self, chars: list[str]) -> str:
        """Describe characters by codepoint and Unicode name.

        Naming the codepoints tells the user which font to install even for
        scripts OCRmyPDF has no language mapping for, which the generic
        "install the matching Noto fonts" advice did not. See issue #1722.

        Args:
            chars: Characters to describe

        Returns:
            Human-readable description, truncated to MAX_REPORTED_CHARS
        """
        described = ", ".join(
            f"{char!r} U+{ord(char):04X} {unicodedata.name(char, 'unnamed character')}"
            for char in chars[: self.MAX_REPORTED_CHARS]
        )
        if len(chars) > self.MAX_REPORTED_CHARS:
            described += f", and {len(chars) - self.MAX_REPORTED_CHARS} more"
        return described

    def _is_char_renderable(self, char: str) -> bool:
        """Check whether any font already known to us has a glyph for char."""
        for font_name in [*self.FALLBACK_FONTS, *self._discovered_fonts]:
            font = self.font_provider.get_font(font_name)
            if font is not None and self._has_all_glyphs(font, char):
                return True
        return False

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
