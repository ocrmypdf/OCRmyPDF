# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Defines context objects that are passed to child processes/threads."""

from __future__ import annotations

import os
from argparse import Namespace
from collections.abc import Iterator
from copy import copy
from pathlib import Path

from pluggy import PluginManager

from ocrmypdf.pdfinfo import PdfInfo
from ocrmypdf.pdfinfo.info import PageInfo


class PdfContext:
    """Holds the context for a particular run of the pipeline."""

    options: Namespace  #: The specified options for processing this PDF.
    origin: Path  #: The filename of the original input file.
    pdfinfo: PdfInfo  #: Detailed data for this PDF.
    plugin_manager: PluginManager  #: PluginManager for processing the current PDF.

    def __init__(
        self,
        options: Namespace,
        work_folder: Path,
        origin: Path,
        pdfinfo: PdfInfo,
        plugin_manager,
    ):
        self.options = options
        self.work_folder = work_folder
        self.origin = origin
        self.pdfinfo = pdfinfo
        self.plugin_manager = plugin_manager

    def get_path(self, name: str) -> Path:
        """Generate a ``Path`` for an intermediate file involved in processing.

        The path will be in a temporary folder that is common for all processing
        of this particular PDF.
        """
        return self.work_folder / name

    def get_page_contexts(self) -> Iterator[PageContext]:
        """Get all ``PageContext`` for this PDF."""
        npages = len(self.pdfinfo)
        for n in range(npages):
            yield PageContext(self, n)

    def get_page_context_args(self) -> Iterator[tuple[PageContext]]:
        """Get all ``PageContext`` for this PDF packaged in tuple for args-splatting."""
        npages = len(self.pdfinfo)
        for n in range(npages):
            yield (PageContext(self, n),)


class PageContext:
    """Holds our context for a page.

    Must be pickle-able, so stores only intrinsic/simple data elements or those
    capable of their serializing themselves via ``__getstate__``.
    """

    options: Namespace  #: The specified options for processing this PDF.
    origin: Path  #: The filename of the original input file.
    pageno: int  #: This page number (zero-based).
    pageinfo: PageInfo  #: Information on this page.
    plugin_manager: PluginManager  #: PluginManager for processing the current PDF.

    def __init__(self, pdf_context: PdfContext, pageno):
        self.work_folder = pdf_context.work_folder
        self.origin = pdf_context.origin
        self.options = pdf_context.options
        self.pageno = pageno
        self.pageinfo = pdf_context.pdfinfo[pageno]
        self.plugin_manager = pdf_context.plugin_manager

    def get_path(self, name: str) -> Path:
        """Generate a ``Path`` for a file that is part of processing this page.

        The path will be based in a common temporary folder and have a prefix based
        on the page number.
        """
        return self.work_folder / f"{(self.pageno + 1):06d}_{name}"

    def __getstate__(self):
        state = self.__dict__.copy()

        state['options'] = copy(self.options)
        if not isinstance(state['options'].input_file, str | bytes | os.PathLike):
            state['options'].input_file = 'stream'
        if not isinstance(state['options'].output_file, str | bytes | os.PathLike):
            state['options'].output_file = 'stream'
        return state
