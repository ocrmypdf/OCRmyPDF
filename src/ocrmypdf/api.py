# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Python API for OCRmyPDF.

This module provides the main Python API for OCRmyPDF, allowing you to perform
OCR operations programmatically without using the command line interface.

Main Functions:
    ocr(): The primary function for OCR processing. Takes an input PDF or image
        file and produces an OCR'd PDF with searchable text.

    configure_logging(): Set up logging to match the command line interface
        behavior, with support for progress bars and colored output.

Experimental Functions:
    _pdf_to_hocr(): Extract text from PDF pages and save as hOCR files for
        manual editing before final PDF generation.

    _hocr_to_ocr_pdf(): Convert hOCR files back to a searchable PDF after
        manual text corrections.

The API maintains thread safety through internal locking since OCRmyPDF uses
global state for plugins. Only one OCR operation can run per Python process
at a time. For parallel processing, use multiple Python processes.

Example:
    import ocrmypdf

    # Configure logging (optional)
    ocrmypdf.configure_logging(ocrmypdf.Verbosity.default)

    # Perform OCR
    ocrmypdf.ocr('input.pdf', 'output.pdf', language='eng')

For detailed parameter documentation, see the ocr() function docstring and
the equivalent command line parameters in the OCRmyPDF documentation.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from collections.abc import Iterable, Sequence
from enum import IntEnum
from io import IOBase
from pathlib import Path
from typing import BinaryIO, overload
from warnings import warn

from ocrmypdf._logging import PageNumberFilter
from ocrmypdf._options import OcrOptions
from ocrmypdf._pipelines.hocr_to_ocr_pdf import run_hocr_to_ocr_pdf_pipeline
from ocrmypdf._pipelines.ocr import run_pipeline, run_pipeline_cli
from ocrmypdf._pipelines.pdf_to_hocr import run_hocr_pipeline
from ocrmypdf._plugin_manager import OcrmypdfPluginManager, get_plugin_manager
from ocrmypdf._validation import check_options
from ocrmypdf.cli import ArgumentParser, get_parser
from ocrmypdf.exceptions import ExitCode

StrPath = Path | str | bytes
PathOrIO = BinaryIO | StrPath

# Installing plugins affects the global state of the Python interpreter,
# so we need to use a lock to prevent multiple threads from installing
# plugins at the same time.
_api_lock = threading.Lock()


def setup_plugin_infrastructure(
    plugins: Sequence[Path | str] | None = None,
    plugin_manager: OcrmypdfPluginManager | None = None,
) -> OcrmypdfPluginManager:
    """Set up plugin infrastructure with proper initialization.

    This function handles:
    1. Creating or validating the plugin manager
    2. Calling plugin initialization hooks
    3. Setting up plugin option registry

    Args:
        plugins: List of plugin paths/names to load
        plugin_manager: Existing plugin manager (if any)

    Returns:
        Properly initialized plugin manager

    Raises:
        ValueError: If both plugins and plugin_manager are provided
    """
    if plugins and plugin_manager:
        raise ValueError("plugins= and plugin_manager are mutually exclusive")

    if not plugins:
        plugins = []
    elif isinstance(plugins, str | Path):
        plugins = [plugins]
    else:
        plugins = list(plugins)

    # Create plugin manager if not provided
    if not plugin_manager:
        plugin_manager = get_plugin_manager(plugins)

    # Initialize plugins (pass the underlying pluggy manager)
    plugin_manager.initialize(plugin_manager=plugin_manager.pluggy)

    # Initialize plugin option registry
    from ocrmypdf._plugin_registry import PluginOptionRegistry

    registry = PluginOptionRegistry()

    # Let plugins register their option models
    option_models = plugin_manager.register_options()
    all_plugin_models: dict[str, type] = {}
    for plugin_options in option_models:
        if plugin_options:  # Skip None returns
            for namespace, model_class in plugin_options.items():
                registry.register_option_model(namespace, model_class)
                all_plugin_models[namespace] = model_class

    # Register plugin models with OcrOptions for dynamic nested access
    OcrOptions.register_plugin_models(all_plugin_models)

    # Store registry in plugin manager for later access
    plugin_manager._option_registry = registry

    return plugin_manager


