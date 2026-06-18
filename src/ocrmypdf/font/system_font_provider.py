# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""System font discovery for PDF rendering.

Provides lazy discovery of Noto fonts installed on the system across
Linux, macOS, and Windows platforms.
"""

from __future__ import annotations

import glob
import logging
import os
import sys
from pathlib import Path

from ocrmypdf.font.font_manager import FontManager

log = logging.getLogger(__name__)


class SystemFontProvider:
    """Discovers and provides system-installed Noto fonts with lazy scanning.

    This provider searches standard system font directories for Noto fonts.
    Scanning is performed lazily - only when a font is actually requested
    and not found in the builtin fonts. Results are cached for the lifetime
    of the provider instance.
    """

    # System font directories by platform
    SYSTEM_FONT_DIRS: dict[str, list[Path]] = {
        'linux': [
            Path('/usr/share/fonts'),
            Path('/usr/local/share/fonts'),
            Path.home() / '.fonts',
            Path.home() / '.local/share/fonts',
        ],
        'freebsd': [
            Path('/usr/local/share/fonts'),
            Path.home() / '.fonts',
        ],
        'darwin': [
            Path('/Library/Fonts'),
            Path('/System/Library/Fonts'),
            Path.home() / 'Library/Fonts',
        ],
        # Windows is handled dynamically in _get_font_dirs()
    }

    # Noto font logical names → possible filenames (priority order)
    # The first match found will be used
    NOTO_FONT_PATTERNS: dict[str, list[str]] = {
        'NotoSans-Regular': [
            'NotoSans-Regular.ttf',
            'NotoSans-Regular.otf',
        ],
        'NotoSansArabic-Regular': [
            'NotoSansArabic-Regular.ttf',
            'NotoSansArabic-Regular.otf',
        ],
        'NotoSansDevanagari-Regular': [
            'NotoSansDevanagari-Regular.ttf',
            'NotoSansDevanagari-Regular.otf',
        ],
        'NotoSansCJK-Regular': [
            # Language-specific variants (any will work for CJK)
            'NotoSansCJKsc-Regular.otf',  # Simplified Chinese
            'NotoSansCJKtc-Regular.otf',  # Traditional Chinese
            'NotoSansCJKjp-Regular.otf',  # Japanese
            'NotoSansCJKkr-Regular.otf',  # Korean
            # TTC collections (common on Linux distros)
            'NotoSansCJK-Regular.ttc',
            'NotoSansCJKsc-Regular.ttc',
            # Variable fonts
            'NotoSansCJKsc-VF.otf',
        ],
        # Per-language CJK families. Modern Google Fonts / Homebrew ship these
        # as region subset variable fonts ('NotoSansJP[wght].ttf'), matched by
        # the flexible base search; the legacy per-region super OTFs (full
        # coverage) are listed here so they also satisfy the logical name.
        'NotoSansSC-Regular': [
            'NotoSansSC-Regular.otf',
            'NotoSansSC-Regular.ttf',
            'NotoSansCJKsc-Regular.otf',
        ],
        'NotoSansTC-Regular': [
            'NotoSansTC-Regular.otf',
            'NotoSansTC-Regular.ttf',
            'NotoSansCJKtc-Regular.otf',
        ],
        'NotoSansHK-Regular': [
            'NotoSansHK-Regular.otf',
            'NotoSansHK-Regular.ttf',
            'NotoSansCJKhk-Regular.otf',
        ],
        'NotoSansJP-Regular': [
            'NotoSansJP-Regular.otf',
            'NotoSansJP-Regular.ttf',
            'NotoSansCJKjp-Regular.otf',
        ],
        'NotoSansKR-Regular': [
            'NotoSansKR-Regular.otf',
            'NotoSansKR-Regular.ttf',
            'NotoSansCJKkr-Regular.otf',
        ],
        'NotoSansThai-Regular': [
            'NotoSansThai-Regular.ttf',
            'NotoSansThai-Regular.otf',
        ],
        'NotoSansHebrew-Regular': [
            'NotoSansHebrew-Regular.ttf',
            'NotoSansHebrew-Regular.otf',
        ],
        'NotoSansBengali-Regular': [
            'NotoSansBengali-Regular.ttf',
            'NotoSansBengali-Regular.otf',
        ],
        'NotoSansTamil-Regular': [
            'NotoSansTamil-Regular.ttf',
            'NotoSansTamil-Regular.otf',
        ],
        'NotoSansGujarati-Regular': [
            'NotoSansGujarati-Regular.ttf',
            'NotoSansGujarati-Regular.otf',
        ],
        'NotoSansTelugu-Regular': [
            'NotoSansTelugu-Regular.ttf',
            'NotoSansTelugu-Regular.otf',
        ],
        'NotoSansKannada-Regular': [
            'NotoSansKannada-Regular.ttf',
            'NotoSansKannada-Regular.otf',
        ],
        'NotoSansMalayalam-Regular': [
            'NotoSansMalayalam-Regular.ttf',
            'NotoSansMalayalam-Regular.otf',
        ],
        'NotoSansMyanmar-Regular': [
            'NotoSansMyanmar-Regular.ttf',
            'NotoSansMyanmar-Regular.otf',
        ],
        'NotoSansKhmer-Regular': [
            'NotoSansKhmer-Regular.ttf',
            'NotoSansKhmer-Regular.otf',
        ],
        'NotoSansLao-Regular': [
            'NotoSansLao-Regular.ttf',
            'NotoSansLao-Regular.otf',
        ],
        'NotoSansGeorgian-Regular': [
            'NotoSansGeorgian-Regular.ttf',
            'NotoSansGeorgian-Regular.otf',
        ],
        'NotoSansArmenian-Regular': [
            'NotoSansArmenian-Regular.ttf',
            'NotoSansArmenian-Regular.otf',
        ],
        'NotoSansEthiopic-Regular': [
            'NotoSansEthiopic-Regular.ttf',
            'NotoSansEthiopic-Regular.otf',
        ],
        'NotoSansSinhala-Regular': [
            'NotoSansSinhala-Regular.ttf',
            'NotoSansSinhala-Regular.otf',
        ],
        'NotoSansGurmukhi-Regular': [
            'NotoSansGurmukhi-Regular.ttf',
            'NotoSansGurmukhi-Regular.otf',
        ],
        'NotoSansOriya-Regular': [
            'NotoSansOriya-Regular.ttf',
            'NotoSansOriya-Regular.otf',
        ],
        'NotoSansTibetan-Regular': [
            'NotoSansTibetan-Regular.ttf',
            'NotoSansTibetan-Regular.otf',
        ],
    }

    # Font file extensions we know how to load.
    _FONT_EXTENSIONS = ('.ttf', '.otf', '.ttc')

    # Acceptable filename variants for a font family, ranked best-first.
    # Lower rank wins when multiple variants of the same family are present.
    _VARIANT_RANK = {'regular': 0, 'variable': 1, 'vf': 2, 'plain': 3}

    # Extra family bases that can satisfy a logical font, tried after its own
    # base (so the listed order is the preference). CJK is the case that needs
    # this: the legacy Adobe-style 'NotoSansCJKsc-Regular.otf' is handled by
    # NOTO_FONT_PATTERNS, but Homebrew casks and current Google Fonts ship the
    # per-language families as variable fonts (e.g. 'NotoSansSC[wght].ttf').
    _ALTERNATE_BASES: dict[str, list[str]] = {
        'NotoSansCJK-Regular': [
            'NotoSansSC',  # Simplified Chinese
            'NotoSansTC',  # Traditional Chinese
            'NotoSansHK',  # Hong Kong
            'NotoSansJP',  # Japanese
            'NotoSansKR',  # Korean
        ],
    }

    def __init__(self) -> None:
        """Initialize system font provider with empty caches."""
        # Cache: font_name -> FontManager (successfully loaded fonts)
        self._font_cache: dict[str, FontManager] = {}
        # Negative cache: font names we've searched for but not found
        self._not_found: set[str] = set()
        # Cached font directories (computed lazily)
        self._font_dirs: list[Path] | None = None

    def _get_platform(self) -> str:
        """Get the current platform identifier.

        Returns:
            Platform string: 'linux', 'darwin', 'windows', or 'freebsd'
        """
        if sys.platform == 'win32':
            return 'windows'
        elif sys.platform == 'darwin':
            return 'darwin'
        elif 'freebsd' in sys.platform:
            return 'freebsd'
        else:
            return 'linux'

    def _get_font_dirs(self) -> list[Path]:
        """Get font directories for the current platform.

        Returns:
            List of paths to search for fonts (may include non-existent paths)
        """
        if self._font_dirs is not None:
            return self._font_dirs

        platform = self._get_platform()

        if platform == 'windows':
            # Get Windows font directories from environment
            windir = os.environ.get('WINDIR', r'C:\Windows')
            self._font_dirs = [Path(windir) / 'Fonts']
            # User-installed fonts (Windows 10+)
            localappdata = os.environ.get('LOCALAPPDATA')
            if localappdata:
                self._font_dirs.append(
                    Path(localappdata) / 'Microsoft' / 'Windows' / 'Fonts'
                )
        else:
            self._font_dirs = list(self.SYSTEM_FONT_DIRS.get(platform, []))

        return self._font_dirs

    def _find_font_file(self, font_name: str) -> Path | None:
        """Search system directories for a font file.

        Args:
            font_name: Logical font name (e.g., 'NotoSansCJK-Regular')

        Returns:
            Path to font file if found, None otherwise
        """
        if font_name not in self.NOTO_FONT_PATTERNS:
            return None

        patterns = self.NOTO_FONT_PATTERNS[font_name]

        for font_dir in self._get_font_dirs():
            if not font_dir.exists():
                continue

            for pattern in patterns:
                # Search recursively for the font file
                try:
                    matches = list(font_dir.rglob(pattern))
                    if matches:
                        log.debug(
                            "Found system font %s at %s", font_name, matches[0]
                        )
                        return matches[0]
                except PermissionError:
                    # Skip directories we can't read
                    continue

        # No exact static '-Regular' file. Many distributors (Homebrew casks,
        # current Google Fonts releases) ship Noto fonts as variable fonts with
        # bracketed axis filenames such as 'NotoSansArabic[wdth,wght].ttf'.
        # Fall back to a flexible search that also accepts those. See #1652.
        return self._find_variant_font_file(font_name)

    @staticmethod
    def _classify_variant(stem: str, base: str) -> str | None:
        """Classify a font filename stem as a usable variant of ``base``.

        Args:
            stem: Filename without extension (e.g. 'NotoSansArabic[wdth,wght]')
            base: Family base name (e.g. 'NotoSansArabic')

        Returns:
            The variant kind ('regular', 'variable', 'vf', 'plain') or None if
            the stem is not an acceptable representative of the family. The
            boundary after ``base`` is required so that 'NotoSans' does not
            match 'NotoSansArabic', and 'NotoSansArabicUI'/'NotoSansArabic-Bold'
            do not match a request for 'NotoSansArabic'.
        """
        if stem == f'{base}-Regular':
            return 'regular'
        if stem.startswith(f'{base}['):  # variable font, e.g. Base[wdth,wght]
            return 'variable'
        if stem == f'{base}-VF':  # alternate variable-font naming
            return 'vf'
        if stem == base:  # bare family name
            return 'plain'
        return None

    def _find_variant_font_file(self, font_name: str) -> Path | None:
        """Search for a variable font or other acceptable filename variant.

        Tries the font's own family base first, then any alternate bases (used
        for the modern per-language CJK families). Within that, a static Regular
        is preferred over a variable font. See issue #1652.

        Args:
            font_name: Logical font name (e.g. 'NotoSansArabic-Regular')

        Returns:
            Path to the best-ranked matching font file, or None.
        """
        bases = [font_name.removesuffix('-Regular')]
        bases.extend(self._ALTERNATE_BASES.get(font_name, []))

        # Selection key (base_index, variant_rank): earlier base wins, then the
        # better variant. Path is carried along but not part of the comparison.
        best: tuple[tuple[int, int], Path] | None = None
        for base_index, base in enumerate(bases):
            for font_dir in self._get_font_dirs():
                if not font_dir.exists():
                    continue
                try:
                    for path in font_dir.rglob(glob.escape(base) + '*'):
                        if path.suffix.lower() not in self._FONT_EXTENSIONS:
                            continue
                        kind = self._classify_variant(path.stem, base)
                        if kind is None:
                            continue
                        key = (base_index, self._VARIANT_RANK[kind])
                        if best is None or key < best[0]:
                            best = (key, path)
                except PermissionError:
                    # Skip directories we can't read
                    continue
        if best is not None:
            log.debug("Found system font %s at %s (variant match)", font_name, best[1])
            return best[1]
        return None

    def get_font(self, font_name: str) -> FontManager | None:
        """Get a FontManager for the named font (lazy loading).

        This method implements lazy scanning: fonts are only searched for
        when first requested. Results (both positive and negative) are
        cached for subsequent calls.

        Args:
            font_name: Logical font name (e.g., 'NotoSansCJK-Regular')

        Returns:
            FontManager if font is found and loadable, None otherwise
        """
        # Check positive cache first
        if font_name in self._font_cache:
            return self._font_cache[font_name]

        # Check negative cache (already searched, not found)
        if font_name in self._not_found:
            return None

        # Lazy scan for this specific font
        font_path = self._find_font_file(font_name)
        if font_path is not None:
            try:
                fm = FontManager(font_path)
                self._font_cache[font_name] = fm
                return fm
            except Exception as e:
                log.warning(
                    "Found font %s at %s but failed to load: %s",
                    font_name,
                    font_path,
                    e,
                )

        # Cache negative result
        self._not_found.add(font_name)
        return None

    def get_available_fonts(self) -> list[str]:
        """Get list of font names this provider can potentially find.

        Note: This returns all font names we know patterns for, not
        necessarily fonts that are actually installed. Use get_font()
        to check if a specific font is available.

        Returns:
            List of logical font names
        """
        return list(self.NOTO_FONT_PATTERNS.keys())

    def get_fallback_font(self) -> FontManager:
        """Get the glyphless fallback font.

        Raises:
            NotImplementedError: System provider doesn't provide fallback.
                Use BuiltinFontProvider for the fallback font.
        """
        raise NotImplementedError(
            "SystemFontProvider does not provide a fallback font. "
            "Use BuiltinFontProvider for Occulta.ttf fallback."
        )
