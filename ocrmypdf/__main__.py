#!/usr/bin/env python3
# © 2015-16 James R. Barlow: github.com/jbarlow83

from contextlib import suppress
from tempfile import mkdtemp
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

from functools import partial

# from ruffus import transform, suffix, merge, active_if, regex, \
#     formatter, split, collate, graphviz, \
#     posttask, Pipeline
from ruffus import formatter, regex, Pipeline, suffix

import ruffus.ruffus_exceptions as ruffus_exceptions
import ruffus.cmdline as cmdline
import ruffus.proxy_logger as proxy_logger

from .hocrtransform import HocrTransform
from .pageinfo import pdf_get_all_pageinfo
from .pdfa import generate_pdfa_def, file_claims_pdfa
from . import ghostscript
from . import tesseract
from . import qpdf
from . import leptonica
from . import ExitCode, page_number, is_iterable_notstr, VERSION
from collections.abc import Sequence

warnings.simplefilter('ignore', pypdf.utils.PdfReadWarning)


BASEDIR = os.path.dirname(os.path.realpath(__file__))

VECTOR_PAGE_DPI = 400


_log = None


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

try:
    import PIL.features
    check_codec = PIL.features.check_codec
except (ImportError, AttributeError):
    def check_codec(codec_name):
        if codec_name == 'jpg':
            return 'jpeg_encoder' in dir(Image.core)
        elif codec_name == 'zlib':
            return 'zip_encoder' in dir(Image.core)
        raise NotImplementedError(codec_name)


def check_pil_encoder(codec_name, friendly_name):
    try:
        if check_codec(codec_name):
            return
    except Exception:
        pass
    complain(
        "ERROR: Your version of the Python imaging library (Pillow) was "
        "compiled without support for " + friendly_name + " encoding/decoding."
        "\n"
        "You will need to uninstall Pillow and reinstall it with PNG and JPEG "
        "support (libjpeg and zlib)."
        "\n"
        "See installation instructions for your platform here:\n"
        "    https://pillow.readthedocs.org/installation.html"
    )
    sys.exit(ExitCode.missing_dependency)


check_pil_encoder('jpg', 'JPEG')
check_pil_encoder('zlib', 'PNG')


# -------------
# Parser

parser = cmdline.get_argparse(
    prog="ocrmypdf",
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
    help="additional Tesseract configuration files")
advanced.add_argument(
    '--tesseract-pagesegmode', action='store', type=int, metavar='PSM',
    help="set Tesseract page segmentation mode (see tesseract --help)")
advanced.add_argument(
    '--pdf-renderer', choices=['auto', 'tesseract', 'hocr'], default='auto',
    help="choose OCR PDF renderer - the default option is to let OCRmyPDF "
         "choose.  The 'tesseract' PDF renderer is more accurate and does a "
         "better job and document structure such as recognizing columns. It "
         "also does a better job on non-Latin languages. However, it does "
         "not work as well when older versions of Tesseract or Ghostscript "
         "are installed, and some combinations of arguments to do not work "
         "with --pdf-renderer tesseract.")
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

_options = parser.parse_args()


# ----------
# Languages

if not _options.language:
    _options.language = ['eng']  # Enforce English hegemony

# Support v2.x "eng+deu" language syntax
if '+' in _options.language[0]:
    _options.language = _options.language[0].split('+')

if not set(_options.language).issubset(tesseract.languages()):
    complain(
        "The installed version of tesseract does not have language "
        "data for the following requested languages: ")
    for lang in (set(_options.language) - tesseract.languages()):
        complain(lang)
    sys.exit(ExitCode.bad_args)


# ----------
# Arguments

_options.verbose_abbreviated_path = 1

if _options.pdf_renderer == 'auto':
    _options.pdf_renderer = 'hocr'

if _options.pdf_renderer == 'tesseract' and tesseract.version() < '3.04.01' \
        and os.environ.get('OCRMYPDF_SHARP_TTF', '') != '1':
    complain(
        "WARNING: Your version of tesseract has problems with PDF output. "
        "Some PDF viewers will fail to find searchable text.\n"
        "--pdf-renderer=tesseract is not recommended.")

if any((_options.clean, _options.clean_final)):
    try:
        from . import unpaper
        if unpaper.version() < '6.1':
            complain(
                "The installed 'unpaper' is not supported. "
                "Install version 6.1 or newer.")
            sys.exit(ExitCode.missing_dependency)
    except FileNotFoundError:
        complain(
            "Install the 'unpaper' program to use --deskew or --clean.")
        sys.exit(ExitCode.missing_dependency)
else:
    unpaper = None

if _options.debug_rendering and _options.pdf_renderer == 'tesseract':
    complain(
        "Ignoring --debug-rendering because it is not supported with"
        "--pdf-renderer=tesseract.")

if _options.force_ocr and _options.skip_text:
    complain(
        "Error: --force-ocr and --skip-text are mutually incompatible.")
    sys.exit(ExitCode.bad_args)

if _options.clean and not _options.clean_final \
        and _options.pdf_renderer == 'tesseract':
    complain(
        "Tesseract PDF renderer cannot render --clean pages without "
        "also performing --clean-final, so --clean-final is assumed.")