class Verbosity(IntEnum):
    """Verbosity level for configure_logging."""

    # pylint: disable=invalid-name
    quiet = -1  #: Suppress most messages
    default = 0  #: Default level of logging
    debug = 1  #: Output ocrmypdf debug messages
    debug_all = 2  #: More detailed debugging from ocrmypdf and dependent modules


def configure_logging(
    verbosity: Verbosity,
    *,
    progress_bar_friendly: bool = True,
    manage_root_logger: bool = False,
    plugin_manager: OcrmypdfPluginManager | None = None,
):
    """Set up logging.

    Before calling :func:`ocrmypdf.ocr()`, you can use this function to
    configure logging if you want ocrmypdf's output to look like the ocrmypdf
    command line interface. It will register log handlers, log filters, and
    formatters, configure color logging to standard error, and adjust the log
    levels of third party libraries. Details of this are fine-tuned and subject
    to change. The ``verbosity`` argument is equivalent to the argument
    ``--verbose`` and applies those settings. If you have a wrapper
    script for ocrmypdf and you want it to be very similar to ocrmypdf, use this
    function; if you are using ocrmypdf as part of an application that manages
    its own logging, you probably do not want this function.

    If this function is not called, ocrmypdf will not configure logging, and it
    is up to the caller of ``ocrmypdf.ocr()`` to set up logging as it wishes using
    the Python standard library's logging module. If this function is called,
    the caller may of course make further adjustments to logging.

    Regardless of whether this function is called, ocrmypdf will perform all of
    its logging under the ``"ocrmypdf"`` logging namespace. In addition,
    ocrmypdf imports pdfminer, which logs under ``"pdfminer"``. A library user
    may wish to configure both; note that pdfminer is extremely chatty at the
    log level ``logging.INFO``.

    This function does not set up the ``debug.log`` log file that the command
    line interface does at certain verbosity levels. Applications should configure
    their own debug logging.

    Args:
        verbosity: Verbosity level.
        progress_bar_friendly: If True (the default), install a custom log handler
            that is compatible with progress bars and colored output.
        manage_root_logger: Configure the process's root logger.
        plugin_manager: The plugin manager, used for obtaining the custom log handler.

    Returns:
        The toplevel logger for ocrmypdf (or the root logger, if we are managing it).
    """
    prefix = '' if manage_root_logger else 'ocrmypdf'

    log = logging.getLogger(prefix)
    log.setLevel(logging.DEBUG)

    console = None
    if plugin_manager and progress_bar_friendly:
        console = plugin_manager.get_logging_console()

    if not console:
        console = logging.StreamHandler(stream=sys.stderr)

    if verbosity < 0:
        console.setLevel(logging.ERROR)
    elif verbosity >= 1:
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.INFO)

    console.addFilter(PageNumberFilter())

    if verbosity >= 2:
        fmt = '%(levelname)7s %(name)s -%(pageno)s %(message)s'
    else:
        fmt = '%(pageno)s%(message)s'

    formatter = None

    if not formatter:
        formatter = logging.Formatter(fmt=fmt)

    console.setFormatter(formatter)
    log.addHandler(console)

    if verbosity <= 1:
        pdfminer_log = logging.getLogger('pdfminer')
        pdfminer_log.setLevel(logging.ERROR)
        pil_log = logging.getLogger('PIL')
        pil_log.setLevel(logging.INFO)
        fonttools_log = logging.getLogger('fontTools')
        fonttools_log.setLevel(logging.ERROR)

    if manage_root_logger:
        logging.captureWarnings(True)

    return log


