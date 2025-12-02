# SPDX-License-Identifier: MPL-2.0

"""Interface to RapidOCR."""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

try:
    from rapidocr_onnxruntime import RapidOCR, __version__

    RAPIDOCR_AVAILABLE = True
except ImportError:
    RAPIDOCR_AVAILABLE = False
    __version__ = 'not installed'


class RapidOcrLoggerAdapter(logging.LoggerAdapter):
    """Prepend [rapidocr] to messages emitted from RapidOCR."""

    def process(self, msg, kwargs):
        kwargs['extra'] = self.extra
        return f'[rapidocr] {msg}', kwargs


def version() -> str:
    """Return RapidOCR version."""
    if RAPIDOCR_AVAILABLE:
        return __version__
    return 'not installed'


def is_available() -> bool:
    """Check if RapidOCR is available."""
    return RAPIDOCR_AVAILABLE


def get_languages() -> set[str]:
    """Return list of supported languages.

    RapidOCR doesn't work with ISO language codes like Tesseract.
    This is a mapping of supported languages.
    """
    if not RAPIDOCR_AVAILABLE:
        return set()

    # Basic language support by RapidOCR
    return {'chi_sim', 'chi_tra', 'eng', 'fre', 'ger', 'kor', 'jpn'}
