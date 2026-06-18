# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for SystemFontProvider and ChainedFontProvider."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ocrmypdf.font import (
    BuiltinFontProvider,
    ChainedFontProvider,
    SystemFontProvider,
)

# --- SystemFontProvider Platform Detection Tests ---


class TestSystemFontProviderPlatform:
    """Test platform detection in SystemFontProvider."""

    def test_get_platform_linux(self):
        """Test Linux platform detection."""
        provider = SystemFontProvider()
        with patch.object(sys, 'platform', 'linux'):
            assert provider._get_platform() == 'linux'

    def test_get_platform_darwin(self):
        """Test macOS platform detection."""
        provider = SystemFontProvider()
        with patch.object(sys, 'platform', 'darwin'):
            assert provider._get_platform() == 'darwin'

    def test_get_platform_windows(self):
        """Test Windows platform detection."""
        provider = SystemFontProvider()
        with patch.object(sys, 'platform', 'win32'):
            assert provider._get_platform() == 'windows'

    def test_get_platform_freebsd(self):
        """Test FreeBSD platform detection."""
        provider = SystemFontProvider()
        with patch.object(sys, 'platform', 'freebsd13'):
            assert provider._get_platform() == 'freebsd'


class TestSystemFontProviderDirectories:
    """Test font directory resolution."""

    def test_linux_font_dirs(self):
        """Test Linux font directories."""
        provider = SystemFontProvider()
        with patch.object(sys, 'platform', 'linux'):
            provider._font_dirs = None  # Reset cache
            dirs = provider._get_font_dirs()
            assert Path('/usr/share/fonts') in dirs
            assert Path('/usr/local/share/fonts') in dirs

    def test_darwin_font_dirs(self):
        """Test macOS font directories."""
        provider = SystemFontProvider()
        with patch.object(sys, 'platform', 'darwin'):
            provider._font_dirs = None  # Reset cache
            dirs = provider._get_font_dirs()
            assert Path('/Library/Fonts') in dirs
            assert Path('/System/Library/Fonts') in dirs

    def test_windows_font_dirs_with_windir(self):
        """Test Windows font directory from WINDIR env var."""
        provider = SystemFontProvider()
        with (
            patch.object(sys, 'platform', 'win32'),
            patch.dict('os.environ', {'WINDIR': r'D:\Windows'}),
        ):
            provider._font_dirs = None  # Reset cache
            dirs = provider._get_font_dirs()
            # Check that Fonts subdir of WINDIR is included
            # Use str comparison to avoid Path normalization issues across platforms
            dir_strs = [str(d) for d in dirs]
            assert any('Fonts' in d for d in dir_strs)

    def test_windows_font_dirs_default(self):
        """Test Windows font directory with default path."""
        provider = SystemFontProvider()
        with (
            patch.object(sys, 'platform', 'win32'),
            patch.dict('os.environ', {}, clear=True),
        ):
            provider._font_dirs = None  # Reset cache
            dirs = provider._get_font_dirs()
            # Check that Windows\Fonts is included (default fallback)
            dir_strs = [str(d) for d in dirs]
            assert any('Windows' in d and 'Fonts' in d for d in dir_strs)

    def test_windows_font_dirs_with_localappdata(self):
        """Test Windows user fonts directory from LOCALAPPDATA env var."""
        provider = SystemFontProvider()
        with (
            patch.object(sys, 'platform', 'win32'),
            patch.dict(
                'os.environ',
                {'WINDIR': r'C:\Windows', 'LOCALAPPDATA': r'C:\Users\Test\AppData\Local'},
            ),
        ):
            provider._font_dirs = None  # Reset cache
            dirs = provider._get_font_dirs()
            dir_strs = [str(d) for d in dirs]
            # Should have both system and user font directories
            assert len(dirs) == 2
            assert any('Windows' in d and 'Fonts' in d for d in dir_strs)
            assert any(
                'AppData' in d and 'Local' in d and 'Fonts' in d
                for d in dir_strs
            )

    def test_font_dirs_cached(self):
        """Test that font directories are cached."""
        provider = SystemFontProvider()
        dirs1 = provider._get_font_dirs()
        dirs2 = provider._get_font_dirs()
        assert dirs1 is dirs2  # Same object, not recomputed