def _check_no_conflicting_ocr_params(
    locals_dict: dict,
    kwargs: dict,
    excluded: set[str] | None = None,
) -> None:
    """Check that no individual OCR parameters conflict with OcrOptions.

    When a user passes an OcrOptions object, they should not also pass
    individual OCR parameters (except plugins/plugin_manager which are
    handled separately).

    Args:
        locals_dict: The locals() dict from the calling function.
        kwargs: The **kwargs dict from the calling function.
        excluded: Parameter names to exclude from conflict checking.

    Raises:
        ValueError: If conflicting parameters are found.
    """
    if excluded is None:
        excluded = set()

    # Parameters that are allowed alongside OcrOptions
    allowed_with_options = {
        'input_file_or_options',
        'options',  # The OcrOptions object itself after assignment
        'plugins',
        'plugin_manager',
        'kwargs',
    } | excluded

    # Check all locals that are OCR parameters (not None and not allowed)
    conflicts = [
        name
        for name, value in locals_dict.items()
        if value is not None and name not in allowed_with_options
    ]

    # Check kwargs
    conflicts.extend(kwargs.keys())

    if conflicts:
        raise ValueError(
            f"When passing OcrOptions as the first argument, do not pass "
            f"additional OCR parameters. Conflicting parameters: "
            f"{', '.join(sorted(conflicts))}. "
            f"Set these values in OcrOptions instead."
        )


def create_options(
    *, input_file: PathOrIO, output_file: PathOrIO, parser: ArgumentParser, **kwargs
) -> OcrOptions:
    """Construct an options object from the input/output files and keyword arguments.

    Args:
        input_file: Input file path or file object.
        output_file: Output file path or file object.
        parser: ArgumentParser object (kept for compatibility,
            may be used for plugin validation).
        **kwargs: Keyword arguments.

    Returns:
        OcrOptions: An options object containing the parsed arguments.

    Raises:
        TypeError: If the type of a keyword argument is not supported.
    """
    # Prepare kwargs for direct OcrOptions construction
    options_kwargs = kwargs.copy()

    # Set input and output files
    options_kwargs['input_file'] = input_file
    options_kwargs['output_file'] = output_file

    # Handle special stream cases for sidecar
    if 'sidecar' in options_kwargs and isinstance(
        options_kwargs['sidecar'], BinaryIO | IOBase
    ):
        # Keep the stream object as-is - OcrOptions can handle it
        pass

    # Remove None values to let OcrOptions use its defaults
    options_kwargs = {k: v for k, v in options_kwargs.items() if v is not None}

    # Remove any kwargs that aren't OcrOptions fields and store in extra_attrs
    extra_attrs = {}
    ocr_fields = set(OcrOptions.model_fields.keys())
    # Legacy mode flags are handled by OcrOptions model validator
    legacy_mode_flags = {'force_ocr', 'skip_text', 'redo_ocr'}

    # Known extra attributes that should be preserved
    known_extra = {'progress_bar', 'plugins'}

    for key in list(options_kwargs.keys()):
        if key in ocr_fields or key in legacy_mode_flags or key in known_extra:
            continue
        extra_attrs[key] = options_kwargs.pop(key)

    # Create OcrOptions directly
    try:
        options = OcrOptions(**options_kwargs)
        # Add any extra attributes
        if extra_attrs:
            options.extra_attrs.update(extra_attrs)
        return options
    except Exception as e:
        # If direct construction fails, provide a helpful error message
        raise TypeError(f"Failed to create OcrOptions: {e}") from e


@overload
def ocr(
    options: OcrOptions,
    /,
    *,
    plugins: Iterable[Path | str] | None = None,
    plugin_manager: OcrmypdfPluginManager | None = None,
) -> ExitCode: ...


