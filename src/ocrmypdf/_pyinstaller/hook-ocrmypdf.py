# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""PyInstaller hook for OCRmyPDF.

Collects OCRmyPDF's submodules, including its builtin plugins, and its data
files: fonts, ICC profiles and other resources that are located at runtime.

pikepdf's data files, needed for PDF/A output, are collected here too, since
pikepdf does not currently ship a hook of its own.
"""

from __future__ import annotations

from PyInstaller.utils.hooks import (  # type: ignore[import-not-found,import-untyped]
    collect_data_files,
    collect_submodules,
)

hiddenimports = collect_submodules(
    'ocrmypdf', filter=lambda name: not name.startswith('ocrmypdf._pyinstaller')
)
datas = collect_data_files('ocrmypdf') + collect_data_files('pikepdf')
