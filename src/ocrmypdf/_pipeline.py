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

import logging
import os
import re
import sys
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO, Dict, Iterable, Optional, Union, cast

import img2pdf
import pikepdf
from pikepdf.models.metadata import encode_pdf_date
from PIL import Image, ImageColor, ImageDraw

from ocrmypdf import leptonica
from ocrmypdf._exec import unpaper
from ocrmypdf._jobcontext import PageContext, PdfContext
from ocrmypdf._version import PROGRAM_NAME
from ocrmypdf._version import __version__ as VERSION
from ocrmypdf.exceptions import (
    DpiError,
    EncryptedPdfError,
    InputFileError,
    PriorOcrFoundError,
    UnsupportedImageFormatError,
)
from ocrmypdf.helpers import Resolution, safe_symlink
from ocrmypdf.hocrtransform import HocrTransform
from ocrmypdf.optimize import optimize
from ocrmypdf.pdfa import generate_pdfa_ps
from ocrmypdf.pdfinfo import Colorspace, Encoding, PdfInfo

log = logging.getLogger(__name__)

VECTOR_PAGE_DPI = 400


def triage_image_file(input_file, output_file, options):
    log.info("Input file is not a PDF, checking if it is an image...")
    try:
        im = Image.open(input_file)
    except EnvironmentError as e:
        # Recover the original filename
        log.error(str(e).replace(str(input_file), str(options.input_file)))
        raise UnsupportedImageFormatError() from e

    with im:
        log.info("Input file is an image")
        if 'dpi' in im.info:
            if im.info['dpi'] <= (96, 96) and not options.image_dpi:
                log.info("Image size: (%d, %d)", *im.size)
                log.info("Image resolution: (%d, %d)", *im.info['dpi'])
                log.error(
                    "Input file is an image, but the resolution (DPI) is "
                    "not credible.  Estimate the resolution at which the "
                    "image was scanned and specify it using --image-dpi."
                )
                raise DpiError()
        elif not options.image_dpi:
            log.info("Image size: (%d, %d)", *im.size)
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
                log.info("Input image has no ICC profile, assuming sRGB")
            elif im.mode == 'CMYK':
                log.error("Input CMYK image has no ICC profile, not usable")
                raise UnsupportedImageFormatError()

    try:
        log.info("Image seems valid. Try converting to PDF...")
        layout_fun = img2pdf.default_layout_fun
        if options.image_dpi:
            layout_fun = img2pdf.get_fixed_dpi_layout_fun(
                Resolution(options.image_dpi, options.image_dpi)
            )
        with open(output_file, 'wb') as outf:
            img2pdf.convert(
                os.fspath(input_file),
                layout_fun=layout_fun,
                with_pdfrw=False,
                outputstream=outf,
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


def triage(original_filename, input_file, output_file, options):
    try:
        if _pdf_guess_version(input_file):
            if options.image_dpi:
                log.warning(
                    "Argument --image-dpi is being ignored because the "
                    "input file is a PDF, not an image."
                )
            # Origin file is a pdf create a symlink with pdf extension
            safe_symlink(input_file, output_file)
            return output_file
    except EnvironmentError as e:
        log.debug(f"Temporary file was at: {input_file}")
        msg = str(e).replace(str(input_file), original_filename)
        raise InputFileError(msg) from e

    triage_image_file(input_file, output_file, options)
    return output_file


def get_pdfinfo(
    input_file,
    detailed_analysis=False,
    progbar=False,
    max_workers=None,
    check_pages=None,
):
    try:
        return PdfInfo(
            input_file,
            detailed_analysis=detailed_analysis,
            progbar=progbar,
            max_workers=max_workers,
            check_pages=check_pages,
        )
    except pikepdf.PasswordError:
        raise EncryptedPdfError()
    except pikepdf.PdfError:
        raise InputFileError()


def validate_pdfinfo_options(context: PdfContext):
    pdfinfo = context.pdfinfo
    options = context.options

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
            raise InputFileError()
        else:
            log.warning(
                "This PDF has a fillable form. "
                "Chances are it is a pure digital "
                "document that does not need OCR."
            )
            if not options.force_ocr:
                log.info(
                    "Use the option --force-ocr to produce an image of the "
                    "form and all filled form fields. The output PDF will be "
                    "'flattened' and will no longer be fillable."
                )
    context.plugin_manager.hook.validate(pdfinfo=pdfinfo, options=options)


def get_page_dpi(pageinfo, options):
    "Get the DPI when nonsquare DPI is tolerable"
    xres = max(
        pageinfo.dpi.x or VECTOR_PAGE_DPI,
        options.oversample or 0.0,
        VECTOR_PAGE_DPI if pageinfo.has_vector else 0.0,
    )
    yres = max(
        pageinfo.dpi.y or VECTOR_PAGE_DPI,
        options.oversample or 0,
        VECTOR_PAGE_DPI if pageinfo.has_vector else 0.0,
    )
    return Resolution(float(xres), float(yres))


def get_page_square_dpi(pageinfo, options) -> Resolution:
    "Get the DPI when we require xres == yres, scaled to physical units"
    xres = pageinfo.dpi.x or 0.0
    yres = pageinfo.dpi.y or 0.0
    userunit = float(pageinfo.userunit) or 1.0
    units = float(
        max(
            (xres * userunit) or VECTOR_PAGE_DPI,
            (yres * userunit) or VECTOR_PAGE_DPI,
            VECTOR_PAGE_DPI if pageinfo.has_vector else 0.0,
            options.oversample or 0.0,
        )
    )
    return Resolution(units, units)


def get_canvas_square_dpi(pageinfo, options) -> Resolution:
    """Get the DPI when we require xres == yres, in Postscript units"""
    units = float(
        max(
            (pageinfo.dpi.x) or VECTOR_PAGE_DPI,
            (pageinfo.dpi.y) or VECTOR_PAGE_DPI,
            VECTOR_PAGE_DPI if pageinfo.has_vector else 0.0,
            options.oversample or 0.0,
        )
    )
    return Resolution(units, units)


def is_ocr_required(page_context: PageContext):
    pageinfo = page_context.pageinfo
    options = page_context.options

    ocr_required = True

    if options.pages and pageinfo.pageno not in options.pages:
        log.debug(f"skipped {pageinfo.pageno} as requested by --pages {options.pages}")
        ocr_required = False
    elif pageinfo.has_text:
        if not options.force_ocr and not (options.skip_text or options.redo_ocr):
            raise PriorOcrFoundError(
                "page already has text! - aborting (use --force-ocr to force OCR; "
                " see also help for the arguments --skip-text and --redo-ocr"
            )
        elif options.force_ocr:
            log.info("page already has text! - rasterizing text and running OCR anyway")
            ocr_required = True
        elif options.redo_ocr:
            if pageinfo.has_corrupt_text:
                log.warning(
                    "some text on this page cannot be mapped to characters: "
                    "consider using --force-ocr instead"
                )
            else:
                log.info("redoing OCR")
            ocr_required = True
        elif options.skip_text:
            log.info("skipping all processing on this page")
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
                "page has no images - "
                f"rasterizing at {options.oversample} DPI because "
                "--force-ocr --oversample was specified"
            )
        elif options.force_ocr:
            # Warn the user they might not want to do this
            log.warning(
                "page has no images - "
                "all vector content will be "
                f"rasterized at {VECTOR_PAGE_DPI} DPI, losing some resolution and likely "
                "increasing file size. Use --oversample to adjust the "
                "DPI."
            )
        else:
            log.info(
                "page has no images - "
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
                "page too big, skipping OCR "
                f"({(pixel_count / 1_000_000):.1f} MPixels > {options.skip_big:.1f} MPixels --skip-big)"
            )
    return ocr_required