if set(_options.language) & {'chi_sim', 'chi_tra'} \
        and (_options.pdf_renderer == 'hocr' or _options.output_type == 'pdfa'):
    complain(
        "Your settings are known to cause problems with OCR of Chinese text. "
        "Try adding these arguments: "
        "    ocrmypdf --pdf-renderer tesseract --output-type pdf")

lossless_reconstruction = False
if _options.pdf_renderer == 'hocr':
    if not _options.deskew and not _options.clean_final and \
            not _options.force_ocr and not _options.remove_background:
        lossless_reconstruction = True


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


_log, _log_mutex = proxy_logger.make_shared_logger_and_proxy(
        logging_factory, __name__, [None, _options.verbose])
_log.debug('ocrmypdf ' + VERSION)


def re_symlink(input_file, soft_link_name, log=_log):
    """
    Helper function: relinks soft symbolic link if necessary
    """

    # Guard against soft linking to oneself
    if input_file == soft_link_name:
        log.debug("Warning: No symbolic link made. You are using " +
                  "the original data directory as the working directory.")
        return

    # Soft link already exists: delete for relink?
    if os.path.lexists(soft_link_name):
        # do not delete or overwrite real (non-soft link) file
        if not os.path.islink(soft_link_name):
            raise FileExistsError(
                "%s exists and is not a link" % soft_link_name)
        try:
            os.unlink(soft_link_name)
        except:
            log.debug("Can't unlink %s" % (soft_link_name))

    if not os.path.exists(input_file):
        raise FileNotFoundError(
            "trying to create a broken symlink to %s" % input_file)

    log.debug("os.symlink(%s, %s)" % (input_file, soft_link_name))

    # Create symbolic link using absolute path
    os.symlink(
        os.path.abspath(input_file),
        soft_link_name
    )


# -------------
# Pipeline state manager

class JobContext:
    """Holds our context for a particular run of the pipeline

    A multiprocessing manager effectively creates a separate process
    that keeps the master job context object.  Other threads access
    job context via multiprocessing proxy objects.

    While this would naturally lend itself @property's it seems to make
    a little more sense to use functions to make it explicitly that the
    invocation requires marshalling data across a process boundary.

    """

    def __init__(self):
        self.pdfinfo = []

    def get_pdfinfo(self):
        "What we know about the input PDF"
        return self.pdfinfo

    def set_pdfinfo(self, pdfinfo):
        self.pdfinfo = pdfinfo

    def get_options(self):
        return self.options

    def set_options(self, options):
        self.options = options

    def get_work_folder(self):
        return self.work_folder

    def set_work_folder(self, work_folder):
        self.work_folder = work_folder


from multiprocessing.managers import BaseManager
class JobContextManager(BaseManager):
    pass


manager = JobContextManager()
manager.register('JobContext', JobContext)
manager.start()

_context = manager.JobContext()


# -------------
# The Pipeline


def done_task(caller):
    "Useful as debug hook"
    pass


def cleanup_working_files(work_folder, options):
    if options.keep_temporary_files:
        print("Temporary working files saved at:\n{0}".format(work_folder),
              file=sys.stderr)
    else:
        with suppress(FileNotFoundError):
            shutil.rmtree(work_folder)


def triage_image_file(input_file, output_file, log, options):
    try:
        log.info("Input file is not a PDF, checking if it is an image...")
        im = Image.open(input_file)
    except EnvironmentError as e:
        msg = str(e)

        # Recover the original filename
        realpath = ''
        if os.path.islink(input_file):
            realpath = os.path.realpath(input_file)
        elif os.path.isfile(input_file):
            realpath = '<stdin>'
        msg = msg.replace(input_file, realpath)
        log.error(msg)
        sys.exit(ExitCode.input_file)
        return
    else:
        log.info("Input file is an image")

        if 'dpi' in im.info:
            if im.info['dpi'] <= (96, 96) and not options.image_dpi:
                log.info("Image size: (%d, %d)" % im.size)
                log.info("Image resolution: (%d, %d)" % im.info['dpi'])
                log.error(
                    "Input file is an image, but the resolution (DPI) is "
                    "not credible.  Estimate the resolution at which the "
                    "image was scanned and specify it using --image-dpi.")
                sys.exit(ExitCode.input_file)
        elif not options.image_dpi:
            log.info("Image size: (%d, %d)" % im.size)
            log.error(
                "Input file is an image, but has no resolution (DPI) "
                "in its metadata.  Estimate the resolution at which "
                "image was scanned and specify it using --image-dpi.")
            sys.exit(ExitCode.input_file)

        if 'iccprofile' not in im.info:
            if im.mode == 'RGB':
                log.info('Input image has no ICC profile, assuming sRGB')
            elif im.mode == 'CMYK':
                log.info('Input CMYK image has no ICC profile, not usable')
                sys.exit(ExitCode.input_file)
        im.close()

    try:
        log.info("Image seems valid. Try converting to PDF...")
        layout_fun = img2pdf.default_layout_fun
        if options.image_dpi:
            layout_fun = img2pdf.get_fixed_dpi_layout_fun(
                (options.image_dpi, options.image_dpi))
        with open(output_file, 'wb') as outf:
            img2pdf.convert(
                input_file,
                layout_fun=layout_fun,
                with_pdfrw=False,
                outputstream=outf)
        log.info("Successfully converted to PDF, processing...")
    except img2pdf.ImageOpenError as e:
        log.error(e)
        sys.exit(ExitCode.input_file)


