# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Functions for using ocrmypdf as an API."""

from __future__ import annotations

import logging
import os
import sys
import threading
from argparse import Namespace
from collections.abc import Iterable, Sequence
from enum import IntEnum
from io import IOBase
from pathlib import Path
from typing import AnyStr, BinaryIO
from warnings import warn

import pluggy

from ocrmypdf._logging import PageNumberFilter
from ocrmypdf._pipelines.hocr_to_ocr_pdf import run_hocr_to_ocr_pdf_pipeline
from ocrmypdf._pipelines.ocr import run_pipeline, run_pipeline_cli
from ocrmypdf._pipelines.pdf_to_hocr import run_hocr_pipeline
from ocrmypdf._plugin_manager import get_plugin_manager
from ocrmypdf._validation import check_options
from ocrmypdf.cli import ArgumentParser, get_parser
from ocrmypdf.helpers import is_iterable_notstr

StrPath = Path | AnyStr
PathOrIO = BinaryIO | StrPath

# Installing plugins affects the global state of the Python interpreter,
# so we need to use a lock to prevent multiple threads from installing
# plugins at the same time.
_api_lock = threading.Lock()


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
    plugin_manager: pluggy.PluginManager | None = None,
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
        console = plugin_manager.hook.get_logging_console()

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

    if manage_root_logger:
        logging.captureWarnings(True)

    return log


def _kwargs_to_cmdline(
    *, defer_kwargs: set[str], **kwargs
) -> tuple[list[str], dict[str, AnyStr]]:
    """Convert kwargs to command line arguments."""
    cmdline = []
    deferred = {}
    for arg, val in kwargs.items():
        if val is None:
            continue

        # Skip arguments that are handled elsewhere
        if arg in defer_kwargs:
            deferred[arg] = val
            continue

        cmd_style_arg = arg.replace('_', '-')

        # Booleans are special: add only if True, omit for False
        if isinstance(val, bool):
            if val:
                cmdline.append(f"--{cmd_style_arg}")
            continue

        if is_iterable_notstr(val):
            for elem in val:
                cmdline.append(f"--{cmd_style_arg}")
                cmdline.append(elem)
            continue

        # We have a parameter
        cmdline.append(f"--{cmd_style_arg}")
        if isinstance(val, int | float):
            cmdline.append(str(val))
        elif isinstance(val, str):
            cmdline.append(val)
        elif isinstance(val, Path):
            cmdline.append(str(val))
        else:
            raise TypeError(f"{arg}: {val} ({type(val)})")
    return cmdline, deferred


def create_options(
    *, input_file: PathOrIO, output_file: PathOrIO, parser: ArgumentParser, **kwargs
) -> Namespace:
    """Construct an options object from the input/output files and keyword arguments.

    Args:
        input_file: Input file path or file object.
        output_file: Output file path or file object.
        parser: ArgumentParser object.
        **kwargs: Keyword arguments.

    Returns:
        argparse.Namespace: A Namespace object containing the parsed arguments.

    Raises:
        TypeError: If the type of a keyword argument is not supported.
    """
    cmdline, deferred = _kwargs_to_cmdline(
        defer_kwargs={'progress_bar', 'plugins', 'parser', 'input_file', 'output_file'},
        **kwargs,
    )
    if isinstance(input_file, BinaryIO | IOBase):
        cmdline.append('stream://input_file')
    else:
        cmdline.append(os.fspath(input_file))
    if isinstance(output_file, BinaryIO | IOBase):
        cmdline.append('stream://output_file')
    else:
        cmdline.append(os.fspath(output_file))
    if 'sidecar' in kwargs and isinstance(kwargs['sidecar'], BinaryIO | IOBase):
        cmdline.append('--sidecar')
        cmdline.append('stream://sidecar')

    parser.enable_api_mode()
    options = parser.parse_args(cmdline)
    for keyword, val in deferred.items():
        setattr(options, keyword, val)

    if options.input_file == 'stream://input_file':
        options.input_file = input_file
    if options.output_file == 'stream://output_file':
        options.output_file = output_file
    if options.sidecar == 'stream://sidecar':
        options.sidecar = kwargs['sidecar']

    return options


