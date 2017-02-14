#!/usr/bin/env python3
# © 2015-16 James R. Barlow: github.com/jbarlow83

from contextlib import suppress
from tempfile import mkdtemp
from collections.abc import Sequence
import sys
import os
import re
import shutil
import warnings
import multiprocessing
import atexit
import textwrap
import img2pdf
import logging
import argparse

import PyPDF2 as pypdf
from PIL import Image

import ruffus.ruffus_exceptions as ruffus_exceptions
import ruffus.cmdline as cmdline
import ruffus.proxy_logger as proxy_logger

from .pipeline import JobContext, JobContextManager, re_symlink, \
    cleanup_working_files, build_pipeline
from .pdfa import file_claims_pdfa
from .helpers import is_iterable_notstr, re_symlink, is_file_writable
from .exec import tesseract, qpdf
from . import PROGRAM_NAME, VERSION

from .exceptions import *
from . import exceptions as ocrmypdf_exceptions

warnings.simplefilter('ignore', pypdf.utils.PdfReadWarning)


# -------------
# External dependencies

MINIMUM_TESS_VERSION = '3.02.02'


def complain(message):
    print(*textwrap.wrap(message), file=sys.stderr)


if tesseract.version() < MINIMUM_TESS_VERSION:
    complain(
        "Please install tesseract {0} or newer "
        "(currently installed version is {1})".format(
            MINIMUM_TESS_VERSION, tesseract.version()))
    sys.exit(ExitCode.missing_dependency)


# -------------
# Parser

