#!/usr/bin/env python3
# © 2015-17 James R. Barlow: github.com/jbarlow83

from tempfile import mkdtemp
from collections.abc import Sequence
import sys
import os
import re
import warnings
import multiprocessing
import atexit
import textwrap
import logging
import argparse

import PyPDF2 as pypdf
import PIL

import ruffus.ruffus_exceptions as ruffus_exceptions
import ruffus.cmdline as cmdline
import ruffus.proxy_logger as proxy_logger

from .pipeline import JobContext, JobContextManager, \
    cleanup_working_files, build_pipeline
from .pdfa import file_claims_pdfa
from .helpers import is_iterable_notstr, re_symlink, is_file_writable
from .exec import tesseract, qpdf, ghostscript
from . import PROGRAM_NAME, VERSION

from .exceptions import ExitCode, ExitCodeException, MissingDependencyError, \
    InputFileError, BadArgsError, OutputFileAccessError
from . import exceptions as ocrmypdf_exceptions
from ._unicodefun import verify_python3_env

warnings.simplefilter('ignore', pypdf.utils.PdfReadWarning)


# -------------
# External dependencies

MINIMUM_TESS_VERSION = '3.04'

HOCR_OK_LANGS = frozenset([
    'eng', 'deu', 'spa', 'ita', 'por'
])

def complain(message):
    print(*textwrap.wrap(message), file=sys.stderr)


# Hack to help debugger context find /usr/local/bin
if 'IDE_PROJECT_ROOTS' in os.environ:
    os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']

# -------- 
# Critical environment tests

verify_python3_env()

if tesseract.version() < MINIMUM_TESS_VERSION:
    complain(
        "Please install tesseract {0} or newer "
        "(currently installed version is {1})".format(
            MINIMUM_TESS_VERSION, tesseract.version()))
    sys.exit(ExitCode.missing_dependency)

# -------------
# Parser

parser = argparse.ArgumentParser(
    prog=PROGRAM_NAME,
    fromfile_prefix_chars='@',
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
    'input_file', metavar="input_pdf_or_image",
    help="PDF file containing the images to be OCRed (or '-' to read from "
         "standard input)")
parser.add_argument(
    'output_file', metavar="output_pdf",
    help="Output searchable PDF file (or '-' to write to standard output). "
         "Existing files will be ovewritten. If same as input file, the "
         "input file will be updated only if processing is successful.")
parser.add_argument(
    '-l', '--language', action='append',
    help="Language(s) of the file to be OCRed (see tesseract --list-langs for "
         "all language packs installed in your system). Use -l eng+deu for "
         "multiple languages.")
parser.add_argument(
    '--image-dpi', metavar='DPI', type=int,
    help="For input image instead of PDF, use this DPI instead of file's.")
parser.add_argument(
    '--output-type', choices=['pdfa', 'pdf', 'pdfa-1', 'pdfa-2'], 
    default='pdfa',
    help="Choose output type. 'pdfa' creates a PDF/A-2b compliant file for "
         "long term archiving (default, recommended) but may not suitable "
         "for users who want their file altered as little as possible. 'pdfa' "
         "also has problems with full Unicode text. 'pdf' attempts to "
         "preserve file contents as much as possible. 'pdf-a1' creates a "
         "PDF/A1-b file. 'pdf-a2' is equivalent to 'pdfa'."
         )

# Use null string '\0' as sentinel to indicate the user supplied no argument,
# since that is the only invalid character for filepaths on all platforms
# bool('\0') is True in Python
parser.add_argument(
    '--sidecar', nargs='?', const='\0', default=None, metavar='FILE',
    help="Generate sidecar text files that contain the same text recognized "
         "by Tesseract. This may be useful for building a OCR text database. "
         "If FILE is omitted, the sidecar file be named {output_file}.txt "
         "If FILE is set to '-', the sidecar is written to stdout (a "
         "convenient way to preview OCR quality). The output file and sidecar "
         "may not both use stdout at the same time.")

