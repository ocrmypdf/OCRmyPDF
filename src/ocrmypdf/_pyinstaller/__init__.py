# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""PyInstaller hook registration.

PyInstaller finds this module through the ``pyinstaller40`` entry point. It is
not imported by OCRmyPDF itself, and PyInstaller is not a dependency.
"""

from __future__ import annotations

from pathlib import Path


def get_hook_dirs() -> list[str]:
    """Return the directories containing OCRmyPDF's PyInstaller hooks."""
    return [str(Path(__file__).parent)]
