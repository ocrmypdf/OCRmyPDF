# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement PDF page rasterization and PDF/A production."""

from __future__ import annotations

import logging
from pathlib import Path

from packaging.version import Version
from pikepdf import Name, Pdf, Stream

from ocrmypdf import hookimpl
from ocrmypdf._exec import ghostscript
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import check_external_program

log = logging.getLogger(__name__)

# Currently all blacklisted versions are lower than 9.55, so none need to
# be added here. If a future version is blacklisted, add it here.
BLACKLISTED_GS_VERSIONS: frozenset[Version] = frozenset()


@hookimpl
def add_options(parser):
    gs = parser.add_argument_group("Ghostscript", "Advanced control of Ghostscript")
    gs.add_argument(
        '--color-conversion-strategy',
        action='store',
        type=str,
        metavar='STRATEGY',
        choices=ghostscript.COLOR_CONVERSION_STRATEGIES,
        default='LeaveColorUnchanged',
        help="Set Ghostscript color conversion strategy",
    )
    gs.add_argument(
        '--pdfa-image-compression',
        choices=['auto', 'jpeg', 'lossless'],
        default='auto',
        help="Specify how to compress images in the output PDF/A. 'auto' lets "
        "OCRmyPDF decide.  'jpeg' changes all grayscale and color images to "
        "JPEG compression.  'lossless' uses PNG-style lossless compression "
        "for all images.  Monochrome images are always compressed using a "
        "lossless codec.  Compression settings "
        "are applied to all pages, including those for which OCR was "
        "skipped.  Not supported for --output-type=pdf ; that setting "
        "preserves the original compression of all images.",
    )


@hookimpl
def check_options(options):
    """Check that the options are valid for this plugin."""
    check_external_program(
        program='gs',
        package='ghostscript',
        version_checker=ghostscript.version,
        need_version='9.54',  # RHEL 9's version; Ubuntu 22.04 has 9.55
    )
    gs_version = ghostscript.version()
    if gs_version in BLACKLISTED_GS_VERSIONS:
        raise MissingDependencyError(
            f"Ghostscript {gs_version} contains serious regressions and is not "
            "supported. Please upgrade to a newer version."
        )
    if Version('10.0.0') <= gs_version < Version('10.02.1') and (
        options.skip_text or options.redo_ocr
    ):
        raise MissingDependencyError(
            f"Ghostscript 10.0.0 through 10.02.0 (your version: {gs_version}) "
            "contain serious regressions that corrupt PDFs with existing text, "
            "such as those processed using --skip-text or --redo-ocr. "
            "Please upgrade to a "
            "newer version, or use --output-type pdf to avoid Ghostscript, or "
            "use --force-ocr to discard existing text."
        )

    if gs_version >= Version('10.6.0') and options.output_type.startswith('pdfa'):
        log.warning(
            "Ghostscript 10.6.x contains JPEG encoding errors that may corrupt "
            "images. OCRmyPDF will attempt to mitigate, but this version is "
            "strongly not recommended. Please upgrade to a newer version. "
            "As of 2025-12, 10.6.0 is the latest version of Ghostscript."
        )
    if options.output_type == 'pdfa':
        options.output_type = 'pdfa-2'
    if options.color_conversion_strategy not in ghostscript.COLOR_CONVERSION_STRATEGIES:
        raise ValueError(
            f"Invalid color conversion strategy: {options.color_conversion_strategy}"
        )
    if options.pdfa_image_compression != 'auto' and not options.output_type.startswith(
        'pdfa'
    ):
        log.warning(
            "--pdfa-image-compression argument only applies when "
            "--output-type is one of 'pdfa', 'pdfa-1', or 'pdfa-2'"
        )


@hookimpl
def rasterize_pdf_page(
    input_file,
    output_file,
    raster_device,
    raster_dpi,
    pageno,
    page_dpi,
    rotation,
    filter_vector,
    stop_on_soft_error,
):
    """Rasterize a single page of a PDF file using Ghostscript."""
    ghostscript.rasterize_pdf(
        input_file,
        output_file,
        raster_device=raster_device,
        raster_dpi=raster_dpi,
        pageno=pageno,
        page_dpi=page_dpi,
        rotation=rotation,
        filter_vector=filter_vector,
        stop_on_error=stop_on_soft_error,
    )
    return output_file