parser.add_argument(
    '--version', action='version', version=VERSION,
    help="Print program version and exit")

jobcontrol = parser.add_argument_group(
    "Job control options")
jobcontrol.add_argument(
    '-j', '--jobs', metavar='N', type=int,
    help="Use up to N CPU cores simultaneously (default: use all).")
jobcontrol.add_argument(
    '-q', '--quiet', action='store_true', help="Suppress INFO messages")
jobcontrol.add_argument(
    '-v', '--verbose', const="+", default=[], nargs='?', action="append",
    help="Print more verbose messages for each additional verbose level")

metadata = parser.add_argument_group(
    "Metadata options",
    "Set output PDF/A metadata (default: copy input document's metadata)")
metadata.add_argument(
    '--title', type=str,
    help="Set document title (place multiple words in quotes)")
metadata.add_argument(
    '--author', type=str,
    help="Set document author")
metadata.add_argument(
    '--subject', type=str,
    help="Set document subject description")
metadata.add_argument(
    '--keywords', type=str,
    help="Set document keywords")

preprocessing = parser.add_argument_group(
    "Image preprocessing options",
    "Options to improve the quality of the final PDF and OCR")
preprocessing.add_argument(
    '-r', '--rotate-pages', action='store_true',
    help="Automatically rotate pages based on detected text orientation")
preprocessing.add_argument(
    '--remove-background', action='store_true',
    help="Attempt to remove background from gray or color pages, setting it "
         "to white ")
preprocessing.add_argument(
    '-d', '--deskew', action='store_true',
    help="Deskew each page before performing OCR")
preprocessing.add_argument(
    '-c', '--clean', action='store_true',
    help="Clean pages from scanning artifacts before performing OCR, and send "
         "the cleaned page to OCR, but do not include the cleaned page in "
         "the output")
preprocessing.add_argument(
    '-i', '--clean-final', action='store_true',
    help="Clean page as above, and incorporate the cleaned image in the final "
         "PDF.  Might remove desired content.")
preprocessing.add_argument(
    '--oversample', metavar='DPI', type=int, default=0,
    help="Oversample images to at least the specified DPI, to improve OCR "
         "results slightly")

ocrsettings = parser.add_argument_group(
    "OCR options",
    "Control how OCR is applied")
ocrsettings.add_argument(
    '-f', '--force-ocr', action='store_true',
    help="Rasterize any fonts or vector objects on each page, apply OCR, and "
         "save the rastered output (this rewrites the PDF)")
ocrsettings.add_argument(
    '-s', '--skip-text', action='store_true',
    help="Skip OCR on any pages that already contain text, but include the "
         "page in final output; useful for PDFs that contain a mix of "
         "images, text pages, and/or previously OCRed pages")
# ocrsettings.add_argument(
#     '--redo-ocr', action='store_true',
#     help="removing any existing OCR text, but otherwise preserve mixed PDF "
#          "pages")

ocrsettings.add_argument(
    '--skip-big', type=float, metavar='MPixels',
    help="Skip OCR on pages larger than the specified amount of megapixels, "
         "but include skipped pages in final output")

advanced = parser.add_argument_group(
    "Advanced",
    "Advanced options to control Tesseract's OCR behavior")
advanced.add_argument(
    '--max-image-mpixels', action='store', type=float, metavar='MPixels',
    help="Set maximum number of pixels to unpack before treating an image as a "
         "decompression bomb",
    default=128.0)
advanced.add_argument(
    '--tesseract-config', action='append', metavar='CFG', default=[],
    help="Additional Tesseract configuration files -- see documentation")
advanced.add_argument(
    '--tesseract-pagesegmode', action='store', type=int, metavar='PSM',
    choices=range(0, 14),
    help="Set Tesseract page segmentation mode (see tesseract --help)")
