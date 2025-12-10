# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Defines context objects that are passed to child processes/threads."""

from __future__ import annotations

import os
from collections.abc import Iterator
from copy import copy
from argparse import Namespace
from pathlib import Path
from typing import Union

from pluggy import PluginManager

from ocrmypdf._options import OCROptions
from ocrmypdf.pdfinfo import PdfInfo
from ocrmypdf.pdfinfo.info import PageInfo


class PdfContext:
    """Holds the context for a particular run of the pipeline."""

    options: OCROptions  #: The specified options for processing this PDF.
    origin: Path  #: The filename of the original input file.
    pdfinfo: PdfInfo  #: Detailed data for this PDF.
    plugin_manager: PluginManager  #: PluginManager for processing the current PDF.

    def __init__(
        self,
        options: Union[OCROptions, Namespace],
        work_folder: Path,
        origin: Path,
        pdfinfo: PdfInfo,
        plugin_manager,
    ):
        # Handle both OCROptions and Namespace during transition
        if isinstance(options, OCROptions):
            self.options = options
        else:
            # Convert Namespace to OCROptions
            self.options = OCROptions.from_namespace(options)
        
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
    
    Note: Uses OCROptions with JSON serialization for multiprocessing compatibility.
    """

    origin: Path  #: The filename of the original input file.
    pageno: int  #: This page number (zero-based).
    pageinfo: PageInfo  #: Information on this page.
    plugin_manager: PluginManager  #: PluginManager for processing the current PDF.

    def __init__(self, pdf_context: PdfContext, pageno):
        self.work_folder = pdf_context.work_folder
        self.origin = pdf_context.origin
        # Store OCROptions directly instead of Namespace
        self.options = pdf_context.options
        self.pageno = pageno
        self.pageinfo = pdf_context.pdfinfo[pageno]
        self.plugin_manager = pdf_context.plugin_manager
        # Ensure no reference to PdfContext which contains OCROptions
        self._pdf_context = None

    def get_path(self, name: str) -> Path:
        """Generate a ``Path`` for a file that is part of processing this page.

        The path will be based in a common temporary folder and have a prefix based
        on the page number.
        """
        return self.work_folder / f"{(self.pageno + 1):06d}_{name}"

    def __getstate__(self):
        state = self.__dict__.copy()

        # Use JSON serialization instead of Namespace
        try:
            options_json = self.options.model_dump_json_safe()
            state['options_json'] = options_json
            # Remove the OCROptions object to avoid pickle issues
            del state['options']
        except Exception:
            # Fallback: if JSON serialization fails, convert to namespace
            # This shouldn't happen but provides safety
            from argparse import Namespace
            import os

            clean_options = Namespace()
            for key, value in vars(self.options.to_namespace()).items():
                if key.startswith('_'):
                    continue
                try:
                    import pickle
                    pickle.dumps(value)
                    setattr(clean_options, key, value)
                except TypeError:
                    continue
            state['options'] = clean_options

        # Remove any potential references to Pydantic objects
        state.pop('_pdf_context', None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        
        # Reconstruct OCROptions from JSON if available
        if 'options_json' in state:
            from ocrmypdf._options import OCROptions
            self.options = OCROptions.model_validate_json_safe(state['options_json'])
        # Otherwise, we have a fallback Namespace (shouldn't happen in normal operation)
        # Leave it as-is for compatibility
