# © 2016 James R. Barlow: github.com/jbarlow83
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

import os
import re
import sys
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile, copyfileobj

import img2pdf
from PIL import Image
from ruffus import Pipeline, formatter, regex, suffix

import pikepdf
from pikepdf.models.metadata import encode_pdf_date

from . import PROGRAM_NAME, VERSION, leptonica
from ._weave import weave_layers
from .exceptions import (
    DpiError,
    EncryptedPdfError,
    InputFileError,
    PriorOcrFoundError,
    UnsupportedImageFormatError,
)
from .exec import ghostscript, tesseract
from .helpers import flatten_groups, is_iterable_notstr, page_number, re_symlink
from .hocrtransform import HocrTransform
from .optimize import optimize
from .pdfa import generate_pdfa_ps
from .pdfinfo import Colorspace, PdfInfo

VECTOR_PAGE_DPI = 400

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
                    "image was scanned and specify it using --image-dpi."
                )
                raise DpiError()
        elif not options.image_dpi:
            log.info("Image size: (%d, %d)" % im.size)
            log.error(
                "Input file is an image, but has no resolution (DPI) "
                "in its metadata.  Estimate the resolution at which "
                "image was scanned and specify it using --image-dpi."
            )
            raise DpiError()

        if im.mode in ('RGBA', 'LA'):
            log.error(
                "The input image has an alpha channel. Remove the alpha "
                "channel first."
            )
            raise UnsupportedImageFormatError()

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
                (options.image_dpi, options.image_dpi)
            )
        with open(output_file, 'wb') as outf:
            img2pdf.convert(
                input_file, layout_fun=layout_fun, with_pdfrw=False, outputstream=outf
            )
        log.info("Successfully converted to PDF, processing...")
    except img2pdf.ImageOpenError as e:
        log.error(e)
        raise UnsupportedImageFormatError() from e


def _pdf_guess_version(input_file, search_window=1024):
    """Try to find version signature at start of file.

    Not robust enough to deal with appended files.

    Returns empty string if not found, indicating file is probably not PDF.
    """

    with open(input_file, 'rb') as f:
        signature = f.read(search_window)
    m = re.search(br'%PDF-(\d\.\d)', signature)
    if m:
        return m.group(1)
    return ''


def triage(input_file, output_file, log, context):

    options = context.get_options()
    try:
        if _pdf_guess_version(input_file):
            if options.image_dpi:
                log.warning(
                    "Argument --image-dpi ignored because the "
                    "input file is a PDF, not an image."
                )
            re_symlink(input_file, output_file, log)
            return
    except EnvironmentError as e:
        log.error(e)
        raise InputFileError() from e

    triage_image_file(input_file, output_file, log, options)


def repair_and_parse_pdf(input_file, output_file, log, context):
    options = context.get_options()
    copyfile(input_file, output_file)

    detailed_page_analysis = False
    if options.redo_ocr:
        detailed_page_analysis = True

    try:
        pdfinfo = PdfInfo(
            output_file, detailed_page_analysis=detailed_page_analysis, log=log
        )
    except pikepdf.PasswordError as e:
        raise EncryptedPdfError()
    except pikepdf.PdfError as e:
        log.error(e)
        raise InputFileError()

    if pdfinfo.needs_rendering:
        log.error(
            "This PDF contains dynamic XFA forms created by Adobe LiveCycle "
            "Designer and can only be read by Adobe Acrobat or Adobe Reader."
        )
        raise InputFileError()

    if pdfinfo.has_userunit and options.output_type.startswith('pdfa'):
        log.error(
            "This input file uses a PDF feature that is not supported "
            "by Ghostscript, so you cannot use --output-type=pdfa for this "
            "file. (Specifically, it uses the PDF-1.6 /UserUnit feature to "
            "support very large or small page sizes, and Ghostscript cannot "
            "output these files.)  Use --output-type=pdf instead."
        )
        raise InputFileError()

    if pdfinfo.has_acroform:
        if options.redo_ocr:
            log.error(
                "This PDF has a user fillable form. --redo-ocr is not "
                "currently possible on such files."
            )
            raise PriorOcrFoundError()
        else:
            log.warning(
                "This PDF has a fillable form. Chances are it is a pure digital "
                "document that does not need OCR."
            )
            if not options.force_ocr:
                log.info(
                    "Use the option --force-ocr to produce an image of the "
                    "form and all filled form fields. The output PDF will be "
                    "'flattened' and will no longer be fillable."
                )

    context.set_pdfinfo(pdfinfo)
    log.debug(pdfinfo)