advanced.add_argument(
    '--tesseract-oem', action='store', type=int, metavar='MODE',
    choices=range(0, 4),
    help=("Set Tesseract 4.0 OCR engine mode: "
         "0 - original Tesseract only; "
         "1 - neural nets LSTM only; "
         "2 - Tesseract + LSTM; "
         "3 - default.")
    )
advanced.add_argument(
    '--pdf-renderer',
    choices=['auto', 'tesseract', 'hocr', 'tess4', 'sandwich'], default='auto',
    help="Choose OCR PDF renderer - the default option is to let OCRmyPDF "
         "choose."
         "auto - let OCRmyPDF choose; "
         "sandwich - default renderer for Tesseract 3.05.01 and newer; "
         "hocr - default renderer for older versions of Tesseract; "
         "tesseract - gives better results for non-Latin languages and "
         "Tesseract older than 3.05.01 but has problems with some versions "
         " of Ghostscript; deprecated"
         "tess4 - deprecated alias for 'sandwich'"
    )
advanced.add_argument(
    '--tesseract-timeout', default=180.0, type=float, metavar='SECONDS',
    help='Give up on OCR after the timeout, but copy the preprocessed page '
         'into the final output')
advanced.add_argument(
    '--rotate-pages-threshold', default=14.0, type=float, metavar='CONFIDENCE',
    help="Only rotate pages when confidence is above this value (arbitrary "
         "units reported by tesseract)")
advanced.add_argument(
    '--pdfa-image-compression', choices=['auto', 'jpeg', 'lossless'],
    default='auto',
    help="Specify how to compress images in the output PDF/A. 'auto' lets "
         "OCRmyPDF decide.  'jpeg' changes all grayscale and color images to "
         "JPEG compression.  'lossless' uses PNG-style lossless compression "
         "for all images.  Monochrome images are always compressed using a "
         "lossless codec.  Compression settings "
         "are applied to all pages, including those for which OCR was "
         "skipped.  Not supported for --output-type=pdf ; that setting "
         "preserves the original compression of all images.")
advanced.add_argument(
    '--user-words', metavar='FILE',
    help="Specify the location of the Tesseract user words file. This is a "
         "list of words Tesseract should consider while performing OCR in "
         "addition to its standard language dictionaries. This can improve "
         "OCR quality especially for specialized and technical documents.")
advanced.add_argument(
    '--user-patterns', metavar='FILE',
    help="Specify the location of the Tesseract user patterns file.")

debugging = parser.add_argument_group(
    "Debugging",
    "Arguments to help with troubleshooting and debugging")
debugging.add_argument(
    '-k', '--keep-temporary-files', action='store_true',
    help="Keep temporary files (helpful for debugging)")
debugging.add_argument(
    '-g', '--debug-rendering', action='store_true',
    help="Render each page twice with debug information on second page")
debugging.add_argument(
    '--flowchart', type=str,
    help="Generate the pipeline execution flowchart")


def check_options_languages(options, _log):
    if not options.language:
        options.language = ['eng']  # Enforce English hegemony

    # Support v2.x "eng+deu" language syntax
    if '+' in options.language[0]:
        options.language = options.language[0].split('+')

    languages = set(options.language)
    if not languages.issubset(tesseract.languages()):
        msg = (
            "The installed version of tesseract does not have language "
            "data for the following requested languages: \n")
        for lang in (languages - tesseract.languages()):
            msg += lang + '\n'
        raise MissingDependencyError(msg)