def rasterize_preview(input_file: Path, page_context: PageContext):
    output_file = page_context.get_path('rasterize_preview.jpg')
    canvas_dpi = get_canvas_square_dpi(page_context.pageinfo, page_context.options)
    page_dpi = get_page_square_dpi(page_context.pageinfo, page_context.options)
    page_context.plugin_manager.hook.rasterize_pdf_page(
        input_file=input_file,
        output_file=output_file,
        raster_device='jpeggray',
        raster_dpi=canvas_dpi,
        page_dpi=page_dpi,
        pageno=page_context.pageinfo.pageno + 1,
    )
    return output_file


def describe_rotation(page_context: PageContext, orient_conf, correction: int):
    """
    Describe the page rotation we are going to perform.
    """
    direction = {0: '⇧', 90: '⇨', 180: '⇩', 270: '⇦'}
    turns = {0: ' ', 90: '⬏', 180: '↻', 270: '⬑'}

    existing_rotation = page_context.pageinfo.rotation
    action = ''
    if orient_conf.confidence >= page_context.options.rotate_pages_threshold:
        if correction != 0:
            action = 'will rotate ' + turns[correction]
        else:
            action = 'rotation appears correct'
    else:
        if correction != 0:
            action = 'confidence too low to rotate'
        else:
            action = 'no change'

    facing = ''

    if existing_rotation != 0:
        facing = f"with existing rotation {direction.get(existing_rotation, '?')}, "
    facing += f"page is facing {direction.get(orient_conf.angle, '?')}"

    return f"{facing}, confidence {orient_conf.confidence:.2f} - {action}"


