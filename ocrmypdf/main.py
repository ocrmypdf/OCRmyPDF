#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from contextlib import suppress
from tempfile import NamedTemporaryFile, mkdtemp
import sys
import os
import fileinput
import re
import shutil
import warnings
import multiprocessing
import atexit
import textwrap

import PyPDF2 as pypdf
from PIL import Image

from subprocess import Popen, check_call, PIPE, CalledProcessError, \
    TimeoutExpired, check_output
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


from ruffus import transform, suffix, merge, active_if, regex, jobs_limit, \
    formatter, follows, split, collate, check_if_uptodate
import ruffus.cmdline as cmdline

from .hocrtransform import HocrTransform
from .pageinfo import pdf_get_all_pageinfo
from .pdfa import generate_pdfa_def
from . import ghostscript
from . import tesseract


warnings.simplefilter('ignore', pypdf.utils.PdfReadWarning)


BASEDIR = os.path.dirname(os.path.realpath(__file__))
JHOVE_PATH = os.path.realpath(os.path.join(BASEDIR, 'jhove'))
JHOVE_JAR = os.path.join(JHOVE_PATH, 'bin', 'JhoveApp.jar')
JHOVE_CFG = os.path.join(JHOVE_PATH, 'conf', 'jhove.conf')

EXIT_BAD_ARGS = 1
EXIT_BAD_INPUT_FILE = 2
EXIT_MISSING_DEPENDENCY = 3
EXIT_INVALID_OUTPUT_PDFA = 4
EXIT_FILE_ACCESS_ERROR = 5
EXIT_ALREADY_DONE_OCR = 6
EXIT_OTHER_ERROR = 15

# -------------
# External dependencies

MINIMUM_TESS_VERSION = '3.02.02'


def complain(message):
    print(textwrap.wrap(message), file=sys.stderr)


if tesseract.version() < MINIMUM_TESS_VERSION:
    complain(
        "Please install tesseract {0} or newer "
        "(currently installed version is {1})".format(
            MINIMUM_TESS_VERSION, tesseract.version()))
    sys.exit(EXIT_MISSING_DEPENDENCY)


# -------------
# Parser

parser = cmdline.get_argparse(
    prog="ocrmypdf",
    description="Generate searchable PDF file from an image-only PDF file.",
    version='3.0rc2',
    fromfile_prefix_chars='@',
    ignored_args=[
        'touch_files_only', 'recreate_database', 'checksum_file_name',
        'key_legend_in_graph', 'draw_graph_horizontally', 'flowchart_format',
        'forced_tasks', 'target_tasks'])

parser.add_argument(
    'input_file',
    help="PDF file containing the images to be OCRed")
parser.add_argument(
    'output_file',
    help="output searchable PDF file")
parser.add_argument(
    '-l', '--language', action='append',
    help="language of the file to be OCRed")

metadata = parser.add_argument_group(
    "Metadata options",
    "Set output PDF/A metadata (default: use input document's title)")
metadata.add_argument(
    '--title', type=str,
    help="set document title (place multiple words in quotes)")
metadata.add_argument(
    '--author', type=str,
    help="set document author")
metadata.add_argument(
    '--subject', type=str,
    help="set document")
metadata.add_argument(
    '--keywords', type=str,
    help="set document keywords")


preprocessing = parser.add_argument_group(
    "Preprocessing options",
    "Improve OCR quality and final image")
preprocessing.add_argument(
    '-d', '--deskew', action='store_true',
    help="deskew each page before performing OCR")
preprocessing.add_argument(
    '-c', '--clean', action='store_true',
    help="clean pages with unpaper before performing OCR")
preprocessing.add_argument(
    '-i', '--clean-final', action='store_true',
    help="incorporate the cleaned image in the final PDF file")
preprocessing.add_argument(
    '--oversample', metavar='DPI', type=int, default=0,
    help="oversample images to improve OCR results slightly")

parser.add_argument(
    '-f', '--force-ocr', action='store_true',
    help="force image into OCR, even if the page already contains text")
parser.add_argument(
    '-s', '--skip-text', action='store_true',
    help="skip OCR on any pages that already contain text")
parser.add_argument(
    '--skip-big', type=float, metavar='MPixels',
    help="skip OCR on pages larger than the specified amount of megapixels")
# parser.add_argument(
#     '--exact-image', action='store_true',
#     help="Use original page from PDF without re-rendering")

advanced = parser.add_argument_group(
    "Advanced",
    "Advanced options for power users")
advanced.add_argument(
    '--tesseract-config', default=[], type=list, action='append',
    help="additional Tesseract configuration files")