class TestSystemFontProviderLazyLoading:
    """Test lazy loading behavior."""

    def test_no_scanning_on_init(self):
        """Test that no directory scanning happens during initialization."""
        provider = SystemFontProvider()
        # Caches should be empty
        assert len(provider._font_cache) == 0
        assert len(provider._not_found) == 0

    def test_get_font_unknown_name_returns_none(self):
        """Test that unknown font names return None."""
        provider = SystemFontProvider()
        result = provider.get_font('UnknownFont-Regular')
        assert result is None
        # Unknown fonts are added to not_found to cache the negative result
        assert 'UnknownFont-Regular' in provider._not_found

    def test_negative_cache(self):
        """Test that not-found results are cached."""
        provider = SystemFontProvider()
        # Mock _find_font_file to return None
        with patch.object(provider, '_find_font_file', return_value=None):
            result1 = provider.get_font('NotoSansCJK-Regular')
            assert result1 is None
            assert 'NotoSansCJK-Regular' in provider._not_found

            # Second call should not call _find_font_file again
            provider._find_font_file = MagicMock(return_value=None)
            result2 = provider.get_font('NotoSansCJK-Regular')
            assert result2 is None
            provider._find_font_file.assert_not_called()

    def test_positive_cache(self):
        """Test that found fonts are cached."""
        provider = SystemFontProvider()
        font_dir = Path(__file__).parent.parent / "src" / "ocrmypdf" / "data"
        font_path = font_dir / "NotoSans-Regular.ttf"

        if not font_path.exists():
            pytest.skip("Test font not available")

        with patch.object(provider, '_find_font_file', return_value=font_path):
            result1 = provider.get_font('NotoSans-Regular')
            assert result1 is not None
            assert 'NotoSans-Regular' in provider._font_cache

            # Second call should use cache
            provider._find_font_file = MagicMock()
            result2 = provider.get_font('NotoSans-Regular')
            assert result2 is result1
            provider._find_font_file.assert_not_called()


class TestSystemFontProviderAvailableFonts:
    """Test get_available_fonts method."""

    def test_returns_all_patterns(self):
        """Test that get_available_fonts returns all known font patterns."""
        provider = SystemFontProvider()
        fonts = provider.get_available_fonts()
        assert 'NotoSans-Regular' in fonts
        assert 'NotoSansCJK-Regular' in fonts
        assert 'NotoSansArabic-Regular' in fonts
        assert 'NotoSansThai-Regular' in fonts
        # Per-language CJK families (modern Google Fonts / Homebrew naming)
        assert 'NotoSansSC-Regular' in fonts
        assert 'NotoSansJP-Regular' in fonts

    def test_fallback_font_raises(self):
        """Test that get_fallback_font raises NotImplementedError."""
        provider = SystemFontProvider()
        with pytest.raises(NotImplementedError):
            provider.get_fallback_font()