def get_orientation_correction(preview: Path, page_context: PageContext):
    """Work out orientation correct for each page.

    We ask Ghostscript to draw a preview page, which will rasterize with the
    current /Rotate applied, and then ask OCR which way the page is
    oriented. If the value of /Rotate is correct (e.g., a user already
    manually fixed rotation), then OCR will say the page is pointing
    up and the correction is zero. Otherwise, the orientation found by
    OCR represents the clockwise rotation, or the counterclockwise
    correction to rotation.

    When we draw the real page for OCR, we rotate it by the CCW correction,
    which points it (hopefully) upright. _graft.py takes care of the orienting
    the image and text layers.
    """

    orient_conf = page_context.plugin_manager.hook.get_ocr_engine().get_orientation(
        preview, page_context.options
    )

    correction = orient_conf.angle % 360
    log.info(describe_rotation(page_context, orient_conf, correction))
    if (
        orient_conf.confidence >= page_context.options.rotate_pages_threshold
        and correction != 0
    ):
        return correction

    return 0


def rasterize(
    input_file: Path,
    page_context: PageContext,
    correction: int = 0,
    output_tag: str = '',
    remove_vectors=None,
):
    colorspaces = ['pngmono', 'pnggray', 'png256', 'png16m']
    device_idx = 0

    if remove_vectors is None:
        remove_vectors = page_context.options.remove_vectors

    output_file = page_context.get_path(f'rasterize{output_tag}.png')
    pageinfo = page_context.pageinfo

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

    if pageinfo.has_vector:
        device_idx = at_least('png16m')

    device = colorspaces[device_idx]

    log.debug(f"Rasterize with {device}")

    # Produce the page image with square resolution or else deskew and OCR
    # will not work properly.
    canvas_dpi = get_canvas_square_dpi(pageinfo, page_context.options)
    page_dpi = get_page_square_dpi(pageinfo, page_context.options)

    page_context.plugin_manager.hook.rasterize_pdf_page(
        input_file=input_file,
        output_file=output_file,
        raster_device=device,
        raster_dpi=canvas_dpi,
        page_dpi=page_dpi,
        pageno=pageinfo.pageno + 1,
        rotation=correction,
        filter_vector=remove_vectors,
    )
    return output_file


def preprocess_remove_background(input_file: Path, page_context: PageContext):
    if any(image.bpc > 1 for image in page_context.pageinfo.images):
        output_file = page_context.get_path('pp_rm_bg.png')
        leptonica.remove_background(input_file, output_file)
        return output_file
    else:
        log.info("background removal skipped on mono page")
        return input_file


def preprocess_deskew(input_file: Path, page_context: PageContext):
    output_file = page_context.get_path('pp_deskew.png')
    dpi = get_page_square_dpi(page_context.pageinfo, page_context.options)
    leptonica.deskew(input_file, output_file, dpi.x)
    return output_file


def preprocess_clean(input_file: Path, page_context: PageContext):
    output_file = page_context.get_path('pp_clean.png')
    dpi = get_page_square_dpi(page_context.pageinfo, page_context.options)
    unpaper.clean(input_file, output_file, dpi.x, page_context.options.unpaper_args)
    return output_file


