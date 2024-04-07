# SPDX-FileCopyrightText: 2018-2022 James R. Barlow
# SPDX-FileCopyrightText: 2019 Martin Wind
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF page processing pipeline functions."""

from __future__ import annotations

import logging
import os
import re
import sys
from collections.abc import Iterable, Iterator, Sequence
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from shutil import copyfileobj
from typing import Any, BinaryIO, TypeVar, cast

import img2pdf
import pikepdf
from PIL import Image, ImageColor, ImageDraw

from ocrmypdf._concurrent import Executor
from ocrmypdf._exec import unpaper
from ocrmypdf._jobcontext import PageContext, PdfContext
from ocrmypdf._metadata import repair_docinfo_nuls
from ocrmypdf.exceptions import (
    DigitalSignatureError,
    DpiError,
    EncryptedPdfError,
    InputFileError,
    PriorOcrFoundError,
    TaggedPDFError,
    UnsupportedImageFormatError,
)
from ocrmypdf.helpers import IMG2PDF_KWARGS, Resolution, safe_symlink
from ocrmypdf.hocrtransform import DebugRenderOptions, HocrTransform
from ocrmypdf.hocrtransform._font import Courier
from ocrmypdf.pdfa import generate_pdfa_ps
from ocrmypdf.pdfinfo import Colorspace, Encoding, PageInfo, PdfInfo
from ocrmypdf.pluginspec import OrientationConfidence

try:
    from pi_heif import register_heif_opener
except ImportError:

    def register_heif_opener():
        pass


T = TypeVar("T")
log = logging.getLogger(__name__)

VECTOR_PAGE_DPI = 400


register_heif_opener()


def triage_image_file(input_file: Path, output_file: Path, options) -> None:
    """Triage the input image file.

    If the input file is an image, check its resolution and convert it to PDF.

    Args:
        input_file: The path to the input file.
        output_file: The path to the output file.
        options: An object containing the options passed to the OCRmyPDF command.

    Raises:
        UnsupportedImageFormatError: If the input file is not a supported image format.
        DpiError: If the input image has no resolution (DPI) in its metadata or if the
            resolution is not credible.
    """
    log.info("Input file is not a PDF, checking if it is an image...")
    try:
        im = Image.open(input_file)
    except OSError as e:
        # Recover the original filename
        log.error(str(e).replace(str(input_file), str(options.input_file)))
        raise UnsupportedImageFormatError() from e

    with im:
        log.info("Input file is an image")
        if 'dpi' in im.info:
            if im.info['dpi'] <= (96, 96) and not options.image_dpi:
                log.info("Image size: (%d, %d)", *im.size)
                log.info("Image resolution: (%d, %d)", *im.info['dpi'])
                raise DpiError(
                    "Input file is an image, but the resolution (DPI) is "
                    "not credible.  Estimate the resolution at which the "
                    "image was scanned and specify it using --image-dpi."
                )
        elif not options.image_dpi:
            log.info("Image size: (%d, %d)", *im.size)
            raise DpiError(
                "Input file is an image, but has no resolution (DPI) "
                "in its metadata.  Estimate the resolution at which "
                "image was scanned and specify it using --image-dpi."
            )

        if im.mode in ('RGBA', 'LA'):
            raise UnsupportedImageFormatError(
                "The input image has an alpha channel. Remove the alpha "
                "channel first."
            )

        if 'iccprofile' not in im.info:
            if im.mode == 'RGB':
                log.info("Input image has no ICC profile, assuming sRGB")
            elif im.mode == 'CMYK':
                raise UnsupportedImageFormatError(
                    "Input CMYK image has no ICC profile, not usable"
                )

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
                outputstream=outf,
                **IMG2PDF_KWARGS,
            )
        log.info("Successfully converted to PDF, processing...")
    except img2pdf.ImageOpenError as e:
        raise UnsupportedImageFormatError() from e


def _pdf_guess_version(input_file: Path, search_window=1024) -> str:
    """Try to find version signature at start of file.

    Not robust enough to deal with appended files.

    Returns empty string if not found, indicating file is probably not PDF.
    """
    with open(input_file, 'rb') as f:
        signature = f.read(search_window)
    m = re.search(rb'%PDF-(\d\.\d)', signature)
    if m:
        return m.group(1).decode('ascii')
    return ''


def triage(
    original_filename: str, input_file: Path, output_file: Path, options
) -> Path:
    """Triage the input file. We can handle PDFs and images."""
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
    except OSError as e:
        log.debug(f"Temporary file was at: {input_file}")
        msg = str(e).replace(str(input_file), original_filename)
        raise InputFileError(msg) from e

    triage_image_file(input_file, output_file, options)
    return output_file


def get_pdfinfo(
    input_file,
    *,
    executor: Executor,
    detailed_analysis: bool = False,
    progbar: bool = False,
    max_workers: int | None = None,
    use_threads: bool = True,
    check_pages=None,
) -> PdfInfo:
    """Get the PDF info."""
    try:
        return PdfInfo(
            input_file,
            detailed_analysis=detailed_analysis,
            progbar=progbar,
            max_workers=max_workers,
            use_threads=use_threads,
            check_pages=check_pages,
            executor=executor,
        )
    except pikepdf.PasswordError as e:
        raise EncryptedPdfError() from e
    except pikepdf.PdfError as e:
        raise InputFileError() from e


def validate_pdfinfo_options(context: PdfContext) -> None:
    """Validate the PDF info options."""
    pdfinfo = context.pdfinfo
    options = context.options

    if pdfinfo.needs_rendering:
        raise InputFileError(
            "This PDF contains dynamic XFA forms created by Adobe LiveCycle "
            "Designer and can only be read by Adobe Acrobat or Adobe Reader."
        )
    if pdfinfo.has_signature:
        if options.invalidate_digital_signatures:
            log.warning("All digital signatures will be invalidated")
        else:
            raise DigitalSignatureError()
    if pdfinfo.has_acroform:
        if options.redo_ocr:
            raise InputFileError(
                "This PDF has a user fillable form. --redo-ocr is not "
                "currently possible on such files."
            )
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
    if pdfinfo.is_tagged:
        if options.force_ocr or options.skip_text or options.redo_ocr:
            log.warning(
                "This PDF is marked as a Tagged PDF. This often indicates "
                "that the PDF was generated from an office document and does "
                "not need OCR. PDF pages processed by OCRmyPDF may not be "
                "tagged correctly."
            )
        else:
            raise TaggedPDFError()
    context.plugin_manager.hook.validate(pdfinfo=pdfinfo, options=options)


def _vector_page_dpi(pageinfo: PageInfo) -> int:
    """Get a DPI to use for vector pages, if the page has vector content."""
    return VECTOR_PAGE_DPI if pageinfo.has_vector or pageinfo.has_text else 0


def get_page_square_dpi(
    page_context: PageContext, image_dpi: Resolution | None = None
) -> Resolution:
    """Get the DPI when we require xres == yres, scaled to physical units.

    Page DPI includes UserUnit scaling.
    """
    pageinfo = page_context.pageinfo
    options = page_context.options
    if not image_dpi:
        image_dpi = pageinfo.dpi
    xres = image_dpi.x or 0.0
    yres = image_dpi.y or 0.0
    userunit = float(pageinfo.userunit) or 1.0
    units = float(
        max(
            (xres * userunit) or VECTOR_PAGE_DPI,
            (yres * userunit) or VECTOR_PAGE_DPI,
            _vector_page_dpi(pageinfo),
            options.oversample or 0.0,
        )
    )
    return Resolution(units, units)


def get_canvas_square_dpi(
    page_context: PageContext, image_dpi: Resolution | None = None
) -> Resolution:
    """Get the DPI when we require xres == yres, in Postscript units.

    Canvas DPI is independent of PDF UserUnit scaling, which is
    used to describe situations where the PDF user space is not 1:1 with
    the physical units of the page.
    """
    pageinfo = page_context.pageinfo
    options = page_context.options
    if not image_dpi:
        image_dpi = pageinfo.dpi
    units = float(
        max(
            image_dpi.x or VECTOR_PAGE_DPI,
            image_dpi.y or VECTOR_PAGE_DPI,
            _vector_page_dpi(pageinfo),
            options.oversample or 0.0,
        )
    )
    return Resolution(units, units)


def is_ocr_required(page_context: PageContext) -> bool:
    """Check if the page needs to be OCR'd."""
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
                f"rasterized at {VECTOR_PAGE_DPI} DPI, losing some resolution and "
                "likely increasing file size. Use --oversample to adjust the "
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
                f"({(pixel_count / 1_000_000):.1f} MPixels > "
                f"{options.skip_big:.1f} MPixels --skip-big)"
            )
    return ocr_required


