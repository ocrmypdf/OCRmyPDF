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
import logging.handlers
import os
import sys
import threading
from functools import partial
from pathlib import Path
from tempfile import mkdtemp
from typing import List, NamedTuple, Optional, Tuple

import pikepdf
import PIL

from ocrmypdf._concurrent import exec_progress_pool
from ocrmypdf._graft import OcrGrafter
from ocrmypdf._jobcontext import PageContext, PdfContext, cleanup_working_files
from ocrmypdf._logging import PageNumberFilter
from ocrmypdf._pipeline import (
    convert_to_pdfa,
    copy_final,
    create_ocr_image,
    create_pdf_page_from_image,
    create_visible_page_jpg,
    generate_postscript_stub,
    get_orientation_correction,
    get_pdfinfo,
    is_ocr_required,
    merge_sidecars,
    metadata_fixup,
    ocr_engine_hocr,
    ocr_engine_textonly_pdf,
    optimize_pdf,
    preprocess_clean,
    preprocess_deskew,
    preprocess_remove_background,
    rasterize,
    rasterize_preview,
    render_hocr_page,
    should_visible_page_image_use_jpg,
    triage,
    validate_pdfinfo_options,
)
from ocrmypdf._plugin_manager import get_plugin_manager
from ocrmypdf._validation import (
    check_requested_output_file,
    create_input_file,
    report_output_file_size,
)
from ocrmypdf.exceptions import ExitCode, ExitCodeException
from ocrmypdf.helpers import (
    available_cpu_count,
    check_pdf,
    pikepdf_enable_mmap,
    samefile,
)
from ocrmypdf.pdfa import file_claims_pdfa

log = logging.getLogger(__name__)


class PageResult(NamedTuple):
    pageno: int
    pdf_page_from_image: Optional[Path]
    ocr: Optional[Path]
    text: Optional[Path]
    orientation_correction: int


tls = threading.local()
tls.pageno = None


old_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    if hasattr(tls, 'pageno'):
        record.pageno = tls.pageno
    return record


logging.setLogRecordFactory(record_factory)


def preprocess(
    page_context: PageContext,
    image: Path,
    remove_background: bool,
    deskew: bool,
    clean: bool,
) -> Path:
    if remove_background:
        image = preprocess_remove_background(image, page_context)
    if deskew:
        image = preprocess_deskew(image, page_context)
    if clean:
        image = preprocess_clean(image, page_context)
    return image


def make_intermediate_images(
    page_context: PageContext, orientation_correction: int
) -> Tuple[Path, Optional[Path]]:
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


def exec_page_sync(page_context: PageContext):
    options = page_context.options
    tls.pageno = page_context.pageno + 1

    if not is_ocr_required(page_context):
        return PageResult(
            pageno=page_context.pageno,
            pdf_page_from_image=None,
            ocr=None,
            text=None,
            orientation_correction=0,
        )

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
        if filtered_image:
            visible_image_out = filtered_image
        pdf_page_from_image_out = create_pdf_page_from_image(
            visible_image_out, page_context
        )

    if options.pdf_renderer == 'hocr':
        (hocr_out, text_out) = ocr_engine_hocr(ocr_image_out, page_context)
        ocr_out = render_hocr_page(hocr_out, page_context)

    if options.pdf_renderer == 'sandwich':
        (ocr_out, text_out) = ocr_engine_textonly_pdf(ocr_image_out, page_context)

    return PageResult(
        pageno=page_context.pageno,
        pdf_page_from_image=pdf_page_from_image_out,
        ocr=ocr_out,
        text=text_out,
        orientation_correction=orientation_correction,
    )


def post_process(pdf_file, context: PdfContext):
    pdf_out = pdf_file
    if context.options.output_type.startswith('pdfa'):
        ps_stub_out = generate_postscript_stub(context)
        pdf_out = convert_to_pdfa(pdf_out, ps_stub_out, context)

    pdf_out = metadata_fixup(pdf_out, context)
    return optimize_pdf(pdf_out, context)


def worker_init(max_pixels: int):
    # In Windows, child process will not inherit our change to this value in
    # the parent process, so ensure workers get it set. Not needed when running
    # threaded, but harmless to set again.
    PIL.Image.MAX_IMAGE_PIXELS = max_pixels
    pikepdf_enable_mmap()