def get_pageinfo(input_file, context):
    "Get zero-based page info implied by filename, e.g. 000002.pdf -> 1"
    pageno = page_number(input_file) - 1
    pageinfo = context.get_pdfinfo()[pageno]
    return pageinfo


def get_page_dpi(pageinfo, options):
    "Get the DPI when nonsquare DPI is tolerable"
    xres = max(
        pageinfo.xres or VECTOR_PAGE_DPI,
        options.oversample or 0,
        VECTOR_PAGE_DPI if pageinfo.has_vector else 0,
    )
    yres = max(
        pageinfo.yres or VECTOR_PAGE_DPI,
        options.oversample or 0,
        VECTOR_PAGE_DPI if pageinfo.has_vector else 0,
    )
    return (float(xres), float(yres))


def get_page_square_dpi(pageinfo, options):
    "Get the DPI when we require xres == yres, scaled to physical units"
    xres = pageinfo.xres or 0
    yres = pageinfo.yres or 0
    userunit = pageinfo.userunit or 1
    return float(
        max(
            (xres * userunit) or VECTOR_PAGE_DPI,
            (yres * userunit) or VECTOR_PAGE_DPI,
            VECTOR_PAGE_DPI if pageinfo.has_vector else 0,
            options.oversample or 0,
        )
    )


def get_canvas_square_dpi(pageinfo, options):
    """Get the DPI when we require xres == yres, in Postscript units"""
    return float(
        max(
            (pageinfo.xres) or VECTOR_PAGE_DPI,
            (pageinfo.yres) or VECTOR_PAGE_DPI,
            VECTOR_PAGE_DPI if pageinfo.has_vector else 0,
            options.oversample or 0,
        )
    )


def is_ocr_required(pageinfo, log, options):
    page = pageinfo.pageno + 1
    ocr_required = True

    if pageinfo.has_text:
        prefix = f"{page:4d}: page already has text! - "

        if not options.force_ocr and not (options.skip_text or options.redo_ocr):
            log.error(prefix + "aborting (use --force-ocr to force OCR)")
            raise PriorOcrFoundError()
        elif options.force_ocr:
            log.info(prefix + "rasterizing text and running OCR anyway")
            ocr_required = True
        elif options.redo_ocr:
            if pageinfo.has_corrupt_text:
                log.warning(
                    prefix
                    + (
                        "some text on this page cannot be mapped to characters: "
                        "consider using --force-ocr instead",
                    )
                )
                raise PriorOcrFoundError()  # Wrong error but will do for now
            else:
                log.info(prefix + "redoing OCR")
            ocr_required = True
        elif options.skip_text:
            log.info(prefix + "skipping all processing on this page")
            ocr_required = False
    elif not pageinfo.images and not options.lossless_reconstruction:
        # We found a page with no images and no text. That means it may
        # have vector art that the user wants to OCR. If we determined
        # lossless reconstruction is not possible then we have to rasterize
        # the image. So if OCR is being forced, take that to mean YES, go
        # ahead and rasterize. If not forced, then pretend there's no text
        # on the page at all so we don't lose anything.
        # This could be made smarter by explicitly searching for vector art.
        if options.force_ocr and options.oversample:
            # The user really wants to reprocess this file
            log.info(
                f"{page:4d}: page has no images - "
                f"rasterizing at {options.oversample} DPI because "
                "--force-ocr --oversample was specified"
            )
        elif options.force_ocr:
            # Warn the user they might not want to do this
            log.warning(
                f"{page:4d}: page has no images - "
                "all vector content will be "
                f"rasterized at {VECTOR_PAGE_DPI} DPI, losing some resolution and likely "
                "increasing file size. Use --oversample to adjust the "
                "DPI."
            )
        else:
            log.info(
                f"{page:4d}: page has no images - "
                "skipping all processing on this page to avoid losing detail. "
                "Use --force-ocr if you wish to perform OCR on pages that "
                "have vector content."
            )
            ocr_required = False

    if ocr_required and options.skip_big and pageinfo.images:
        pixel_count = pageinfo.width_pixels * pageinfo.height_pixels
        if pixel_count > (options.skip_big * 1_000_000):
            ocr_required = False
            log.warning(
                f"{page:4d}: page too big, skipping OCR "
                f"({(pixel_count / 1_000_000):.1f} MPixels > {options.skip_big:.1f} MPixels --skip-big)"
            )
    return ocr_required


def marker_pages(input_files, output_files, log, context):

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
        log.error(f"{options.input_file}: file not found or invalid argument")
        raise InputFileError()

    pdfinfo = context.get_pdfinfo()
    npages = len(pdfinfo)

    # Ruffus needs to see a file for any task it generates, so make very
    # file a symlink back to the source.
    for n in range(npages):
        page = Path(work_folder) / f'{(n + 1):06d}.marker.pdf'
        page.symlink_to(input_file)  # pylint: disable=E1101