def triage(
        input_file,
        output_file,
        log,
        context):

    try:
        with open(input_file, 'rb') as f:
            signature = f.read(4)
            if signature == b'%PDF':
                re_symlink(input_file, output_file)
                return
    except EnvironmentError as e:
        log.error(e)
        sys.exit(ExitCode.input_file)

    options = context.get_options()
    triage_image_file(input_file, output_file, log, options)


def repair_pdf(
        input_file,
        output_file,
        log,
        context):

    qpdf.repair(input_file, output_file, log)
    pdfinfo = pdf_get_all_pageinfo(output_file)
    context.set_pdfinfo(pdfinfo)
    log.debug(pdfinfo)


def get_pageinfo(input_file, context):
    pageno = int(os.path.basename(input_file)[0:6]) - 1
    pageinfo = context.get_pdfinfo()[pageno].copy()
    return pageinfo


def get_page_dpi(pageinfo, options):
    "Get the DPI when nonsquare DPI is tolerable"
    xres = max(pageinfo.get('xres', VECTOR_PAGE_DPI), options.oversample or 0)
    yres = max(pageinfo.get('yres', VECTOR_PAGE_DPI), options.oversample or 0)
    return (float(xres), float(yres))


def get_page_square_dpi(pageinfo, options):
    "Get the DPI when we require xres == yres"
    return float(max(
        pageinfo.get('xres', VECTOR_PAGE_DPI),
        pageinfo.get('yres', VECTOR_PAGE_DPI),
        options.oversample or 0))


def is_ocr_required(pageinfo, log, options):
    page = pageinfo['pageno'] + 1
    ocr_required = True
    if not pageinfo['images']:
        if options.force_ocr and options.oversample:
            # The user really wants to reprocess this file
            log.info(
                "{0:4d}: page has no images - "
                "rasterizing at {1} DPI because "
                "--force-ocr --oversample was specified".format(
                    page, options.oversample))
        elif options.force_ocr:
            # Warn the user they might not want to do this
            log.warning(
                "{0:4d}: page has no images - "
                "all vector content will be "
                "rasterized at {1} DPI, losing some resolution and likely "
                "increasing file size. Use --oversample to adjust the "
                "DPI.".format(page, VECTOR_PAGE_DPI))
        else:
            log.info(
                "{0:4d}: page has no images - "
                "skipping all processing on this page".format(page))
            ocr_required = False

    elif pageinfo['has_text']:
        msg = "{0:4d}: page already has text! – {1}"

        if not options.force_ocr and not options.skip_text:
            log.error(msg.format(page,
                                 "aborting (use --force-ocr to force OCR)"))
            sys.exit(ExitCode.already_done_ocr)
        elif options.force_ocr:
            log.info(msg.format(page,
                                "rasterizing text and running OCR anyway"))
            ocr_required = True
        elif options.skip_text:
            log.info(msg.format(page,
                                "skipping all processing on this page"))
            ocr_required = False

    if ocr_required and options.skip_big:
        pixel_count = pageinfo['width_pixels'] * pageinfo['height_pixels']
        if pixel_count > (options.skip_big * 1000000):
            ocr_required = False
            log.warning(
                "{0:4d}: page too big, skipping OCR "
                "({1:.1f} MPixels > {2:.1f} MPixels --skip-big)".format(
                    page, pixel_count / 1000000, options.skip_big))
    return ocr_required


def split_pages(
        input_files,
        output_files,
        log,
        context):

    options = context.get_options()
    work_folder = context.get_work_folder()

    if is_iterable_notstr(input_files):
        input_file = input_files[0]
    else:
        input_file = input_files

    for oo in output_files:
        with suppress(FileNotFoundError):
            os.unlink(oo)

    # If no files were repaired the input will be empty
    if not input_file:
        log.error("{0}: file not found or invalid argument".format(
                options.input_file))
        sys.exit(ExitCode.input_file)

    npages = qpdf.get_npages(input_file, log)
    qpdf.split_pages(input_file, work_folder, npages)

    from glob import glob
    for filename in glob(os.path.join(work_folder, '*.page.pdf')):
        pageinfo = get_pageinfo(filename, context)

        alt_suffix = \
            '.ocr.page.pdf' if is_ocr_required(pageinfo, log, options) \
            else '.skip.page.pdf'
        re_symlink(
            filename,
            os.path.join(
                work_folder,
                os.path.basename(filename)[0:6] + alt_suffix))


def rasterize_preview(
        input_file,
        output_file,
        log,
        context):
    ghostscript.rasterize_pdf(
        input_file=input_file,
        output_file=output_file,
        xres=200,
        yres=200,
        raster_device='jpeggray',
        log=log)


