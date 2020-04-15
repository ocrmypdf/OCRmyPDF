# © 2019 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import logging
import os
import sys
from contextlib import suppress
from enum import IntEnum
from pathlib import Path
from typing import Dict, Iterable

from tqdm import tqdm

from ._sync import run_pipeline
from ._validation import check_options
from .cli import parser


class TqdmConsole:
    """Wrapper to log messages in a way that is compatible with tqdm progress bar

    This routes log messages through tqdm so that it can print them above the
    progress bar, and then refresh the progress bar, rather than overwriting
    it which looks messy.

    For some reason Python 3.6 prints extra empty messages from time to time,
    so we suppress those.
    """

    def __init__(self, file):
        self.file = file
        self.py36 = sys.version_info[0:2] == (3, 6)

    def write(self, msg):
        # When no progress bar is active, tqdm.write() routes to print()
        if self.py36:
            if msg.strip() != '':
                tqdm.write(msg.rstrip(), end='\n', file=self.file)
        else:
            tqdm.write(msg.rstrip(), end='\n', file=self.file)

    def flush(self):
        with suppress(AttributeError):
            self.file.flush()


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

    Library users may wish to use this function if they want their log output to be
    similar to ocrmypdf command line interface. If not used, the external application
    should configure logging on its own.

    ocrmypdf will perform all of its logging under the ``"ocrmypdf"`` logging namespace.
    In addition, ocrmypdf imports pdfminer, which logs under ``"pdfminer"``. A library
    user may wish to configure both; note that pdfminer is extremely chatty at the log
    level ``logging.INFO``.

    Library users may perform additional configuration afterwards.

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

    formatter = logging.Formatter('%(levelname)7s - %(message)s')
    if verbosity >= 2:
        formatter = logging.Formatter('%(name)s - %(levelname)7s - %(message)s')

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


def create_options(*, input_file: os.PathLike, output_file: os.PathLike, **kwargs):
    cmdline = []
    deferred = []

    for arg, val in kwargs.items():
        if val is None:
            continue

        # These arguments with special handling for which we bypass
        # argparse
        if arg in {'tesseract_env', 'progress_bar'}:
            deferred.append((arg, val))
            continue

        cmd_style_arg = arg.replace('_', '-')

        # Booleans are special: add only if True, omit for False
        if isinstance(val, bool):
            if val:
                cmdline.append(f"--{cmd_style_arg}")
            continue

        if isinstance(val, Iterable) and not isinstance(val, str):
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

    cmdline.append(str(input_file))
    cmdline.append(str(output_file))

    parser.api_mode = True
    options = parser.parse_args(cmdline)
    for keyword, val in deferred:
        setattr(options, keyword, val)

    # If we are running a Tesseract spoof, ensure it knows what the input file is
    if os.environ.get('PYTEST_CURRENT_TEST') and options.tesseract_env:
        options.tesseract_env['_OCRMYPDF_TEST_INFILE'] = os.fspath(input_file)

    return options


def ocr(  # pylint: disable=unused-argument
    input_file: os.PathLike,
    output_file: os.PathLike,
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
    keep_temporary_files: bool = None,
    progress_bar: bool = None,
    tesseract_env: Dict[str, str] = None,
):
    """Run OCRmyPDF on one PDF or image.

    For most arguments, see documentation for the equivalent command line parameter.
    A few specific arguments are discussed here:

    Args:
        use_threads (bool): Use worker threads instead of processes. This reduces
            performance but may make debugging easier since it is easier to set
            breakpoints.
        tesseract_env (dict): Override environment variables for Tesseract
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

    options = create_options(**locals())
    check_options(options)
    return run_pipeline(options, api=True)