parser = cmdline.get_argparse(
    prog=PROGRAM_NAME,
    version=VERSION,
    fromfile_prefix_chars='@',
    ignored_args=[
        'touch_files_only', 'recreate_database', 'checksum_file_name',
        'key_legend_in_graph', 'draw_graph_horizontally', 'flowchart_format',
        'forced_tasks', 'target_tasks', 'use_threads', 'jobs', 'log_file'],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""\
Generates a searchable PDF or PDF/A from a regular PDF.

OCRmyPDF rasterizes each page of the input PDF, optionally corrects page
rotation and performs image processing, runs the Tesseract OCR engine on the
image, and then creates a PDF from the OCR information.
""",
    epilog="""\
OCRmyPDF attempts to keep the output file at about the same size.  If a file
contains losslessly compressed images, and output file will be losslessly
compressed as well.

PDF is a page description file that attempts to preserve a layout exactly.
A PDF can contain vector objects (such as text or lines) and raster objects
(images).  A page might have multiple images.  OCRmyPDF is prepared to deal
with the wide variety of PDFs that exist in the wild.

When a PDF page contains text, OCRmyPDF assumes that the page has already
been OCRed or is a "born digital" page that should not be OCRed.  The default
behavior is to exit in this case without producing a file.  You can use the
option --skip-text to ignore pages with text, or --force-ocr to rasterize
all objects on the page and produce an image-only PDF as output.

    ocrmypdf --skip-text file_with_some_text_pages.pdf output.pdf

    ocrmypdf --force-ocr word_document.pdf output.pdf

If you are concerned about long-term archiving of PDFs, use the default option
--output-type pdfa which converts the PDF to a standardized PDF/A-2b.  This
converts images to sRGB colorspace, removes some features from the PDF such
as Javascript or forms. If you want to minimize the number of changes made to
your PDF, use --output-type pdf.

If OCRmyPDF is given an image file as input, it will attempt to convert the
image to a PDF before processing.  For more control over the conversion of
images to PDF, use the Python package img2pdf or other image to PDF software.

For example, this command uses img2pdf to convert all .png files beginning
with the 'page' prefix to a PDF, fitting each image on A4-sized paper, and
sending the result to OCRmyPDF through a pipe.  img2pdf is a dependency of
ocrmypdf so it is already installed.

    img2pdf --pagesize A4 page*.png | ocrmypdf - myfile.pdf

Online documentation is located at:
    https://ocrmypdf.readthedocs.io/en/latest/introduction.html

""")

parser.add_argument(
    'input_file',
    help="PDF file containing the images to be OCRed (or '-' to read from "
         "standard input)")
parser.add_argument(
    'output_file',
    help="output searchable PDF file (or '-' to write to standard output)")
parser.add_argument(
    '-l', '--language', action='append',
    help="Language(s) of the file to be OCRed (see tesseract --list-langs for "
         "all language packs installed in your system). To specify multiple "
         "languages, join them with '+' or issue this argument once for each "
         "language.")
parser.add_argument(
    '-j', '--jobs', metavar='N', type=int,
    help="Use up to N CPU cores simultaneously (default: use all)")
parser.add_argument(
    '--image-dpi', metavar='DPI', type=int,
    help="for input image instead of PDF, use this DPI instead of file's")
parser.add_argument(
    '--output-type', choices=['pdfa', 'pdf'], default='pdfa',
    help="Choose output type. 'pdfa' creates a PDF/A-2b compliant file for "
         "long term archiving (default, recommended) but may not suitable "
         "for users who want their file altered as little as possible. 'pdfa' "
         "also has problems with full Unicode text. 'pdf' attempts to "
         "preserve file contents as much as possible.")

metadata = parser.add_argument_group(
    "Metadata options",
    "Set output PDF/A metadata (default: use input document's metadata)")
metadata.add_argument(
    '--title', type=str,
    help="set document title (place multiple words in quotes)")
metadata.add_argument(
    '--author', type=str,
    help="set document author")
metadata.add_argument(
    '--subject', type=str,
    help="set document subject description")
metadata.add_argument(
    '--keywords', type=str,
    help="set document keywords")

preprocessing = parser.add_argument_group(
    "Image preprocessing options",
    "Options to improve the quality of the final PDF and OCR")
preprocessing.add_argument(
    '-r', '--rotate-pages', action='store_true',
    help="automatically rotate pages based on detected text orientation")
preprocessing.add_argument(
    '--remove-background', action='store_true',
    help="attempt to remove background from gray or color pages, setting it "
         "to white ")
preprocessing.add_argument(
    '-d', '--deskew', action='store_true',
    help="deskew each page before performing OCR")
preprocessing.add_argument(
    '-c', '--clean', action='store_true',
    help="clean pages from scanning artifacts before performing OCR, and send "
         "the cleaned page to OCR, but do not include the cleaned page in "
         "the output ")
preprocessing.add_argument(
    '-i', '--clean-final', action='store_true',
    help="clean page as above, and incorporate the cleaned image in the final "
         "PDF")
preprocessing.add_argument(
    '--oversample', metavar='DPI', type=int, default=0,
    help="oversample images to at least the specified DPI, to improve OCR "
         "results slightly")

ocrsettings = parser.add_argument_group(
    "OCR options",
    "Control how OCR is applied")
ocrsettings.add_argument(
    '-f', '--force-ocr', action='store_true',
    help="rasterize any fonts or vector objects on each page, apply OCR, and "
         "save the rastered output (this rewrites the PDF)")
ocrsettings.add_argument(
    '-s', '--skip-text', action='store_true',
    help="skip OCR on any pages that already contain text, but include the "
         "page in final output; useful for PDFs that contain a mix of "
         "images, text pages, and/or previously OCRed pages")
ocrsettings.add_argument(
    '--skip-big', type=float, metavar='MPixels',
    help="skip OCR on pages larger than the specified amount of megapixels, "
         "but include skipped pages in final output")

advanced = parser.add_argument_group(
    "Advanced",
    "Advanced options for power users")
advanced.add_argument(
    '--tesseract-config', action='append', metavar='CFG', default=[],
    help="additional Tesseract configuration files -- see documentation")
advanced.add_argument(
    '--tesseract-pagesegmode', action='store', type=int, metavar='PSM',
    choices=range(0, 14),
    help="set Tesseract page segmentation mode (see tesseract --help)")
advanced.add_argument(
    '--tesseract-oem', action='store', type=int, metavar='MODE',
    choices=range(0, 4),
    help=("set Tesseract 4.0 OCR engine mode: "
         "0 - original Tesseract only; "
         "1 - neural nets LSTM only; "
         "2 - Tesseract + LSTM; "
         "3 - default.")
    )
advanced.add_argument(
    '--pdf-renderer', choices=['auto', 'tesseract', 'hocr', 'tess4'], default='auto',
    help="choose OCR PDF renderer - the default option is to let OCRmyPDF "
         "choose.  The 'tesseract' PDF renderer is more accurate and does a "
         "better job and document structure such as recognizing columns. It "
         "also does a better job on non-Latin languages. However, it does "
         "not work as well when older versions of Tesseract or Ghostscript "
         "are installed, and some combinations of arguments to do not work "
         "with --pdf-renderer tesseract.  The 'tess4' PDF renderer is similar "
         "to 'tesseract', requires tesseract 4, and gives superior results.")
advanced.add_argument(
    '--tesseract-timeout', default=180.0, type=float, metavar='SECONDS',
    help='give up on OCR after the timeout, but copy the preprocessed page '
         'into the final output')
advanced.add_argument(
    '--rotate-pages-threshold', default=14.0, type=float, metavar='CONFIDENCE',
    help="only rotate pages when confidence is above this value (arbitrary "
         "units reported by tesseract)")

debugging = parser.add_argument_group(
    "Debugging",
    "Arguments to help with troubleshooting and debugging")
debugging.add_argument(
    '-k', '--keep-temporary-files', action='store_true',
    help="keep temporary files (helpful for debugging)")
debugging.add_argument(
    '-g', '--debug-rendering', action='store_true',
    help="render each page twice with debug information on second page")


def check_options_languages(options, _log):
    if not options.language:
        options.language = ['eng']  # Enforce English hegemony

    # Support v2.x "eng+deu" language syntax
    if '+' in options.language[0]:
        options.language = options.language[0].split('+')

    if not set(options.language).issubset(tesseract.languages()):
        msg = (
            "The installed version of tesseract does not have language "
            "data for the following requested languages: \n")
        for lang in (set(options.language) - tesseract.languages()):
            msg += lang + '\n'
        raise argparse.ArgumentError(msg)


def check_options_output(options, log):
    if options.pdf_renderer == 'auto':
        options.pdf_renderer = 'hocr'

    if options.pdf_renderer in ('tesseract', 'tess4'):
        if tesseract.version() < '3.05':
            log.warning(
                "tesseract < 3.05 may corrupt PDF output. "
                "--pdf-renderer=tesseract is not recommend.")
        elif tesseract.version() == '4.00.00alpha':
            log.warning(
                "tesseract 4.00.00alpha may corrupt PDF output. "
                "--pdf-renderer={tesseract,tess4} is not recommend.")

    if options.debug_rendering and options.pdf_renderer == 'tesseract':
        log.info(
            "Ignoring --debug-rendering because it is not supported with"
            "--pdf-renderer=tesseract.")

    lossless_reconstruction = False
    if options.pdf_renderer == 'hocr':
        if not any((options.deskew, options.clean_final, options.force_ocr,
                   options.remove_background)):
            lossless_reconstruction = True
    options.lossless_reconstruction = lossless_reconstruction


def check_options_preprocessing(options, log):
    if any((options.clean, options.clean_final)):
        from .exec import unpaper
        try:
            if unpaper.version() < '6.1':
                raise MissingDependencyError(
                    "The installed 'unpaper' is not supported. "
                    "Install version 6.1 or newer.")
        except FileNotFoundError:
            raise MissingDependencyError(
                "Install the 'unpaper' program to use --clean, --clean-final.")

    if options.clean and \
            not options.clean_final and \
            options.pdf_renderer == 'tesseract':
        log.info(
            "Tesseract PDF renderer cannot render --clean pages without "
            "also performing --clean-final, so --clean-final is assumed.")


def check_options_ocr_behavior(options, log):
    if options.force_ocr and options.skip_text:
        raise argparse.ArgumentError(
            "Error: --force-ocr and --skip-text are mutually incompatible.")

    if set(options.language) & {'chi_sim', 'chi_tra'} and \
            (options.pdf_renderer == 'hocr' or options.output_type == 'pdfa'):
        log.warning(
            "Your settings are known to cause problems with OCR of Chinese text. "
            "Try adding these arguments: "
            "    ocrmypdf --pdf-renderer tesseract --output-type pdf")


def check_options_advanced(options, log):
    if tesseract.v4():
        log.info(
            "Tesseract v4.x.alpha found. OCRmyPDF support is experimental.")
    if options.tesseract_oem and not tesseract.v4():
        log.warning(
            "--tesseract-oem requires Tesseract 4.x -- argument ignored")
    if options.pdf_renderer == 'tess4' and not tesseract.has_textonly_pdf():
        raise MissingDependencyError(
            "--pdf-renderer tess4 requires Tesseract 4.x "
            "commit 3d9fb3b or later")


def check_options(options, log):
    try:
        check_options_languages(options, log)
        check_options_output(options, log)
        check_options_preprocessing(options, log)
        check_options_ocr_behavior(options, log)
        check_options_advanced(options, log)
    except argparse.ArgumentError as e:
        log.error(e)
        sys.exit(ExitCode.bad_args)
    except MissingDependencyError as e:
        log.error(e)
        sys.exit(ExitCode.missing_dependency)


# ----------
# Logging


def logging_factory(logger_name, listargs):
    log_file_name, verbose = listargs

    root_logger = logging.getLogger(logger_name)
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stderr)
    formatter_ = logging.Formatter("%(levelname)7s - %(message)s")
    handler.setFormatter(formatter_)
    if verbose:
        handler.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    return root_logger


def available_cpu_count():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        pass

    try:
        import psutil
        return psutil.cpu_count()
    except (ImportError, AttributeError):
        pass

    complain(
        "Could not get CPU count.  Assuming one (1) CPU."
        "Use -j N to set manually.")
    return 1


def cleanup_ruffus_error_message(msg):
    msg = re.sub(r'\s+', r' ', msg, re.MULTILINE)
    msg = re.sub(r"\((.+?)\)", r'\1', msg)
    msg = msg.strip()
    return msg


def do_ruffus_exception(ruffus_five_tuple, options, log):
    """Replace the elaborate ruffus stack trace with a user friendly
    description of the error message that occurred."""

    task_name, job_name, exc_name, exc_value, exc_stack = ruffus_five_tuple
    if exc_name == 'builtins.SystemExit':
        match = re.search(r"\.(.+?)\)", exc_value)
        exit_code_name = match.groups()[0]
        exit_code = getattr(ExitCode, exit_code_name, 'other_error')
        return exit_code
    elif exc_name == 'ruffus.ruffus_exceptions.MissingInputFileError':
        log.error(cleanup_ruffus_error_message(exc_value))
        return ExitCode.input_file
    elif exc_name == 'builtins.TypeError':
        # Even though repair_pdf will fail, ruffus will still try
        # to call split_pages with no input files, likely due to a bug
        if task_name == 'split_pages':
            log.error("Input file '{0}' is not a valid PDF".format(
                options.input_file))
            return ExitCode.input_file
    elif exc_name == 'builtins.KeyboardInterrupt':
        log.error("Interrupted by user")
        return ExitCode.ctrl_c
    elif exc_name == 'subprocess.CalledProcessError':
        # It's up to the subprocess handler to report something useful
        msg = "Error occurred while running this command:"
        log.error(msg + '\n' + exc_value)
        return ExitCode.child_process_error
    elif exc_name == 'ocrmypdf.exceptions.PdfMergeFailedError':
        log.error(textwrap.dedent("""\
            Failed to merge PDF image layer with OCR layer

            Usually this happens because the input PDF file is mal-formed and
            ocrmypdf cannot automatically correct the problem on its own.

            Try using
                ocrmypdf --pdf-renderer tesseract  [..other args..]
            """))
        return ExitCode.input_file
    elif exc_name.startswith('ocrmypdf.exceptions.'):
        base_exc_name = exc_name.replace('ocrmypdf.exceptions.', '')
        exc_class = getattr(ocrmypdf_exceptions, base_exc_name)
        return exc_class.exit_code
    elif exc_name == 'PyPDF2.utils.PdfReadError' and \
            'not been decrypted' in exc_value:
        log.error(textwrap.dedent("""\
            Input PDF uses either an encryption algorithm or a PDF security
            handler that is not supported by ocrmypdf.

            For information about this PDF's security use
                qpdf --show-encryption [...input PDF...]

            (Only algorithms "R = 1" and "R = 2" are supported.)

            """))
        return ExitCode.encrypted_pdf

    if not options.verbose:
        log.error(exc_stack)
    return ExitCode.other_error


def traverse_ruffus_exception(e_args, options, log):
    """Walk through a RethrownJobError and find the first exception.

    The exit code will be based on this, even if multiple exceptions occurred
    at the same time."""

    if isinstance(e_args, Sequence) and isinstance(e_args[0], str) and \
            len(e_args) == 5:
        return do_ruffus_exception(e_args, options, log)
    elif is_iterable_notstr(e_args):
        for exc in e_args:
            return traverse_ruffus_exception(exc, options, log)


def run_pipeline():
    options = parser.parse_args()
    options.verbose_abbreviated_path = 1

    _log, _log_mutex = proxy_logger.make_shared_logger_and_proxy(
        logging_factory, __name__, [None, options.verbose])
    _log.debug('ocrmypdf ' + VERSION)
    _log.debug('tesseract ' + tesseract.version())

    check_options(options, _log)

    # Any changes to options will not take effect for options that are already
    # bound to function parameters in the pipeline. (For example
    # options.input_file, options.pdf_renderer are already bound.)
    if not options.jobs:
        options.jobs = available_cpu_count()
    try:
        work_folder = mkdtemp(prefix="com.github.ocrmypdf.")
        options.history_file = os.path.join(
            work_folder, 'ruffus_history.sqlite')
        start_input_file = os.path.join(
            work_folder, 'origin')

        if options.input_file == '-':
            # stdin
            _log.info('reading file from standard input')
            with open(start_input_file, 'wb') as stream_buffer:
                from shutil import copyfileobj
                copyfileobj(sys.stdin.buffer, stream_buffer)
        else:
            try:
                re_symlink(options.input_file, start_input_file, _log)
            except FileNotFoundError:
                _log.error("File not found - " + options.input_file)
                return ExitCode.input_file

        if options.output_file == '-':
            if sys.stdout.isatty():
                _log.error(textwrap.dedent("""\
                    Output was set to stdout '-' but it looks like stdout
                    is connected to a terminal.  Please redirect stdout to a
                    file."""))
                return ExitCode.bad_args
        elif not is_file_writable(options.output_file):
                _log.error(textwrap.dedent("""\
                    Cutput file location is not writable."""))
                return ExitCode.file_access_error

        manager = JobContextManager()
        manager.register('JobContext', JobContext)
        manager.start()

        context = manager.JobContext()
        context.set_options(options)
        context.set_work_folder(work_folder)

        build_pipeline(options, work_folder, _log, context)
        atexit.register(cleanup_working_files, work_folder, options)
        cmdline.run(options)
    except ruffus_exceptions.RethrownJobError as e:
        if options.verbose:
            _log.debug(str(e))  # stringify exception so logger doesn't have to

        # Ruffus flattens exception to 5 element tuples. Because of a bug
        # in <= 2.6.3 it may present either the single:
        #   (task, job, exc, value, stack)
        # or something like:
        #   [[(task, job, exc, value, stack)]]
        #
        # Generally cross-process exception marshalling doesn't work well
        # and ruffus doesn't support because BaseException has its own
        # implementation of __reduce__ that attempts to reconstruct the
        # exception based on e.__init__(e.args).
        #
        # Attempting to log the exception directly marshalls it to the logger
        # which is probably in another process, so it's better to log only
        # data from the exception at this point.

        exitcode = traverse_ruffus_exception(e.args, options, _log)
        if exitcode is None:
            _log.error("Unexpected ruffus exception: " + str(e))
            _log.error(repr(e))
            return ExitCode.other_error
        else:
            return exitcode
    except ExitCodeException as e:
        return e.exit_code
    except Exception as e:
        _log.error(e)
        return ExitCode.other_error

    if options.output_file != '-':
        if options.output_type == 'pdfa':
            pdfa_info = file_claims_pdfa(options.output_file)
            if pdfa_info['pass']:
                msg = 'Output file is a {} (as expected)'
                _log.info(msg.format(pdfa_info['conformance']))
            else:
                msg = 'Output file is okay but is not PDF/A (seems to be {})'
                _log.warning(msg.format(pdfa_info['conformance']))

                return ExitCode.invalid_output_pdf
        if not qpdf.check(options.output_file, _log):
            _log.warning('Output file: The generated PDF is INVALID')
            return ExitCode.invalid_output_pdf
    else:
        _log.info("Output sent to stdout")

    pdfinfo = context.get_pdfinfo()
    if options.verbose:
        from pprint import pformat
        _log.debug(pformat(pdfinfo))
    direction = {0: 'n', 90: 'e',
                 180: 's', 270: 'w'}
    orientations = []
    for n, page in enumerate(pdfinfo):
        angle = pdfinfo[n].get('rotated', 0)
        if angle != 0:
            orientations.append('{0}{1}'.format(
                n + 1,
                direction.get(angle, '')))
    if orientations:
        _log.info('Page orientations detected: ' + ' '.join(orientations))

    return ExitCode.ok


if __name__ == '__main__':
    sys.exit(run_pipeline())