@overload
def ocr(
    input_file_or_options: PathOrIO,
    output_file: PathOrIO,
    *,
    language: Iterable[str] | None = None,
    image_dpi: int | None = None,
    output_type: str | None = None,
    sidecar: PathOrIO | None = None,
    jobs: int | None = None,
    use_threads: bool | None = None,
    title: str | None = None,
    author: str | None = None,
    subject: str | None = None,
    keywords: str | None = None,
    rotate_pages: bool | None = None,
    remove_background: bool | None = None,
    deskew: bool | None = None,
    clean: bool | None = None,
    clean_final: bool | None = None,
    unpaper_args: str | None = None,
    oversample: int | None = None,
    remove_vectors: bool | None = None,
    mode: str | None = None,
    force_ocr: bool | None = None,
    skip_text: bool | None = None,
    redo_ocr: bool | None = None,
    skip_big: float | None = None,
    optimize: int | None = None,
    jpg_quality: int | None = None,
    png_quality: int | None = None,
    jbig2_lossy: bool | None = None,
    jbig2_page_group_size: int | None = None,
    jbig2_threshold: float | None = None,
    pages: str | None = None,
    max_image_mpixels: float | None = None,
    tesseract_config: Iterable[str] | None = None,
    tesseract_pagesegmode: int | None = None,
    tesseract_oem: int | None = None,
    tesseract_thresholding: int | None = None,
    pdf_renderer: str | None = None,
    rasterizer: str | None = None,
    tesseract_timeout: float | None = None,
    tesseract_non_ocr_timeout: float | None = None,
    tesseract_downsample_above: int | None = None,
    tesseract_downsample_large_images: bool | None = None,
    rotate_pages_threshold: float | None = None,
    pdfa_image_compression: str | None = None,
    color_conversion_strategy: str | None = None,
    user_words: os.PathLike | None = None,
    user_patterns: os.PathLike | None = None,
    fast_web_view: float | None = None,
    continue_on_soft_render_error: bool | None = None,
    invalidate_digital_signatures: bool | None = None,
    plugins: Iterable[Path | str] | None = None,
    plugin_manager: OcrmypdfPluginManager | None = None,
    keep_temporary_files: bool | None = None,
    progress_bar: bool | None = None,
    **kwargs,
) -> ExitCode: ...