def check_options_output(options, log):
    if options.pdf_renderer == 'auto':
        if tesseract.has_textonly_pdf():
            options.pdf_renderer = 'sandwich'
        else:
            options.pdf_renderer = 'hocr'

    if options.pdf_renderer == 'sandwich' and not tesseract.has_textonly_pdf():
        raise MissingDependencyError(
            "The 'sandwich' renderer requires Tesseract 3.05.01 or newer; "
            "or Tesseract 4.00 alpha newer than February 2017.")

    if options.pdf_renderer == 'tess4':
        log.warning("The 'tess4' PDF renderer has been renamed to 'sandwich'. "
                    "Please use --pdf-renderer=sandwich.")
        options.pdf_renderer = 'sandwich'

    if options.pdf_renderer == 'tesseract':
        if tesseract.version() < '3.05' and \
                options.output_type.startswith('pdfa'):
            log.warning(
                "For best results use --pdf-renderer=tesseract "
                "--output-type=pdf to disable PDF/A generation via "
                "Ghostscript, which is known to corrupt the OCR text of "
                "some PDFs produced your version of Tesseract.")
        elif tesseract.has_textonly_pdf():
            log.warning(
                "The argument --pdf-renderer=tesseract provides support for "
                "versions of tesseract older than your version. For best "
                "results omit this argument and let OCRmyPDF choose the "
                "best available renderer.")

    if options.debug_rendering and options.pdf_renderer != 'hocr':
        log.info(
            "Ignoring --debug-rendering because it requires --pdf-renderer=hocr")

    lossless_reconstruction = False
    if options.pdf_renderer in ('hocr', 'sandwich'):
        if not any((options.deskew, options.clean_final, options.force_ocr,
                   options.remove_background)):
            lossless_reconstruction = True
    options.lossless_reconstruction = lossless_reconstruction


def check_options_sidecar(options, log):
    if options.sidecar == '\0':
        if options.output_file == '-':
            raise argparse.ArgumentError(
                None,
                "--sidecar filename must be specified when output file is "
                "stdout.")
        options.sidecar = options.output_file + '.txt'


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
            None,
            "Error: --force-ocr and --skip-text are mutually incompatible.")

    # if options.redo_ocr and (options.skip_text or options.force_ocr):
    #     raise argparse.ArgumentError(
    #         "Error: --redo-ocr and other OCR options are incompatible.")
    languages = set(options.language)
    if options.pdf_renderer == 'hocr' and \
            not languages.issubset(HOCR_OK_LANGS):
        msg = (
            "The 'hocr' PDF renderer is known to cause problems with one "
            "or more of the languages in your document. ")

        if tesseract.has_textonly_pdf():
            msg += (
                "Use --pdf-renderer auto (the default) to avoid this issue.")
        else:
            msg += (
                "Use --pdf-renderer tesseract --output-type pdf to avoid "
                "this issue")
        log.warning(msg)
    elif ghostscript.version() < '9.20' and \
            not languages.issubset(HOCR_OK_LANGS) \
            and options.output_type != 'pdf':
        msg = (
            "The installed version of Ghostscript does not work correctly "
            "with the OCR languages you specified. Use --output-type pdf or "
            "upgrade to Ghostscript 9.20 or later to avoid this issue.")
        msg += "Found Ghostscript {}".format(ghostscript.version())
        log.warning(msg)


def check_options_advanced(options, log):
    if tesseract.v4():
        log.info(
            "Tesseract v4.x.alpha found.")
    if options.tesseract_oem and not tesseract.v4():
        log.warning(
            "--tesseract-oem requires Tesseract 4.x -- argument ignored")
    if options.pdf_renderer == 'tess4' and not tesseract.has_textonly_pdf():
        raise MissingDependencyError(
            "--pdf-renderer tess4 requires Tesseract 4.x "
            "commit 3d9fb3b or later")
    if options.pdfa_image_compression != 'auto' and \
            options.output_type.startswith('pdfa'):
        log.warning(
            "--pdfa-image-compression argument has no effect when "
            "--output-type is not 'pdfa', 'pdfa-1', or 'pdfa-2'"
        )


def check_options_metadata(options, log):
    import unicodedata
    docinfo = [options.title, options.author, options.keywords,
               options.subject]
    for s in (m for m in docinfo if m):
        for c in s:
            if unicodedata.category(c) == 'Co' or ord(c) >= 0x10000:
                raise ValueError(
                    "One of the metadata strings contains "
                    "an unsupported Unicode character: '{}' (U+{})".format(
                        c, hex(ord(c))[2:].upper()
                ))