def ocr_or_skip(input_files, output_files, log, context):
    options = context.get_options()
    work_folder = context.get_work_folder()
    pdfinfo = context.get_pdfinfo()

    for input_file in input_files:
        pageno = page_number(input_file) - 1
        pageinfo = pdfinfo[pageno]
        alt_suffix = (
            '.ocr.page.pdf'
            if is_ocr_required(pageinfo, log, options)
            else '.skip.page.pdf'
        )

        re_symlink(
            input_file,
            os.path.join(work_folder, os.path.basename(input_file)[0:6] + alt_suffix),
            log,
        )


def rasterize_preview(input_file, output_file, log, context):
    pageinfo = get_pageinfo(input_file, context)
    options = context.get_options()
    canvas_dpi = get_canvas_square_dpi(pageinfo, options)
    page_dpi = get_page_square_dpi(pageinfo, options)

    ghostscript.rasterize_pdf(
        input_file,
        output_file,
        xres=canvas_dpi,
        yres=canvas_dpi,
        raster_device='jpeggray',
        log=log,
        page_dpi=(page_dpi, page_dpi),
        pageno=page_number(input_file),
    )


def orient_page(infiles, output_file, log, context):
    """
    Work out orientation correct for each page.

    We ask Ghostscript to draw a preview page, which will rasterize with the
    current /Rotate applied, and then ask Tesseract which way the page is
    oriented. If the value of /Rotate is correct (e.g., a user already
    manually fixed rotation), then Tesseract will say the page is pointing
    up and the correction is zero. Otherwise, the orientation found by
    Tesseract represents the clockwise rotation, or the counterclockwise
    correction to rotation.

    When we draw the real page for OCR, we rotate it by the CCW correction,
    which points it (hopefully) upright. _weave.py takes care of the orienting
    the image and text layers.

    """

    options = context.get_options()
    page_pdf = next(ii for ii in infiles if ii.endswith('.page.pdf'))

    if not options.rotate_pages:
        re_symlink(page_pdf, output_file, log)
        return
    preview = next(ii for ii in infiles if ii.endswith('.preview.jpg'))

    orient_conf = tesseract.get_orientation(
        preview,
        engine_mode=options.tesseract_oem,
        timeout=options.tesseract_timeout,
        log=log,
    )

    direction = {0: '⇧', 90: '⇨', 180: '⇩', 270: '⇦'}

    pageno = page_number(page_pdf) - 1
    pdfinfo = context.get_pdfinfo()
    existing_rotation = pdfinfo[pageno].rotation

    correction = orient_conf.angle % 360

    apply_correction = False
    action = ''
    if orient_conf.confidence >= options.rotate_pages_threshold:
        if correction != 0:
            apply_correction = True
            action = ' - will rotate'
        else:
            action = ' - rotation appears correct'
    else:
        if correction != 0:
            action = ' - confidence too low to rotate'
        else:
            action = ' - no change'

    facing = ''
    if existing_rotation != 0:
        facing = 'with existing rotation {}, '.format(
            direction.get(existing_rotation, '?')
        )
    facing += 'page is facing {}'.format(direction.get(orient_conf.angle, '?'))

    log.info(
        '{pagenum:4d}: {facing}, confidence {conf:.2f}{action}'.format(
            pagenum=page_number(preview),
            facing=facing,
            conf=orient_conf.confidence,
            action=action,
        )
    )

    re_symlink(page_pdf, output_file, log)
    if apply_correction:
        context.set_rotation(pageno, correction)


def rasterize_with_ghostscript(input_file, output_file, log, context):
    options = context.get_options()
    pageinfo = get_pageinfo(input_file, context)

    colorspaces = ['pngmono', 'pnggray', 'png256', 'png16m']
    device_idx = 0

    def at_least(cs):
        return max(device_idx, colorspaces.index(cs))

    for image in pageinfo.images:
        if image.type_ != 'image':
            continue  # ignore masks
        if image.bpc > 1:
            if image.color == Colorspace.index:
                device_idx = at_least('png256')
            elif image.color == Colorspace.gray:
                device_idx = at_least('pnggray')
            else:
                device_idx = at_least('png16m')

    device = colorspaces[device_idx]

    log.debug(f"Rasterize {os.path.basename(input_file)} with {device}")

    # Produce the page image with square resolution or else deskew and OCR
    # will not work properly.
    canvas_dpi = get_canvas_square_dpi(pageinfo, options)
    page_dpi = get_page_square_dpi(pageinfo, options)

    correction = context.get_rotation(page_number(input_file) - 1)

    ghostscript.rasterize_pdf(
        input_file,
        output_file,
        xres=canvas_dpi,
        yres=canvas_dpi,
        raster_device=device,
        log=log,
        page_dpi=(page_dpi, page_dpi),
        pageno=page_number(input_file),
        rotation=correction,
        filter_vector=options.remove_vectors,
    )