def orient_page(
        infiles,
        output_file,
        log,
        context):

    options = context.get_options()
    page_pdf = next(ii for ii in infiles if ii.endswith('.page.pdf'))

    if not options.rotate_pages:
        re_symlink(page_pdf, output_file)
        return
    preview = next(ii for ii in infiles if ii.endswith('.preview.jpg'))

    orient_conf = tesseract.get_orientation(
        preview,
        language=options.language,
        timeout=options.tesseract_timeout,
        log=log)

    direction = {
        0: '⇧',
        90: '⇨',
        180: '⇩',
        270: '⇦'
    }

    apply_correction = False
    description = ''
    if orient_conf.confidence >= options.rotate_pages_threshold:
        if orient_conf.angle != 0:
            apply_correction = True
            description = ' - will rotate'
        else:
            description = ' - rotation appears correct'
    else:
        if orient_conf.angle != 0:
            description = ' - confidence too low to rotate'
        else:
            description = ' - no change'

    log.info(
        '{0:4d}: page is facing {1}, confidence {2:.2f}{3}'.format(
            page_number(preview),
            direction.get(orient_conf.angle, '?'),
            orient_conf.confidence,
            description)
    )

    if not apply_correction:
        re_symlink(page_pdf, output_file)
    else:
        writer = pypdf.PdfFileWriter()
        reader = pypdf.PdfFileReader(page_pdf)
        page = reader.pages[0]

        # angle is a clockwise angle, so rotating ccw will correct the error
        rotated_page = page.rotateCounterClockwise(orient_conf.angle)
        writer.addPage(rotated_page)
        with open(output_file, 'wb') as out:
            writer.write(out)

        pageno = int(os.path.basename(page_pdf)[0:6]) - 1
        pdfinfo = context.get_pdfinfo()
        pdfinfo[pageno]['rotated'] = orient_conf.angle
        context.set_pdfinfo(pdfinfo)