def check_options_pillow(options, log):
    PIL.Image.MAX_IMAGE_PIXELS = int(options.max_image_mpixels * 1000000)
    if PIL.Image.MAX_IMAGE_PIXELS == 0:
        PIL.Image.MAX_IMAGE_PIXELS = None


def check_options(options, log):
    try:
        check_options_languages(options, log)
        check_options_metadata(options, log)
        check_options_output(options, log)
        check_options_sidecar(options, log)
        check_options_preprocessing(options, log)
        check_options_ocr_behavior(options, log)
        check_options_advanced(options, log)
        check_options_pillow(options, log)
    except ValueError as e:
        log.error(e)
        sys.exit(ExitCode.bad_args)
    except argparse.ArgumentError as e:
        log.error(e)
        sys.exit(ExitCode.bad_args)
    except MissingDependencyError as e:
        log.error(e)
        sys.exit(ExitCode.missing_dependency)


# ----------
# Logging


def logging_factory(logger_name, logger_args):
    verbose = logger_args['verbose']
    quiet = logger_args['quiet']

    root_logger = logging.getLogger(logger_name)
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stderr)
    formatter_ = logging.Formatter("%(levelname)7s - %(message)s")
    handler.setFormatter(formatter_)
    if verbose:
        handler.setLevel(logging.DEBUG)
    elif quiet:
        handler.setLevel(logging.WARNING)
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
    msg = re.sub(r'\s+', r' ', msg)
    msg = re.sub(r"\((.+?)\)", r'\1', msg)
    msg = msg.strip()
    return msg


def do_ruffus_exception(ruffus_five_tuple, options, log):
    """Replace the elaborate ruffus stack trace with a user friendly
    description of the error message that occurred."""
    exit_code = None

    task_name, job_name, exc_name, exc_value, exc_stack = ruffus_five_tuple
    job_name = job_name  # unused
    if exc_name == 'builtins.SystemExit':
        match = re.search(r"\.(.+?)\)", exc_value)
        exit_code_name = match.groups()[0]
        exit_code = getattr(ExitCode, exit_code_name, 'other_error')        
    elif exc_name == 'ruffus.ruffus_exceptions.MissingInputFileError':
        log.error(cleanup_ruffus_error_message(exc_value))
        exit_code = ExitCode.input_file
    elif exc_name == 'builtins.TypeError':
        # Even though repair_pdf will fail, ruffus will still try
        # to call split_pages with no input files, likely due to a bug
        if task_name == 'split_pages':
            log.error("Input file '{0}' is not a valid PDF".format(
                options.input_file))
            exit_code = ExitCode.input_file
    elif exc_name == 'builtins.KeyboardInterrupt':
        log.error("Interrupted by user")
        exit_code = ExitCode.ctrl_c
    elif exc_name == 'subprocess.CalledProcessError':
        # It's up to the subprocess handler to report something useful
        msg = "Error occurred while running this command:"
        log.error(msg + '\n' + exc_value)
        exit_code = ExitCode.child_process_error
    elif (exc_name == 'PyPDF2.utils.PdfReadError' and \
            'not been decrypted' in exc_value) or \
            (exc_name == 'ocrmypdf.exceptions.EncryptedPdfError'):
        log.error(textwrap.dedent("""\
            Input PDF is encrypted. The encryption must be removed to
            perform OCR. 

            For information about this PDF's security use
                qpdf --show-encryption infilename

            You can remove the encryption using
                qpdf --decrypt [--password=[password]] infilename

            """))
        exit_code = ExitCode.encrypted_pdf        
    elif exc_name == 'ocrmypdf.exceptions.PdfMergeFailedError':
        log.error(textwrap.dedent("""\
            Failed to merge PDF image layer with OCR layer

            Usually this happens because the input PDF file is mal-formed and
            ocrmypdf cannot automatically correct the problem on its own.

            Try using
                ocrmypdf --pdf-renderer tesseract  [..other args..]
            """))
        exit_code = ExitCode.input_file
    elif exc_name.startswith('ocrmypdf.exceptions.'):
        base_exc_name = exc_name.replace('ocrmypdf.exceptions.', '')
        exc_class = getattr(ocrmypdf_exceptions, base_exc_name)
        exit_code = exc_class.exit_code
    elif exc_name == 'PIL.Image.DecompressionBombError':
        msg = cleanup_ruffus_error_message(exc_value)
        msg += ("\nUse the --max-image-mpixels argument to set increase the "
                "maximum number of megapixels to accept.")
        log.error(msg)
        exit_code = ExitCode.input_file

    if exit_code is not None:
        return exit_code

    if not options.verbose:
        log.error(exc_stack)
    return ExitCode.other_error