def preprocess_remove_background(input_file, output_file, log, context):
    options = context.get_options()
    if not options.remove_background:
        re_symlink(input_file, output_file, log)
        return

    pageinfo = get_pageinfo(input_file, context)

    if any(image.bpc > 1 for image in pageinfo.images):
        leptonica.remove_background(input_file, output_file)
    else:
        log.info(f"{pageinfo.pageno:4d}: background removal skipped on mono page")
        re_symlink(input_file, output_file, log)


def preprocess_deskew(input_file, output_file, log, context):
    options = context.get_options()
    if not options.deskew:
        re_symlink(input_file, output_file, log)
        return

    pageinfo = get_pageinfo(input_file, context)
    dpi = get_page_square_dpi(pageinfo, options)

    leptonica.deskew(input_file, output_file, dpi)


def preprocess_clean(input_file, output_file, log, context):
    options = context.get_options()
    if not options.clean:
        re_symlink(input_file, output_file, log)
        return

    from .exec import unpaper

    pageinfo = get_pageinfo(input_file, context)
    dpi = get_page_square_dpi(pageinfo, options)

    unpaper.clean(input_file, output_file, dpi, log, options.unpaper_args)


def select_ocr_image(infiles, output_file, log, context):
    """Select the image we send for OCR. May not be the same as the display
    image depending on preprocessing. This image will never be shown to the
    user."""

    image = infiles[0]
    options = context.get_options()
    pageinfo = get_pageinfo(image, context)

    with Image.open(image) as im:
        from PIL import ImageColor
        from PIL import ImageDraw

        white = ImageColor.getcolor('#ffffff', im.mode)
        # pink = ImageColor.getcolor('#ff0080', im.mode)
        draw = ImageDraw.ImageDraw(im)

        xres, yres = im.info['dpi']
        log.debug('resolution %r %r', xres, yres)

        if not options.force_ocr:
            # Do not mask text areas when forcing OCR, because we need to OCR
            # all text areas
            mask = None  # Exclude both visible and invisible text from OCR
            if options.redo_ocr:
                mask = True  # Mask visible text, but not invisible text

            for textarea in pageinfo.get_textareas(visible=mask, corrupt=None):
                # Calculate resolution based on the image size and page dimensions
                # without regard whatever resolution is in pageinfo (may differ or
                # be None)
                bbox = [float(v) for v in textarea]
                xscale, yscale = float(xres) / 72.0, float(yres) / 72.0
                pixcoords = [
                    bbox[0] * xscale,
                    im.height - bbox[3] * yscale,
                    bbox[2] * xscale,
                    im.height - bbox[1] * yscale,
                ]
                pixcoords = [int(round(c)) for c in pixcoords]
                log.debug('blanking %r', pixcoords)
                draw.rectangle(pixcoords, fill=white)
                # draw.rectangle(pixcoords, outline=pink)

        if options.mask_barcodes or options.threshold:
            pix = leptonica.Pix.frompil(im)
            if options.threshold:
                pix = pix.masked_threshold_on_background_norm()
            if options.mask_barcodes:
                barcodes = pix.locate_barcodes()
                for barcode in barcodes:
                    decoded, rect = barcode
                    log.info('masking barcode %s %r', decoded, rect)
                    draw.rectangle(rect, fill=white)
            im = pix.topil()

        del draw
        # Pillow requires integer DPI
        dpi = round(xres), round(yres)
        im.save(output_file, dpi=dpi)


def ocr_tesseract_hocr(input_file, output_files, log, context):
    options = context.get_options()
    tesseract.generate_hocr(
        input_file=input_file,
        output_files=output_files,
        language=options.language,
        engine_mode=options.tesseract_oem,
        tessconfig=options.tesseract_config,
        timeout=options.tesseract_timeout,
        pagesegmode=options.tesseract_pagesegmode,
        user_words=options.user_words,
        user_patterns=options.user_patterns,
        log=log,
    )