def rasterize_with_ghostscript(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    pageinfo = get_pageinfo(input_file, context)

    device = 'png16m'  # 24-bit
    if all(image['comp'] == 1 for image in pageinfo['images']):
        if all(image['bpc'] == 1 for image in pageinfo['images']):
            device = 'pngmono'
        elif all(image['bpc'] > 1 and image['color'] == 'index'
                 for image in pageinfo['images']):
            device = 'png256'
        elif all(image['bpc'] > 1 and image['color'] == 'gray'
                 for image in pageinfo['images']):
            device = 'pnggray'

    log.debug("Rasterize {0} with {1}".format(
              os.path.basename(input_file), device))

    # Produce the page image with square resolution or else deskew and OCR
    # will not work properly
    dpi = get_page_square_dpi(pageinfo, options)
    ghostscript.rasterize_pdf(
        input_file, output_file, xres=dpi, yres=dpi, raster_device=device,
        log=log)


def preprocess_remove_background(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    if not options.remove_background:
        re_symlink(input_file, output_file, log)
        return

    pageinfo = get_pageinfo(input_file, context)

    if any(image['bpc'] > 1 for image in pageinfo['images']):
        leptonica.remove_background(input_file, output_file)
    else:
        log.info("{0:4d}: background removal skipped on mono page".format(
            pageinfo['pageno']))
        re_symlink(input_file, output_file, log)


def preprocess_deskew(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    if not options.deskew:
        re_symlink(input_file, output_file, log)
        return

    pageinfo = get_pageinfo(input_file, context)
    dpi = get_page_square_dpi(pageinfo, options)

    leptonica.deskew(input_file, output_file, dpi)


def preprocess_clean(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    if not options.clean:
        re_symlink(input_file, output_file, log)
        return

    pageinfo = get_pageinfo(input_file, context)
    dpi = get_page_square_dpi(pageinfo, options)

    unpaper.clean(input_file, output_file, dpi, log)


def ocr_tesseract_hocr(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    tesseract.generate_hocr(
        input_file=input_file,
        output_hocr=output_file,
        language=options.language,
        tessconfig=options.tesseract_config,
        timeout=options.tesseract_timeout,
        pageinfo_getter=partial(get_pageinfo, input_file, context),
        pagesegmode=options.tesseract_pagesegmode,
        log=log
        )


def select_image_for_pdf(
        infiles,
        output_file,
        log,
        context):
    options = context.get_options()
    if options.clean_final:
        image_suffix = '.pp-clean.png'
    elif options.deskew:
        image_suffix = '.pp-deskew.png'
    elif options.remove_background:
        image_suffix = '.pp-background.png'
    else:
        image_suffix = '.page.png'
    image = next(ii for ii in infiles if ii.endswith(image_suffix))

    pageinfo = get_pageinfo(image, context)
    if all(orig_image['enc'] == 'jpeg' for orig_image in pageinfo['images']):
        # If all images were JPEGs originally, produce a JPEG as output
        im = Image.open(image)

        # At this point the image should be a .png, but deskew, unpaper might
        # have removed the DPI information. In this case, fall back to square
        # DPI used to rasterize. When the preview image was rasterized, it
        # was also converted to square resolution, which is what we want to
        # give tesseract, so keep it square.
        fallback_dpi = get_page_square_dpi(pageinfo, options)
        dpi = im.info.get('dpi', (fallback_dpi, fallback_dpi))

        # Pillow requires integer DPI
        dpi = round(dpi[0]), round(dpi[1])
        im.save(output_file, format='JPEG', dpi=dpi)
    else:
        re_symlink(image, output_file)


def select_image_layer(
        infiles,
        output_file,
        log,
        context):
    options = context.get_options()
    page_pdf = next(ii for ii in infiles if ii.endswith('.ocr.oriented.pdf'))
    image = next(ii for ii in infiles if ii.endswith('.image'))

    if lossless_reconstruction:
        log.debug("{:4d}: page eligible for lossless reconstruction".format(
            page_number(page_pdf)))
        re_symlink(page_pdf, output_file)
    else:
        pageinfo = get_pageinfo(image, context)
        dpi = get_page_dpi(pageinfo, options)
        dpi = float(dpi[0]), float(dpi[1])
        layout_fun = img2pdf.get_fixed_dpi_layout_fun(dpi)

        with open(image, 'rb') as imfile, \
                open(output_file, 'wb') as pdf:
            rawdata = imfile.read()
            log.debug('{:4d}: convert'.format(page_number(page_pdf)))
            img2pdf.convert(
                rawdata, with_pdfrw=False,
                layout_fun=layout_fun, outputstream=pdf)
            log.debug('{:4d}: convert done'.format(page_number(page_pdf)))


def render_hocr_page(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    hocr = input_file
    pageinfo = get_pageinfo(hocr, context)
    dpi = get_page_square_dpi(pageinfo, options)

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=None,
                         showBoundingboxes=False, invisibleText=True)


def render_hocr_debug_page(
        infiles,
        output_file,
        log,
        context):
    options = context.get_options()
    hocr = next(ii for ii in infiles if ii.endswith('.hocr'))
    image = next(ii for ii in infiles if ii.endswith('.image'))

    pageinfo = get_pageinfo(image, context)
    dpi = get_page_square_dpi(pageinfo, options)

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=None,
                         showBoundingboxes=True, invisibleText=False)


class PdfMergeFailedError(Exception):
    pass


def add_text_layer(
        infiles,
        output_file,
        log,
        context):
    text = next(ii for ii in infiles if ii.endswith('.hocr.pdf'))
    image = next(ii for ii in infiles if ii.endswith('.image-layer.pdf'))

    pdf_text = pypdf.PdfFileReader(open(text, "rb"))
    pdf_image = pypdf.PdfFileReader(open(image, "rb"))

    page_text = pdf_text.getPage(0)

    # The text page always will be oriented up by this stage
    # but if lossless_reconstruction, pdf_image may have a rotation applied
    # We have to eliminate the /Rotate tag (because it applies to the whole
    # page) and rotate the image layer to match the text page
    # Also, pdf_image may not have its mediabox nailed to (0, 0), so may need
    # translation
    page_image = pdf_image.getPage(0)
    try:
        # pypdf DictionaryObject.get() does not resolve indirect objects but
        # __getitem__ does
        rotation = page_image['/Rotate']
    except KeyError:
        rotation = 0

    # /Rotate is a clockwise rotation: 90 means page facing "east"
    # The negative of this value is the angle that eliminates that rotation
    rotation = -rotation % 360

    x1 = page_image.mediaBox.getLowerLeft_x()
    x2 = page_image.mediaBox.getUpperRight_x()
    y1 = page_image.mediaBox.getLowerLeft_y()
    y2 = page_image.mediaBox.getUpperRight_y()

    # Rotation occurs about the page's (0, 0). Most pages will have the media
    # box at (0, 0) with all content in the first quadrant but some cropped
    # files may have an offset mediabox. We translate the page so that its
    # bottom left corner after rotation is pinned to (0, 0) with the image
    # in the first quadrant.
    if rotation == 0:
        tx, ty = -x1, -y1
    elif rotation == 90:
        tx, ty = y2, -x1
    elif rotation == 180:
        tx, ty = x2, y2
    elif rotation == 270:
        tx, ty = -y1, x2
    else:
        pass

    if rotation != 0:
        log.info("{0:4d}: rotating image layer {1} degrees".format(
            page_number(image), rotation, tx, ty))

    try:
        page_text.mergeRotatedScaledTranslatedPage(
            page_image, rotation, 1.0, tx, ty, expand=False)
    except (AttributeError, ValueError) as e:
        if 'writeToStream' in str(e) or 'invalid literal' in str(e):
            raise PdfMergeFailedError() from e

    pdf_output = pypdf.PdfFileWriter()
    pdf_output.addPage(page_text)

    with open(output_file, "wb") as out:
        pdf_output.write(out)


def tesseract_ocr_and_render_pdf(
        input_files,
        output_file,
        log,
        context):
    options = context.get_options()
    input_image = next((ii for ii in input_files if ii.endswith('.image')), '')
    input_pdf = next((ii for ii in input_files if ii.endswith('.pdf')))
    if not input_image:
        # Skipping this page
        re_symlink(input_pdf, output_file)
        return

    tesseract.generate_pdf(
        input_image=input_image,
        skip_pdf=input_pdf,
        output_pdf=output_file,
        language=options.language,
        tessconfig=options.tesseract_config,
        timeout=options.tesseract_timeout,
        pagesegmode=options.tesseract_pagesegmode,
        log=log)


def get_pdfmark(base_pdf, options):
    def from_document_info(key):
        # pdf.documentInfo.get() DOES NOT behave as expected for a dict-like
        # object, so call with precautions.  TypeError may occur if the PDF
        # is missing the optional document info section.
        try:
            s = base_pdf.documentInfo[key]
            return str(s)
        except (KeyError, TypeError):
            return ''

    pdfmark = {
        '/Title': from_document_info('/Title'),
        '/Author': from_document_info('/Author'),
        '/Keywords': from_document_info('/Keywords'),
        '/Subject': from_document_info('/Subject'),
    }
    if options.title:
        pdfmark['/Title'] = options.title
    if options.author:
        pdfmark['/Author'] = options.author
    if options.keywords:
        pdfmark['/Keywords'] = options.keywords
    if options.subject:
        pdfmark['/Subject'] = options.subject

    pdfmark['/Creator'] = '{0} {1} / Tesseract OCR{2} {3}'.format(
            parser.prog, VERSION,
            '+PDF' if options.pdf_renderer == 'tesseract' else '',
            tesseract.version())
    return pdfmark


def generate_postscript_stub(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    pdf = pypdf.PdfFileReader(input_file)
    pdfmark = get_pdfmark(pdf, options)
    generate_pdfa_def(output_file, pdfmark)


def skip_page(
        input_file,
        output_file,
        log):
    # The purpose of this step is its filter to forward only the skipped
    # files (.skip.oriented.pdf) while disregarding the processed ones
    # (.ocr.oriented.pdf).  Alternative would be for merge_pages to filter
    # pages itself if it gets multiple copies of a page.
    re_symlink(input_file, output_file, log)


def merge_pages_ghostscript(
        input_files,
        output_file,
        log,
        context):
    options = context.get_options()
    def input_file_order(s):
        '''Sort order: All rendered pages followed
        by their debug page, if any, followed by Postscript stub.
        Ghostscript documentation has the Postscript stub at the
        beginning, but it works at the end and also gets document info
        right that way.'''
        if s.endswith('.ps'):
            return 99999999
        key = int(os.path.basename(s)[0:6]) * 10
        if 'debug' in os.path.basename(s):
            key += 1
        return key

    pdf_pages = sorted(input_files, key=input_file_order)
    log.debug("Final pages: " + "\n".join(pdf_pages))
    ghostscript.generate_pdfa(pdf_pages, output_file, log, options.jobs or 1)


def merge_pages_qpdf(
        input_files,
        output_file,
        log,
        context):
    options = context.get_options()
    metadata_file = next(
        (ii for ii in input_files if ii.endswith('.repaired.pdf')))
    input_files.remove(metadata_file)

    def input_file_order(s):
        '''Sort order: All rendered pages followed
        by their debug page.'''
        key = int(os.path.basename(s)[0:6]) * 10
        if 'debug' in os.path.basename(s):
            key += 1
        return key

    pdf_pages = sorted(input_files, key=input_file_order)
    log.debug("Final pages: " + "\n".join(pdf_pages))

    reader_metadata = pypdf.PdfFileReader(metadata_file)
    pdfmark = get_pdfmark(reader_metadata, options)
    pdfmark['/Producer'] = 'qpdf ' + qpdf.version()

    first_page = pypdf.PdfFileReader(pdf_pages[0])

    writer = pypdf.PdfFileWriter()
    writer.appendPagesFromReader(first_page)
    writer.addMetadata(pdfmark)
    writer_file = pdf_pages[0].replace('.pdf', '.metadata.pdf')
    with open(writer_file, 'wb') as f:
        writer.write(f)

    pdf_pages[0] = writer_file

    qpdf.merge(pdf_pages, output_file)


def copy_final(
        input_files,
        output_file,
        log,
        context):
    input_file = next((ii for ii in input_files if ii.endswith('.pdf')))

    if output_file == '-':
        from shutil import copyfileobj
        with open(input_file, 'rb') as input_stream:
            copyfileobj(input_stream, sys.stdout.buffer)
    else:
        shutil.copy(input_file, output_file)


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


def do_ruffus_exception(ruffus_five_tuple, options):
    """Replace the elaborate ruffus stack trace with a user friendly
    description of the error message that occurred."""

    task_name, job_name, exc_name, exc_value, exc_stack = ruffus_five_tuple
    if exc_name == 'builtins.SystemExit':
        match = re.search(r"\.(.+?)\)", exc_value)
        exit_code_name = match.groups()[0]
        exit_code = getattr(ExitCode, exit_code_name, 'other_error')
        return exit_code
    elif exc_name == 'ruffus.ruffus_exceptions.MissingInputFileError':
        _log.error(cleanup_ruffus_error_message(exc_value))
        return ExitCode.input_file
    elif exc_name == 'builtins.TypeError':
        # Even though repair_pdf will fail, ruffus will still try
        # to call split_pages with no input files, likely due to a bug
        if task_name == 'split_pages':
            _log.error("Input file '{0}' is not a valid PDF".format(
                options.input_file))
            return ExitCode.input_file
    elif exc_name == 'builtins.KeyboardInterrupt':
        _log.error("Interrupted by user")
        return ExitCode.ctrl_c
    elif exc_name == 'subprocess.CalledProcessError':
        # It's up to the subprocess handler to report something useful
        msg = "Error occurred while running this command:"
        _log.error(msg + '\n' + exc_value)
        return ExitCode.child_process_error
    elif exc_name == 'ocrmypdf.main.PdfMergeFailedError':
        _log.error(textwrap.dedent("""\
            Failed to merge PDF image layer with OCR layer

            Usually this happens because the input PDF file is mal-formed and
            ocrmypdf cannot automatically correct the problem on its own.

            Try using
                ocrmypdf --pdf-renderer tesseract  [..other args..]
            """))
        return ExitCode.input_file
    elif exc_name == 'PyPDF2.utils.PdfReadError' and \
            'not been decrypted' in exc_value:
        _log.error(textwrap.dedent("""\
            Input PDF uses either an encryption algorithm or a PDF security
            handler that is not supported by ocrmypdf.

            For information about this PDF's security use
                qpdf --show-encryption [...input PDF...]

            (Only algorithms "R = 1" and "R = 2" are supported.)

            """))
        return ExitCode.encrypted_pdf

    if not options.verbose:
        _log.error(exc_stack)
    return ExitCode.other_error


def traverse_ruffus_exception(e_args, options):
    """Walk through a RethrownJobError and find the first exception.

    The exit code will be based on this, even if multiple exceptions occurred
    at the same time."""

    if isinstance(e_args, Sequence) and isinstance(e_args[0], str) and \
            len(e_args) == 5:
        return do_ruffus_exception(e_args, options)
    elif is_iterable_notstr(e_args):
        for exc in e_args:
            return traverse_ruffus_exception(exc, options)


def build_pipeline(options, work_folder):
    main_pipeline = Pipeline.pipelines['main']

    _context.set_options(options)
    _context.set_work_folder(work_folder)

    # Triage
    task_triage = main_pipeline.transform(
        task_func=triage,
        input=os.path.join(work_folder, 'origin'),
        filter=formatter('(?i)'),
        output=os.path.join(work_folder, 'origin.pdf'),
        extras=[_log, _context])

    task_repair_pdf = main_pipeline.transform(
        task_func=repair_pdf,
        input=task_triage,
        filter=suffix('.pdf'),
        output='.repaired.pdf',
        output_dir=work_folder,
        extras=[_log, _context])

    # Split
    task_split_pages = main_pipeline.split(
        split_pages,
        task_repair_pdf,
        os.path.join(work_folder, '*.page.pdf'),
        extras=[_log, _context])

    # Rasterize preview
    task_rasterize_preview = main_pipeline.transform(
        task_func=rasterize_preview,
        input=task_split_pages,
        filter=suffix('.page.pdf'),
        output='.preview.jpg',
        output_dir=work_folder,
        extras=[_log, _context])
    task_rasterize_preview.active_if(options.rotate_pages)

    # Orient
    task_orient_page = main_pipeline.collate(
        task_func=orient_page,
        input=[task_split_pages, task_rasterize_preview],
        filter=regex(r".*/(\d{6})(\.ocr|\.skip)(?:\.page\.pdf|\.preview\.jpg)"),
        output=os.path.join(work_folder, r'\1\2.oriented.pdf'),
        extras=[_log, _context])

    # Rasterize actual
    task_rasterize_with_ghostscript = main_pipeline.transform(
        task_func=rasterize_with_ghostscript,
        input=task_orient_page,
        filter=suffix('.ocr.oriented.pdf'),
        output='.page.png',
        output_dir=work_folder,
        extras=[_log, _context])

    # Preprocessing subpipeline
    task_preprocess_remove_background = main_pipeline.transform(
        task_func=preprocess_remove_background,
        input=task_rasterize_with_ghostscript,
        filter=suffix(".page.png"),
        output=".pp-background.png",
        extras=[_log, _context])

    task_preprocess_deskew = main_pipeline.transform(
        task_func=preprocess_deskew,
        input=task_preprocess_remove_background,
        filter=suffix(".pp-background.png"),
        output=".pp-deskew.png",
        extras=[_log, _context])

    task_preprocess_clean = main_pipeline.transform(
        task_func=preprocess_clean,
        input=task_preprocess_deskew,
        filter=suffix(".pp-deskew.png"),
        output=".pp-clean.png",
        extras=[_log, _context])

    # HOCR OCR
    task_ocr_tesseract_hocr = main_pipeline.transform(
        task_func=ocr_tesseract_hocr,
        input=task_preprocess_clean,
        filter=suffix(".pp-clean.png"),
        output=".hocr",
        extras=[_log, _context])
    task_ocr_tesseract_hocr.graphviz(fillcolor='"#00cc66"')
    task_ocr_tesseract_hocr.active_if(options.pdf_renderer == 'hocr')

    task_select_image_for_pdf = main_pipeline.collate(
        task_func=select_image_for_pdf,
        input=[task_rasterize_with_ghostscript,
               task_preprocess_remove_background,
               task_preprocess_deskew,
               task_preprocess_clean],
        filter=regex(r".*/(\d{6})(?:\.page|\.pp-.*)\.png"),
        output=os.path.join(work_folder, r'\1.image'),
        extras=[_log, _context])
    task_select_image_for_pdf.graphviz(shape='diamond')

    task_select_image_layer = main_pipeline.collate(
        task_func=select_image_layer,
        input=[task_select_image_for_pdf, task_orient_page],
        filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
        output=os.path.join(work_folder, r'\1.image-layer.pdf'),
        extras=[_log, _context])
    task_select_image_layer.graphviz(
        fillcolor='"#00cc66"', shape='diamond')
    task_select_image_layer.active_if(options.pdf_renderer == 'hocr')

    task_render_hocr_page = main_pipeline.transform(
        task_func=render_hocr_page,
        input=task_ocr_tesseract_hocr,
        filter=suffix('.hocr'),
        output='.hocr.pdf',
        extras=[_log, _context])
    task_render_hocr_page.graphviz(fillcolor='"#00cc66"')
    task_render_hocr_page.active_if(options.pdf_renderer == 'hocr')

    task_render_hocr_debug_page = main_pipeline.collate(
        task_func=render_hocr_debug_page,
        input=[task_select_image_for_pdf, task_ocr_tesseract_hocr],
        filter=regex(r".*/(\d{6})(?:\.image|\.hocr)"),
        output=os.path.join(work_folder, r'\1.debug.pdf'),
        extras=[_log, _context])
    task_render_hocr_debug_page.graphviz(fillcolor='"#00cc66"')
    task_render_hocr_debug_page.active_if(options.pdf_renderer == 'hocr')
    task_render_hocr_debug_page.active_if(options.debug_rendering)

    task_add_text_layer = main_pipeline.collate(
        task_func=add_text_layer,
        input=[task_render_hocr_page, task_select_image_layer],
        filter=regex(r".*/(\d{6})(?:\.hocr\.pdf|\.image-layer\.pdf)"),
        output=os.path.join(work_folder, r'\1.rendered.pdf'),
        extras=[_log, _context])
    task_add_text_layer.graphviz(fillcolor='"#00cc66"')
    task_add_text_layer.active_if(options.pdf_renderer == 'hocr')

    # Tesseract OCR
    task_tesseract_ocr_and_render_pdf = main_pipeline.collate(
        task_func=tesseract_ocr_and_render_pdf,
        input=[task_select_image_for_pdf, task_orient_page],
        filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
        output=os.path.join(work_folder, r'\1.rendered.pdf'),
        extras=[_log, _context])
    task_tesseract_ocr_and_render_pdf.graphviz(fillcolor='"#66ccff"')
    task_tesseract_ocr_and_render_pdf.active_if(options.pdf_renderer == 'tesseract')

    # PDF/A
    task_generate_postscript_stub = main_pipeline.transform(
        task_func=generate_postscript_stub,
        input=task_repair_pdf,
        filter=formatter(r'\.repaired\.pdf'),
        output=os.path.join(work_folder, 'pdfa_def.ps'),
        extras=[_log, _context])
    task_generate_postscript_stub.active_if(options.output_type == 'pdfa')


    # Bypass valve
    task_skip_page = main_pipeline.transform(
        task_func=skip_page,
        input=task_orient_page,
        filter=suffix('.skip.oriented.pdf'),
        output='.done.pdf',
        output_dir=work_folder,
        extras=[_log])

    # Merge pages
    task_merge_pages_ghostscript = main_pipeline.merge(
        task_func=merge_pages_ghostscript,
        input=[task_add_text_layer,
               task_render_hocr_debug_page,
               task_skip_page,
               task_tesseract_ocr_and_render_pdf,
               task_generate_postscript_stub],
        output=os.path.join(work_folder, 'merged.pdf'),
        extras=[_log, _context])
    task_merge_pages_ghostscript.active_if(options.output_type == 'pdfa')

    task_merge_pages_qpdf = main_pipeline.merge(
        task_func=merge_pages_qpdf,
        input=[task_add_text_layer,
               task_render_hocr_debug_page,
               task_skip_page,
               task_tesseract_ocr_and_render_pdf,
               task_repair_pdf],
        output=os.path.join(work_folder, 'merged.pdf'),
        extras=[_log, _context])
    task_merge_pages_qpdf.active_if(options.output_type == 'pdf')

    # Finalize
    task_copy_final = main_pipeline.merge(
        task_func=copy_final,
        input=[task_merge_pages_ghostscript, task_merge_pages_qpdf],
        output=options.output_file,
        extras=[_log, _context])


def run_pipeline():
    options = _options

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

        build_pipeline(options, work_folder)
        atexit.register(cleanup_working_files, options)
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

        exitcode = traverse_ruffus_exception(e.args, options)
        if exitcode is None:
            _log.error("Unexpected ruffus exception: " + str(e))
            _log.error(repr(e))
            return ExitCode.other_error
        else:
            return exitcode
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

    pdfinfo = _context.get_pdfinfo()
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
