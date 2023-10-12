# SPDX-FileCopyrightText: 2019-2022 James R. Barlow
# SPDX-FileCopyrightText: 2019 Martin Wind
# SPDX-License-Identifier: MPL-2.0

"""Implements the concurrent and page synchronous parts of the pipeline."""


from __future__ import annotations

import argparse
import logging
import logging.handlers
import sys
import threading
from collections.abc import Sequence
from concurrent.futures.process import BrokenProcessPool
from concurrent.futures.thread import BrokenThreadPool
from functools import partial
from pathlib import Path
from typing import cast

import PIL

from ocrmypdf._concurrent import Executor
from ocrmypdf._graft import OcrGrafter
from ocrmypdf._jobcontext import PageContext, PdfContext, cleanup_working_files
from ocrmypdf._pipeline import (
    copy_final,
    get_pdfinfo,
    is_ocr_required,
    merge_sidecars,
    ocr_engine_hocr,
    ocr_engine_textonly_pdf,
    render_hocr_page,
    triage,
    validate_pdfinfo_options,
)
from ocrmypdf._pipelines.common import (
    PageResult,
    post_process,
    process_page,
    report_output_pdf,
    setup_pipeline,
    worker_init,
)
from ocrmypdf._plugin_manager import OcrmypdfPluginManager
from ocrmypdf._validation import (
    check_requested_output_file,
    create_input_file,
)
from ocrmypdf.exceptions import ExitCode, ExitCodeException
from ocrmypdf.helpers import (
    NeverRaise,
)

log = logging.getLogger(__name__)


tls = threading.local()
tls.pageno = None


old_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    if hasattr(tls, 'pageno'):
        record.pageno = tls.pageno
    return record


logging.setLogRecordFactory(record_factory)


def _image_to_ocr_text(
    page_context: PageContext, ocr_image_out: Path
) -> tuple[Path, Path]:
    """Run OCR engine on image to create OCR PDF and text file."""
    options = page_context.options
    if options.pdf_renderer.startswith('hocr'):
        hocr_out, text_out = ocr_engine_hocr(ocr_image_out, page_context)
        ocr_out = render_hocr_page(hocr_out, page_context)
    elif options.pdf_renderer == 'sandwich':
        ocr_out, text_out = ocr_engine_textonly_pdf(ocr_image_out, page_context)
    else:
        raise NotImplementedError(f"pdf_renderer {options.pdf_renderer}")
    return ocr_out, text_out


def exec_page_sync(page_context: PageContext) -> PageResult:
    """Execute a pipeline for a single page synchronously."""
    tls.pageno = page_context.pageno + 1

    if not is_ocr_required(page_context):
        return PageResult(pageno=page_context.pageno)

    ocr_image_out, pdf_page_from_image_out, orientation_correction = process_page(
        page_context
    )
    ocr_out, text_out = _image_to_ocr_text(page_context, ocr_image_out)

    return PageResult(
        pageno=page_context.pageno,
        pdf_page_from_image=pdf_page_from_image_out,
        ocr=ocr_out,
        text=text_out,
        orientation_correction=orientation_correction,
    )