def ocr(  # noqa: D417
    input_file: PathOrIO,
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
    plugins: Iterable[StrPath] | None = None,
    plugin_manager=None,
    keep_temporary_files: bool | None = None,
    progress_bar: bool | None = None,
    **kwargs,
):
    """Run OCRmyPDF on one PDF or image.

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
        use_threads: Use worker threads instead of processes. This reduces
            performance but may make debugging easier since it is easier to set
            breakpoints.
        input_file: If a :class:`pathlib.Path`, ``str`` or ``bytes``, this is
            interpreted as file system path to the input file. If the object
            appears to be a readable stream (with methods such as ``.read()``
            and ``.seek()``), the object will be read in its entirety and saved to
            a temporary file. If ``input_file`` is  ``"-"``, standard input will be
            read.
        output_file: If a :class:`pathlib.Path`, ``str`` or ``bytes``, this is
            interpreted as file system path to the output file. If the object
            appears to be a writable stream (with methods such as ``.write()`` and
            ``.seek()``), the output will be written to this stream. If
            ``output_file`` is ``"-"``, the output will be written to ``sys.stdout``
            (provided that standard output does not seem to be a terminal device).
            When a stream is used as output, whether via a writable object or
            ``"-"``, some final validation steps are not performed (we do not read
            back the stream after it is written).

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

    Returns:
        :class:`ocrmypdf.ExitCode`
    """
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
        if k not in {'input_file', 'output_file', 'kwargs'}
    }
    create_options_kwargs.update(kwargs)

    parser = get_parser()
    with _api_lock:
        if not plugin_manager:
            plugin_manager = get_plugin_manager(plugins)
        plugin_manager.hook.add_options(parser=parser)  # pylint: disable=no-member

        if 'verbose' in kwargs:
            warn("ocrmypdf.ocr(verbose=) is ignored. Use ocrmypdf.configure_logging().")

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
    force_ocr: bool | None = None,
    skip_text: bool | None = None,
    redo_ocr: bool | None = None,
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
    user_words: os.PathLike | None = None,
    user_patterns: os.PathLike | None = None,
    continue_on_soft_render_error: bool | None = None,
    invalidate_digital_signatures: bool | None = None,
    plugin_manager=None,
    plugins: Sequence[StrPath] | None = None,
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
    # No new variable names should be assigned until these two steps are run
    create_options_kwargs = {
        k: v
        for k, v in locals().items()
        if k not in {'input_pdf', 'output_folder', 'kwargs'}
    }
    create_options_kwargs.update(kwargs)

    parser = get_parser()

    with _api_lock:
        if not plugin_manager:
            plugin_manager = get_plugin_manager(plugins)
        plugin_manager.hook.add_options(parser=parser)  # pylint: disable=no-member

        cmdline, deferred = _kwargs_to_cmdline(
            defer_kwargs={'input_pdf', 'output_folder', 'plugins'},
            **create_options_kwargs,
        )
        cmdline.append(str(input_pdf))
        cmdline.append(str(output_folder))
        parser.enable_api_mode()
        options = parser.parse_args(cmdline)
        for keyword, val in deferred.items():
            setattr(options, keyword, val)
        delattr(options, 'output_file')
        setattr(options, 'output_folder', output_folder)

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
    jbig2_lossy: bool | None = None,
    jbig2_page_group_size: int | None = None,
    jbig2_threshold: float | None = None,
    pdfa_image_compression: str | None = None,
    color_conversion_strategy: str | None = None,
    fast_web_view: float | None = None,
    plugin_manager=None,
    plugins: Sequence[StrPath] | None = None,
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
    # No new variable names should be assigned until these two steps are run
    create_options_kwargs = {
        k: v
        for k, v in locals().items()
        if k not in {'work_folder', 'output_pdf', 'kwargs'}
    }
    create_options_kwargs.update(kwargs)

    parser = get_parser()

    with _api_lock:
        if not plugin_manager:
            plugin_manager = get_plugin_manager(plugins)
        plugin_manager.hook.add_options(parser=parser)  # pylint: disable=no-member

        cmdline, deferred = _kwargs_to_cmdline(
            defer_kwargs={'work_folder', 'output_file', 'plugins'},
            **create_options_kwargs,
        )
        cmdline.append(str(work_folder))
        cmdline.append(str(output_file))
        parser.enable_api_mode()
        options = parser.parse_args(cmdline)
        for keyword, val in deferred.items():
            setattr(options, keyword, val)
        delattr(options, 'input_file')
        setattr(options, 'work_folder', work_folder)

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
]