def ocr(  # noqa: D417
    input_file_or_options: PathOrIO | OcrOptions,
    output_file: PathOrIO | None = None,
    *,
    language: Iterable[str] | None = None,
    image_dpi: int | None = None,
    output_type: str | None = None,
    sidecar: PathOrIO | None = None,
    jobs: int | None = None,
    use_threads: bool | None = None,
    title: str | None = None,
    author: str | None = None,
    subject: str | None = None,
    keywords: str | None = None,
    rotate_pages: bool | None = None,
    remove_background: bool | None = None,
    deskew: bool | None = None,
    clean: bool | None = None,
    clean_final: bool | None = None,
    unpaper_args: str | None = None,
    oversample: int | None = None,
    remove_vectors: bool | None = None,
    mode: str | None = None,
    force_ocr: bool | None = None,  # Legacy, use mode='force' instead
    skip_text: bool | None = None,  # Legacy, use mode='skip' instead
    redo_ocr: bool | None = None,  # Legacy, use mode='redo' instead
    skip_big: float | None = None,
    optimize: int | None = None,
    jpg_quality: int | None = None,
    png_quality: int | None = None,
    jbig2_lossy: bool | None = None,  # Deprecated, ignored
    jbig2_page_group_size: int | None = None,  # Deprecated, ignored
    jbig2_threshold: float | None = None,
    pages: str | None = None,
    max_image_mpixels: float | None = None,
    tesseract_config: Iterable[str] | None = None,
    tesseract_pagesegmode: int | None = None,
    tesseract_oem: int | None = None,
    tesseract_thresholding: int | None = None,
    pdf_renderer: str | None = None,
    rasterizer: str | None = None,
    tesseract_timeout: float | None = None,
    tesseract_non_ocr_timeout: float | None = None,
    tesseract_downsample_above: int | None = None,
    tesseract_downsample_large_images: bool | None = None,
    rotate_pages_threshold: float | None = None,
    pdfa_image_compression: str | None = None,
    color_conversion_strategy: str | None = None,
    user_words: os.PathLike | None = None,
    user_patterns: os.PathLike | None = None,
    fast_web_view: float | None = None,
    continue_on_soft_render_error: bool | None = None,
    invalidate_digital_signatures: bool | None = None,
    plugins: Iterable[Path | str] | None = None,
    plugin_manager: OcrmypdfPluginManager | None = None,
    keep_temporary_files: bool | None = None,
    progress_bar: bool | None = None,
    **kwargs,
) -> ExitCode:
    """Run OCRmyPDF on one PDF or image.

    This function supports two calling conventions:

    **New style (recommended):**
        >>> from ocrmypdf import ocr
        >>> from ocrmypdf._options import OcrOptions
        >>> options = OcrOptions(
        ...     input_file="input.pdf",
        ...     output_file="output.pdf",
        ...     languages=["eng"],
        ... )
        >>> ocr(options)

    **Old style:**
        >>> ocr("input.pdf", "output.pdf", language=["eng"])

    For most arguments, see documentation for the equivalent command line parameter.

    This API takes a threading lock, because OCRmyPDF uses global state in particular
    for the plugin system. The jobs parameter will be used to create a pool of
    worker threads or processes at different times, subject to change. A Python
    process can only run one OCRmyPDF task at a time.

    To run parallelize instances OCRmyPDF, use separate Python processes to scale
    horizontally. Generally speaking you should set jobs=sqrt(cpu_count) and run
    sqrt(cpu_count) processes as a starting point. If you have files with a high page
    count, run fewer processes and more jobs per process. If you have a lot of short
    files, run more processes and fewer jobs per process.

    A few specific arguments are discussed here:

    Args:
        input_file_or_options: Either an OcrOptions object containing all settings,
            or a path/stream for the input file (old-style API).
        output_file: Output file path or stream. Required when using old-style API
            with input_file as first argument. Must be None when passing OcrOptions.
        use_threads: Use worker threads instead of processes. This reduces
            performance but may make debugging easier since it is easier to set
            breakpoints.
        plugins: List of plugin paths to load. Can be passed alongside OcrOptions.
        plugin_manager: Pre-configured plugin manager. Can be passed alongside
            OcrOptions.

        For input_file (old-style API): If a :class:`pathlib.Path`, ``str`` or
            ``bytes``, this is interpreted as file system path to the input file.
            If the object appears to be a readable stream (with methods such as
            ``.read()`` and ``.seek()``), the object will be read in its entirety
            and saved to a temporary file. If ``input_file`` is ``"-"``, standard
            input will be read.

        For output_file (old-style API): If a :class:`pathlib.Path`, ``str`` or
            ``bytes``, this is interpreted as file system path to the output file.
            If the object appears to be a writable stream (with methods such as
            ``.write()`` and ``.seek()``), the output will be written to this
            stream. If ``output_file`` is ``"-"``, the output will be written to
            ``sys.stdout`` (provided that standard output does not seem to be a
            terminal device). When a stream is used as output, whether via a
            writable object or ``"-"``, some final validation steps are not
            performed (we do not read back the stream after it is written).

    Raises:
        ocrmypdf.MissingDependencyError: If a required dependency program is missing or
            was not found on PATH.
        ocrmypdf.UnsupportedImageFormatError: If the input file type was an image that
            could not be read, or some other file type that is not a PDF.
        ocrmypdf.DpiError: If the input file is an image, but the resolution of the
            image is not credible (allowing it to proceed would cause poor OCR).
        ocrmypdf.OutputFileAccessError: If an attempt to write to the intended output
            file failed.
        ocrmypdf.PriorOcrFoundError: If the input PDF seems to have OCR or digital
            text already, and settings did not tell us to proceed.
        ocrmypdf.InputFileError: Any other problem with the input file.
        ocrmypdf.SubprocessOutputError: Any error related to executing a subprocess.
        ocrmypdf.EncryptedPdfError: If the input PDF is encrypted (password protected).
            OCRmyPDF does not remove passwords.
        ocrmypdf.TesseractConfigError: If Tesseract reported its configuration was not
            valid.
        ValueError: If OcrOptions is passed along with other OCR parameters, or if
            both plugins and plugin_manager are provided.
        TypeError: If output_file is missing when using the old-style API.

    Returns:
        :class:`ocrmypdf.ExitCode`
    """
    # Detect calling convention: OcrOptions object vs individual parameters
    if isinstance(input_file_or_options, OcrOptions):
        # New-style API: OcrOptions passed directly
        options = input_file_or_options

        # Check for conflicting parameters
        # (all should be None except plugins/plugin_manager)
        _check_no_conflicting_ocr_params(locals(), kwargs)

        # plugins and plugin_manager can still be passed alongside OcrOptions
        if plugins and plugin_manager:
            raise ValueError("plugins= and plugin_manager are mutually exclusive")

        # Use plugins from OcrOptions if not explicitly passed
        if plugins is None:
            plugins = options.plugins or []

        if isinstance(plugins, str | Path):
            plugins = [plugins]
        else:
            plugins = list(plugins) if plugins else []

        # Run the pipeline with the OcrOptions
        with _api_lock:
            plugin_manager = setup_plugin_infrastructure(
                plugins=plugins, plugin_manager=plugin_manager
            )

            parser = get_parser()
            plugin_manager.add_options(parser=parser)

            check_options(options, plugin_manager)
            return run_pipeline(options=options, plugin_manager=plugin_manager)

    else:
        # Old-style API: positional arguments
        input_file = input_file_or_options

        if output_file is None:
            raise TypeError(
                "ocr() missing required argument: 'output_file'. "
                "Either pass output_file as the second argument, or pass "
                "an OcrOptions object as the first argument."
            )

        if plugins and plugin_manager:
            raise ValueError("plugins= and plugin_manager are mutually exclusive")

        if not plugins:
            plugins = []
        elif isinstance(plugins, str | Path):
            plugins = [plugins]
        else:
            plugins = list(plugins)

        # No new variable names should be assigned until these two steps are run
        create_options_kwargs = {
            k: v
            for k, v in locals().items()
            if k
            not in {
                'input_file_or_options',
                'input_file',
                'output_file',
                'kwargs',
                'plugin_manager',
            }
        }
        create_options_kwargs.update(kwargs)

        parser = get_parser()
        with _api_lock:
            # Set up plugin infrastructure with proper initialization
            plugin_manager = setup_plugin_infrastructure(
                plugins=plugins, plugin_manager=plugin_manager
            )

            # Get parser and let plugins add their options
            parser = get_parser()
            plugin_manager.add_options(parser=parser)

            if 'verbose' in kwargs:
                warn(
                    "ocrmypdf.ocr(verbose=) is ignored. "
                    "Use ocrmypdf.configure_logging()."
                )

            # Warn about deprecated jbig2 options and remove from kwargs
            if jbig2_lossy:
                warn(
                    "jbig2_lossy is deprecated and will be ignored. "
                    "Lossy JBIG2 has been removed due to character substitution risks."
                )
                create_options_kwargs.pop('jbig2_lossy', None)
            if jbig2_page_group_size:
                warn("jbig2_page_group_size is deprecated and will be ignored.")
                create_options_kwargs.pop('jbig2_page_group_size', None)

            options = create_options(
                input_file=input_file,
                output_file=output_file,
                parser=parser,
                **create_options_kwargs,
            )
            check_options(options, plugin_manager)
            return run_pipeline(options=options, plugin_manager=plugin_manager)