def select_visible_page_image(infiles, output_file, log, context):
    """Selects a whole page image that we can show the user (if necessary)"""

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
    if pageinfo.images and all(im.enc == 'jpeg' for im in pageinfo.images):
        log.debug(f'{page_number(image):4d}: JPEG input -> JPEG output')
        # If all images were JPEGs originally, produce a JPEG as output
        with Image.open(image) as im:
            # At this point the image should be a .png, but deskew, unpaper
            # might have removed the DPI information. In this case, fall back to
            # square DPI used to rasterize. When the preview image was
            # rasterized, it was also converted to square resolution, which is
            # what we want to give tesseract, so keep it square.
            fallback_dpi = get_page_square_dpi(pageinfo, options)
            dpi = im.info.get('dpi', (fallback_dpi, fallback_dpi))

            # Pillow requires integer DPI
            dpi = round(dpi[0]), round(dpi[1])
            im.save(output_file, format='JPEG', dpi=dpi)
    else:
        re_symlink(image, output_file, log)


def select_image_layer(infiles, output_file, log, context):
    """Selects the image layer for the output page. If possible this is the
    orientation-corrected input page, or an image of the whole page converted
    to PDF."""

    options = context.get_options()
    page_pdf = next(ii for ii in infiles if ii.endswith('.ocr.oriented.pdf'))
    image = next(ii for ii in infiles if ii.endswith('.image'))

    if options.lossless_reconstruction:
        log.debug(
            f"{page_number(page_pdf):4d}: page eligible for lossless reconstruction"
        )
        re_symlink(page_pdf, output_file, log)  # Still points to multipage
        return

    pageinfo = get_pageinfo(image, context)

    # We rasterize a square DPI version of each page because most image
    # processing tools don't support rectangular DPI. Use the square DPI as it
    # accurately describes the image. It would be possible to resample the image
    # at this stage back to non-square DPI to more closely resemble the input,
    # except that the hocr renderer does not understand non-square DPI. The
    # sandwich renderer would be fine.
    dpi = get_page_square_dpi(pageinfo, options)
    layout_fun = img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))

    # This create a single page PDF
    with open(image, 'rb') as imfile, open(output_file, 'wb') as pdf:
        log.debug(f'{page_number(page_pdf):4d}: convert')
        img2pdf.convert(
            imfile, with_pdfrw=False, layout_fun=layout_fun, outputstream=pdf
        )
        log.debug(f'{page_number(page_pdf):4d}: convert done')


def render_hocr_page(infiles, output_file, log, context):
    options = context.get_options()
    hocr = next(ii for ii in infiles if ii.endswith('.hocr'))
    pageinfo = get_pageinfo(hocr, context)
    dpi = get_page_square_dpi(pageinfo, options)

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(
        output_file,
        imageFileName=None,
        showBoundingboxes=False,
        invisibleText=True,
        interwordSpaces=True,
    )


def ocr_tesseract_textonly_pdf(infiles, outfiles, log, context):
    options = context.get_options()
    input_image = next((ii for ii in infiles if ii.endswith('.ocr.png')), '')
    if not input_image:
        raise ValueError("No image rendered?")

    output_pdf = next((ii for ii in outfiles if ii.endswith('.pdf')))
    output_text = next((ii for ii in outfiles if ii.endswith('.txt')))

    tesseract.generate_pdf(
        input_image=input_image,
        skip_pdf=None,
        output_pdf=output_pdf,
        output_text=output_text,
        language=options.language,
        engine_mode=options.tesseract_oem,
        text_only=True,
        tessconfig=options.tesseract_config,
        timeout=options.tesseract_timeout,
        pagesegmode=options.tesseract_pagesegmode,
        user_words=options.user_words,
        user_patterns=options.user_patterns,
        log=log,
    )


def get_docinfo(base_pdf, options):
    def from_document_info(key):
        try:
            s = base_pdf.docinfo[key]
            return str(s)
        except (KeyError, TypeError):
            return ''

    pdfmark = {
        k: from_document_info(k)
        for k in ('/Title', '/Author', '/Keywords', '/Subject', '/CreationDate')
    }
    if options.title:
        pdfmark['/Title'] = options.title
    if options.author:
        pdfmark['/Author'] = options.author
    if options.keywords:
        pdfmark['/Keywords'] = options.keywords
    if options.subject:
        pdfmark['/Subject'] = options.subject

    if options.pdf_renderer == 'sandwich':
        renderer_tag = 'OCR-PDF'
    else:
        renderer_tag = 'OCR'

    pdfmark['/Creator'] = (
        f'{PROGRAM_NAME} {VERSION} / ' f'Tesseract {renderer_tag} {tesseract.version()}'
    )
    pdfmark['/Producer'] = f'pikepdf {pikepdf.__version__}'
    if 'OCRMYPDF_CREATOR' in os.environ:
        pdfmark['/Creator'] = os.environ['OCRMYPDF_CREATOR']
    if 'OCRMYPDF_PRODUCER' in os.environ:
        pdfmark['/Producer'] = os.environ['OCRMYPDF_PRODUCER']

    pdfmark['/ModDate'] = encode_pdf_date(datetime.now(timezone.utc))
    return pdfmark