def create_ocr_image(image: Path, page_context: PageContext):
    """Create the image we send for OCR. May not be the same as the display
    image depending on preprocessing. This image will never be shown to the
    user."""

    output_file = page_context.get_path('ocr.png')
    options = page_context.options
    with Image.open(image) as im:
        white = ImageColor.getcolor('#ffffff', im.mode)
        # pink = ImageColor.getcolor('#ff0080', im.mode)
        draw = ImageDraw.ImageDraw(im)

        log.debug('resolution %r', im.info['dpi'])

        if not options.force_ocr:
            # Do not mask text areas when forcing OCR, because we need to OCR
            # all text areas
            mask = None  # Exclude both visible and invisible text from OCR
            if options.redo_ocr:
                mask = True  # Mask visible text, but not invisible text

            for textarea in page_context.pageinfo.get_textareas(
                visible=mask, corrupt=None
            ):
                # Calculate resolution based on the image size and page dimensions
                # without regard whatever resolution is in pageinfo (may differ or
                # be None)
                bbox = [float(v) for v in textarea]
                xyscale = tuple(float(coord) / 72.0 for coord in im.info['dpi'])
                pixcoords = [
                    bbox[0] * xyscale[0],
                    im.height - bbox[3] * xyscale[1],
                    bbox[2] * xyscale[0],
                    im.height - bbox[1] * xyscale[1],
                ]
                pixcoords = [int(round(c)) for c in pixcoords]
                log.debug('blanking %r', pixcoords)
                draw.rectangle(pixcoords, fill=white)
                # draw.rectangle(pixcoords, outline=pink)

        if options.threshold:
            pix = leptonica.Pix.frompil(im)
            pix = pix.masked_threshold_on_background_norm()
            im = pix.topil()

        del draw

        filter_im = page_context.plugin_manager.hook.filter_ocr_image(
            page=page_context, image=im
        )
        if filter_im is not None:
            im = filter_im

        # Pillow requires integer DPI
        dpi = tuple(round(coord) for coord in im.info['dpi'])
        im.save(output_file, dpi=dpi)
    return output_file


def ocr_engine_hocr(input_file: Path, page_context: PageContext):
    hocr_out = page_context.get_path('ocr_hocr.hocr')
    hocr_text_out = page_context.get_path('ocr_hocr.txt')
    options = page_context.options

    ocr_engine = page_context.plugin_manager.hook.get_ocr_engine()
    ocr_engine.generate_hocr(
        input_file=input_file,
        output_hocr=hocr_out,
        output_text=hocr_text_out,
        options=options,
    )
    return (hocr_out, hocr_text_out)


def should_visible_page_image_use_jpg(pageinfo):
    # If all images were JPEGs originally, produce a JPEG as output
    return pageinfo.images and all(im.enc == Encoding.jpeg for im in pageinfo.images)


def create_visible_page_jpg(image: Path, page_context: PageContext) -> Path:
    output_file = page_context.get_path('visible.jpg')
    with Image.open(image) as im:
        # At this point the image should be a .png, but deskew, unpaper
        # might have removed the DPI information. In this case, fall back to
        # square DPI used to rasterize. When the preview image was
        # rasterized, it was also converted to square resolution, which is
        # what we want to give to the OCR engine, so keep it square.
        if 'dpi' in im.info:
            dpi = Resolution(*im.info['dpi'])
        else:
            # Fallback to page-implied DPI
            dpi = get_page_square_dpi(page_context.pageinfo, page_context.options)

        # Pillow requires integer DPI
        im.save(output_file, format='JPEG', dpi=dpi.to_int())
    return output_file


def create_pdf_page_from_image(image: Path, page_context: PageContext):
    # We rasterize a square DPI version of each page because most image
    # processing tools don't support rectangular DPI. Use the square DPI as it
    # accurately describes the image. It would be possible to resample the image
    # at this stage back to non-square DPI to more closely resemble the input,
    # except that the hocr renderer does not understand non-square DPI. The
    # sandwich renderer would be fine.
    output_file = page_context.get_path('visible.pdf')
    dpi = get_page_square_dpi(page_context.pageinfo, page_context.options)
    layout_fun = img2pdf.get_fixed_dpi_layout_fun(dpi)

    # This create a single page PDF
    with open(image, 'rb') as imfile, open(output_file, 'wb') as pdf:
        log.debug('convert')
        img2pdf.convert(
            imfile, with_pdfrw=False, layout_fun=layout_fun, outputstream=pdf
        )
        log.debug('convert done')
    return output_file