class TestSystemFontProviderVariableFonts:
    """Test discovery of variable fonts and non-static filename variants.

    Homebrew casks and Google Fonts ship Noto fonts as variable fonts with
    bracketed axis filenames (e.g. ``NotoSansArabic[wdth,wght].ttf``) rather
    than the static ``NotoSansArabic-Regular.ttf``. See issue #1652.
    """

    @pytest.fixture
    def real_font_bytes(self):
        """Bytes of a real, loadable font (content is irrelevant to the test)."""
        font_path = (
            Path(__file__).parent.parent
            / "src"
            / "ocrmypdf"
            / "data"
            / "NotoSans-Regular.ttf"
        )
        if not font_path.exists():
            pytest.skip("Builtin font not available")
        return font_path.read_bytes()

    def _provider_for(self, tmp_path, filenames, real_font_bytes):
        """Build a provider whose only font dir is tmp_path with given files."""
        for name in filenames:
            (tmp_path / name).write_bytes(real_font_bytes)
        provider = SystemFontProvider()
        provider._font_dirs = [tmp_path]
        return provider

    def test_finds_variable_font_with_axes(self, tmp_path, real_font_bytes):
        """A bracketed variable font satisfies a request for the static name."""
        provider = self._provider_for(
            tmp_path, ['NotoSansArabic[wdth,wght].ttf'], real_font_bytes
        )
        font = provider.get_font('NotoSansArabic-Regular')
        assert font is not None
        assert font.font_path.name == 'NotoSansArabic[wdth,wght].ttf'

    def test_finds_weight_only_variable_font(self, tmp_path, real_font_bytes):
        """A variable font with only a weight axis is also discovered."""
        provider = self._provider_for(
            tmp_path, ['NotoSansHebrew[wght].ttf'], real_font_bytes
        )
        assert provider.get_font('NotoSansHebrew-Regular') is not None

    def test_variable_font_does_not_cross_match_other_script(
        self, tmp_path, real_font_bytes
    ):
        """The generic NotoSans request must not match a script-specific font."""
        provider = self._provider_for(
            tmp_path, ['NotoSansArabic[wdth,wght].ttf'], real_font_bytes
        )
        # NotoSans (Latin) must NOT be satisfied by NotoSansArabic.
        assert provider.get_font('NotoSans-Regular') is None

    def test_does_not_match_ui_or_bold_variants(self, tmp_path, real_font_bytes):
        """Width/UI and weight variants must not satisfy the Regular request."""
        provider = self._provider_for(
            tmp_path,
            ['NotoSansArabicUI-Regular.ttf', 'NotoSansArabic-Bold.ttf'],
            real_font_bytes,
        )
        assert provider.get_font('NotoSansArabic-Regular') is None

    def test_prefers_static_regular_over_variable(self, tmp_path, real_font_bytes):
        """When both exist, the static Regular is preferred for predictability."""
        provider = self._provider_for(
            tmp_path,
            ['NotoSansArabic[wdth,wght].ttf', 'NotoSansArabic-Regular.ttf'],
            real_font_bytes,
        )
        font = provider.get_font('NotoSansArabic-Regular')
        assert font is not None
        assert font.font_path.name == 'NotoSansArabic-Regular.ttf'

    # --- Modern per-language CJK families (NotoSansSC/TC/HK/JP/KR) ---
    # Homebrew casks (font-noto-sans-sc, ...) and Google Fonts ship CJK as
    # variable fonts under these bases rather than the legacy NotoSansCJK*.

    @pytest.mark.parametrize(
        'filename',
        [
            'NotoSansSC[wght].ttf',  # Simplified Chinese (Homebrew/Google)
            'NotoSansTC[wght].ttf',  # Traditional Chinese
            'NotoSansHK[wght].ttf',  # Hong Kong
            'NotoSansJP[wght].ttf',  # Japanese
            'NotoSansKR[wght].ttf',  # Korean
        ],
    )
    def test_finds_modern_cjk_variable_font(self, tmp_path, real_font_bytes, filename):
        """A modern per-language CJK variable font satisfies NotoSansCJK."""
        provider = self._provider_for(tmp_path, [filename], real_font_bytes)
        font = provider.get_font('NotoSansCJK-Regular')
        assert font is not None
        assert font.font_path.name == filename

    def test_finds_static_cjk_language_variant(self, tmp_path, real_font_bytes):
        """A static per-language CJK Regular also satisfies NotoSansCJK."""
        provider = self._provider_for(
            tmp_path, ['NotoSansTC-Regular.otf'], real_font_bytes
        )
        assert provider.get_font('NotoSansCJK-Regular') is not None

    def test_prefers_pan_cjk_over_language_variant(self, tmp_path, real_font_bytes):
        """The pan-CJK family is preferred over a single-language variant."""
        provider = self._provider_for(
            tmp_path,
            ['NotoSansSC[wght].ttf', 'NotoSansCJK[wght].ttf'],
            real_font_bytes,
        )
        font = provider.get_font('NotoSansCJK-Regular')
        assert font is not None
        assert font.font_path.name == 'NotoSansCJK[wght].ttf'

    def test_modern_cjk_does_not_cross_match_latin(self, tmp_path, real_font_bytes):
        """A CJK variable font must not satisfy the generic NotoSans request."""
        provider = self._provider_for(
            tmp_path, ['NotoSansSC[wght].ttf'], real_font_bytes
        )
        assert provider.get_font('NotoSans-Regular') is None

    # --- Per-language CJK families reachable by their own logical name ---
    # Needed so MultiFontManager can prefer the family matching the document
    # language (NotoSansJP for Japanese, NotoSansSC for Simplified Chinese, ...).

    @pytest.mark.parametrize(
        'logical,filename',
        [
            ('NotoSansSC-Regular', 'NotoSansSC[wght].ttf'),
            ('NotoSansTC-Regular', 'NotoSansTC[wght].ttf'),
            ('NotoSansHK-Regular', 'NotoSansHK[wght].ttf'),
            ('NotoSansJP-Regular', 'NotoSansJP[wght].ttf'),
            ('NotoSansKR-Regular', 'NotoSansKR[wght].ttf'),
        ],
    )
    def test_per_language_cjk_logical_name_resolves(
        self, tmp_path, real_font_bytes, logical, filename
    ):
        """Each per-language CJK family is reachable by its own logical name."""
        provider = self._provider_for(tmp_path, [filename], real_font_bytes)
        font = provider.get_font(logical)
        assert font is not None
        assert font.font_path.name == filename

    def test_per_language_cjk_static_resolves(self, tmp_path, real_font_bytes):
        """A static per-language Regular also resolves by logical name."""
        provider = self._provider_for(
            tmp_path, ['NotoSansJP-Regular.otf'], real_font_bytes
        )
        assert provider.get_font('NotoSansJP-Regular') is not None

    def test_per_language_cjk_does_not_cross_match(self, tmp_path, real_font_bytes):
        """A JP font must not satisfy an SC request (distinct families)."""
        provider = self._provider_for(
            tmp_path, ['NotoSansJP[wght].ttf'], real_font_bytes
        )
        assert provider.get_font('NotoSansSC-Regular') is None