def generate_postscript_stub(input_file, output_file, log, context):
    generate_pdfa_ps(output_file)


def convert_to_pdfa(input_files_groups, output_file, log, context):
    options = context.get_options()
    input_pdfinfo = context.get_pdfinfo()

    input_files = list(f for f in flatten_groups(input_files_groups))
    layers_file = next(
        (ii for ii in input_files if ii.endswith('layers.rendered.pdf')), None
    )

    # If the DocumentInfo record contains NUL characters, Ghostscript will
    # produce XMP metadata which contains invalid XML entities (&#0;).
    # NULs in DocumentInfo seem to be common since older Acrobats included them.
    # pikepdf can deal with this, but we make the world a better place by
    # stamping them out as soon as possible.
    with pikepdf.open(layers_file) as pdf_layers_file:
        if pdf_layers_file.docinfo:
            modified = False
            for k, v in pdf_layers_file.docinfo.items():
                if b'\x00' in bytes(v):
                    pdf_layers_file.docinfo[k] = bytes(v).replace(b'\x00', b'')
                    modified = True
            if modified:
                pdf_layers_file.save(layers_file)

    ps = next((ii for ii in input_files if ii.endswith('.ps')), None)
    ghostscript.generate_pdfa(
        pdf_version=input_pdfinfo.min_version,
        pdf_pages=[layers_file, ps],
        output_file=output_file,
        compression=options.pdfa_image_compression,
        log=log,
        threads=options.jobs or 1,
        pdfa_part=options.output_type[-1],  # is pdfa-1, pdfa-2, or pdfa-3
    )


def metadata_fixup(input_files_groups, output_file, log, context):
    options = context.get_options()

    input_files = list(f for f in flatten_groups(input_files_groups))
    original_file = next(
        (ii for ii in input_files if ii.endswith('.repaired.pdf')), None
    )
    layers_file = next(
        (ii for ii in input_files if ii.endswith('layers.rendered.pdf')), None
    )
    pdfa_file = next((ii for ii in input_files if ii.endswith('pdfa.pdf')), None)
    original = pikepdf.open(original_file)
    docinfo = get_docinfo(original, options)

    working_file = pdfa_file if pdfa_file else layers_file

    pdf = pikepdf.open(working_file)
    with pdf.open_metadata() as meta:
        meta.load_from_docinfo(docinfo, delete_missing=False)
        # If xmp:CreateDate is missing, set it to the modify date to
        # match Ghostscript, for consistency
        if 'xmp:CreateDate' not in meta:
            meta['xmp:CreateDate'] = meta.get('xmp:ModifyDate', '')
        if pdfa_file:
            meta_original = original.open_metadata()
            not_copied = set(meta_original.keys()) - set(meta.keys())
            if not_copied:
                log.warning(
                    "Some input metadata could not be copied because it is not "
                    "permitted in PDF/A. You may wish to examine the output "
                    "PDF's XMP metadata."
                )
                log.debug(
                    "The following metadata fields were not copied: %r", not_copied
                )

    pdf.save(
        output_file,
        compress_streams=True,
        object_stream_mode=pikepdf.ObjectStreamMode.generate,
    )
    original.close()
    pdf.close()


def optimize_pdf(input_file, output_file, log, context):
    optimize(input_file, output_file, log, context)


def merge_sidecars(input_files_groups, output_file, log, context):
    pdfinfo = context.get_pdfinfo()

    txt_files = [None] * len(pdfinfo)

    for infile in flatten_groups(input_files_groups):
        if infile.endswith('.txt'):
            idx = page_number(infile) - 1
            txt_files[idx] = infile

    def write_pages(stream):
        for page_num, txt_file in enumerate(txt_files):
            if page_num != 0:
                stream.write('\f')  # Form feed between pages
            if txt_file:
                with open(txt_file, 'r', encoding="utf-8") as in_:
                    txt = in_.read()
                    # Tesseract v4 alpha started adding form feeds in
                    # commit aa6eb6b
                    # No obvious way to detect what binaries will do this, so
                    # for consistency just ignore its form feeds and insert our
                    # own
                    if txt.endswith('\f'):
                        stream.write(txt[:-1])
                    else:
                        stream.write(txt)
            else:
                stream.write(f'[OCR skipped on page {(page_num + 1)}]')

    if output_file == '-':
        write_pages(sys.stdout)
        sys.stdout.flush()
    else:
        with open(output_file, 'w', encoding="utf-8") as out:
            write_pages(out)


