from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
from typing import NamedTuple

import PIL

from ocrmypdf._concurrent import Executor, setup_executor
from ocrmypdf._jobcontext import PageContext, PdfContext
from ocrmypdf._logging import PageNumberFilter
from ocrmypdf._pipeline import (
    convert_to_pdfa,
    create_ocr_image,
    create_pdf_page_from_image,
    create_visible_page_jpg,
    generate_postscript_stub,
    get_orientation_correction,
    metadata_fixup,
    optimize_pdf,
    preprocess_clean,
    preprocess_deskew,
    preprocess_remove_background,
    rasterize,
    rasterize_preview,
    should_visible_page_image_use_jpg,
)
from ocrmypdf._plugin_manager import OcrmypdfPluginManager, get_plugin_manager
from ocrmypdf._validation import (
    report_output_file_size,
)
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.helpers import (
    available_cpu_count,
    check_pdf,
    pikepdf_enable_mmap,
    samefile,
)
from ocrmypdf.pdfa import file_claims_pdfa

log = logging.getLogger(__name__)


def set_logging_tls(tls):
    old_factory = logging.getLogRecordFactory()

    def wrapper(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        if hasattr(tls, 'pageno'):
            record.pageno = tls.pageno
        return record

    logging.setLogRecordFactory(wrapper)


class PageResult(NamedTuple):
    """Result when a page is finished processing."""

    pageno: int
    """Page number, 0-based."""

    pdf_page_from_image: Path | None = None
    """Single page PDF from image."""

    ocr: Path | None = None
    """Single page OCR PDF."""

    text: Path | None = None
    """Single page text file."""

    orientation_correction: int = 0
    """Orientation correction in degrees."""


@dataclass
class HOCRResult:
    """Result when hOCR is finished processing."""

    pageno: int
    """Page number, 0-based."""

    pdf_page_from_image: Path | None = None
    """Single page PDF from image."""

    hocr: Path | None = None
    """Single page hOCR file."""

    textpdf: Path | None = None
    """hOCR file after conversion to PDF."""

    orientation_correction: int = 0
    """Orientation correction in degrees."""

    def __getstate__(self):
        """Return state values to be pickled."""
        return {
            k: (str(v) if k in ('pdf_page_from_image', 'hocr', 'textpdf') else v)
            for k, v in self.__dict__.items()
        }

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.__dict__.update(
            {
                k: (Path(v) if k in ('pdf_page_from_image', 'hocr', 'textpdf') else v)
                for k, v in state.items()
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> HOCRResult:
        """Create an instance from a dict."""
        return cls(**json.loads(json_str))

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.__getstate__())


def configure_debug_logging(
    log_filename: Path, prefix: str = ''
) -> logging.FileHandler:
    """Create a debug log file at a specified location.

    Args:
        log_filename: Where to the put the log file.
        prefix: The logging domain prefix that should be sent to the log.
    """
    log_file_handler = logging.FileHandler(log_filename, delay=True)
    log_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(asctime)s] - %(name)s - %(levelname)7s -%(pageno)s %(message)s'
    )
    log_file_handler.setFormatter(formatter)
    log_file_handler.addFilter(PageNumberFilter())
    logging.getLogger(prefix).addHandler(log_file_handler)
    return log_file_handler


def worker_init(max_pixels: int) -> None:
    """Initialize a worker thread or process."""
    # In Windows, child process will not inherit our change to this value in
    # the parent process, so ensure workers get it set. Not needed when running
    # threaded, but harmless to set again.
    PIL.Image.MAX_IMAGE_PIXELS = max_pixels
    pikepdf_enable_mmap()


def setup_pipeline(
    *,
    options: argparse.Namespace,
    plugin_manager: OcrmypdfPluginManager | None,
    api: bool = False,
    work_folder: Path | None,
) -> tuple[Path, logging.FileHandler | None, Executor, OcrmypdfPluginManager]:
    # Any changes to options will not take effect for options that are already
    # bound to function parameters in the pipeline. (For example
    # options.input_file, options.pdf_renderer are already bound.)
    if not options.jobs:
        options.jobs = available_cpu_count()
    if not plugin_manager:
        plugin_manager = get_plugin_manager(options.plugins)
    if not work_folder:
        work_folder = Path(mkdtemp(prefix="ocrmypdf.io."))
    debug_log_handler = None
    if (
        (options.keep_temporary_files or options.verbose >= 1)
        and not os.environ.get('PYTEST_CURRENT_TEST', '')
        and not api
    ):
        # Debug log for command line interface only with verbose output
        # See https://github.com/pytest-dev/pytest/issues/5502 for why we skip this
        # when pytest is running
        debug_log_handler = configure_debug_logging(
            Path(work_folder) / "debug.log"
        )  # pragma: no cover

    pikepdf_enable_mmap()
    executor = setup_executor(plugin_manager)
    return work_folder, debug_log_handler, executor, plugin_manager


