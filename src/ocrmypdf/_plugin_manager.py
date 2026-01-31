# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Plugin manager using pluggy with type-safe interface."""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from logging import Handler
from pathlib import Path
from typing import TYPE_CHECKING

import pluggy
from pydantic import BaseModel

import ocrmypdf.builtin_plugins
from ocrmypdf import Executor, PdfContext, pluginspec
from ocrmypdf._options import OcrOptions
from ocrmypdf._progressbar import ProgressBar
from ocrmypdf.helpers import Resolution
from ocrmypdf.pluginspec import OcrEngine

if TYPE_CHECKING:
    from PIL import Image

    from ocrmypdf._jobcontext import PageContext
    from ocrmypdf.pdfinfo import PdfInfo


class OcrmypdfPluginManager:
    """Type-safe wrapper around pluggy.PluginManager.

    Capable of reconstructing itself in child workers via pickle.

    This class provides type-safe methods for all hooks defined in pluginspec.py,
    removing the need for unsafe `hook.method_name()` calls.
    """

    def __init__(
        self,
        *args,
        plugins: Sequence[str | Path],
        builtins: bool = True,
        **kwargs,
    ):
        self._init_args = args
        self._init_kwargs = kwargs
        self._plugins = plugins
        self._builtins = builtins
        self._pm = pluggy.PluginManager(*args, **kwargs)
        self._setup_plugins()

    @property
    def pluggy(self) -> pluggy.PluginManager:
        """Access the underlying pluggy.PluginManager for advanced use cases.

        This is useful for plugins that need to call methods like set_blocked()
        in their initialize hook.
        """
        return self._pm

    def __getstate__(self):
        state = dict(
            init_args=self._init_args,
            plugins=self._plugins,
            builtins=self._builtins,
            init_kwargs=self._init_kwargs,
        )
        return state

    def __setstate__(self, state):
        self.__init__(
            *state['init_args'],
            plugins=state['plugins'],
            builtins=state['builtins'],
            **state['init_kwargs'],
        )

    def _setup_plugins(self):
        self._pm.add_hookspecs(pluginspec)

        # 1. Register builtins
        if self._builtins:
            for module in sorted(
                pkgutil.iter_modules(ocrmypdf.builtin_plugins.__path__)
            ):
                name = f'ocrmypdf.builtin_plugins.{module.name}'
                module = importlib.import_module(name)
                self._pm.register(module)

        # 2. Register setuptools plugins
        self._pm.load_setuptools_entrypoints('ocrmypdf')

        # 3. Register plugins specified on command line
        for name in self._plugins:
            if isinstance(name, Path) or name.endswith('.py'):
                # Import by filename
                module_name = Path(name).stem
                spec = importlib.util.spec_from_file_location(module_name, name)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            else:
                # Import by dotted module name
                module = importlib.import_module(name)
            self._pm.register(module)

    # =========================================================================
    # Type-safe hook methods
    # =========================================================================

    # --- firstresult hooks ---

    def get_logging_console(self) -> Handler | None:
        """Returns a custom logging handler for progress bar compatibility."""
        return self._pm.hook.get_logging_console()

    def get_executor(self, *, progressbar_class: type[ProgressBar]) -> Executor | None:
        """Returns an executor for parallel processing."""
        return self._pm.hook.get_executor(progressbar_class=progressbar_class)

    def get_progressbar_class(self) -> type[ProgressBar] | None:
        """Returns a progress bar class."""
        return self._pm.hook.get_progressbar_class()

    def rasterize_pdf_page(
        self,
        *,
        input_file: Path,
        output_file: Path,
        raster_device: str,
        raster_dpi: Resolution,
        pageno: int,
        page_dpi: Resolution | None,
        rotation: int | None,
        filter_vector: bool,
        stop_on_soft_error: bool,
        options: OcrOptions | None,
        use_cropbox: bool,
    ) -> Path | None:
        """Rasterize one page of a PDF at specified resolution."""
        return self._pm.hook.rasterize_pdf_page(
            input_file=input_file,
            output_file=output_file,
            raster_device=raster_device,
            raster_dpi=raster_dpi,
            pageno=pageno,
            page_dpi=page_dpi,
            rotation=rotation,
            filter_vector=filter_vector,
            stop_on_soft_error=stop_on_soft_error,
            options=options,
            use_cropbox=use_cropbox,
        )

    def filter_ocr_image(
        self, *, page: PageContext, image: Image.Image
    ) -> Image.Image | None:
        """Filter the image before it is sent to OCR."""
        return self._pm.hook.filter_ocr_image(page=page, image=image)

    def filter_page_image(
        self, *, page: PageContext, image_filename: Path
    ) -> Path | None:
        """Filter the whole page image before it is inserted into the PDF."""
        return self._pm.hook.filter_page_image(page=page, image_filename=image_filename)

    def filter_pdf_page(
        self, *, page: PageContext, image_filename: Path, output_pdf: Path
    ) -> Path:
        """Convert a filtered whole page image into a PDF."""
        result = self._pm.hook.filter_pdf_page(
            page=page, image_filename=image_filename, output_pdf=output_pdf
        )
        if result is None:
            raise ValueError('No PDF produced')
        if result != output_pdf:
            raise ValueError('filter_pdf_page must return output_pdf')
        return result

    def get_ocr_engine(self, *, options: OcrOptions | None = None) -> OcrEngine:
        """Returns an OcrEngine to use for processing.

        Args:
            options: OcrOptions to pass to the hook for engine selection.
        """
        result = self._pm.hook.get_ocr_engine(options=options)
        if result is None:
            raise ValueError('No OCR engine selected')
        return result

    def generate_pdfa(
        self,
        *,
        pdf_pages: list[Path],
        pdfmark: Path,
        output_file: Path,
        context: PdfContext,
        pdf_version: str,
        pdfa_part: str,
        progressbar_class: type[ProgressBar] | None,
        stop_on_soft_error: bool,
    ) -> Path | None:
        """Generate a PDF/A file."""
        return self._pm.hook.generate_pdfa(
            pdf_pages=pdf_pages,
            pdfmark=pdfmark,
            output_file=output_file,
            context=context,
            pdf_version=pdf_version,
            pdfa_part=pdfa_part,
            progressbar_class=progressbar_class,
            stop_on_soft_error=stop_on_soft_error,
        )

    def optimize_pdf(
        self,
        *,
        input_pdf: Path,
        output_pdf: Path,
        context: PdfContext,
        executor: Executor,
        linearize: bool,
    ) -> tuple[Path, Sequence[str]]:
        """Optimize a PDF after OCR processing."""
        result = self._pm.hook.optimize_pdf(
            input_pdf=input_pdf,
            output_pdf=output_pdf,
            context=context,
            executor=executor,
            linearize=linearize,
        )
        if result is None:
            return input_pdf, []
        return result

    def is_optimization_enabled(self, *, context: PdfContext) -> bool | None:
        """Returns whether optimization is enabled for given context."""
        return self._pm.hook.is_optimization_enabled(context=context)

    # --- non-firstresult hooks ---

    def initialize(self, *, plugin_manager: pluggy.PluginManager) -> list[None]:
        """Called when plugins are first loaded.

        Args:
            plugin_manager: The underlying pluggy.PluginManager, allowing
                plugins to call methods like set_blocked().
        """
        return self._pm.hook.initialize(plugin_manager=plugin_manager)

    def add_options(self, *, parser: ArgumentParser) -> list[None]:
        """Allows plugins to add command line and API arguments."""
        return self._pm.hook.add_options(parser=parser)

    def register_options(self) -> list[dict[str, type[BaseModel]]]:
        """Returns plugin option models keyed by namespace."""
        return self._pm.hook.register_options()

    def check_options(self, *, options: OcrOptions) -> list[None]:
        """Called to validate options after parsing."""
        return self._pm.hook.check_options(options=options)

    def validate(self, *, pdfinfo: PdfInfo, options: OcrOptions) -> list[None]:
        """Called to validate options and pdfinfo after PDF is loaded."""
        return self._pm.hook.validate(pdfinfo=pdfinfo, options=options)


def get_plugin_manager(
    plugins: Sequence[str | Path] | None = None, builtins=True
) -> OcrmypdfPluginManager:
    return OcrmypdfPluginManager(
        project_name='ocrmypdf',
        plugins=plugins if plugins is not None else [],
        builtins=builtins,
    )


__all__ = ['OcrmypdfPluginManager', 'get_plugin_manager']