def _pdf_to_hocr(  # noqa: D417
    input_pdf: Path,
    output_folder: Path,
    *,
    language: Iterable[str] | None = None,
    image_dpi: int | None = None,
    jobs: int | None = None,
    use_threads: bool | None = None,
    title: str | None = None,
    author: str | None = None,
    subject: str | None = None,
    keywords: str | None = None,
    rotate_pages: bool | None = None,
    remove_background: bool | None = None,
    deskew: bool | None = None,
    clean: bool | None = None,
    clean_final: bool | None = None,
    unpaper_args: str | None = None,
    oversample: int | None = None,
    remove_vectors: bool | None = None,
    mode: str | None = None,
    force_ocr: bool | None = None,  # Legacy, use mode='force' instead
    skip_text: bool | None = None,  # Legacy, use mode='skip' instead
    redo_ocr: bool | None = None,  # Legacy, use mode='redo' instead
    skip_big: float | None = None,
    pages: str | None = None,
    max_image_mpixels: float | None = None,
    tesseract_config: Iterable[str] | None = None,
    tesseract_pagesegmode: int | None = None,
    tesseract_oem: int | None = None,
    tesseract_thresholding: int | None = None,
    tesseract_timeout: float | None = None,
    tesseract_non_ocr_timeout: float | None = None,
    tesseract_downsample_above: int | None = None,
    tesseract_downsample_large_images: bool | None = None,
    rotate_pages_threshold: float | None = None,
    rasterizer: str | None = None,
    user_words: os.PathLike | None = None,
    user_patterns: os.PathLike | None = None,
    continue_on_soft_render_error: bool | None = None,
    invalidate_digital_signatures: bool | None = None,
    plugin_manager=None,
    plugins: Sequence[Path | str] | None = None,
    keep_temporary_files: bool | None = None,
    **kwargs,
):
    """Partially run OCRmyPDF and produces an output folder containing hOCR files.

    Given a PDF file, this function will run OCRmyPDF up to the point where
    the PDF is rasterized to images, OCRed, and the hOCR files are produced,
    all of which are saved to the output folder. This is useful for applications
    that want to provide an interface for users to edit the text before
    rendering the final PDF.

    Use :func:`hocr_to_ocr_pdf` to produce the final PDF.

    For arguments not explicitly documented here, see documentation for the
    equivalent command line parameter.

    This API is **experimental** and subject to change.

    Args:
        input_pdf: Input PDF file path.
        output_folder: Output folder path.
        **kwargs: Keyword arguments.
    """
    if plugins and plugin_manager:
        raise ValueError("plugins= and plugin_manager are mutually exclusive")

    if not plugins:
        plugins = []
    elif isinstance(plugins, str | Path):
        plugins = [plugins]
    else:
        plugins = list(plugins)

    # Prepare kwargs for direct OcrOptions construction
    options_kwargs = kwargs.copy()

    # Set input file and handle special output_folder case
    options_kwargs['input_file'] = input_pdf
    options_kwargs['output_file'] = '/dev/null'  # Placeholder for hOCR pipeline

    # Add all the function parameters
    for param_name, param_value in locals().items():
        if (
            param_name
            not in {'input_pdf', 'output_folder', 'kwargs', 'plugin_manager', 'plugins'}
            and param_value is not None
        ):
            options_kwargs[param_name] = param_value

    # Handle plugins
    if plugins:
        options_kwargs['plugins'] = plugins

    # Remove None values to let OcrOptions use its defaults
    options_kwargs = {k: v for k, v in options_kwargs.items() if v is not None}

    # Add output_folder to options_kwargs since it's now a proper field
    options_kwargs['output_folder'] = output_folder

    # Remove any kwargs that aren't OcrOptions fields and store in extra_attrs
    extra_attrs = {}
    ocr_fields = set(OcrOptions.model_fields.keys())
    # Legacy mode flags are handled by OcrOptions model validator
    legacy_mode_flags = {'force_ocr', 'skip_text', 'redo_ocr'}
    known_extra = {'progress_bar', 'plugins'}

    for key in list(options_kwargs.keys()):
        if key in ocr_fields or key in legacy_mode_flags or key in known_extra:
            continue
        extra_attrs[key] = options_kwargs.pop(key)

    with _api_lock:
        # Set up plugin infrastructure with proper initialization
        plugin_manager = setup_plugin_infrastructure(
            plugins=plugins, plugin_manager=plugin_manager
        )

        plugin_manager.add_options(parser=get_parser())

        # Create OcrOptions directly
        try:
            options = OcrOptions(**options_kwargs)
            # Add any extra attributes
            if extra_attrs:
                options.extra_attrs.update(extra_attrs)
        except Exception as e:
            raise TypeError(
                f"Failed to create OcrOptions for hOCR pipeline: {e}"
            ) from e

        return run_hocr_pipeline(options=options, plugin_manager=plugin_manager)


