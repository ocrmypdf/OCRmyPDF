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
        # Cached (logical name, path) of every Noto face on the system, in the
        # order the coverage search should try them (computed lazily)
        self._noto_candidates: list[tuple[str, Path]] | None = None
        # Memoized results of find_font_with_glyphs(), keyed by codepoint set
        self._coverage_cache: dict[frozenset[int], str | None] = {}
        # Font files that failed to load, so we only complain about them once
        self._unloadable: set[Path] = set()

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
                        log.debug("Found system font %s at %s", font_name, matches[0])
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

    @staticmethod
    def _family_base(stem: str) -> str | None:
        """Get the Noto family base a filename stem is the Regular face of.

        Args:
            stem: Filename without extension, e.g. 'NotoSansCherokee-Regular'

        Returns:
            The family base ('NotoSansCherokee') or None if the stem is not a
            Noto font, or is a weight/slope variant such as '-Bold' or
            '-Italic' that should not stand in for the family.
        """
        head = stem.split('[', 1)[0]  # drop variable-font axes, e.g. '[wght]'
        if head.endswith('-Regular'):
            head = head[: -len('-Regular')]
        elif head.endswith('-VF'):
            head = head[: -len('-VF')]
        elif '-' in head:
            return None
        return head if head.startswith('Noto') else None

    @classmethod
    def _candidate_sort_key(cls, base: str) -> tuple[int, int, str]:
        """Rank a family base for the coverage search.

        Sans comes before serif before everything else, and plain families come
        ahead of their narrower UI and Mono cousins.
        """
        if base.startswith('NotoSans'):
            family_rank = 0
        elif base.startswith('NotoSerif'):
            family_rank = 1
        else:
            family_rank = 2
        narrow_use = base.endswith('UI') or base.startswith('NotoSansMono')
        return (family_rank, int(narrow_use), base)

    def _get_noto_candidates(self) -> list[tuple[str, Path]]:
        """Enumerate every Noto family installed on the system.

        Scans each font directory once and keeps the best-ranked file per
        family, so a family present in several directories or in several
        variants contributes a single candidate.

        Returns:
            List of (logical font name, path) in the order to try them.
        """
        if self._noto_candidates is not None:
            return self._noto_candidates

        best: dict[str, tuple[int, Path]] = {}
        for font_dir in self._get_font_dirs():
            if not font_dir.exists():
                continue
            try:
                paths = sorted(font_dir.rglob('Noto*'))
            except OSError:
                # Skip directories we can't read
                continue
            for path in paths:
                if path.suffix.lower() not in self._FONT_EXTENSIONS:
                    continue
                base = self._family_base(path.stem)
                if base is None:
                    continue
                kind = self._classify_variant(path.stem, base)
                if kind is None:
                    continue
                rank = self._VARIANT_RANK[kind]
                if base not in best or rank < best[base][0]:
                    best[base] = (rank, path)

        self._noto_candidates = [
            (f'{base}-Regular', path)
            for base, (_rank, path) in sorted(
                best.items(), key=lambda item: self._candidate_sort_key(item[0])
            )
        ]
        return self._noto_candidates

    def find_font_with_glyphs(self, text: str) -> tuple[str, FontManager] | None:
        """Find any installed Noto font that covers every character in text.

        ``NOTO_FONT_PATTERNS`` enumerates the couple dozen scripts OCRmyPDF
        knows by name, but systems ship far more: macOS alone installs around a
        hundred script-specific Noto faces in
        ``/System/Library/Fonts/Supplemental``. This is the last resort that
        makes those usable, so a document is only rendered glyphless when no
        installed font can actually cover it. See issue #1722.

        This walks every Noto face on the system and is therefore expensive;
        results are memoized, and callers should only reach it after the named
        fonts have failed.

        Args:
            text: Text that the returned font must fully cover

        Returns:
            (logical font name, FontManager) of the first covering font, or
            None if nothing installed covers the text.
        """
        if not text:
            return None
        needed = frozenset(ord(c) for c in text)

        if needed in self._coverage_cache:
            cached_name = self._coverage_cache[needed]
            if cached_name is None:
                return None
            if cached := self._font_cache.get(cached_name):
                return cached_name, cached

        for font_name, path in self._get_noto_candidates():
            font = self._font_cache.get(font_name)
            if font is None:
                if path in self._unloadable:
                    continue
                try:
                    font = FontManager(path)
                except Exception as e:
                    log.debug("Skipping unreadable font %s: %s", path, e)
                    self._unloadable.add(path)
                    continue
            if all(font.has_glyph(cp) for cp in needed):
                # Keep only fonts we actually use; the rest are released so a
                # full scan doesn't retain every font file on the system.
                self._font_cache[font_name] = font
                self._not_found.discard(font_name)
                self._coverage_cache[needed] = font_name
                log.debug(
                    "Found system font %s at %s (glyph coverage match)",
                    font_name,
                    path,
                )
                return font_name, font

        self._coverage_cache[needed] = None
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