def render_hocr_page(hocr: Path, page_context: PageContext):
    output_file = page_context.get_path('ocr_hocr.pdf')
    dpi = get_page_square_dpi(page_context.pageinfo, page_context.options)
    hocrtransform = HocrTransform(hocr, dpi.x)  # square
    hocrtransform.to_pdf(
        output_file,
        image_filename=None,
        show_bounding_boxes=False,
        invisible_text=True,
        interword_spaces=True,
    )
    return output_file


def ocr_engine_textonly_pdf(input_image: Path, page_context: PageContext):
    output_pdf = page_context.get_path('ocr_tess.pdf')
    output_text = page_context.get_path('ocr_tess.txt')
    options = page_context.options

    ocr_engine = page_context.plugin_manager.hook.get_ocr_engine()
    ocr_engine.generate_pdf(
        input_file=input_image,
        output_pdf=output_pdf,
        output_text=output_text,
        options=options,
    )
    return (output_pdf, output_text)


def get_docinfo(base_pdf: pikepdf.Pdf, context: PdfContext) -> Dict[str, str]:
    options = context.options

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
    if options is not None:
        if options.title:
            pdfmark['/Title'] = options.title
        if options.author:
            pdfmark['/Author'] = options.author
        if options.keywords:
            pdfmark['/Keywords'] = options.keywords
        if options.subject:
            pdfmark['/Subject'] = options.subject

    creator_tag = context.plugin_manager.hook.get_ocr_engine().creator_tag(options)

    pdfmark['/Creator'] = f'{PROGRAM_NAME} {VERSION} / {creator_tag}'
    pdfmark['/Producer'] = f'pikepdf {pikepdf.__version__}'
    if 'OCRMYPDF_CREATOR' in os.environ:
        pdfmark['/Creator'] = os.environ['OCRMYPDF_CREATOR']
    if 'OCRMYPDF_PRODUCER' in os.environ:
        pdfmark['/Producer'] = os.environ['OCRMYPDF_PRODUCER']

    pdfmark['/ModDate'] = encode_pdf_date(datetime.now(timezone.utc))
    return pdfmark


def generate_postscript_stub(context: PdfContext):
    output_file = context.get_path('pdfa.ps')
    generate_pdfa_ps(output_file)
    return output_file


def convert_to_pdfa(input_pdf: Path, input_ps_stub: Path, context: PdfContext):
    options = context.options
    input_pdfinfo = context.pdfinfo
    fix_docinfo_file = context.get_path('fix_docinfo.pdf')
    output_file = context.get_path('pdfa.pdf')

    # If the DocumentInfo record contains NUL characters, Ghostscript will
    # produce XMP metadata which contains invalid XML entities (&#0;).
    # NULs in DocumentInfo seem to be common since older Acrobats included them.
    # pikepdf can deal with this, but we make the world a better place by
    # stamping them out as soon as possible.
    modified = False
    with pikepdf.open(input_pdf) as pdf_file:
        try:
            len(pdf_file.docinfo)
        except TypeError:
            log.error(
                "File contains a malformed DocumentInfo block - continuing anyway"
            )
        else:
            if pdf_file.docinfo:
                for k, v in pdf_file.docinfo.items():
                    if b'\x00' in bytes(v):
                        pdf_file.docinfo[k] = bytes(v).replace(b'\x00', b'')
                        modified = True
        if modified:
            pdf_file.save(fix_docinfo_file)
        else:
            safe_symlink(input_pdf, fix_docinfo_file)

    context.plugin_manager.hook.generate_pdfa(
        pdf_version=input_pdfinfo.min_version,
        pdf_pages=[fix_docinfo_file],
        pdfmark=input_ps_stub,
        output_file=output_file,
        compression=options.pdfa_image_compression,
        pdfa_part=options.output_type[-1],  # is pdfa-1, pdfa-2, or pdfa-3
    )

    return output_file


