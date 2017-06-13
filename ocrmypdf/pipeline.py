#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

from contextlib import suppress
from tempfile import mkdtemp
from functools import partial
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

from ruffus import formatter, regex, Pipeline, suffix

from .hocrtransform import HocrTransform
from .pdfinfo import PdfInfo, Encoding, Colorspace
from .pdfa import generate_pdfa_ps, file_claims_pdfa
from .helpers import re_symlink, is_iterable_notstr, page_number
from .exec import ghostscript, tesseract, qpdf
from .exceptions import *
from . import leptonica
from . import PROGRAM_NAME, VERSION


VECTOR_PAGE_DPI = 400

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
        self.pdfinfo = None

    def generate_pdfinfo(self, infile):
        self.pdfinfo = PdfInfo(infile)

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


from multiprocessing.managers import SyncManager
class JobContextManager(SyncManager):
    pass


def cleanup_working_files(work_folder, options):
    if options.keep_temporary_files:
        print("Temporary working files saved at:\n{0}".format(work_folder),
              file=sys.stderr)
    else:
        with suppress(FileNotFoundError):
            shutil.rmtree(work_folder)


#
# The Pipeline
#


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
        raise UnsupportedImageFormatError() from e
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
                raise DpiError()
        elif not options.image_dpi:
            log.info("Image size: (%d, %d)" % im.size)
            log.error(
                "Input file is an image, but has no resolution (DPI) "
                "in its metadata.  Estimate the resolution at which "
                "image was scanned and specify it using --image-dpi.")
            raise DpiError()

        if 'iccprofile' not in im.info:
            if im.mode == 'RGB':
                log.info('Input image has no ICC profile, assuming sRGB')
            elif im.mode == 'CMYK':
                log.info('Input CMYK image has no ICC profile, not usable')
                raise UnsupportedImageFormatError()
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
        raise UnsupportedImageFormatError() from e


def triage(
        input_file,
        output_file,
        log,
        context):

    options = context.get_options()
    try:
        with open(input_file, 'rb') as f:
            signature = f.read(4)
            if signature == b'%PDF':
                if options.image_dpi:
                    log.warning("Argument --image-dpi ignored because the "
                                "input file is a PDF, not an image.")
                re_symlink(input_file, output_file, log)
                return
    except EnvironmentError as e:
        log.error(e)
        raise InputFileError() from e

    triage_image_file(input_file, output_file, log, options)


def repair_pdf(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    qpdf.repair(input_file, output_file, log)
    pdfinfo = PdfInfo(output_file)

    if pdfinfo.has_userunit and options.output_type == 'pdfa':
        log.error("This input file uses a PDF feature that is not supported "
            "by Ghostscript, so you cannot use --output-type=pdfa for this "
            "file. (Specifically, it uses the PDF-1.6 /UserUnit feature to "
            "support very large or small page sizes, and Ghostscript cannot "
            "output these files.)  Use --output-type=pdf instead."
        )
        raise InputFileError()

    context.set_pdfinfo(pdfinfo)
    log.debug(pdfinfo)


def get_pageinfo(input_file, context):
    pageno = int(os.path.basename(input_file)[0:6]) - 1
    pageinfo = context.get_pdfinfo()[pageno]
    return pageinfo


def get_page_dpi(pageinfo, options):
    "Get the DPI when nonsquare DPI is tolerable"
    xres = max(pageinfo.xres or VECTOR_PAGE_DPI, options.oversample or 0)
    yres = max(pageinfo.yres or VECTOR_PAGE_DPI, options.oversample or 0)
    return (float(xres), float(yres))


def get_page_square_dpi(pageinfo, options):
    "Get the DPI when we require xres == yres, scaled to physical units"
    xres = pageinfo.xres or 0
    yres = pageinfo.yres or 0
    userunit = pageinfo.userunit or 1
    return float(max(
        (xres * userunit) or VECTOR_PAGE_DPI,
        (yres * userunit) or VECTOR_PAGE_DPI,
        options.oversample or 0))


def get_canvas_square_dpi(pageinfo, options):
    """Get the DPI when we require xres == yres, in Postscript units"""
    return float(max(
        (pageinfo.xres) or VECTOR_PAGE_DPI,
        (pageinfo.yres) or VECTOR_PAGE_DPI,
        options.oversample or 0))


def is_ocr_required(pageinfo, log, options):
    page = pageinfo.pageno + 1
    ocr_required = True
    if not pageinfo.images:
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

    elif pageinfo.has_text:
        msg = "{0:4d}: page already has text! – {1}"

        if not options.force_ocr and not options.skip_text:
            log.error(msg.format(page,
                                 "aborting (use --force-ocr to force OCR)"))
            raise PriorOcrFoundError()
        elif options.force_ocr:
            log.info(msg.format(page,
                                "rasterizing text and running OCR anyway"))
            ocr_required = True
        elif options.skip_text:
            log.info(msg.format(page,
                                "skipping all processing on this page"))
            ocr_required = False

    if ocr_required and options.skip_big and pageinfo.images:
        pixel_count = pageinfo.width_pixels * pageinfo.height_pixels
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
        raise InputFileError()

    pdfinfo = context.get_pdfinfo()
    npages = len(pdfinfo)
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
                os.path.basename(filename)[0:6] + alt_suffix),
            log)