def preprocess(
    page_context: PageContext,
    image: Path,
    remove_background: bool,
    deskew: bool,
    clean: bool,
) -> Path:
    """Preprocess an image."""
    if remove_background:
        image = preprocess_remove_background(image, page_context)
    if deskew:
        image = preprocess_deskew(image, page_context)
    if clean:
        image = preprocess_clean(image, page_context)
    return image


def make_intermediate_images(
    page_context: PageContext, orientation_correction: int
) -> tuple[Path, Path | None]:
    """Create intermediate and preprocessed images for OCR."""
    options = page_context.options

    ocr_image = preprocess_out = None
    rasterize_out = rasterize(
        page_context.origin,
        page_context,
        correction=orientation_correction,
        remove_vectors=False,
    )

    if not any([options.clean, options.clean_final, options.remove_vectors]):
        ocr_image = preprocess_out = preprocess(
            page_context,
            rasterize_out,
            options.remove_background,
            options.deskew,
            clean=False,
        )
    else:
        if not options.lossless_reconstruction:
            preprocess_out = preprocess(
                page_context,
                rasterize_out,
                options.remove_background,
                options.deskew,
                clean=options.clean_final,
            )
        if options.remove_vectors:
            rasterize_ocr_out = rasterize(
                page_context.origin,
                page_context,
                correction=orientation_correction,
                remove_vectors=True,
                output_tag='_ocr',
            )
        else:
            rasterize_ocr_out = rasterize_out

        if (
            preprocess_out
            and rasterize_ocr_out == rasterize_out
            and options.clean == options.clean_final
        ):
            # Optimization: image for OCR is identical to presentation image
            ocr_image = preprocess_out
        else:
            ocr_image = preprocess(
                page_context,
                rasterize_ocr_out,
                options.remove_background,
                options.deskew,
                clean=options.clean,
            )
    return ocr_image, preprocess_out


def process_page(page_context: PageContext) -> tuple[Path, Path | None, int]:
    """Process page to create OCR image, visible page image and orientation."""
    options = page_context.options
    orientation_correction = 0
    if options.rotate_pages:
        # Rasterize
        rasterize_preview_out = rasterize_preview(page_context.origin, page_context)
        orientation_correction = get_orientation_correction(
            rasterize_preview_out, page_context
        )

    ocr_image, preprocess_out = make_intermediate_images(
        page_context, orientation_correction
    )
    ocr_image_out = create_ocr_image(ocr_image, page_context)

    pdf_page_from_image_out = None
    if not options.lossless_reconstruction:
        assert preprocess_out
        visible_image_out = preprocess_out
        if should_visible_page_image_use_jpg(page_context.pageinfo):
            visible_image_out = create_visible_page_jpg(visible_image_out, page_context)
        filtered_image = page_context.plugin_manager.hook.filter_page_image(
            page=page_context, image_filename=visible_image_out
        )
        if filtered_image is not None:  # None if no hook is present
            visible_image_out = filtered_image
        pdf_page_from_image_out = create_pdf_page_from_image(
            visible_image_out, page_context, orientation_correction
        )
    return ocr_image_out, pdf_page_from_image_out, orientation_correction


def post_process(
    pdf_file: Path, context: PdfContext, executor: Executor
) -> tuple[Path, Sequence[str]]:
    """Postprocess the PDF file."""
    pdf_out = pdf_file
    if context.options.output_type.startswith('pdfa'):
        ps_stub_out = generate_postscript_stub(context)
        pdf_out = convert_to_pdfa(pdf_out, ps_stub_out, context)

    pdf_out = metadata_fixup(pdf_out, context)
    return optimize_pdf(pdf_out, context, executor)


def report_output_pdf(options, start_input_file, optimize_messages):
    if options.output_file == '-':
        log.info("Output sent to stdout")
    elif hasattr(options.output_file, 'writable') and options.output_file.writable():
        log.info("Output written to stream")
    elif samefile(options.output_file, Path(os.devnull)):
        pass  # Say nothing when sending to dev null
    else:
        if options.output_type.startswith('pdfa'):
            pdfa_info = file_claims_pdfa(options.output_file)
            if pdfa_info['pass']:
                log.info("Output file is a %s (as expected)", pdfa_info['conformance'])
            else:
                log.warning(
                    "Output file is okay but is not PDF/A (seems to be %s)",
                    pdfa_info['conformance'],
                )
                return ExitCode.pdfa_conversion_failed
        if not check_pdf(options.output_file):
            log.warning('Output file: The generated PDF is INVALID')
            return ExitCode.invalid_output_pdf
        report_output_file_size(
            options, start_input_file, options.output_file, optimize_messages
        )
