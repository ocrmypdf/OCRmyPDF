#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

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

import PyPDF2 as pypdf
from PIL import Image

from functools import partial

from ruffus import transform, suffix, merge, active_if, regex, jobs_limit, \
    formatter, follows, split, collate, check_if_uptodate
import ruffus.ruffus_exceptions as ruffus_exceptions
import ruffus.cmdline as cmdline
import ruffus.proxy_logger as proxy_logger

from .hocrtransform import HocrTransform
from .pageinfo import pdf_get_all_pageinfo
from .pdfa import generate_pdfa_def
from . import ghostscript
from . import tesseract
from . import qpdf
from . import ExitCode, page_number

import pkg_resources

VERSION = pkg_resources.get_distribution('ocrmypdf').version

warnings.simplefilter('ignore', pypdf.utils.PdfReadWarning)


BASEDIR = os.path.dirname(os.path.realpath(__file__))


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
    description="Generate searchable PDF file from an image-only PDF file.",
    version=VERSION,
    fromfile_prefix_chars='@',
    ignored_args=[
        'touch_files_only', 'recreate_database', 'checksum_file_name',
        'key_legend_in_graph', 'draw_graph_horizontally', 'flowchart_format',
        'forced_tasks', 'target_tasks', 'use_threads', 'jobs', 'log_file'])

parser.add_argument(
    'input_file',
    help="PDF file containing the images to be OCRed")
parser.add_argument(
    'output_file',
    help="output searchable PDF file")
parser.add_argument(
    '-l', '--language', action='append',
    help="languages of the file to be OCRed")
parser.add_argument(
    '-j', '--jobs', metavar='N', type=int,
    help="Use up to N CPU cores simultaneously (default: use all)")

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
    "Preprocessing options",
    "Improve OCR quality and final image")
preprocessing.add_argument(
    '-r', '--rotate-pages', action='store_true',
    help="automatically rotate pages based on detected text orientation")
preprocessing.add_argument(
    '-d', '--deskew', action='store_true',
    help="deskew each page before performing OCR")
preprocessing.add_argument(
    '-c', '--clean', action='store_true',
    help="clean pages from scanning artifacts before performing OCR")
preprocessing.add_argument(
    '-i', '--clean-final', action='store_true',
    help="incorporate the cleaned image in the final PDF file")
preprocessing.add_argument(
    '--oversample', metavar='DPI', type=int, default=0,
    help="oversample images to at least the specified DPI, to improve OCR "
         "results slightly")

ocrsettings = parser.add_argument_group(
    "OCR options",
    "Control how OCR is applied")
ocrsettings.add_argument(
    '-f', '--force-ocr', action='store_true',
    help="rasterize any fonts or vector images on each page and apply OCR")
ocrsettings.add_argument(
    '-s', '--skip-text', action='store_true',
    help="skip OCR on any pages that already contain text, but include the"
         " page in final output")
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
    help='choose OCR PDF renderer')
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
        complain(lang)
    sys.exit(ExitCode.bad_args)


# ----------
# Arguments

if options.pdf_renderer == 'auto':
    options.pdf_renderer = 'hocr'

if options.pdf_renderer == 'tesseract' and tesseract.version() < '3.04.01' \
        and os.environ.get('OCRMYPDF_SHARP_TTF', '') != '1':
    complain(
        "WARNING: Your version of tesseract has problems with PDF output. "
        "Some PDF viewers will fail to find searchable text.\n"
        "--pdf-renderer=tesseract is not recommended.")

if any((options.clean, options.clean_final)):
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

if options.debug_rendering and options.pdf_renderer == 'tesseract':
    complain(
        "Ignoring --debug-rendering because it is not supported with"
        "--pdf-renderer=tesseract.")

if options.force_ocr and options.skip_text:
    complain(
        "Error: --force-ocr and --skip-text are mutually incompatible.")
    sys.exit(ExitCode.bad_args)

if options.clean and not options.clean_final \
        and options.pdf_renderer == 'tesseract':
    complain(
        "Tesseract PDF renderer cannot render --clean pages without "
        "also performing --clean-final, so --clean-final is assumed.")

lossless_reconstruction = False
if options.pdf_renderer == 'hocr':
    if not options.deskew and not options.clean_final and not options.force_ocr:
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