def rasterize_preview(
        input_file,
        output_file,
        log,
        context):
    pageinfo = get_pageinfo(input_file, context)
    options = context.get_options()
    canvas_dpi = get_canvas_square_dpi(pageinfo, options) / 2
    page_dpi = get_page_square_dpi(pageinfo, options) / 2

    ghostscript.rasterize_pdf(
        input_file, output_file, xres=canvas_dpi, yres=canvas_dpi,
        raster_device='jpeggray', log=log, page_dpi=(page_dpi, page_dpi))


def orient_page(
        infiles,
        output_file,
        log,
        context):

    options = context.get_options()
    page_pdf = next(ii for ii in infiles if ii.endswith('.page.pdf'))

    if not options.rotate_pages:
        re_symlink(page_pdf, output_file, log)
        return
    preview = next(ii for ii in infiles if ii.endswith('.preview.jpg'))

    orient_conf = tesseract.get_orientation(
        preview,
        language=options.language,
        engine_mode=options.tesseract_oem,
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
        re_symlink(page_pdf, output_file, log)
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
        pdfinfo[pageno].rotation = orient_conf.angle
        context.set_pdfinfo(pdfinfo)


def rasterize_with_ghostscript(
        input_file,
        output_file,
        log,
        context):
    options = context.get_options()
    pageinfo = get_pageinfo(input_file, context)

    device = 'png16m'  # 24-bit
    if pageinfo.images:
        if all(image.comp == 1 for image in pageinfo.images):
            if all(image.bpc == 1 for image in pageinfo.images):
                device = 'pngmono'
            elif all(image.bpc > 1 and image.color == Colorspace.index
                     for image in pageinfo.images):
                device = 'png256'
            elif all(image.bpc > 1 and image.color == Colorspace.gray
                     for image in pageinfo.images):
                device = 'pnggray'

    log.debug("Rasterize {0} with {1}".format(
              os.path.basename(input_file), device))

    # Produce the page image with square resolution or else deskew and OCR
    # will not work properly.
    canvas_dpi = get_canvas_square_dpi(pageinfo, options)
    page_dpi = get_page_square_dpi(pageinfo, options)

    ghostscript.rasterize_pdf(
        input_file, output_file, xres=canvas_dpi, yres=canvas_dpi,
        raster_device=device, log=log, page_dpi=(page_dpi, page_dpi))


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

    if any(image.bpc > 1 for image in pageinfo.images):
        leptonica.remove_background(input_file, output_file)
    else:
        log.info("{0:4d}: background removal skipped on mono page".format(
            pageinfo.pageno))
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

    from .exec import unpaper
    pageinfo = get_pageinfo(input_file, context)
    dpi = get_page_square_dpi(pageinfo, options)

    unpaper.clean(input_file, output_file, dpi, log)


def select_ocr_image(
        infiles,
        output_file,
        log,
        context):
    """Select the image we send for OCR. May not be the same as the display
    image depending on preprocessing."""

    # For the moment this is always the .pp-clean.png image
    image = infiles[0]
    re_symlink(image, output_file, log)


def ocr_tesseract_hocr(
        input_file,
        output_files,
        log,
        context):
    options = context.get_options()
    tesseract.generate_hocr(
        input_file=input_file,
        output_files=output_files,
        language=options.language,
        engine_mode=options.tesseract_oem,
        tessconfig=options.tesseract_config,
        timeout=options.tesseract_timeout,
        pagesegmode=options.tesseract_pagesegmode,
        log=log
        )


def select_visible_page_image(
        infiles,
        output_file,
        log,
        context):
    "Selects a whole page image that we can show the user (if necessary)"

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
    if pageinfo.images and \
            all(im['enc'] == 'jpeg' for im in pageinfo.images):
        log.debug('{:4d}: JPEG input -> JPEG output'.format(
            page_number(image)))
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
        re_symlink(image, output_file, log)


def select_image_layer(
        infiles,
        output_file,
        log,
        context):
    """Selects the image layer for the output page. If possible this is the
    orientation-corrected input page, or an image of the whole page converted
    to PDF."""

    options = context.get_options()
    page_pdf = next(ii for ii in infiles if ii.endswith('.ocr.oriented.pdf'))
    image = next(ii for ii in infiles if ii.endswith('.image'))

    if options.lossless_reconstruction:
        log.debug("{:4d}: page eligible for lossless reconstruction".format(
            page_number(page_pdf)))
        re_symlink(page_pdf, output_file, log)
    else:
        pageinfo = get_pageinfo(image, context)

        # We rasterize a square DPI version of each page because most image
        # processing tools don't support rectangular DPI. Use the square DPI
        # as it accurately describes the image. It would be possible to
        # resample the image at this stage back to non-square DPI to more
        # closely resemble the input, except that the hocr renderer does not
        # understand non-square DPI. The sandwich renderer would be fine.
        dpi = get_page_square_dpi(pageinfo, options)
        layout_fun = img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))

        with open(image, 'rb') as imfile, \
                open(output_file, 'wb') as pdf:
            log.debug('{:4d}: convert'.format(page_number(page_pdf)))
            img2pdf.convert(
                imfile, with_pdfrw=False,
                layout_fun=layout_fun, outputstream=pdf)
            log.debug('{:4d}: convert done'.format(page_number(page_pdf)))