def should_linearize(working_file: Path, context: PdfContext):
    filesize = os.stat(working_file).st_size
    if filesize > (context.options.fast_web_view * 1_000_000):
        return True
    return False


def metadata_fixup(working_file: Path, context: PdfContext):
    output_file = context.get_path('metafix.pdf')
    options = context.options

    def report_on_metadata(missing):
        if not missing:
            return
        if options.output_type.startswith('pdfa'):
            log.warning(
                "Some input metadata could not be copied because it is not "
                "permitted in PDF/A. You may wish to examine the output "
                "PDF's XMP metadata."
            )
            log.debug("The following metadata fields were not copied: %r", missing)
        else:
            log.error(
                "Some input metadata could not be copied."
                "You may wish to examine the output PDF's XMP metadata."
            )
            log.info("The following metadata fields were not copied: %r", missing)

    with pikepdf.open(context.origin) as original, pikepdf.open(working_file) as pdf:
        docinfo = get_docinfo(original, context)
        with pdf.open_metadata() as meta:
            meta.load_from_docinfo(docinfo, delete_missing=False, raise_failure=False)
            # If xmp:CreateDate is missing, set it to the modify date to
            # match Ghostscript, for consistency
            if 'xmp:CreateDate' not in meta:
                meta['xmp:CreateDate'] = meta.get('xmp:ModifyDate', '')

            # Ghostscript likes to set title to Untitled if omitted from input.
            # Reverse this, because PDF/A TechNote 0003:Metadata in PDF/A-1
            # and the XMP Spec do not make this recommendation.
            if meta.get('dc:title') == 'Untitled':
                with original.open_metadata() as original_meta:
                    if 'dc:title' not in original_meta:
                        del meta['dc:title']

            meta_original = original.open_metadata()
            missing = set(meta_original.keys()) - set(meta.keys())
            report_on_metadata(missing)

        pdf.save(
            output_file,
            compress_streams=True,
            preserve_pdfa=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            linearize=(  # Don't linearize if optimize() will be linearizing too
                should_linearize(working_file, context)
                if options.optimize == 0
                else False
            ),
        )

    return output_file


def optimize_pdf(input_file: Path, context: PdfContext):
    output_file = context.get_path('optimize.pdf')
    save_settings = dict(
        compress_streams=True,
        preserve_pdfa=True,
        object_stream_mode=pikepdf.ObjectStreamMode.generate,
        linearize=should_linearize(input_file, context),
    )
    optimize(input_file, output_file, context, save_settings)
    return output_file


def merge_sidecars(txt_files: Iterable[Optional[Path]], context: PdfContext):
    output_file = context.get_path('sidecar.txt')
    with open(output_file, 'w', encoding="utf-8") as stream:
        for page_num, txt_file in enumerate(txt_files):
            if page_num != 0:
                stream.write('\f')  # Form feed between pages
            if txt_file:
                with open(txt_file, 'r', encoding="utf-8") as in_:
                    txt = in_.read()
                    # Some OCR engines (e.g. Tesseract v4 alpha) add form feeds
                    # between pages, and some do not. For consistency, we ignore
                    # any added by the OCR engine and them on our own.
                    if txt.endswith('\f'):
                        stream.write(txt[:-1])
                    else:
                        stream.write(txt)
            else:
                stream.write(f'[OCR skipped on page {(page_num + 1)}]')
    return output_file


def copy_final(input_file, output_file, _context: PdfContext):
    log.debug('%s -> %s', input_file, output_file)
    with open(input_file, 'rb') as input_stream:
        if output_file == '-':
            copyfileobj(input_stream, sys.stdout.buffer)
            sys.stdout.flush()
        elif hasattr(output_file, 'writable'):
            output_stream = output_file
            copyfileobj(input_stream, output_stream)
            with suppress(AttributeError):
                output_stream.flush()
        else:
            # At this point we overwrite the output_file specified by the user
            # use copyfileobj because then we use open() to create the file and
            # get the appropriate umask, ownership, etc.
            with open(output_file, 'wb') as output_stream:
                copyfileobj(input_stream, output_stream)