_logger, _logger_mutex = proxy_logger.make_shared_logger_and_proxy(
    logging_factory, __name__, [None, options.verbose])


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
    filter=formatter('(?i)\.pdf'),
    output=os.path.join(work_folder, '{basename[0]}.repaired.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def repair_pdf(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    qpdf.repair(input_file, output_file, log)
    with pdfinfo_lock:
        pdfinfo.extend(pdf_get_all_pageinfo(output_file))
        log.debug(pdfinfo)


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
            "{0:4d}: page has no images - skipping OCR".format(page)
        )
        ocr_required = False
    elif pageinfo['has_text']:
        s = "{0:4d}: page already has text! – {1}"

        if not options.force_ocr and not options.skip_text:
            log.error(s.format(page,
                               "aborting (use --force-ocr to force OCR)"))
            sys.exit(ExitCode.already_done_ocr)
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
            log.warning(
                "{0:4d}: page too big, skipping OCR "
                "({1:.1f} MPixels > {2:.1f} MPixels --skip-big)".format(
                    page, pixel_count / 1000000, options.skip_big))
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

    # If no files were repaired the input will be empty
    if not input_file:
        log.error("{0}: file not found or invalid argument".format(
                options.input_file))
        sys.exit(ExitCode.input_file)

    npages = qpdf.get_npages(input_file, log)
    qpdf.split_pages(input_file, work_folder, npages)

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