advanced.add_argument(
    '--pdf-renderer', choices=['tesseract', 'hocr'], default='hocr',
    help='choose OCR PDF renderer')
advanced.add_argument(
    '--tesseract-timeout', default=180.0, type=float,
    help='give up on OCR after timeout')

debugging = parser.add_argument_group(
    "Debugging",
    "Arguments to help with troubleshooting and debugging")
debugging.add_argument(
    '-k', '--keep-temporary-files', action='store_true',
    help="keep temporary files (helpful for debugging)")
debugging.add_argument(
    '-g', '--debug-rendering', action='store_true',
    help="render each page twice with debug information on second page")

options = parser.parse_args()


# ----------
# Languages

if not options.language:
    options.language = ['eng']  # Enforce English hegemony

# Support v2.x "eng+deu" language syntax
if '+' in options.language[0]:
    options.language = options.language[0].split('+')

if not set(options.language).issubset(tesseract.languages()):
    complain(
        "The installed version of tesseract does not have language "
        "data for the following requested languages: ")
    for lang in (set(options.language) - tesseract.languages()):
        complain(lang, file=sys.stderr)
    sys.exit(EXIT_BAD_ARGS)


# ----------
# Arguments


if any((options.deskew, options.clean, options.clean_final)):
    try:
        from . import unpaper
    except ImportError:
        complain(
            "Install the 'unpaper' program to use --deskew or --clean.")
        sys.exit(EXIT_BAD_ARGS)
else:
    unpaper = None

if options.debug_rendering and options.pdf_renderer == 'tesseract':
    complain(
        "Ignoring --debug-rendering because it is not supported with"
        "--pdf-renderer=tesseract.")

if options.force_ocr and options.skip_text:
    complain(
        "Error: --force-ocr and --skip-text are mutually incompatible.")
    sys.exit(EXIT_BAD_ARGS)

if options.clean and not options.clean_final \
        and options.pdf_renderer == 'tesseract':
    complain(
        "Tesseract PDF renderer cannot render --clean pages without "
        "also performing --clean-final, so --clean-final is assumed.")


# ----------
# Logging


_logger, _logger_mutex = cmdline.setup_logging(__name__, options.log_file,
                                               options.verbose)


class WrappedLogger:

    def __init__(self, my_logger, my_mutex):
        self.logger = my_logger
        self.mutex = my_mutex

    def log(self, *args, **kwargs):
        with self.mutex:
            self.logger.log(*args, **kwargs)

    def debug(self, *args, **kwargs):
        with self.mutex:
            self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        with self.mutex:
            self.logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        with self.mutex:
            self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        with self.mutex:
            self.logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        with self.mutex:
            self.logger.critical(*args, **kwargs)

_log = WrappedLogger(_logger, _logger_mutex)


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
            raise Exception("%s exists and is not a link" % soft_link_name)
        try:
            os.unlink(soft_link_name)
        except:
            log.debug("Can't unlink %s" % (soft_link_name))

    if not os.path.exists(input_file):
        raise Exception("trying to create a broken symlink to %s" % input_file)

    log.debug("os.symlink(%s, %s)" % (input_file, soft_link_name))

    # Create symbolic link using absolute path
    os.symlink(
        os.path.abspath(input_file),
        soft_link_name
    )


# -------------
# The Pipeline

manager = multiprocessing.Manager()
_pdfinfo = manager.list()
_pdfinfo_lock = manager.Lock()

work_folder = mkdtemp(prefix="com.github.ocrmypdf.")


@atexit.register
def cleanup_working_files(*args):
    if options.keep_temporary_files:
        print("Temporary working files saved at:")
        print(work_folder)
    else:
        with suppress(FileNotFoundError):
            shutil.rmtree(work_folder)