def render_hocr_page(
        infiles,
        output_file,
        log,
        context):
    options = context.get_options()
    hocr = next(ii for ii in infiles if ii.endswith('.hocr'))
    pageinfo = get_pageinfo(hocr, context)
    dpi = get_page_square_dpi(pageinfo, options)

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=None,
                         showBoundingboxes=False, invisibleText=True)


def flatten_groups(groups):
    for obj in groups:
        if is_iterable_notstr(obj):
            yield from obj
        else:
            yield obj


def render_hocr_debug_page(
        infiles,
        output_file,
        log,
        context):
    options = context.get_options()
    hocr = next(ii for ii in flatten_groups(infiles) if ii.endswith('.hocr'))
    image = next(ii for ii in flatten_groups(infiles) if ii.endswith('.image'))

    pageinfo = get_pageinfo(image, context)
    dpi = get_page_square_dpi(pageinfo, options)

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=None,
                         showBoundingboxes=True, invisibleText=False)


def combine_layers(
        infiles,
        output_file,
        log,
        context):
    text = next(ii for ii in flatten_groups(infiles)
                if ii.endswith('.text.pdf'))
    image = next(ii for ii in flatten_groups(infiles)
                 if ii.endswith('.image-layer.pdf'))

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

    # If the input was scaled, re-apply the scaling
    pageinfo = get_pageinfo(text, context)
    if pageinfo.userunit != 1:
        page_text[pypdf.generic.NameObject('/UserUnit')] = pageinfo.userunit
        pdf_output._header = b'%PDF-1.6'  # Hack header to correct version

    with open(output_file, "wb") as out:
        pdf_output.write(out)


def ocr_tesseract_and_render_pdf(
        infiles,
        outfiles,
        log,
        context):
    options = context.get_options()
    input_image = next((ii for ii in infiles if ii.endswith('.image')), '')
    input_pdf = next((ii for ii in infiles if ii.endswith('.pdf')))
    output_pdf = next((ii for ii in outfiles if ii.endswith('.pdf')))
    output_text = next((ii for ii in outfiles if ii.endswith('.txt')))

    if not input_image:
        # Skipping this page
        re_symlink(input_pdf, output_pdf, log)
        with open(output_text, 'w') as f:
            f.write('[skipped page]')
        return

    tesseract.generate_pdf(
        input_image=input_image,
        skip_pdf=input_pdf,
        output_pdf=output_pdf,
        output_text=output_text,
        language=options.language,
        engine_mode=options.tesseract_oem,
        text_only=False,
        tessconfig=options.tesseract_config,
        timeout=options.tesseract_timeout,
        pagesegmode=options.tesseract_pagesegmode,
        log=log)