def _collect_dctdecode_images(pdf: Pdf) -> dict[tuple, list[tuple[Stream, bytes]]]:
    """Collect all DCTDecode (JPEG) images from a PDF.

    Returns a dict mapping image signatures to a list of (stream, raw_bytes) tuples.
    The signature is (Width, Height, Filter, BitsPerComponent, ColorSpace).
    """
    images: dict[tuple, list[tuple[Stream, bytes]]] = {}

    def get_colorspace_key(obj):
        """Get a hashable key for the colorspace."""
        cs = obj.get(Name.ColorSpace)
        if cs is None:
            return None
        if isinstance(cs, Name):
            return str(cs)
        # For array colorspaces like [/ICCBased ...], use the first element
        try:
            return str(cs[0]) if len(cs) > 0 else str(cs)
        except (TypeError, KeyError):
            return str(cs)

    def process_xobject_dict(xobjects, depth=0):
        """Process an XObject dictionary for DCTDecode images."""
        if xobjects is None:
            return
        if depth > 10:
            log.warning("Recursion depth exceeded in _collect_dctdecode_images")
            return
        for key in xobjects.keys():
            obj = xobjects[key]
            if obj is None:
                continue
            # Check if it's an image with DCTDecode
            if obj.get(Name.Subtype) == Name.Image:
                filt = obj.get(Name.Filter)
                if filt == Name.DCTDecode:
                    sig = (
                        int(obj.get(Name.Width, 0)),
                        int(obj.get(Name.Height, 0)),
                        str(filt),
                        int(obj.get(Name.BitsPerComponent, 0)),
                        get_colorspace_key(obj),
                    )
                    raw_bytes = obj.read_raw_bytes()
                    if sig not in images:
                        images[sig] = []
                    images[sig].append((obj, raw_bytes))
            # Recurse into Form XObjects
            elif obj.get(Name.Subtype) == Name.Form:
                if Name.Resources in obj:
                    res = obj[Name.Resources]
                    if Name.XObject in res:
                        process_xobject_dict(res[Name.XObject], depth=depth + 1)

    for page in pdf.pages:
        if Name.Resources not in page:
            continue
        resources = page[Name.Resources]
        if Name.XObject not in resources:
            continue
        process_xobject_dict(resources[Name.XObject])

    return images


def _repair_gs106_jpeg_corruption(
    input_pdf_path: Path,
    output_pdf_path: Path,
) -> bool:
    """Repair JPEG corruption caused by Ghostscript 10.6.

    Ghostscript 10.6 has a bug that truncates JPEG data by 1-15 bytes.
    This function detects and repairs such corruption by copying the
    original JPEG bytes from the input PDF.

    Returns True if any repairs were made.
    """
    repaired_count = 0
    first_error_logged = False

    with (
        Pdf.open(input_pdf_path) as input_pdf,
        Pdf.open(output_pdf_path, allow_overwriting_input=True) as output_pdf,
    ):
        # Collect all DCTDecode images from both PDFs
        input_images = _collect_dctdecode_images(input_pdf)
        output_images = _collect_dctdecode_images(output_pdf)

        # For each output image, try to find a corresponding input image
        for sig, output_list in output_images.items():
            if sig not in input_images:
                continue
            input_list = input_images[sig]

            for output_stream, output_bytes in output_list:
                # Try to find a matching input image
                for _input_stream, input_bytes in input_list:
                    input_len = len(input_bytes)
                    output_len = len(output_bytes)

                    # Check if output is 1-15 bytes shorter
                    diff = input_len - output_len
                    if not (1 <= diff <= 15):
                        continue

                    # Check if the bytes are identical up to the truncation point
                    if output_bytes != input_bytes[:output_len]:
                        continue

                    # This is a corrupt image - repair it
                    if not first_error_logged:
                        log.error(
                            "Ghostscript 10.6 JPEG corruption detected. "
                            "Repairing damaged images from original PDF."
                        )
                        first_error_logged = True
                    log.warning(
                        f"Replacing corrupt JPEG image "
                        f"({sig[0]}x{sig[1]}, {diff} bytes truncated)"
                    )

                    # Write the original bytes back to the output stream
                    output_stream.write(
                        input_bytes,
                        filter=Name.DCTDecode,
                    )
                    repaired_count += 1
                    break  # Move to next output image

        if repaired_count > 0:
            output_pdf.save(output_pdf_path)
            log.info(
                f"Repaired {repaired_count} JPEG image(s) corrupted by Ghostscript"
            )

    return repaired_count > 0


@hookimpl
def generate_pdfa(
    pdf_pages,
    pdfmark,
    output_file,
    context,
    pdf_version,
    pdfa_part,
    progressbar_class,
    stop_on_soft_error,
):
    """Generate a PDF/A from the list of PDF pages and PDF/A metadata."""
    ghostscript.generate_pdfa(
        pdf_pages=[pdfmark, *pdf_pages],
        output_file=output_file,
        compression=context.options.pdfa_image_compression,
        color_conversion_strategy=context.options.color_conversion_strategy,
        pdf_version=pdf_version,
        pdfa_part=pdfa_part,
        progressbar_class=progressbar_class,
        stop_on_error=stop_on_soft_error,
    )

    # Repair JPEG corruption caused by Ghostscript 10.6.x
    gs_version = ghostscript.version()
    if gs_version >= Version('10.6.0') and len(pdf_pages) == 1:
        input_pdf = Path(pdf_pages[0])
        _repair_gs106_jpeg_corruption(input_pdf, Path(output_file))

    return output_file
