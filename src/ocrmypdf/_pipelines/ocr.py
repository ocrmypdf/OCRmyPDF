# SPDX-FileCopyrightText: 2019-2023 James R. Barlow
# SPDX-FileCopyrightText: 2019 Martin Wind
# SPDX-License-Identifier: MPL-2.0

"""Implements the concurrent and page synchronous parts of the pipeline."""

from __future__ import annotations

import argparse
import logging
import logging.handlers
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from tempfile import mkdtemp

import PIL

from ocrmypdf._concurrent import Executor
from ocrmypdf._graft import OcrGrafter
from ocrmypdf._jobcontext import PageContext, PdfContext
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
from ocrmypdf._pipelines._common import (
    PageResult,
    cli_exception_handler,
    manage_debug_log_handler,
    manage_work_folder,
    postprocess,
    process_page,
    report_output_pdf,
    set_thread_pageno,
    setup_pipeline,
    worker_init,
)
from ocrmypdf._plugin_manager import OcrmypdfPluginManager
from ocrmypdf._progressbar import ProgressBar
from ocrmypdf._validation import (
    check_requested_output_file,
    create_input_file,
)
from ocrmypdf.exceptions import ExitCode

log = logging.getLogger(__name__)


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


def _exec_page_sync(page_context: PageContext) -> PageResult:
    """Execute a pipeline for a single page synchronously."""
    set_thread_pageno(page_context.pageno + 1)

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
    options = context.options
    max_workers = min(len(context.pdfinfo), options.jobs)
    if max_workers > 1:
        log.info("Start processing %d pages concurrently", max_workers)

    sidecars: list[Path | None] = [None] * len(context.pdfinfo)
    ocrgraft = OcrGrafter(context)

    def update_page(result: PageResult, pbar: ProgressBar):
        """After OCR is complete for a page, update the PDF."""
        try:
            set_thread_pageno(result.pageno + 1)
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
            set_thread_pageno(None)

    executor(
        use_threads=options.use_threads,
        max_workers=max_workers,
        progress_kwargs=dict(
            total=(2 * len(context.pdfinfo)),
            desc='OCR' if options.tesseract_timeout > 0 else 'Image processing',
            unit='page',
            unit_scale=0.5,
            disable=not options.progress_bar,
        ),
        worker_initializer=partial(worker_init, PIL.Image.MAX_IMAGE_PIXELS),
        task=_exec_page_sync,
        task_arguments=context.get_page_context_args(),
        task_finished=update_page,
    )

    # Output sidecar text
    if options.sidecar:
        text = merge_sidecars(sidecars, context)
        # Copy text file to destination
        copy_final(text, options.sidecar, options.input_file)

    # Merge layers to one single pdf
    pdf = ocrgraft.finalize()

    messages: Sequence[str] = []
    if options.output_type != 'none':
        # PDF/A and metadata
        log.info("Postprocessing...")
        pdf, messages = postprocess(pdf, context, executor)

        # Copy PDF file to destination
        copy_final(pdf, options.output_file, options.input_file)
    return messages


def _run_pipeline(
    options: argparse.Namespace,
    plugin_manager: OcrmypdfPluginManager,
) -> ExitCode:
    with (
        manage_work_folder(
            work_folder=Path(mkdtemp(prefix="ocrmypdf.io.")),
            retain=options.keep_temporary_files,
            print_location=options.keep_temporary_files,
        ) as work_folder,
        manage_debug_log_handler(options=options, work_folder=work_folder),
    ):
        executor = setup_pipeline(options, plugin_manager)
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
            max_workers=options.jobs,
            use_threads=options.use_threads,
            check_pages=options.pages,
        )

        context = PdfContext(options, work_folder, origin_pdf, pdfinfo, plugin_manager)

        # Validate options are okay for this pdf
        validate_pdfinfo_options(context)

        # Execute the pipeline
        optimize_messages = exec_concurrent(context, executor)

        exitcode = report_output_pdf(options, start_input_file, optimize_messages)
        return exitcode


def run_pipeline_cli(
    options: argparse.Namespace,
    *,
    plugin_manager: OcrmypdfPluginManager,
) -> ExitCode:
    """Run the OCR pipeline with command line exception handling.

    Args:
        options: The parsed command line options.
        plugin_manager: The plugin manager to use. If not provided, one will be
            created.
    """
    return cli_exception_handler(_run_pipeline, options, plugin_manager)


def run_pipeline(
    options: argparse.Namespace,
    *,
    plugin_manager: OcrmypdfPluginManager,
) -> ExitCode:
    """Run the OCR pipeline without command line exception handling.

    Args:
        options: The parsed command line options.
        plugin_manager: The plugin manager to use. If not provided, one will be
            created.
    """
    return _run_pipeline(options, plugin_manager)