# --- ChainedFontProvider Tests ---


class TestChainedFontProvider:
    """Test ChainedFontProvider."""

    def test_requires_at_least_one_provider(self):
        """Test that empty provider list raises error."""
        with pytest.raises(ValueError, match="At least one provider"):
            ChainedFontProvider([])

    def test_get_font_tries_providers_in_order(self):
        """Test that get_font tries providers in order."""
        provider1 = MagicMock()
        provider1.get_font.return_value = None

        provider2 = MagicMock()
        mock_font = MagicMock()
        provider2.get_font.return_value = mock_font

        chain = ChainedFontProvider([provider1, provider2])
        result = chain.get_font('TestFont')

        provider1.get_font.assert_called_once_with('TestFont')
        provider2.get_font.assert_called_once_with('TestFont')
        assert result is mock_font

    def test_get_font_stops_on_first_match(self):
        """Test that get_font stops after first successful match."""
        mock_font = MagicMock()
        provider1 = MagicMock()
        provider1.get_font.return_value = mock_font

        provider2 = MagicMock()

        chain = ChainedFontProvider([provider1, provider2])
        result = chain.get_font('TestFont')

        provider1.get_font.assert_called_once()
        provider2.get_font.assert_not_called()
        assert result is mock_font

    def test_get_font_returns_none_if_all_fail(self):
        """Test that get_font returns None if all providers fail."""
        provider1 = MagicMock()
        provider1.get_font.return_value = None

        provider2 = MagicMock()
        provider2.get_font.return_value = None

        chain = ChainedFontProvider([provider1, provider2])
        result = chain.get_font('TestFont')

        assert result is None

    def test_get_available_fonts_combines_providers(self):
        """Test that get_available_fonts combines all providers."""
        provider1 = MagicMock()
        provider1.get_available_fonts.return_value = ['Font1', 'Font2']

        provider2 = MagicMock()
        provider2.get_available_fonts.return_value = ['Font2', 'Font3']

        chain = ChainedFontProvider([provider1, provider2])
        fonts = chain.get_available_fonts()

        assert fonts == ['Font1', 'Font2', 'Font3']  # Deduplicated, order preserved

    def test_get_fallback_font_from_first_provider(self):
        """Test that get_fallback_font uses first available fallback."""
        mock_font = MagicMock()
        provider1 = MagicMock()
        provider1.get_fallback_font.return_value = mock_font

        provider2 = MagicMock()

        chain = ChainedFontProvider([provider1, provider2])
        result = chain.get_fallback_font()

        assert result is mock_font
        provider2.get_fallback_font.assert_not_called()

    def test_get_fallback_font_skips_not_implemented(self):
        """Test that get_fallback_font skips providers that raise."""
        provider1 = MagicMock()
        provider1.get_fallback_font.side_effect = NotImplementedError()

        mock_font = MagicMock()
        provider2 = MagicMock()
        provider2.get_fallback_font.return_value = mock_font

        chain = ChainedFontProvider([provider1, provider2])
        result = chain.get_fallback_font()

        assert result is mock_font

    def test_get_fallback_font_raises_if_none_available(self):
        """Test that get_fallback_font raises if no provider has fallback."""
        provider1 = MagicMock()
        provider1.get_fallback_font.side_effect = NotImplementedError()

        provider2 = MagicMock()
        provider2.get_fallback_font.side_effect = KeyError()

        chain = ChainedFontProvider([provider1, provider2])
        with pytest.raises(RuntimeError, match="No fallback font available"):
            chain.get_fallback_font()


class TestChainedFontProviderIntegration:
    """Integration tests with real providers."""

    @pytest.fixture
    def font_dir(self):
        """Return path to font directory."""
        return Path(__file__).parent.parent / "src" / "ocrmypdf" / "data"

    def test_builtin_then_system_chain(self, font_dir):
        """Test chaining BuiltinFontProvider with SystemFontProvider."""
        builtin = BuiltinFontProvider(font_dir)
        system = SystemFontProvider()

        chain = ChainedFontProvider([builtin, system])

        # Should find NotoSans from builtin
        font = chain.get_font('NotoSans-Regular')
        assert font is not None

        # Should get fallback from builtin
        fallback = chain.get_fallback_font()
        assert fallback is not None

    def test_system_fonts_extend_builtin(self, font_dir):
        """Test that system fonts add to builtin fonts."""
        builtin = BuiltinFontProvider(font_dir)
        system = SystemFontProvider()

        chain = ChainedFontProvider([builtin, system])

        builtin_fonts = set(builtin.get_available_fonts())
        chain_fonts = set(chain.get_available_fonts())

        # Chain should have at least as many fonts as builtin
        assert chain_fonts >= builtin_fonts
