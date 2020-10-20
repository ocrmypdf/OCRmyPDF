# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import os
import sys
from enum import IntEnum
from pathlib import Path
from typing import BinaryIO, Iterable, Union
from warnings import warn

from ocrmypdf._logging import PageNumberFilter, TqdmConsole
from ocrmypdf._plugin_manager import get_plugin_manager
from ocrmypdf._sync import run_pipeline
from ocrmypdf._validation import check_options
from ocrmypdf.cli import ArgumentParser, get_parser
from ocrmypdf.helpers import is_iterable_notstr

try:
    import coloredlogs
except ModuleNotFoundError:
    coloredlogs = None


PathOrIO = Union[BinaryIO, os.PathLike, str, bytes]


class Verbosity(IntEnum):
    """Verbosity level for configure_logging."""

    quiet = -1  #: Suppress most messages
    default = 0  #: Default level of logging
    debug = 1  #: Output ocrmypdf debug messages
    debug_all = 2  #: More detailed debugging from ocrmypdf and dependent modules


def configure_logging(
    verbosity: Verbosity,
    progress_bar_friendly: bool = True,
    manage_root_logger: bool = False,
):
    """Set up logging.

    Before calling :func:`ocrmypdf.ocr()`, you can use this function to
    configure logging, if you want ocrmypdf's output to look like the ocrmypdf
    command line interface. It will register log handlers, log filters, and
    formatters, configure color logging to standard error, and adjust the log
    levels of third party libraries. Details of this are fine-tuned and subject
    to change. The ``verbosity`` argument is equivalent to the argument
    ``--verbose`` and applies those settings.

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
        verbosity (Verbosity): Verbosity level.
        progress_bar_friendly (bool): Install the TqdmConsole log handler, which is
            compatible with the tqdm progress bar; without this log messages will
            overwrite the progress bar
        manage_root_logger (bool): Configure the process's root logger, to ensure
            all log output is sent through

    Returns:
        The toplevel logger for ocrmypdf (or the root logger, if we are managing it).
    """

    prefix = '' if manage_root_logger else 'ocrmypdf'

    log = logging.getLogger(prefix)
    log.setLevel(logging.DEBUG)

    if progress_bar_friendly:
        console = logging.StreamHandler(stream=TqdmConsole(sys.stderr))
    else:
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

    use_colors = progress_bar_friendly
    if not coloredlogs:
        use_colors = False
    if use_colors:
        if os.name == 'nt':
            use_colors = coloredlogs.enable_ansi_support()
        if use_colors:
            use_colors = coloredlogs.terminal_supports_colors()
    if use_colors:
        formatter = coloredlogs.ColoredFormatter(fmt=fmt)
    else:
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


def create_options(
    *, input_file: PathOrIO, output_file: PathOrIO, parser: ArgumentParser, **kwargs
):
    cmdline = []
    deferred = []

    for arg, val in kwargs.items():
        if val is None:
            continue

        # These arguments with special handling for which we bypass
        # argparse
        if arg in {'progress_bar', 'plugins'}:
            deferred.append((arg, val))
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
        if isinstance(val, (int, float)):
            cmdline.append(str(val))
        elif isinstance(val, str):
            cmdline.append(val)
        elif isinstance(val, Path):
            cmdline.append(str(val))
        else:
            raise TypeError(f"{arg}: {val} ({type(val)})")

    try:
        cmdline.append(os.fspath(input_file))
    except TypeError:
        cmdline.append('stream://input_file')
    try:
        cmdline.append(os.fspath(output_file))
    except TypeError:
        cmdline.append('stream://output_file')

    parser._api_mode = True
    options = parser.parse_args(cmdline)
    for keyword, val in deferred:
        setattr(options, keyword, val)

    if options.input_file == 'stream://input_file':
        options.input_file = input_file
    if options.output_file == 'stream://output_file':
        options.output_file = output_file

    return options


def ocr(  # pylint: disable=unused-argument
    input_file: PathOrIO,
    output_file: PathOrIO,
    *,
    language: Iterable[str] = None,
    image_dpi: int = None,
    output_type=None,
    sidecar: os.PathLike = None,
    jobs: int = None,
    use_threads: bool = None,
    title: str = None,
    author: str = None,
    subject: str = None,
    keywords: str = None,
    rotate_pages: bool = None,
    remove_background: bool = None,
    deskew: bool = None,
    clean: bool = None,
    clean_final: bool = None,
    unpaper_args: str = None,
    oversample: int = None,
    remove_vectors: bool = None,
    threshold: bool = None,
    force_ocr: bool = None,
    skip_text: bool = None,
    redo_ocr: bool = None,
    skip_big: float = None,
    optimize: int = None,
    jpg_quality: int = None,
    png_quality: int = None,
    jbig2_lossy: bool = None,
    jbig2_page_group_size: int = None,
    pages: str = None,
    max_image_mpixels: float = None,
    tesseract_config: Iterable[str] = None,
    tesseract_pagesegmode: int = None,
    tesseract_oem: int = None,
    pdf_renderer=None,
    tesseract_timeout: float = None,
    rotate_pages_threshold: float = None,
    pdfa_image_compression=None,
    user_words: os.PathLike = None,
    user_patterns: os.PathLike = None,
    fast_web_view: float = None,
    plugins: Iterable[Union[str, Path]] = None,
    keep_temporary_files: bool = None,
    progress_bar: bool = None,
    **kwargs,
):
    """Run OCRmyPDF on one PDF or image.

    For most arguments, see documentation for the equivalent command line parameter.
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
            appears to be a writable stream (with methods such as ``.read()`` and
            ``.seek()``), the output will be written to this stream. If
            ``output_file`` is ``"-"``, the output will be written to ``sys.stdout``
            (provided that standard output does not seem to be a terminal device).
            When a stream is used as output, whether via a writable object or
            ``"-"``, some final validation steps are not performed (we do not read
            back the stream after it is written).
    Raises:
        ocrmypdf.PdfMergeFailedError: If the input PDF is malformed, preventing merging
            with the OCR layer.
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
        ocrmypdf.EncryptedPdfERror: If the input PDF is encrypted (password protected).
            OCRmyPDF does not remove passwords.
        ocrmypdf.TesseractConfigError: If Tesseract reported its configuration was not
            valid.

    Returns:
        :class:`ocrmypdf.ExitCode`
    """
    if not plugins:
        plugins = []
    elif isinstance(plugins, (str, Path)):
        plugins = [plugins]
    else:
        plugins = list(plugins)

    parser = get_parser()
    _plugin_manager = get_plugin_manager(plugins)
    _plugin_manager.hook.add_options(parser=parser)  # pylint: disable=no-member

    create_options_kwargs = {
        k: v for k, v in locals().items() if not k.startswith('_') and k != 'kwargs'
    }
    create_options_kwargs.update(kwargs)

    if 'verbose' in kwargs:
        warn("ocrmypdf.ocr(verbose=) is ignored. Use ocrmypdf.configure_logging().")

    options = create_options(**create_options_kwargs)
    check_options(options, _plugin_manager)
    return run_pipeline(options=options, plugin_manager=_plugin_manager, api=True)