@transform(
    input=options.input_file,
    filter=suffix('.pdf'),
    output='.repaired.pdf',
    output_dir=work_folder,
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def repair_pdf(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
    args_qpdf = [
        'qpdf', input_file, output_file
    ]
    check_call(args_qpdf)

    with pdfinfo_lock:
        pdfinfo.extend(pdf_get_all_pageinfo(output_file))
        log.info(pdfinfo)


def get_pageinfo(input_file, pdfinfo, pdfinfo_lock):
    pageno = int(os.path.basename(input_file)[0:6]) - 1
    with pdfinfo_lock:
        pageinfo = pdfinfo[pageno].copy()
    return pageinfo


def is_ocr_required(pageinfo, log):
    page = pageinfo['pageno'] + 1
    ocr_required = True
    if not pageinfo['images']:
        # If the page has no images, then it contains vector content or text
        # or both. It seems quite unlikely that one would find meaningful text
        # from rasterizing vector content. So skip the page.
        log.info(
            "Page {0} has no images - skipping OCR".format(page)
        )
        ocr_required = False
    elif pageinfo['has_text']:
        s = "Page {0} already has text! – {1}"

        if not options.force_ocr and not options.skip_text:
            log.error(s.format(page,
                               "aborting (use --force-ocr to force OCR)"))
            sys.exit(EXIT_ALREADY_DONE_OCR)
        elif options.force_ocr:
            log.info(s.format(page,
                              "rasterizing text and running OCR anyway"))
            ocr_required = True
        elif options.skip_text:
            log.info(s.format(page,
                              "skipping all processing on this page"))
            ocr_required = False

    if ocr_required and options.skip_big:
        pixel_count = pageinfo['width_pixels'] * pageinfo['height_pixels']
        if pixel_count > (options.skip_big * 1000000):
            ocr_required = False
            log.info(
                "Page {0} is very large; skipping due to -b".format(page))

    return ocr_required


@split(
    repair_pdf,
    os.path.join(work_folder, '*.page.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def split_pages(
        input_file,
        output_files,
        log,
        pdfinfo,
        pdfinfo_lock):

    for oo in output_files:
        with suppress(FileNotFoundError):
            os.unlink(oo)

    pages = check_output(['qpdf', '--show-npages', input_file],
                         universal_newlines=True, close_fds=True)

    for n in range(int(pages)):
        args_qpdf = [
            'qpdf', input_file,
            '--pages', input_file, '{0}'.format(n + 1), '--',
            os.path.join(work_folder, '{0:06d}.page.pdf'.format(n + 1))
        ]
        check_call(args_qpdf)

    from glob import glob
    for filename in glob(os.path.join(work_folder, '*.page.pdf')):
        pageinfo = get_pageinfo(filename, pdfinfo, pdfinfo_lock)

        alt_suffix = '.ocr.page.pdf' if is_ocr_required(pageinfo, log) \
                     else '.skip.page.pdf'
        re_symlink(
            filename,
            os.path.join(
                work_folder,
                os.path.basename(filename)[0:6] + alt_suffix))


@transform(
    input=split_pages,
    filter=suffix('.ocr.page.pdf'),
    output='.page.png',
    output_dir=work_folder,
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def rasterize_with_ghostscript(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    pageinfo = get_pageinfo(input_file, pdfinfo, pdfinfo_lock)

    device = 'png16m'  # 24-bit
    if all(image['comp'] == 1 for image in pageinfo['images']):
        if all(image['bpc'] == 1 for image in pageinfo['images']):
            device = 'pngmono'
        elif not any(image['color'] == 'color'
                     for image in pageinfo['images']):
            device = 'pnggray'

    xres = max(pageinfo['xres'], options.oversample or 0)
    yres = max(pageinfo['yres'], options.oversample or 0)

    ghostscript.rasterize_pdf(input_file, output_file, xres, yres, device, log)


@transform(
    input=rasterize_with_ghostscript,
    filter=suffix(".page.png"),
    output=".pp-deskew.png",
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def preprocess_deskew(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    if not options.deskew:
        re_symlink(input_file, output_file, log)
        return

    pageinfo = get_pageinfo(input_file, pdfinfo, pdfinfo_lock)
    dpi = int(pageinfo['xres'])

    unpaper.deskew(input_file, output_file, dpi, log)


@transform(
    input=preprocess_deskew,
    filter=suffix(".pp-deskew.png"),
    output=".pp-clean.png",
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def preprocess_clean(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    if not options.clean:
        re_symlink(input_file, output_file, log)
        return

    pageinfo = get_pageinfo(input_file, pdfinfo, pdfinfo_lock)
    dpi = int(pageinfo['xres'])

    unpaper.clean(input_file, output_file, dpi, log)


@active_if(options.pdf_renderer == 'hocr')
@transform(
    input=preprocess_clean,
    filter=suffix(".pp-clean.png"),
    output=".hocr",
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def ocr_tesseract_hocr(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    pageinfo = get_pageinfo(input_file, pdfinfo, pdfinfo_lock)

    args_tesseract = [
        'tesseract',
        '-l', '+'.join(options.language),
        input_file,
        output_file,
        'hocr'
    ] + options.tesseract_config
    p = Popen(args_tesseract, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    try:
        stdout, stderr = p.communicate(timeout=options.tesseract_timeout)
    except TimeoutExpired:
        p.kill()
        stdout, stderr = p.communicate()
        # Generate a HOCR file with no recognized text if tesseract times out
        # Temporary workaround to hocrTransform not being able to function if
        # it does not have a valid hOCR file.
        with open(output_file, 'w', encoding="utf-8") as f:
            f.write(tesseract.HOCR_TEMPLATE.format(
                pageinfo['width_pixels'],
                pageinfo['height_pixels']))
    else:
        if stdout:
            log.info(stdout)
        if stderr:
            log.error(stderr)

        if p.returncode != 0:
            raise CalledProcessError(p.returncode, args_tesseract)

        if os.path.exists(output_file + '.html'):
            # Tesseract 3.02 appends suffix ".html" on its own (.hocr.html)
            shutil.move(output_file + '.html', output_file)
        elif os.path.exists(output_file + '.hocr'):
            # Tesseract 3.03 appends suffix ".hocr" on its own (.hocr.hocr)
            shutil.move(output_file + '.hocr', output_file)

        # Tesseract 3.03 inserts source filename into hocr file without
        # escaping it, creating invalid XML and breaking the parser.
        # As a workaround, rewrite the hocr file, replacing the filename
        # with a space.
        regex_nested_single_quotes = re.compile(
            r"""title='image "([^"]*)";""")
        with fileinput.input(files=(output_file,), inplace=True) as f:
            for line in f:
                line = regex_nested_single_quotes.sub(
                    r"""title='image " ";""", line)
                print(line, end='')  # fileinput.input redirects stdout


@active_if(options.pdf_renderer == 'hocr')
@collate(
    input=[rasterize_with_ghostscript, preprocess_deskew, preprocess_clean],
    filter=regex(r".*/(\d{6})(?:\.page|\.pp-deskew|\.pp-clean)\.png"),
    output=os.path.join(work_folder, r'\1.image'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def select_image_for_pdf(
        infiles,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
    if options.clean_final:
        image_suffix = '.pp-clean.png'
    elif options.deskew:
        image_suffix = '.pp-deskew.png'
    else:
        image_suffix = '.page.png'
    image = next(ii for ii in infiles if ii.endswith(image_suffix))

    pageinfo = get_pageinfo(image, pdfinfo, pdfinfo_lock)
    if all(image['enc'] == 'jpeg' for image in pageinfo['images']):
        # If all images were JPEGs originally, produce a JPEG as output
        Image.open(image).save(output_file, format='JPEG')
    else:
        re_symlink(image, output_file)


@active_if(options.pdf_renderer == 'hocr')
@collate(
    input=[select_image_for_pdf, ocr_tesseract_hocr],
    filter=regex(r".*/(\d{6})(?:\.image|\.hocr)"),
    output=os.path.join(work_folder, r'\1.rendered.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def render_hocr_page(
        infiles,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
    hocr = next(ii for ii in infiles if ii.endswith('.hocr'))
    image = next(ii for ii in infiles if ii.endswith('.image'))

    pageinfo = get_pageinfo(image, pdfinfo, pdfinfo_lock)
    dpi = round(max(pageinfo['xres'], pageinfo['yres'], options.oversample))

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=image,
                         showBoundingboxes=False, invisibleText=True)


@active_if(options.pdf_renderer == 'hocr')
@active_if(options.debug_rendering)
@collate(
    input=[select_image_for_pdf, ocr_tesseract_hocr],
    filter=regex(r".*/(\d{6})(?:\.image|\.hocr)"),
    output=os.path.join(work_folder, r'\1.debug.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def render_hocr_debug_page(
        infiles,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
    hocr = next(ii for ii in infiles if ii.endswith('.hocr'))
    image = next(ii for ii in infiles if ii.endswith('.image'))

    pageinfo = get_pageinfo(image, pdfinfo, pdfinfo_lock)
    dpi = round(max(pageinfo['xres'], pageinfo['yres'], options.oversample))

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=None,
                         showBoundingboxes=True, invisibleText=False)


@active_if(options.pdf_renderer == 'tesseract')
@collate(
    input=[preprocess_clean, split_pages],
    filter=regex(r".*/(\d{6})(?:\.pp-clean\.png|\.page\.pdf)"),
    output=os.path.join(work_folder, r'\1.rendered.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def tesseract_ocr_and_render_pdf(
        input_files,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    input_image = next((ii for ii in input_files if ii.endswith('.png')), '')
    input_pdf = next((ii for ii in input_files if ii.endswith('.pdf')))
    if not input_image:
        # Skipping this page
        re_symlink(input_pdf, output_file)
        return

    args_tesseract = [
        'tesseract',
        '-l', '+'.join(options.language),
        input_image,
        os.path.splitext(output_file)[0],  # Tesseract appends suffix
        'pdf'
    ] + options.tesseract_config
    p = Popen(args_tesseract, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)

    try:
        stdout, stderr = p.communicate(timeout=options.tesseract_timeout)
        if stdout:
            log.info(stdout)
        if stderr:
            log.error(stderr)
    except TimeoutError:
        p.kill()
        log.info("Tesseract - page timed out")
        re_symlink(input_pdf, output_file)


@transform(
    input=repair_pdf,
    filter=suffix('.repaired.pdf'),
    output='.pdfa_def.ps',
    output_dir=work_folder,
    extras=[_log])
def generate_postscript_stub(
        input_file,
        output_file,
        log):

    pdf = pypdf.PdfFileReader(input_file)

    def from_document_info(key):
        # pdf.documentInfo.get() DOES NOT work as expected
        try:
            s = pdf.documentInfo[key]
            return str(s)
        except KeyError:
            return ''

    pdfmark = {
        'title': from_document_info('/Title'),
        'author': from_document_info('/Author'),
        'keywords': from_document_info('/Keywords'),
        'subject': from_document_info('/Subject'),
    }
    if options.title:
        pdfmark['title'] = options.title
    if options.author:
        pdfmark['author'] = options.author
    if options.keywords:
        pdfmark['keywords'] = options.keywords
    if options.subject:
        pdfmark['subject'] = options.subject

    generate_pdfa_def(output_file, pdfmark)


@transform(
    input=split_pages,
    filter=suffix('.skip.page.pdf'),
    output='.done.pdf',
    output_dir=work_folder,
    extras=[_log])
def skip_page(
        input_file,
        output_file,
        log):
    re_symlink(input_file, output_file, log)


@merge(
    input=[render_hocr_page, render_hocr_debug_page, skip_page,
           tesseract_ocr_and_render_pdf, generate_postscript_stub],
    output=os.path.join(work_folder, 'merged.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def merge_pages(
        input_files,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

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
    log.info(pdf_pages)
    ghostscript.generate_pdfa(pdf_pages, output_file)


@transform(
    input=merge_pages,
    filter=formatter(),
    output=options.output_file,
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def validate_pdfa(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    args_jhove = [
        'java',
        '-jar', JHOVE_JAR,
        '-c', JHOVE_CFG,
        '-m', 'PDF-hul',
        input_file
    ]
    p_jhove = Popen(args_jhove, close_fds=True, universal_newlines=True,
                    stdout=PIPE, stderr=DEVNULL)
    stdout, _ = p_jhove.communicate()

    log.debug(stdout)
    if p_jhove.returncode != 0:
        log.error(stdout)
        raise RuntimeError(
            "Unexpected error while checking compliance to PDF/A file.")

    pdf_is_valid = True
    if re.search(r'ErrorMessage', stdout,
                 re.IGNORECASE | re.MULTILINE):
        pdf_is_valid = False
    if re.search(r'^\s+Status.*not valid', stdout,
                 re.IGNORECASE | re.MULTILINE):
        pdf_is_valid = False
    if re.search(r'^\s+Status.*Not well-formed', stdout,
                 re.IGNORECASE | re.MULTILINE):
        pdf_is_valid = False

    pdf_is_pdfa = False
    if re.search(r'^\s+Profile:.*PDF/A-1', stdout,
                 re.IGNORECASE | re.MULTILINE):
        pdf_is_pdfa = True

    if not pdf_is_valid:
        log.warning('Output file: The generated PDF/A file is INVALID')
    elif pdf_is_valid and not pdf_is_pdfa:
        log.warning('Output file: Generated file is a VALID PDF but not PDF/A')
    elif pdf_is_valid and pdf_is_pdfa:
        log.info('Output file: The generated PDF/A file is VALID')
    shutil.copy(input_file, output_file)


# @active_if(ocr_required and options.exact_image)
# @merge([render_hocr_blank_page, extract_single_page],
#        os.path.join(work_folder, "%04i.merged.pdf") % pageno)
# def merge_hocr_with_original_page(infiles, output_file):
#     with open(infiles[0], 'rb') as hocr_input, \
#             open(infiles[1], 'rb') as page_input, \
#             open(output_file, 'wb') as output:
#         hocr_reader = pypdf.PdfFileReader(hocr_input)
#         page_reader = pypdf.PdfFileReader(page_input)
#         writer = pypdf.PdfFileWriter()

#         the_page = hocr_reader.getPage(0)
#         the_page.mergePage(page_reader.getPage(0))
#         writer.addPage(the_page)
#         writer.write(output)


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


def run_pipeline():
    cmdline.run(options, multiprocess=available_cpu_count())


if __name__ == '__main__':
    run_pipeline()