def traverse_ruffus_exception(e_args, options, log):
    """Walk through a RethrownJobError and find the first exception.

    Ruffus flattens exception to 5 element tuples. Because of a bug
    in <= 2.6.3 it may present either the single:
      (task, job, exc, value, stack)
    or something like:
      [[(task, job, exc, value, stack)]]
    
    Generally cross-process exception marshalling doesn't work well
    and ruffus doesn't support because BaseException has its own
    implementation of __reduce__ that attempts to reconstruct the
    exception based on e.__init__(e.args).
    
    Attempting to log the exception directly marshalls it to the logger
    which is probably in another process, so it's better to log only
    data from the exception at this point.

    The exit code will be based on this, even if multiple exceptions occurred
    at the same time."""

    if isinstance(e_args, Sequence) and isinstance(e_args[0], str) and \
            len(e_args) == 5:
        return do_ruffus_exception(e_args, options, log)
    elif is_iterable_notstr(e_args):
        for exc in e_args:
            return traverse_ruffus_exception(exc, options, log)


def check_closed_streams(options):
    """Work around Python issue with multiprocessing forking on closed streams

    https://bugs.python.org/issue28326

    Attempting to a fork/exec a new Python process when any of std{in,out,err}
    are closed or not flushable for some reason may raise an exception.
    Fix this by opening devnull if the handle seems to be closed.  Do this
    globally to avoid tracking places all places that fork.

    Seems to be specific to multiprocessing.Process not all Python process
    forkers.

    The error actually occurs when the stream object is not flushable,
    but replacing an open stream object that is not flushable with
    /dev/null is a bad idea since it will create a silent failure.  Replacing
    a closed handle with /dev/null seems safe.

    """

    if sys.version_info[0:3] >= (3, 6, 4):
        return True  # Issued fixed in Python 3.6.4+

    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

    if sys.stdin is None:
        if options.input_file == '-':
            print("Trying to read from stdin but stdin seems closed",
                  file=sys.stderr)
            return False
        sys.stdin = open(os.devnull, 'r')

    if sys.stdout is None:
        if options.output_file == '-':
            # Can't replace stdout if the user is piping
            # If this case can even happen, it must be some kind of weird
            # stream.
            print(textwrap.dedent("""\
                Output was set to stdout '-' but the stream attached to
                stdout does not support the flush() system call.  This
                will fail."""), file=sys.stderr)
            return False
        sys.stdout = open(os.devnull, 'w')

    return True


def log_page_orientations(pdfinfo, _log):
    direction = {0: 'n', 90: 'e',
                180: 's', 270: 'w'}
    orientations = []
    for n, page in enumerate(pdfinfo):
        angle = page.rotation or 0
        if angle != 0:
            orientations.append('{0}{1}'.format(
                n + 1,
                direction.get(angle, '')))
    if orientations:
        _log.info('Page orientations detected: ' + ' '.join(orientations))


def preamble(_log):
    _log.debug('ocrmypdf ' + VERSION)
    _log.debug('tesseract ' + tesseract.version())
    _log.debug('qpdf ' + qpdf.version())