@active_if(options.rotate_pages)
@transform(
    input=split_pages,
    filter=suffix('.page.pdf'),
    output='.preview.jpg',
    output_dir=work_folder,
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def rasterize_preview(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
    ghostscript.rasterize_pdf(
        input_file=input_file,
        output_file=output_file,
        xres=200,
        yres=200,
        raster_device='jpeggray',
        log=log)


@collate(
    input=[split_pages, rasterize_preview],
    filter=regex(r".*/(\d{6})(\.ocr|\.skip)(?:\.page\.pdf|\.preview\.jpg)"),
    output=os.path.join(work_folder, r'\1\2.oriented.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def orient_page(
        infiles,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

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

        with pdfinfo_lock:
            pageno = int(os.path.basename(page_pdf)[0:6]) - 1
            pageinfo = pdfinfo[pageno].copy()
            pageinfo['rotated'] = orient_conf.angle
            pdfinfo[pageno] = pageinfo


@transform(
    input=orient_page,
    filter=suffix('.ocr.oriented.pdf'),
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
        elif all(image['bpc'] > 1 and image['color'] == 'index'
                 for image in pageinfo['images']):
            device = 'png256'
        elif all(image['bpc'] > 1 and image['color'] == 'gray'
                 for image in pageinfo['images']):
            device = 'pnggray'

    log.debug("Rasterize {0} with {1}".format(
            os.path.basename(input_file), device))
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

    from . import leptonica
    leptonica.deskew(input_file, output_file, dpi)


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

    tesseract.generate_hocr(
        input_file=input_file,
        output_hocr=output_file,
        language=options.language,
        tessconfig=options.tesseract_config,
        timeout=options.tesseract_timeout,
        pageinfo_getter=partial(get_pageinfo, input_file, pdfinfo,
                                pdfinfo_lock),
        pagesegmode=options.tesseract_pagesegmode,
        log=log
        )


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
        im = Image.open(image)
        dpi = im.info.get(
            'dpi',
            (int(pageinfo['xres']), int(pageinfo['yres']))
        )
        im.save(output_file, format='JPEG', dpi=dpi)
    else:
        re_symlink(image, output_file)


@active_if(options.pdf_renderer == 'hocr')
@collate(
    input=[select_image_for_pdf, orient_page],
    filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
    output=os.path.join(work_folder, r'\1.image-layer.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def select_image_layer(
        infiles,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

    page_pdf = next(ii for ii in infiles if ii.endswith('.ocr.oriented.pdf'))
    image = next(ii for ii in infiles if ii.endswith('.image'))

    if lossless_reconstruction:
        log.debug("{:4d}: page eligible for lossless reconstruction".format(
            page_number(page_pdf)))
        re_symlink(page_pdf, output_file)
    else:
        pageinfo = get_pageinfo(image, pdfinfo, pdfinfo_lock)
        dpi = round(max(pageinfo['xres'], pageinfo['yres'],
                        options.oversample))
        imgsize = ((img2pdf.ImgSize.dpi, dpi), (img2pdf.ImgSize.dpi, dpi))

        layout_fun = img2pdf.get_layout_fun(None, imgsize, None, None, None)

        with open(image, 'rb') as imfile, \
                open(output_file, 'wb') as pdf:
            rawdata = imfile.read()
            pdf.write(img2pdf.convert(
                rawdata, producer="img2pdf", with_pdfrw=False,
                layout_fun=layout_fun))


@active_if(options.pdf_renderer == 'hocr')
@transform(
    input=ocr_tesseract_hocr,
    filter=suffix('.hocr'),
    output='.hocr.pdf',
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def render_hocr_page(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
    hocr = input_file
    pageinfo = get_pageinfo(hocr, pdfinfo, pdfinfo_lock)
    dpi = round(max(pageinfo['xres'], pageinfo['yres'], options.oversample))

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=None,
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


class PdfMergeFailedError(Exception):
    pass


@active_if(options.pdf_renderer == 'hocr')
@collate(
    input=[render_hocr_page, select_image_layer],
    filter=regex(r".*/(\d{6})(?:\.hocr\.pdf|\.image-layer\.pdf)"),
    output=os.path.join(work_folder, r'\1.rendered.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def add_text_layer(
        infiles,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
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
    rotation = page_image.get('/Rotate', 0)

    # /Rotate is a clockwise rotation: 90 means page facing "east"
    # The negative of this value is the angle that eliminates that rotation
    rotation = -rotation % 360

    x1 = page_image.mediaBox.getLowerLeft_x()
    x2 = page_image.mediaBox.getUpperRight_x()
    y1 = page_image.mediaBox.getLowerLeft_y()
    y2 = page_image.mediaBox.getUpperRight_y()

    # Rotation occurs about the page's (0, 0). Most pages will have the media
    # box at (0, 0) will all content in the first quadrant but some cropped
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


@active_if(options.pdf_renderer == 'tesseract')
@collate(
    input=[select_image_for_pdf, orient_page],
    filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
    output=os.path.join(work_folder, r'\1.rendered.pdf'),
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def tesseract_ocr_and_render_pdf(
        input_files,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):

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


@transform(
    input=repair_pdf,
    filter=formatter(r'\.repaired\.pdf'),
    output=os.path.join(work_folder, 'pdfa_def.ps'),
    extras=[_log])
def generate_postscript_stub(
        input_file,
        output_file,
        log):

    pdf = pypdf.PdfFileReader(input_file)

    def from_document_info(key):
        # pdf.documentInfo.get() DOES NOT behave as expected for a dict-like
        # object, so call with precautions.  TypeError may occur if the PDF
        # is missing the optional document info section.
        try:
            s = pdf.documentInfo[key]
            return str(s)
        except (KeyError, TypeError):
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

    pdfmark['creator'] = '{0} {1} / Tesseract OCR{2} {3}'.format(
            parser.prog, VERSION,
            '+PDF' if options.pdf_renderer == 'tesseract' else '',
            tesseract.version())

    generate_pdfa_def(output_file, pdfmark)


@transform(
    input=orient_page,
    filter=suffix('.skip.oriented.pdf'),
    output='.done.pdf',
    output_dir=work_folder,
    extras=[_log])
def skip_page(
        input_file,
        output_file,
        log):
    # The purpose of this step is its filter to forward only the skipped
    # files (.skip.oriented.pdf) while disregarding the processed ones
    # (.ocr.oriented.pdf).  Alternative would be for merge_pages to filter
    # pages itself if it gets multiple copies of a page.
    re_symlink(input_file, output_file, log)


@merge(
    input=[add_text_layer, render_hocr_debug_page, skip_page,
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
    log.debug("Final pages: " + "\n".join(pdf_pages))
    ghostscript.generate_pdfa(pdf_pages, output_file, options.jobs or 1)


@transform(
    input=merge_pages,
    filter=formatter(),
    output=options.output_file,
    extras=[_log, _pdfinfo, _pdfinfo_lock])
def copy_final(
        input_file,
        output_file,
        log,
        pdfinfo,
        pdfinfo_lock):
    shutil.copy(input_file, output_file)


def validate_pdfa(
        input_file,
        log):
    return qpdf.check(input_file, log)


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


def do_ruffus_exception(ruffus_five_tuple):
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
    elif not options.verbose:
        _log.error(exc_stack)
        return ExitCode.other_error


def traverse_ruffus_exception(e):
    """Walk through a RethrownJobError and find the first exception.

    The exit code will be based on this, even if multiple exceptions occurred
    at the same time."""

    if isinstance(e[0], str) and len(e) == 5:
        return do_ruffus_exception(e)
    elif hasattr(e, '__iter__'):
        for exc in e:
            return traverse_ruffus_exception(exc)


def run_pipeline():
    if not options.jobs:
        options.jobs = available_cpu_count()
    try:
        options.history_file = os.path.join(
            work_folder, 'ruffus_history.sqlite')
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

        exitcode = traverse_ruffus_exception(e.args)
        if exitcode is None:
            _log.error("Unexpected ruffus exception: " + str(e))
            _log.error(repr(e))
            return ExitCode.other_error
        else:
            return exitcode
    except Exception as e:
        _log.error(e)
        return ExitCode.other_error

    if not validate_pdfa(options.output_file, _log):
        _log.warning('Output file: The generated PDF/A file is INVALID')
        return ExitCode.invalid_output_pdfa

    with _pdfinfo_lock:
        _log.debug(_pdfinfo)
        direction = {0: 'n', 90: 'e',
                     180: 's', 270: 'w'}
        orientations = []
        for n, page in enumerate(_pdfinfo):
            angle = _pdfinfo[n].get('rotated', 0)
            if angle != 0:
                orientations.append('{0}{1}'.format(
                    n + 1,
                    direction.get(angle, '')))
        if orientations:
            _log.info('Page orientations detected: ' + ' '.join(orientations))

    return ExitCode.ok


if __name__ == '__main__':
    sys.exit(run_pipeline())