def _hocr_to_ocr_pdf(  # noqa: D417
    work_folder: Path,
    output_file: Path,
    *,
    jobs: int | None = None,
    use_threads: bool | None = None,
    optimize: int | None = None,
    jpg_quality: int | None = None,
    png_quality: int | None = None,
    jbig2_lossy: bool | None = None,  # Deprecated, ignored
    jbig2_page_group_size: int | None = None,  # Deprecated, ignored
    jbig2_threshold: float | None = None,
    pdfa_image_compression: str | None = None,
    color_conversion_strategy: str | None = None,
    fast_web_view: float | None = None,
    plugin_manager=None,
    plugins: Sequence[Path | str] | None = None,
    **kwargs,
):
    """Run OCRmyPDF on a work folder and produce an output PDF.

    After running :func:`pdf_to_hocr`, this function will run OCRmyPDF on the work
    folder to produce an output PDF. This function consolidates any changes made
    to the hOCR files in the work folder and produces a final PDF.

    For arguments not explicitly documented here, see documentation for the
    equivalent command line parameter.

    This API is **experimental** and subject to change.

    Args:
        work_folder: Work folder path, as generated by :func:`pdf_to_hocr`.
        output_file: Output PDF file path.
        **kwargs: Keyword arguments.
    """
    if plugins and plugin_manager:
        raise ValueError("plugins= and plugin_manager are mutually exclusive")

    if not plugins:
        plugins = []
    elif isinstance(plugins, str | Path):
        plugins = [plugins]
    else:
        plugins = list(plugins)

    # Prepare kwargs for direct OcrOptions construction
    options_kwargs = kwargs.copy()

    # Set output file and handle special work_folder case
    options_kwargs['input_file'] = '/dev/null'  # Placeholder for hOCR to PDF pipeline
    options_kwargs['output_file'] = output_file

    # Add all the function parameters
    for param_name, param_value in locals().items():
        if (
            param_name
            not in {'work_folder', 'output_file', 'kwargs', 'plugin_manager', 'plugins'}
            and param_value is not None
        ):
            options_kwargs[param_name] = param_value

    # Handle plugins
    if plugins:
        options_kwargs['plugins'] = plugins

    # Remove None values to let OcrOptions use its defaults
    options_kwargs = {k: v for k, v in options_kwargs.items() if v is not None}

    # Warn about deprecated jbig2 options and remove from kwargs
    if jbig2_lossy:
        warn(
            "jbig2_lossy is deprecated and will be ignored. "
            "Lossy JBIG2 has been removed due to character substitution risks."
        )
        options_kwargs.pop('jbig2_lossy', None)
    if jbig2_page_group_size:
        warn("jbig2_page_group_size is deprecated and will be ignored.")
        options_kwargs.pop('jbig2_page_group_size', None)

    # Add work_folder to options_kwargs since it's now a proper field
    options_kwargs['work_folder'] = work_folder

    # Remove any kwargs that aren't OcrOptions fields and store in extra_attrs
    extra_attrs = {}
    ocr_fields = set(OcrOptions.model_fields.keys())
    # Legacy mode flags are handled by OcrOptions model validator
    legacy_mode_flags = {'force_ocr', 'skip_text', 'redo_ocr'}
    known_extra = {'progress_bar', 'plugins'}

    for key in list(options_kwargs.keys()):
        if key in ocr_fields or key in legacy_mode_flags or key in known_extra:
            continue
        extra_attrs[key] = options_kwargs.pop(key)

    with _api_lock:
        # Set up plugin infrastructure with proper initialization
        plugin_manager = setup_plugin_infrastructure(
            plugins=plugins, plugin_manager=plugin_manager
        )

        plugin_manager.add_options(parser=get_parser())

        # Create OcrOptions directly
        try:
            options = OcrOptions(**options_kwargs)
            # Add any extra attributes
            if extra_attrs:
                options.extra_attrs.update(extra_attrs)
        except Exception as e:
            raise TypeError(
                f"Failed to create OcrOptions for hOCR to PDF pipeline: {e}"
            ) from e

        return run_hocr_to_ocr_pdf_pipeline(
            options=options, plugin_manager=plugin_manager
        )


__all__ = [
    'PageNumberFilter',
    'Verbosity',
    'check_options',
    'configure_logging',
    'create_options',
    'get_parser',
    'get_plugin_manager',
    'ocr',
    'run_pipeline',
    'run_pipeline_cli',
    'setup_plugin_infrastructure',
]