def check_input_file(options, _log, start_input_file):
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
            raise InputFileError()


def check_output_file(options, _log):
    if options.output_file == '-':
        if sys.stdout.isatty():
            _log.error(textwrap.dedent("""\
                Output was set to stdout '-' but it looks like stdout
                is connected to a terminal.  Please redirect stdout to a
                file."""))
            raise BadArgsError()
    elif not is_file_writable(options.output_file):
        _log.error(
            "Output file location (" + options.output_file + ") " +
            "is not a writable file.")
        raise OutputFileAccessError()


def run_pipeline():
    options = parser.parse_args()
    options.verbose_abbreviated_path = 1

    if not check_closed_streams(options):
        return ExitCode.bad_args

    logger_args = {'verbose': options.verbose, 'quiet': options.quiet}

    _log, _log_mutex = proxy_logger.make_shared_logger_and_proxy(
        logging_factory, __name__, logger_args)
    preamble(_log)
    check_options(options, _log)

    # Complain about qpdf version < 7.0.0
    # Suppress the warning if in the test suite, since there are no PPAs
    # for qpdf 7.0.0 for Ubuntu trusty (i.e. Travis)
    if qpdf.version() < '7.0.0' and not os.environ.get('PYTEST_CURRENT_TEST'):
        complain(
            "You are using qpdf version {0} which has known issues including "
            "security vulnerabilities with certain malformed PDFs. Consider "
            "upgrading to version 7.0.0 or newer.".format(qpdf.version()))

    # Any changes to options will not take effect for options that are already
    # bound to function parameters in the pipeline. (For example
    # options.input_file, options.pdf_renderer are already bound.)
    if not options.jobs:
        options.jobs = available_cpu_count()

    # Performance is improved by setting Tesseract to single threaded. In tests
    # this gives better throughput than letting a smaller number of Tesseract
    # jobs run multithreaded.
    if tesseract.v4():
        os.environ.setdefault('OMP_THREAD_LIMIT', '1')

    try:
        work_folder = mkdtemp(prefix="com.github.ocrmypdf.")
        options.history_file = os.path.join(
            work_folder, 'ruffus_history.sqlite')
        start_input_file = os.path.join(
            work_folder, 'origin')

        check_input_file(options, _log, start_input_file)
        check_output_file(options, _log)

        manager = JobContextManager()
        manager.register('JobContext', JobContext)  # pylint: disable=no-member
        manager.start()

        context = manager.JobContext()  # pylint: disable=no-member
        context.set_options(options)
        context.set_work_folder(work_folder)

        build_pipeline(options, work_folder, _log, context)
        atexit.register(cleanup_working_files, work_folder, options)
        cmdline.run(options)
    except ruffus_exceptions.RethrownJobError as e:
        if options.verbose:
            _log.debug(str(e))  # stringify exception so logger doesn't have to
        exitcode = traverse_ruffus_exception(e.args, options, _log)
        if exitcode is None:
            _log.error("Unexpected ruffus exception: " + str(e))
            _log.error(repr(e))
            return ExitCode.other_error
        return exitcode
    except ExitCodeException as e:
        return e.exit_code
    except Exception as e:
        _log.error(e)
        return ExitCode.other_error

    if options.flowchart:
        _log.info("Flowchart saved to {}".format(options.flowchart))
    elif options.output_file == '-':
        _log.info("Output sent to stdout")
    elif os.path.samefile(options.output_file, os.devnull):
        pass  # Say nothing when sending to dev null
    else:
        if options.output_type.startswith('pdfa'):
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

    pdfinfo = context.get_pdfinfo()
    if options.verbose:
        from pprint import pformat
        _log.debug(pformat(pdfinfo))

    log_page_orientations(pdfinfo, _log)

    return ExitCode.ok


if __name__ == '__main__':
    sys.exit(run_pipeline())