def ocr_tesseract_textonly_pdf(
        infiles,
        outfiles,
        log,
        context):
    options = context.get_options()
    input_image = next((ii for ii in infiles if ii.endswith('.ocr.png')), '')
    if not input_image:
        raise ValueError("No image rendered?")
    skip_pdf = next((ii for ii in infiles if ii.endswith('.pdf')))

    output_pdf = next((ii for ii in outfiles if ii.endswith('.pdf')))
    output_text = next((ii for ii in outfiles if ii.endswith('.txt')))

    tesseract.generate_pdf(
        input_image=input_image,
        skip_pdf=skip_pdf,
        output_pdf=output_pdf,
        output_text=output_text,
        language=options.language,
        engine_mode=options.tesseract_oem,
        text_only=True,
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

    if options.pdf_renderer == 'tesseract':
        renderer_tag = 'OCR+PDF'
    elif options.pdf_renderer == 'sandwich':
        renderer_tag = 'OCR-PDF'
    else:
        renderer_tag = 'OCR'

    pdfmark['/Creator'] = '{0} {1} / Tesseract {2} {3}'.format(
            PROGRAM_NAME, VERSION,
            renderer_tag,
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
    generate_pdfa_ps(output_file, pdfmark)


def skip_page(
        input_file,
        output_file,
        log,
        context):
    # The purpose of this step is its filter to forward only the skipped
    # files (.skip.oriented.pdf) while disregarding the processed ones
    # (.ocr.oriented.pdf).  Alternative would be for merge_pages to filter
    # pages itself if it gets multiple copies of a page.
    re_symlink(input_file, output_file, log)


def merge_pages_ghostscript(
        input_files_groups,
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

    input_files = (f for f in flatten_groups(input_files_groups)
                   if not f.endswith('.txt'))
    pdf_pages = sorted(input_files, key=input_file_order)
    log.debug("Final pages: " + "\n".join(pdf_pages))
    input_pdfinfo = context.get_pdfinfo()
    ghostscript.generate_pdfa(
        pdf_version=input_pdfinfo.min_version,
        pdf_pages=pdf_pages,
        output_file=output_file,
        compression=options.pdfa_image_compression,
        log=log,
        threads=options.jobs or 1)


def merge_pages_qpdf(
        input_files_groups,
        output_file,
        log,
        context):
    options = context.get_options()

    input_files = list(f for f in flatten_groups(input_files_groups)
                       if not f.endswith('.txt'))
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

    qpdf.merge(input_files=pdf_pages, output_file=output_file,
               min_version=context.get_pdfinfo().min_version)


def merge_sidecars(
        input_files_groups,
        output_file,
        log,
        context):
    options = context.get_options()
    pdfinfo = context.get_pdfinfo()

    txt_files = [None] * len(pdfinfo)

    for infile in flatten_groups(input_files_groups):
        if infile.endswith('.txt'):
            idx = page_number(infile) - 1
            txt_files[idx] = infile

    def write_pages(stream):
        for page_number, txt_file in enumerate(txt_files):
            if page_number != 0:
                stream.write('\f')  # Form feed between pages
            if txt_file:
                with open(txt_file, 'r') as in_:
                    stream.write(in_.read())
            else:
                stream.write('[OCR skipped on page {}]'.format(
                        page_number + 1))

    if output_file == '-':
        write_pages(sys.stdout)
        sys.stdout.flush()
    else:
        with open(output_file, 'w', encoding='utf-8') as out:
            write_pages(out)


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
            sys.stdout.flush()
    else:
        shutil.copy(input_file, output_file)


def build_pipeline(options, work_folder, log, context):
    main_pipeline = Pipeline.pipelines['main']

    # Triage
    task_triage = main_pipeline.transform(
        task_func=triage,
        input=os.path.join(work_folder, 'origin'),
        filter=formatter('(?i)'),
        output=os.path.join(work_folder, 'origin.pdf'),
        extras=[log, context])

    task_repair_pdf = main_pipeline.transform(
        task_func=repair_pdf,
        input=task_triage,
        filter=suffix('.pdf'),
        output='.repaired.pdf',
        output_dir=work_folder,
        extras=[log, context])

    # Split (kwargs for split seems to be broken, so pass plain args)
    task_split_pages = main_pipeline.split(
        split_pages,
        task_repair_pdf,
        os.path.join(work_folder, '*.page.pdf'),
        extras=[log, context])

    # Rasterize preview
    task_rasterize_preview = main_pipeline.transform(
        task_func=rasterize_preview,
        input=task_split_pages,
        filter=suffix('.page.pdf'),
        output='.preview.jpg',
        output_dir=work_folder,
        extras=[log, context])
    task_rasterize_preview.active_if(options.rotate_pages)

    # Orient
    task_orient_page = main_pipeline.collate(
        task_func=orient_page,
        input=[task_split_pages, task_rasterize_preview],
        filter=regex(r".*/(\d{6})(\.ocr|\.skip)(?:\.page\.pdf|\.preview\.jpg)"),
        output=os.path.join(work_folder, r'\1\2.oriented.pdf'),
        extras=[log, context])

    # Rasterize actual
    task_rasterize_with_ghostscript = main_pipeline.transform(
        task_func=rasterize_with_ghostscript,
        input=task_orient_page,
        filter=suffix('.ocr.oriented.pdf'),
        output='.page.png',
        output_dir=work_folder,
        extras=[log, context])

    # Preprocessing subpipeline
    task_preprocess_remove_background = main_pipeline.transform(
        task_func=preprocess_remove_background,
        input=task_rasterize_with_ghostscript,
        filter=suffix(".page.png"),
        output=".pp-background.png",
        extras=[log, context])

    task_preprocess_deskew = main_pipeline.transform(
        task_func=preprocess_deskew,
        input=task_preprocess_remove_background,
        filter=suffix(".pp-background.png"),
        output=".pp-deskew.png",
        extras=[log, context])

    task_preprocess_clean = main_pipeline.transform(
        task_func=preprocess_clean,
        input=task_preprocess_deskew,
        filter=suffix(".pp-deskew.png"),
        output=".pp-clean.png",
        extras=[log, context])

    task_select_ocr_image = main_pipeline.collate(
        task_func=select_ocr_image,
        input=[task_preprocess_clean],
        filter=regex(r".*/(\d{6})(?:\.page|\.pp-.*)\.png"),
        output=os.path.join(work_folder, r"\1.ocr.png"),
        extras=[log, context])


    # HOCR OCR
    task_ocr_tesseract_hocr = main_pipeline.transform(
        task_func=ocr_tesseract_hocr,
        input=task_select_ocr_image,
        filter=suffix(".ocr.png"),
        output=[".hocr", ".txt"],
        extras=[log, context])
    task_ocr_tesseract_hocr.graphviz(fillcolor='"#00cc66"')
    task_ocr_tesseract_hocr.active_if(options.pdf_renderer == 'hocr')
    if tesseract.v4():
        task_ocr_tesseract_hocr.jobs_limit(2)  # Uses multi-core on its own

    task_select_visible_page_image = main_pipeline.collate(
        task_func=select_visible_page_image,
        input=[task_rasterize_with_ghostscript,
               task_preprocess_remove_background,
               task_preprocess_deskew,
               task_preprocess_clean],
        filter=regex(r".*/(\d{6})(?:\.page|\.pp-.*)\.png"),
        output=os.path.join(work_folder, r'\1.image'),
        extras=[log, context])
    task_select_visible_page_image.graphviz(shape='diamond')

    task_select_image_layer = main_pipeline.collate(
        task_func=select_image_layer,
        input=[task_select_visible_page_image, task_orient_page],
        filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
        output=os.path.join(work_folder, r'\1.image-layer.pdf'),
        extras=[log, context])
    task_select_image_layer.graphviz(
        fillcolor='"#00cc66"', shape='diamond')
    task_select_image_layer.active_if(
        options.pdf_renderer == 'hocr' or options.pdf_renderer == 'sandwich')

    task_render_hocr_page = main_pipeline.transform(
        task_func=render_hocr_page,
        input=task_ocr_tesseract_hocr,
        filter=regex(r".*/(\d{6})(?:\.hocr)"),
        output=os.path.join(work_folder, r'\1.text.pdf'),
        extras=[log, context])
    task_render_hocr_page.graphviz(fillcolor='"#00cc66"')
    task_render_hocr_page.active_if(options.pdf_renderer == 'hocr')

    task_render_hocr_debug_page = main_pipeline.collate(
        task_func=render_hocr_debug_page,
        input=[task_select_visible_page_image, task_ocr_tesseract_hocr],
        filter=regex(r".*/(\d{6})(?:\.image|\.hocr)"),
        output=os.path.join(work_folder, r'\1.debug.pdf'),
        extras=[log, context])
    task_render_hocr_debug_page.graphviz(fillcolor='"#00cc66"')
    task_render_hocr_debug_page.active_if(options.pdf_renderer == 'hocr')
    task_render_hocr_debug_page.active_if(options.debug_rendering)

    # Tesseract OCR + text only PDF
    task_ocr_tesseract_textonly_pdf = main_pipeline.collate(
        task_func=ocr_tesseract_textonly_pdf,
        input=[task_select_ocr_image, task_orient_page],
        filter=regex(r".*/(\d{6})(?:\.ocr.png|\.ocr\.oriented\.pdf)"),
        output=[os.path.join(work_folder, r'\1.text.pdf'),
                os.path.join(work_folder, r'\1.text.txt')],
        extras=[log, context])
    task_ocr_tesseract_textonly_pdf.graphviz(fillcolor='"#ff69b4"')
    task_ocr_tesseract_textonly_pdf.active_if(options.pdf_renderer == 'sandwich')
    if tesseract.v4():
        task_ocr_tesseract_textonly_pdf.jobs_limit(2)

    task_combine_layers = main_pipeline.collate(
        task_func=combine_layers,
        input=[task_render_hocr_page,
               task_ocr_tesseract_textonly_pdf,
               task_select_image_layer],
        filter=regex(r".*/(\d{6})(?:\.text\.pdf|\.image-layer\.pdf)"),
        output=os.path.join(work_folder, r'\1.rendered.pdf'),
        extras=[log, context])
    task_combine_layers.graphviz(fillcolor='"#00cc66"')
    task_combine_layers.active_if(options.pdf_renderer == 'hocr' or options.pdf_renderer == 'sandwich')

    # Tesseract OCR+PDF
    task_ocr_tesseract_and_render_pdf = main_pipeline.collate(
        task_func=ocr_tesseract_and_render_pdf,
        input=[task_select_visible_page_image, task_orient_page],
        filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
        output=[os.path.join(work_folder, r'\1.rendered.pdf'),
                os.path.join(work_folder, r'\1.rendered.txt')],
        extras=[log, context])
    task_ocr_tesseract_and_render_pdf.graphviz(fillcolor='"#66ccff"')
    task_ocr_tesseract_and_render_pdf.active_if(options.pdf_renderer == 'tesseract')
    if tesseract.v4():
        task_ocr_tesseract_and_render_pdf.jobs_limit(2)  # Uses multi-core

    # PDF/A
    task_generate_postscript_stub = main_pipeline.transform(
        task_func=generate_postscript_stub,
        input=task_repair_pdf,
        filter=formatter(r'\.repaired\.pdf'),
        output=os.path.join(work_folder, 'pdfa.ps'),
        extras=[log, context])
    task_generate_postscript_stub.active_if(options.output_type == 'pdfa')


    # Bypass valve
    task_skip_page = main_pipeline.transform(
        task_func=skip_page,
        input=task_orient_page,
        filter=suffix('.skip.oriented.pdf'),
        output='.done.pdf',
        output_dir=work_folder,
        extras=[log, context])

    # Merge pages
    task_merge_pages_ghostscript = main_pipeline.merge(
        task_func=merge_pages_ghostscript,
        input=[task_combine_layers,
               task_render_hocr_debug_page,
               task_skip_page,
               task_ocr_tesseract_and_render_pdf,
               task_generate_postscript_stub],
        output=os.path.join(work_folder, 'merged.pdf'),
        extras=[log, context])
    task_merge_pages_ghostscript.active_if(options.output_type == 'pdfa')

    task_merge_pages_qpdf = main_pipeline.merge(
        task_func=merge_pages_qpdf,
        input=[task_combine_layers,
               task_render_hocr_debug_page,
               task_skip_page,
               task_ocr_tesseract_and_render_pdf,
               task_repair_pdf],
        output=os.path.join(work_folder, 'merged.pdf'),
        extras=[log, context])
    task_merge_pages_qpdf.active_if(options.output_type == 'pdf')

    task_merge_sidecars = main_pipeline.merge(
        task_func=merge_sidecars,
        input=[task_ocr_tesseract_hocr,
               task_ocr_tesseract_and_render_pdf,
               task_ocr_tesseract_textonly_pdf],
        output=options.sidecar,
        extras=[log, context])
    task_merge_sidecars.active_if(options.sidecar)

    # Finalize
    task_copy_final = main_pipeline.merge(
        task_func=copy_final,
        input=[task_merge_pages_ghostscript, task_merge_pages_qpdf],
        output=options.output_file,
        extras=[log, context])
