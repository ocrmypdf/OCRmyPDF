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
from enum import IntEnum
from pathlib import Path

from tqdm import tqdm

from ._sync import run_pipeline
from ._validation import check_options
from .cli import parser


class TqdmConsole:
    """Wrapper to log messages in a way that is compatible with tqdm progress bar"""

    def __init__(self, file):
        self.file = file
        self.py36 = sys.version_info >= (3, 6)

    def write(self, msg):
        # When no progress bar is active, tqdm.write() routes to print()
        if self.py36:
            if msg.strip() != '':
                tqdm.write(msg.rstrip(), end='\n', file=self.file)
        else:
            tqdm.write(msg.rstrip(), end='\n', file=self.file)

    def flush(self):
        if hasattr(self.file, "flush"):
            self.file.flush()


class Verbosity(IntEnum):
    """Verbosity level for configure_logging."""

    quiet = -1  #: Suppress most messages
    default = 0  #: Default level of logging
    debug = 1  #: Output ocrmypdf debug messages
    debug_all = 2  #: More detailed debugging from ocrmypdf and dependent modules


def configure_logging(verbosity, progress_bar_friendly=True, manage_root_logger=False):
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
    """

    prefix = '' if manage_root_logger else 'ocrmypdf'
    log = logging.getLogger(prefix)
    log.setLevel(logging.INFO)

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
    if verbosity >= 1:
        log.setLevel(logging.DEBUG)
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


def create_options(*, input_file, output_file, **kwargs):
    cmdline = []
    deferred = []

    for arg, val in kwargs.items():
        if val is None:
            continue
        if arg == 'tesseract_env':
            deferred.append((arg, val))
            continue
        cmd_style_arg = arg.replace('_', '-')
        cmdline.append(f"--{cmd_style_arg}")
        if isinstance(val, bool):
            continue
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
        options.tesseract_env['_OCRMYPDF_TEST_INFILE'] = input_file

    return options


def ocr(  # pylint: disable=unused-argument
    input_file,
    output_file,
    *,
    language=None,
    image_dpi=None,
    output_type=None,
    sidecar=None,
    jobs=None,
    use_threads=None,
    title=None,
    author=None,
    subject=None,
    keywords=None,
    rotate_pages=None,
    remove_background=None,
    deskew=None,
    clean=None,
    clean_final=None,
    unpaper_args=None,
    oversample=None,
    remove_vectors=None,
    threshold=None,
    force_ocr=None,
    skip_text=None,
    redo_ocr=None,
    skip_big=None,
    optimize=None,
    jpg_quality=None,
    png_quality=None,
    jbig2_lossy=None,
    jbig2_page_group_size=None,
    pages=None,
    max_image_mpixels=None,
    tesseract_config=None,
    tesseract_pagesegmode=None,
    tesseract_oem=None,
    pdf_renderer=None,
    tesseract_timeout=None,
    rotate_pages_threshold=None,
    pdfa_image_compression=None,
    user_words=None,
    user_patterns=None,
    fast_web_view=None,
    keep_temporary_files=None,
    progress_bar=None,
    tesseract_env=None,
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
