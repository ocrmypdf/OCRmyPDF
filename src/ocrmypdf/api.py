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

import argparse
import logging
import sys
from pathlib import Path

from tqdm import tqdm

from .cli import parser
from ._sync import run_pipeline


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


def configure_logging(options, progress_bar_friendly=True, manage_root_logger=False):
    """Set up logging

    Library users may wish to use this function if they want their log output to be
    similar to ocrmypdf's when run as a command. If not use, the external application
    should configure logging on its own.

    ocrmypdf will perform all of its logging under the `"ocrmypdf"` logging namespace.
    In addition, ocrmypdf imports pdfminer, which logs under `"pdfminer"`. A library
    user may wish to configure both; note that pdfminer is extremely chatty at the log
    level logging.INFO.

    Library users may perform additional configuration afterwards.

    Args:
        options: OCRmyPDF options
        progress_bar_friendly (bool): install the TqdmConsole log handler, which is
            compatible with the tqdm progress bar; without this log messages will
            overwrite the progress bar
        manage_root_logger (bool): configure the process's root logger, to ensure
            all log output is sent through
    """

    prefix = '' if manage_root_logger else 'ocrmypdf'
    log = logging.getLogger(prefix)
    log.setLevel(logging.INFO)

    if progress_bar_friendly:
        console = logging.StreamHandler(stream=TqdmConsole(sys.stderr))
        if options.quiet:
            console.setLevel(logging.ERROR)
        elif options.verbose >= 2:
            console.setLevel(logging.DEBUG)
        else:
            console.setLevel(logging.INFO)

    formatter = logging.Formatter('%(levelname)7s - %(message)s')

    if options.verbose >= 2:
        log.setLevel(logging.DEBUG)

    console.setFormatter(formatter)
    log.addHandler(console)

    pdfminer_log = logging.getLogger('pdfminer')
    pdfminer_log.setLevel(logging.ERROR)


def create_options(*, input_file, output_file, **kwargs):
    cmdline = []

    for arg, val in kwargs.items():
        if val is None:
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
            raise TypeError(f"{val} ({type(val)})")

    cmdline.append(str(input_file))
    cmdline.append(str(output_file))

    try:
        options = parser.parse_args(cmdline)
    except argparse.ArgumentError as e:
        raise ValueError(str(e))
    return options


def ocrmypdf(  # pylint: disable=unused-argument
    input_file,
    output_file,
    *,
    language=None,
    image_dpi=None,
    output_type=None,
    sidecar=None,
    jobs=None,
    quiet=None,
    verbose=None,
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
    mask_barcodes=None,
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
    keep_temporary_files=None,
):
    options = create_options(**locals())
    return run(options)


def run(options):
    return run_pipeline(options)