def copy_final(input_files, output_file, log, context):
    input_file = next((ii for ii in input_files if ii.endswith('.pdf')))
    log.debug('%s -> %s', input_file, output_file)
    with open(input_file, 'rb') as input_stream:
        if output_file == '-':
            copyfileobj(input_stream, sys.stdout.buffer)
            sys.stdout.flush()
        else:
            # At this point we overwrite the output_file specified by the user
            # use copyfileobj because then we use open() to create the file and
            # get the appropriate umask, ownership, etc.
            with open(output_file, 'wb') as output_stream:
                copyfileobj(input_stream, output_stream)


def build_pipeline(options, work_folder, log, context):
    main_pipeline = Pipeline.pipelines['main']

    # Triage
    task_triage = main_pipeline.transform(
        task_func=triage,
        input=os.path.join(work_folder, 'origin'),
        filter=formatter('(?i)'),
        output=os.path.join(work_folder, 'origin.pdf'),
        extras=[log, context],
    )

    task_repair_and_parse_pdf = main_pipeline.transform(
        task_func=repair_and_parse_pdf,
        input=task_triage,
        filter=suffix('.pdf'),
        output='.repaired.pdf',
        output_dir=work_folder,
        extras=[log, context],
    )

    # Split (kwargs for split seems to be broken, so pass plain args)
    task_marker_pages = main_pipeline.split(
        marker_pages,
        task_repair_and_parse_pdf,
        os.path.join(work_folder, '*.marker.pdf'),
        extras=[log, context],
    )

    task_ocr_or_skip = main_pipeline.split(
        ocr_or_skip,
        task_marker_pages,
        [
            os.path.join(work_folder, '*.ocr.page.pdf'),
            os.path.join(work_folder, '*.skip.page.pdf'),
        ],
        extras=[log, context],
    )

    # Rasterize preview
    task_rasterize_preview = main_pipeline.transform(
        task_func=rasterize_preview,
        input=task_ocr_or_skip,
        filter=suffix('.page.pdf'),
        output='.preview.jpg',
        output_dir=work_folder,
        extras=[log, context],
    )
    task_rasterize_preview.active_if(options.rotate_pages)

    # Orient
    task_orient_page = main_pipeline.collate(
        task_func=orient_page,
        input=[task_ocr_or_skip, task_rasterize_preview],
        filter=regex(r".*/(\d{6})(\.ocr|\.skip)(?:\.page\.pdf|\.preview\.jpg)"),
        output=os.path.join(work_folder, r'\1\2.oriented.pdf'),
        extras=[log, context],
    )

    # Rasterize actual
    task_rasterize_with_ghostscript = main_pipeline.transform(
        task_func=rasterize_with_ghostscript,
        input=task_orient_page,
        filter=suffix('.ocr.oriented.pdf'),
        output='.page.png',
        output_dir=work_folder,
        extras=[log, context],
    )

    # Preprocessing subpipeline
    task_preprocess_remove_background = main_pipeline.transform(
        task_func=preprocess_remove_background,
        input=task_rasterize_with_ghostscript,
        filter=suffix(".page.png"),
        output=".pp-background.png",
        extras=[log, context],
    )

    task_preprocess_deskew = main_pipeline.transform(
        task_func=preprocess_deskew,
        input=task_preprocess_remove_background,
        filter=suffix(".pp-background.png"),
        output=".pp-deskew.png",
        extras=[log, context],
    )

    task_preprocess_clean = main_pipeline.transform(
        task_func=preprocess_clean,
        input=task_preprocess_deskew,
        filter=suffix(".pp-deskew.png"),
        output=".pp-clean.png",
        extras=[log, context],
    )

    task_select_ocr_image = main_pipeline.collate(
        task_func=select_ocr_image,
        input=[task_preprocess_clean],
        filter=regex(r".*/(\d{6})(?:\.page|\.pp-.*)\.png"),
        output=os.path.join(work_folder, r"\1.ocr.png"),
        extras=[log, context],
    )

    # HOCR OCR
    task_ocr_tesseract_hocr = main_pipeline.transform(
        task_func=ocr_tesseract_hocr,
        input=task_select_ocr_image,
        filter=suffix(".ocr.png"),
        output=[".hocr", ".txt"],
        extras=[log, context],
    )
    task_ocr_tesseract_hocr.graphviz(fillcolor='"#00cc66"')
    task_ocr_tesseract_hocr.active_if(options.pdf_renderer == 'hocr')

    task_select_visible_page_image = main_pipeline.collate(
        task_func=select_visible_page_image,
        input=[
            task_rasterize_with_ghostscript,
            task_preprocess_remove_background,
            task_preprocess_deskew,
            task_preprocess_clean,
        ],
        filter=regex(r".*/(\d{6})(?:\.page|\.pp-.*)\.png"),
        output=os.path.join(work_folder, r'\1.image'),
        extras=[log, context],
    )
    task_select_visible_page_image.graphviz(shape='diamond')

    task_select_image_layer = main_pipeline.collate(
        task_func=select_image_layer,
        input=[task_select_visible_page_image, task_orient_page],
        filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
        output=os.path.join(work_folder, r'\1.image-layer.pdf'),
        extras=[log, context],
    )
    task_select_image_layer.graphviz(fillcolor='"#00cc66"', shape='diamond')

    task_render_hocr_page = main_pipeline.transform(
        task_func=render_hocr_page,
        input=task_ocr_tesseract_hocr,
        filter=regex(r".*/(\d{6})(?:\.hocr)"),
        output=os.path.join(work_folder, r'\1.text.pdf'),
        extras=[log, context],
    )
    task_render_hocr_page.graphviz(fillcolor='"#00cc66"')
    task_render_hocr_page.active_if(options.pdf_renderer == 'hocr')

    # Tesseract OCR + text only PDF
    task_ocr_tesseract_textonly_pdf = main_pipeline.collate(
        task_func=ocr_tesseract_textonly_pdf,
        input=[task_select_ocr_image],
        filter=regex(r".*/(\d{6})(?:\.ocr.png)"),
        output=[
            os.path.join(work_folder, r'\1.text.pdf'),
            os.path.join(work_folder, r'\1.text.txt'),
        ],
        extras=[log, context],
    )
    task_ocr_tesseract_textonly_pdf.graphviz(fillcolor='"#ff69b4"')
    task_ocr_tesseract_textonly_pdf.active_if(options.pdf_renderer == 'sandwich')

    task_weave_layers = main_pipeline.collate(
        task_func=weave_layers,
        input=[
            task_repair_and_parse_pdf,
            task_render_hocr_page,
            task_ocr_tesseract_textonly_pdf,
            task_select_image_layer,
        ],
        filter=regex(
            r".*/((?:\d{6}(?:\.text\.pdf|\.image-layer\.pdf))|(?:origin\.repaired\.pdf))"
        ),
        output=os.path.join(work_folder, r'layers.rendered.pdf'),
        extras=[log, context],
    )
    task_weave_layers.graphviz(fillcolor='"#00cc66"')

    # PDF/A pdfmark
    task_generate_postscript_stub = main_pipeline.transform(
        task_func=generate_postscript_stub,
        input=task_repair_and_parse_pdf,
        filter=formatter(r'\.repaired\.pdf'),
        output=os.path.join(work_folder, 'pdfa.ps'),
        extras=[log, context],
    )
    task_generate_postscript_stub.active_if(options.output_type.startswith('pdfa'))

    # PDF/A conversion
    task_convert_to_pdfa = main_pipeline.merge(
        task_func=convert_to_pdfa,
        input=[task_generate_postscript_stub, task_weave_layers],
        output=os.path.join(work_folder, 'pdfa.pdf'),
        extras=[log, context],
    )
    task_convert_to_pdfa.active_if(options.output_type.startswith('pdfa'))

    task_metadata_fixup = main_pipeline.merge(
        task_func=metadata_fixup,
        input=[task_repair_and_parse_pdf, task_weave_layers, task_convert_to_pdfa],
        output=os.path.join(work_folder, 'metafix.pdf'),
        extras=[log, context],
    )

    task_merge_sidecars = main_pipeline.merge(
        task_func=merge_sidecars,
        input=[task_ocr_tesseract_hocr, task_ocr_tesseract_textonly_pdf],
        output=options.sidecar,
        extras=[log, context],
    )
    task_merge_sidecars.active_if(options.sidecar)

    # Optimize
    task_optimize_pdf = main_pipeline.transform(
        task_func=optimize_pdf,
        input=task_metadata_fixup,
        filter=suffix('.pdf'),
        output='.optimized.pdf',
        output_dir=work_folder,
        extras=[log, context],
    )

    # Finalize
    main_pipeline.merge(
        task_func=copy_final,
        input=[task_optimize_pdf],
        output=options.output_file,
        extras=[log, context],
    )