def exec_concurrent(context: PdfContext, executor: Executor) -> Sequence[str]:
    """Execute the OCR pipeline concurrently."""
    # Run exec_page_sync on every page
    options = context.options
    max_workers = min(len(context.pdfinfo), options.jobs)
    if max_workers > 1:
        log.info("Start processing %d pages concurrently", max_workers)

    sidecars: list[Path | None] = [None] * len(context.pdfinfo)
    ocrgraft = OcrGrafter(context)

    def update_page(result: PageResult, pbar):
        """After OCR is complete for a page, update the PDF."""
        try:
            tls.pageno = result.pageno + 1
            sidecars[result.pageno] = result.text
            pbar.update()
            ocrgraft.graft_page(
                pageno=result.pageno,
                image=result.pdf_page_from_image,
                textpdf=result.ocr,
                autorotate_correction=result.orientation_correction,
            )
            pbar.update()
        finally:
            tls.pageno = None

    executor(
        use_threads=options.use_threads,
        max_workers=max_workers,
        tqdm_kwargs=dict(
            total=(2 * len(context.pdfinfo)),
            desc='OCR' if options.tesseract_timeout > 0 else 'Image processing',
            unit='page',
            unit_scale=0.5,
            disable=not options.progress_bar,
        ),
        worker_initializer=partial(worker_init, PIL.Image.MAX_IMAGE_PIXELS),
        task=exec_page_sync,
        task_arguments=context.get_page_contexts(),
        task_finished=update_page,
    )

    # Output sidecar text
    if options.sidecar:
        text = merge_sidecars(sidecars, context)
        # Copy text file to destination
        copy_final(text, options.sidecar, context)

    # Merge layers to one single pdf
    pdf = ocrgraft.finalize()

    messages: Sequence[str] = []
    if options.output_type != 'none':
        # PDF/A and metadata
        log.info("Postprocessing...")
        pdf, messages = post_process(pdf, context, executor)

        # Copy PDF file to destination
        copy_final(pdf, options.output_file, context)
    return messages


def run_pipeline(
    options: argparse.Namespace,
    *,
    plugin_manager: OcrmypdfPluginManager | None,
    api: bool = False,
) -> ExitCode:
    """Run the OCR pipeline.

    Args:
        options: The parsed command line options.
        plugin_manager: The plugin manager to use. If not provided, one will be
            created.
        api: If ``True``, the pipeline is being run from the API. This is used
            to manage exceptions in a way appropriate for API or CLI usage.
            For CLI (``api=False``), exceptions are printed and described;
            for API use, they are propagated to the caller.
    """
    work_folder, debug_log_handler, executor, plugin_manager = setup_pipeline(
        options=options, plugin_manager=plugin_manager, api=api, work_folder=None
    )
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
            executor=executor,
            detailed_analysis=options.redo_ocr,
            progbar=options.progress_bar,
            max_workers=options.jobs if not options.use_threads else 1,  # To help debug
            check_pages=options.pages,
        )

        context = PdfContext(options, work_folder, origin_pdf, pdfinfo, plugin_manager)

        # Validate options are okay for this pdf
        validate_pdfinfo_options(context)

        # Execute the pipeline
        optimize_messages = exec_concurrent(context, executor)

        report_output_pdf(options, start_input_file, optimize_messages)

    except KeyboardInterrupt if not api else NeverRaise:
        if options.verbose >= 1:
            log.exception("KeyboardInterrupt")
        else:
            log.error("KeyboardInterrupt")
        return ExitCode.ctrl_c
    except ExitCodeException if not api else NeverRaise as e:
        e = cast(ExitCodeException, e)
        if options.verbose >= 1:
            log.exception("ExitCodeException")
        elif str(e):
            log.error("%s: %s", type(e).__name__, str(e))
        else:
            log.error(type(e).__name__)
        return e.exit_code
    except PIL.Image.DecompressionBombError if not api else NeverRaise:
        log.exception(
            "A decompression bomb error was encountered while executing the "
            "pipeline. Use the argument --max-image-mpixels to raise the maximum "
            "image pixel limit."
        )
        return ExitCode.other_error
    except (
        BrokenProcessPool if not api else NeverRaise,
        BrokenThreadPool if not api else NeverRaise,
    ):
        log.exception(
            "A worker process was terminated unexpectedly. This is known to occur if "
            "processing your file takes all available swap space and RAM. It may "
            "help to try again with a smaller number of jobs, using the --jobs "
            "argument."
        )
        return ExitCode.child_process_error
    except Exception if not api else NeverRaise:  # pylint: disable=broad-except
        log.exception("An exception occurred while executing the pipeline")
        return ExitCode.other_error
    finally:
        if debug_log_handler:
            try:
                debug_log_handler.close()
                log.removeHandler(debug_log_handler)
            except OSError as e:
                print(e, file=sys.stderr)
        cleanup_working_files(work_folder, options)

    return ExitCode.ok