def exec_concurrent(context: PdfContext):
    """Execute the pipeline concurrently"""

    # Run exec_page_sync on every page context
    max_workers = min(len(context.pdfinfo), context.options.jobs)
    if max_workers > 1:
        log.info("Start processing %d pages concurrently", max_workers)

    sidecars: List[Optional[Path]] = [None] * len(context.pdfinfo)
    ocrgraft = OcrGrafter(context)

    def update_page(result: PageResult, pbar):
        sidecars[result.pageno] = result.text
        pbar.update()
        ocrgraft.graft_page(
            pageno=result.pageno,
            image=result.pdf_page_from_image,
            textpdf=result.ocr,
            autorotate_correction=result.orientation_correction,
        )
        pbar.update()

    exec_progress_pool(
        use_threads=context.options.use_threads,
        max_workers=max_workers,
        tqdm_kwargs=dict(
            total=(2 * len(context.pdfinfo)),
            desc='OCR',
            unit='page',
            unit_scale=0.5,
            disable=not context.options.progress_bar,
        ),
        task_initializer=partial(worker_init, PIL.Image.MAX_IMAGE_PIXELS),
        task=exec_page_sync,
        task_arguments=context.get_page_contexts(),
        task_finished=update_page,
    )

    # Output sidecar text
    if context.options.sidecar:
        text = merge_sidecars(sidecars, context)
        # Copy text file to destination
        copy_final(text, context.options.sidecar, context)

    # Merge layers to one single pdf
    pdf = ocrgraft.finalize()

    # PDF/A and metadata
    pdf = post_process(pdf, context)

    # Copy PDF file to destination
    copy_final(pdf, context.options.output_file, context)


class NeverRaise(Exception):
    """An exception that is never raised"""

    pass  # pylint: disable=unnecessary-pass


def configure_debug_logging(log_filename, prefix=''):
    log_file_handler = logging.FileHandler(log_filename, delay=True)
    log_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(asctime)s] - %(name)s - %(levelname)7s -%(pageno)s %(message)s'
    )
    log_file_handler.setFormatter(formatter)
    log_file_handler.addFilter(PageNumberFilter())
    logging.getLogger(prefix).addHandler(log_file_handler)
    return log_file_handler


def run_pipeline(options, *, plugin_manager, api=False):
    # Any changes to options will not take effect for options that are already
    # bound to function parameters in the pipeline. (For example
    # options.input_file, options.pdf_renderer are already bound.)
    if not options.jobs:
        options.jobs = available_cpu_count()
    if not plugin_manager:
        plugin_manager = get_plugin_manager(options.plugins)

    work_folder = Path(mkdtemp(prefix="com.github.ocrmypdf."))
    debug_log_handler = None
    if (options.keep_temporary_files or options.verbose >= 1) and not os.environ.get(
        'PYTEST_CURRENT_TEST', ''
    ):
        debug_log_handler = configure_debug_logging(Path(work_folder) / "debug.log")

    pikepdf_enable_mmap()

    try:
        check_requested_output_file(options)
        start_input_file, original_filename = create_input_file(options, work_folder)

        # Triage image or pdf
        origin_pdf = triage(
            original_filename, start_input_file, work_folder / 'origin.pdf', options
        )

        # Gather pdfinfo and create context
        pdfinfo = get_pdfinfo(
            origin_pdf,
            detailed_analysis=options.redo_ocr,
            progbar=options.progress_bar,
            max_workers=options.jobs if not options.use_threads else 1,  # To help debug
            check_pages=options.pages,
        )

        context = PdfContext(options, work_folder, origin_pdf, pdfinfo, plugin_manager)

        # Validate options are okay for this pdf
        validate_pdfinfo_options(context)

        # Execute the pipeline
        exec_concurrent(context)

        if options.output_file == '-':
            log.info("Output sent to stdout")
        elif (
            hasattr(options.output_file, 'writable') and options.output_file.writable()
        ):
            log.info("Output written to stream")
        elif samefile(options.output_file, os.devnull):
            pass  # Say nothing when sending to dev null
        else:
            if options.output_type.startswith('pdfa'):
                pdfa_info = file_claims_pdfa(options.output_file)
                if pdfa_info['pass']:
                    log.info(
                        "Output file is a %s (as expected)", pdfa_info['conformance']
                    )
                else:
                    log.warning(
                        "Output file is okay but is not PDF/A (seems to be %s)",
                        pdfa_info['conformance'],
                    )
                    return ExitCode.pdfa_conversion_failed
            if not check_pdf(options.output_file):
                log.warning('Output file: The generated PDF is INVALID')
                return ExitCode.invalid_output_pdf
            report_output_file_size(options, start_input_file, options.output_file)

    except (KeyboardInterrupt if not api else NeverRaise) as e:
        if options.verbose >= 1:
            log.exception("KeyboardInterrupt")
        else:
            log.error("KeyboardInterrupt")
        return ExitCode.ctrl_c
    except (ExitCodeException if not api else NeverRaise) as e:
        if str(e):
            log.error("%s: %s", type(e).__name__, str(e))
        else:
            log.error(type(e).__name__)
        return e.exit_code
    except (Exception if not api else NeverRaise) as e:  # pylint: disable=broad-except
        log.exception("An exception occurred while executing the pipeline")
        return ExitCode.other_error
    finally:
        if debug_log_handler:
            try:
                debug_log_handler.close()
                log.removeHandler(debug_log_handler)
            except EnvironmentError as e:
                print(e, file=sys.stderr)
        cleanup_working_files(work_folder, options)

    return ExitCode.ok
