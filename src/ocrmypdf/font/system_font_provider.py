# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""System font discovery for PDF rendering.

Provides lazy discovery of Noto fonts installed on the system across
Linux, macOS, and Windows platforms.
"""

from __future__ import annotations

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