def rasterize_preview(input_file: Path, page_context: PageContext) -> Path:
    """Generate a lower quality preview image."""
    output_file = page_context.get_path('rasterize_preview.jpg')
    canvas_dpi = Resolution(300.0, 300.0).take_min(
        [get_canvas_square_dpi(page_context)]
    )
    page_dpi = Resolution(300.0, 300.0).take_min([get_page_square_dpi(page_context)])
    page_context.plugin_manager.hook.rasterize_pdf_page(
        input_file=input_file,
        output_file=output_file,
        raster_device='jpeggray',
        raster_dpi=canvas_dpi,
        pageno=page_context.pageinfo.pageno + 1,
        page_dpi=page_dpi,
        rotation=0,
        filter_vector=False,
        stop_on_soft_error=not page_context.options.continue_on_soft_render_error,
    )
    return output_file


def describe_rotation(
    page_context: PageContext, orient_conf: OrientationConfidence, correction: int
) -> str:
    """Describe the page rotation we are going to perform (or not perform)."""
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


def get_orientation_correction(preview: Path, page_context: PageContext) -> int:
    """Work out orientation correction for each page.

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


def calculate_image_dpi(page_context: PageContext) -> Resolution:
    """Calculate the DPI for the page image."""
    pageinfo = page_context.pageinfo
    dpi_profile = pageinfo.page_dpi_profile()
    if dpi_profile and dpi_profile.average_to_max_dpi_ratio < 0.8:
        image_dpi = Resolution(dpi_profile.weighted_dpi, dpi_profile.weighted_dpi)
    else:
        image_dpi = pageinfo.dpi
    return image_dpi


def calculate_raster_dpi(page_context: PageContext):
    """Calculate the DPI for rasterization."""
    # Produce the page image with square resolution or else deskew and OCR
    # will not work properly.
    image_dpi = calculate_image_dpi(page_context)
    dpi_profile = page_context.pageinfo.page_dpi_profile()
    canvas_dpi = get_canvas_square_dpi(page_context, image_dpi)
    page_dpi = get_page_square_dpi(page_context, image_dpi)
    if dpi_profile and dpi_profile.average_to_max_dpi_ratio < 0.8:
        log.warning(
            "Weight average image DPI is %0.1f, max DPI is %0.1f. "
            "The discrepancy may indicate a high detail region on this page, "
            "but could also indicate a problem with the input PDF file. "
            "Page image will be rendered at %0.1f DPI.",
            dpi_profile.weighted_dpi,
            dpi_profile.max_dpi,
            canvas_dpi.to_scalar(),
        )
    return canvas_dpi, page_dpi


def rasterize(
    input_file: Path,
    page_context: PageContext,
    correction: int = 0,
    output_tag: str = '',
    remove_vectors: bool | None = None,
) -> Path:
    """Rasterize a PDF page to a PNG image.

    Args:
        input_file: The input PDF file path.
        page_context: The page context object.
        correction: The orientation correction angle. Defaults to 0.
        output_tag: The output tag. Defaults to ''.
        remove_vectors: Whether to remove vectors. Defaults to None, which means
            the value from the page context options will be used. If the value
            is True or False, it will override the page context options.

    Returns:
        Path: The output PNG file path.
    """
    colorspaces = ['pngmono', 'pnggray', 'png256', 'png16m']
    device_idx = 0

    if remove_vectors is None:
        remove_vectors = page_context.options.remove_vectors

    output_file = page_context.get_path(f'rasterize{output_tag}.png')
    pageinfo = page_context.pageinfo

    def at_least(colorspace):
        return max(device_idx, colorspaces.index(colorspace))

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
        log.debug("Page has vector content, using png16m")
        device_idx = at_least('png16m')

    device = colorspaces[device_idx]

    log.debug(f"Rasterize with {device}, rotation {correction}")

    canvas_dpi, page_dpi = calculate_raster_dpi(page_context)

    page_context.plugin_manager.hook.rasterize_pdf_page(
        input_file=input_file,
        output_file=output_file,
        raster_device=device,
        raster_dpi=canvas_dpi,
        page_dpi=page_dpi,
        pageno=pageinfo.pageno + 1,
        rotation=correction,
        filter_vector=remove_vectors,
        stop_on_soft_error=not page_context.options.continue_on_soft_render_error,
    )
    return output_file


def preprocess_remove_background(input_file: Path, page_context: PageContext) -> Path:
    """Remove the background from the input image (temporarily disabled)."""
    if any(image.bpc > 1 for image in page_context.pageinfo.images):
        raise NotImplementedError("--remove-background is temporarily not implemented")
        # output_file = page_context.get_path('pp_rm_bg.png')
        # leptonica.remove_background(input_file, output_file)
        # return output_file
    log.info("background removal skipped on mono page")
    return input_file


def preprocess_deskew(input_file: Path, page_context: PageContext) -> Path:
    """Deskews the input image using the OCR engine and saves the output to a file.

    Args:
        input_file: The input image file to deskew.
        page_context: The context of the page being processed.

    Returns:
        Path: The path to the deskewed image file.
    """
    output_file = page_context.get_path('pp_deskew.png')
    dpi = get_page_square_dpi(page_context, calculate_image_dpi(page_context))

    ocr_engine = page_context.plugin_manager.hook.get_ocr_engine()
    deskew_angle_degrees = ocr_engine.get_deskew(input_file, page_context.options)

    with Image.open(input_file) as im:
        # According to Pillow docs, .rotate() will automatically use Image.NEAREST
        # resampling if image is mode '1' or 'P'
        deskewed = im.rotate(
            deskew_angle_degrees,
            resample=Image.Resampling.BICUBIC,
            fillcolor=ImageColor.getcolor('white', mode=im.mode),  # type: ignore
        )
        deskewed.save(output_file, dpi=dpi)

    return output_file


def preprocess_clean(input_file: Path, page_context: PageContext) -> Path:
    """Clean the input image using unpaper."""
    output_file = page_context.get_path('pp_clean.png')
    dpi = get_page_square_dpi(page_context, calculate_image_dpi(page_context))
    return unpaper.clean(
        input_file,
        output_file,
        dpi=dpi.to_scalar(),
        unpaper_args=page_context.options.unpaper_args,
    )


def create_ocr_image(image: Path, page_context: PageContext) -> Path:
    """Create the image we send for OCR.

    Might not be the same as the display image depending on preprocessing.
    This image will never be shown to the user.
    """
    output_file = page_context.get_path('ocr.png')
    options = page_context.options
    with Image.open(image) as im:
        log.debug('resolution %r', im.info['dpi'])

        if not options.force_ocr:
            # Do not mask text areas when forcing OCR, because we need to OCR
            # all text areas
            mask = None  # Exclude both visible and invisible text from OCR
            if options.redo_ocr:
                mask = True  # Mask visible text, but not invisible text

            draw = ImageDraw.ImageDraw(im)
            for textarea in page_context.pageinfo.get_textareas(
                visible=mask, corrupt=None
            ):
                # Calculate resolution based on the image size and page dimensions
                # without regard whatever resolution is in pageinfo (may differ or
                # be None)
                bbox = [float(v) for v in textarea]
                xyscale = tuple(float(coord) / 72.0 for coord in im.info['dpi'])
                pixcoords = (
                    bbox[0] * xyscale[0],
                    im.height - bbox[3] * xyscale[1],
                    bbox[2] * xyscale[0],
                    im.height - bbox[1] * xyscale[1],
                )
                log.debug('blanking %r', pixcoords)
                draw.rectangle(pixcoords, fill='white')
                # draw.rectangle(pixcoords, outline='pink')

        filter_im = page_context.plugin_manager.hook.filter_ocr_image(
            page=page_context, image=im
        )
        if filter_im is not None:
            im = filter_im

        # Pillow requires integer DPI
        dpi = tuple(round(coord) for coord in im.info['dpi'])
        im.save(output_file, dpi=dpi)
    return output_file


def ocr_engine_hocr(input_file: Path, page_context: PageContext) -> tuple[Path, Path]:
    """Run the OCR engine and generate hOCR output."""
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
    return hocr_out, hocr_text_out


def should_visible_page_image_use_jpg(pageinfo: PageInfo) -> bool:
    """Determines whether the visible page image should be saved as a JPEG.

    If all images were JPEGs originally, permit a JPEG as output.

    Args:
        pageinfo: The PageInfo object containing information about the page.

    Returns:
        A boolean indicating whether the visible page image should be saved as a JPEG.
    """
    return bool(pageinfo.images) and all(
        im.enc == Encoding.jpeg for im in pageinfo.images
    )


def create_visible_page_jpg(image: Path, page_context: PageContext) -> Path:
    """Create a visible page image in JPEG format.

    This is intended to be used when all images on the page were originally JPEGs.
    """
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
            dpi = get_page_square_dpi(page_context, calculate_image_dpi(page_context))

        # Pillow requires integer DPI
        im.save(output_file, format='JPEG', dpi=dpi.to_int())
    return output_file


def create_pdf_page_from_image(
    image: Path, page_context: PageContext, orientation_correction: int
) -> Path:
    """Create a PDF page from a page image."""
    # We rasterize a square DPI version of each page because most image
    # processing tools don't support rectangular DPI. Use the square DPI as it
    # accurately describes the image. It would be possible to resample the image
    # at this stage back to non-square DPI to more closely resemble the input,
    # except that the hocr renderer does not understand non-square DPI. The
    # sandwich renderer would be fine.
    output_file = page_context.get_path('visible.pdf')

    pageinfo = page_context.pageinfo
    pagesize = 72.0 * float(pageinfo.width_inches), 72.0 * float(pageinfo.height_inches)
    effective_rotation = (pageinfo.rotation - orientation_correction) % 360
    swap_axis = effective_rotation % 180 == 90
    if swap_axis:
        pagesize = pagesize[1], pagesize[0]

    # Create a new single page PDF to hold
    bio = BytesIO()
    with open(image, 'rb') as imfile:
        log.debug('convert')

        layout_fun = img2pdf.get_layout_fun(pagesize)
        img2pdf.convert(
            imfile,
            layout_fun=layout_fun,
            outputstream=bio,
            engine=img2pdf.Engine.pikepdf,
            rotation=img2pdf.Rotation.ifvalid,
        )
        log.debug('convert done')

    # img2pdf does not generate boxes correctly, so we fix them
    bio.seek(0)
    fix_pagepdf_boxes(bio, output_file, page_context, swap_axis=swap_axis)

    output_file = page_context.plugin_manager.hook.filter_pdf_page(
        page=page_context, image_filename=image, output_pdf=output_file
    )
    return output_file


def render_hocr_page(hocr: Path, page_context: PageContext) -> Path:
    """Render the hOCR page to a PDF."""
    options = page_context.options
    output_file = page_context.get_path('ocr_hocr.pdf')
    if hocr.stat().st_size == 0:
        # If hOCR file is empty (skipped page marker), create an empty PDF file
        output_file.touch()
        return output_file

    dpi = get_page_square_dpi(page_context, calculate_image_dpi(page_context))
    debug_kwargs = {}
    if options.pdf_renderer == 'hocrdebug':
        debug_kwargs = dict(
            debug_render_options=DebugRenderOptions(
                render_baseline=True,
                render_triangle=True,
                render_line_bbox=False,
                render_word_bbox=True,
                render_paragraph_bbox=False,
                render_space_bbox=False,
            ),
            font=Courier(),
        )
    HocrTransform(
        hocr_filename=hocr,
        dpi=dpi.to_scalar(),
        **debug_kwargs,  # square
    ).to_pdf(
        out_filename=output_file,
        image_filename=None,
        invisible_text=True if not debug_kwargs else False,
    )
    return output_file


def ocr_engine_textonly_pdf(
    input_image: Path, page_context: PageContext
) -> tuple[Path, Path]:
    """Run the OCR engine and generate a text-only PDF (will look blank)."""
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
    return output_pdf, output_text


def _offset_rect(rect: tuple[float, float, float, float], offset: tuple[float, float]):
    """Offset a rectangle by a given amount."""
    return (
        rect[0] + offset[0],
        rect[1] + offset[1],
        rect[2] + offset[0],
        rect[3] + offset[1],
    )


def fix_pagepdf_boxes(
    infile: Path | BinaryIO,
    out_file: Path,
    page_context: PageContext,
    swap_axis: bool = False,
) -> Path:
    """Fix the bounding boxes in a single page PDF.

    The single page PDF is created with a normal MediaBox with its lower left corner
    at (0, 0). infile is the single page PDF. page_context.mediabox has the original
    file's mediabox, which may have a different origin. We needto adjust the other
    boxes in the single page PDF to match the effect they had on the original page.

    When correcting page rotation, we create a single page PDF that is correctly
    rotated instead of an incorrectly rotated and then setting page.Rotate on it.
    If rotation is either 90 or 270 degrees, then this function can be called
    with swap_axis to swap the X and Y coordinates of all the boxes.

    We are not concerned with solving degenerate cases where the boxes overlap or
    or express invalid rectangles. We merely pass the boxes, producing a
    transformation equivalent to the change made by constructing a new page image.
    """
    with pikepdf.open(infile) as pdf:
        for page in pdf.pages:
            # page.BleedBox = page_context.pageinfo.bleedbox
            # page.ArtBox = page_context.pageinfo.artbox
            mediabox = page_context.pageinfo.mediabox
            offset = mediabox[0], mediabox[1]
            cropbox = _offset_rect(page_context.pageinfo.cropbox, offset)
            trimbox = _offset_rect(page_context.pageinfo.trimbox, offset)

            if swap_axis:
                cropbox = cropbox[1], cropbox[0], cropbox[3], cropbox[2]
                trimbox = trimbox[1], trimbox[0], trimbox[3], trimbox[2]
            page.CropBox = cropbox
            page.TrimBox = trimbox
        pdf.save(out_file)
    return pdf


def generate_postscript_stub(context: PdfContext) -> Path:
    """Generates a PostScript file stub for the given PDF context.

    Args:
        context: The PDF context to generate the PostScript file stub for.

    Returns:
        Path: The path to the generated PostScript file stub.
    """
    output_file = context.get_path('pdfa.ps')
    generate_pdfa_ps(output_file)
    return output_file


def convert_to_pdfa(input_pdf: Path, input_ps_stub: Path, context: PdfContext) -> Path:
    """Converts the given PDF to PDF/A.

    Args:
        input_pdf: The input PDF file path (presumably not PDF/A).
        input_ps_stub: The input PostScript file path, containing instructions
            for the PDF/A generator to use.
        context: The PDF context.
    """
    options = context.options
    input_pdfinfo = context.pdfinfo
    fix_docinfo_file = context.get_path('fix_docinfo.pdf')
    output_file = context.get_path('pdfa.pdf')

    # If the DocumentInfo record contains NUL characters, Ghostscript will
    # produce XMP metadata which contains invalid XML entities (&#0;).
    # NULs in DocumentInfo seem to be common since older Acrobats included them.
    # pikepdf can deal with this, but we make the world a better place by
    # stamping them out as soon as possible.
    with pikepdf.open(input_pdf) as pdf_file:
        if repair_docinfo_nuls(pdf_file):
            pdf_file.save(fix_docinfo_file)
        else:
            safe_symlink(input_pdf, fix_docinfo_file)

    context.plugin_manager.hook.generate_pdfa(
        pdf_version=input_pdfinfo.min_version,
        pdf_pages=[fix_docinfo_file],
        pdfmark=input_ps_stub,
        output_file=output_file,
        context=context,
        pdfa_part=options.output_type[-1],  # is pdfa-1, pdfa-2, or pdfa-3
        progressbar_class=(
            context.plugin_manager.hook.get_progressbar_class()
            if options.progress_bar
            else None
        ),
        stop_on_soft_error=not options.continue_on_soft_render_error,
    )

    return output_file


def should_linearize(working_file: Path, context: PdfContext) -> bool:
    """Determine whether the PDF should be linearized.

    For smaller files, linearization is not worth the effort.
    """
    filesize = os.stat(working_file).st_size
    if filesize > (context.options.fast_web_view * 1_000_000):
        return True
    return False


def get_pdf_save_settings(output_type: str) -> dict[str, Any]:
    """Get pikepdf.Pdf.save settings for the given output type.

    Essentially, don't use features that are incompatible with a given
    PDF/A specification.
    """
    if output_type == 'pdfa-1':
        # Trigger recompression to ensure object streams are removed, because
        # Acrobat complains about them in PDF/A-1b validation.
        return dict(
            preserve_pdfa=True,
            compress_streams=True,
            stream_decode_level=pikepdf.StreamDecodeLevel.generalized,
            object_stream_mode=pikepdf.ObjectStreamMode.disable,
        )
    else:
        return dict(
            preserve_pdfa=True,
            compress_streams=True,
            object_stream_mode=(pikepdf.ObjectStreamMode.generate),
        )


def _file_size_ratio(
    input_file: Path, output_file: Path
) -> tuple[float | None, float | None]:
    """Calculate ratio of input to output file sizes and percentage savings.

    Args:
        input_file (Path): The path to the input file.
        output_file (Path): The path to the output file.

    Returns:
        tuple[float | None, float | None]: A tuple containing the file size
        ratio and the percentage savings achieved by the output file size
        compared to the input file size.
    """
    input_size = input_file.stat().st_size
    output_size = output_file.stat().st_size
    if output_size == 0:
        return None, None
    ratio = input_size / output_size
    savings = 1 - output_size / input_size
    return ratio, savings


def optimize_pdf(
    input_file: Path, context: PdfContext, executor: Executor
) -> tuple[Path, Sequence[str]]:
    """Optimize the given PDF file."""
    output_file = context.get_path('optimize.pdf')
    output_pdf, messages = context.plugin_manager.hook.optimize_pdf(
        input_pdf=input_file,
        output_pdf=output_file,
        context=context,
        executor=executor,
        linearize=should_linearize(input_file, context),
    )

    ratio, savings = _file_size_ratio(input_file, output_file)
    if ratio:
        log.info(f"Image optimization ratio: {ratio:.2f} savings: {(savings):.1%}")
    ratio, savings = _file_size_ratio(context.origin, output_file)
    if ratio:
        log.info(f"Total file size ratio: {ratio:.2f} savings: {(savings):.1%}")
    return output_pdf, messages


def enumerate_compress_ranges(
    iterable: Iterable[T],
) -> Iterator[tuple[tuple[int, int], T | None]]:
    """Enumerate the ranges of non-empty elements in an iterable.

    Compresses consecutive ranges of length 1 into single elements.

    Args:
        iterable: An iterable of elements to enumerate.

    Yields:
        A tuple containing a range of indices and the corresponding element.
        If the element is None, the range represents a skipped range of indices.
    """
    skipped_from, index = None, None
    for index, txt_file in enumerate(iterable):
        index += 1
        if txt_file:
            if skipped_from is not None:
                yield (skipped_from, index - 1), None
                skipped_from = None
            yield (index, index), txt_file
        else:
            if skipped_from is None:
                skipped_from = index
    if skipped_from is not None:
        yield (skipped_from, index), None


def merge_sidecars(txt_files: Iterable[Path | None], context: PdfContext) -> Path:
    """Merge the page sidecar files into a single file.

    Sidecar files are created by the OCR engine and contain the text for each
    page in the PDF. This function merges the sidecar files into a single file
    and returns the path to the merged file.
    """
    output_file = context.get_path('sidecar.txt')
    with open(output_file, 'w', encoding="utf-8") as stream:
        for (from_, to_), txt_file in enumerate_compress_ranges(txt_files):
            if from_ != 1:
                stream.write('\f')  # Form feed between pages for all pages after first
            if txt_file:
                txt = txt_file.read_text(encoding="utf-8")
                # Some versions of Tesseract add a form feed at the end and
                # others don't. Remove it if it exists, since we add one manually.
                stream.write(txt.removesuffix('\f'))
            else:
                if from_ != to_:
                    pages = f'{from_}-{to_}'
                else:
                    pages = f'{from_}'
                stream.write(f'[OCR skipped on page(s) {pages}]')
    return output_file


def copy_final(
    input_file: Path, output_file: str | Path | BinaryIO, original_file: Path | None
) -> None:
    """Copy the final temporary file to the output destination.

    Args:
        input_file (Path): The intermediate input file to copy.
        output_file (str | Path | BinaryIO): The output file to copy to.
        original_file: The original file to copy attributes from.

    Returns:
        None
    """
    log.debug('%s -> %s', input_file, output_file)
    with input_file.open('rb') as input_stream:
        if output_file == '-':
            copyfileobj(input_stream, sys.stdout.buffer)  # type: ignore[misc]
            sys.stdout.flush()
        elif hasattr(output_file, 'writable'):
            output_stream = cast(BinaryIO, output_file)
            copyfileobj(input_stream, output_stream)  # type: ignore[misc]
            with suppress(AttributeError):
                output_stream.flush()
        else:
            # At this point we overwrite the output_file specified by the user
            # use copyfileobj because then we use open() to create the file and
            # get the appropriate umask, ownership, etc.
            with open(output_file, 'w+b') as output_stream:
                copyfileobj(input_stream, output_stream)
