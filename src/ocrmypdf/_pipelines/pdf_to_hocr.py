# SPDX-FileCopyrightText: 2019-2023 James R. Barlow
# SPDX-FileCopyrightText: 2019 Martin Wind
# SPDX-License-Identifier: MPL-2.0

"""Implements the concurrent and page synchronous parts of the pipeline."""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import shutil
from functools import partial

import PIL

from ocrmypdf._concurrent import Executor
from ocrmypdf._jobcontext import PageContext, PdfContext
from ocrmypdf._pipeline import (
    get_pdfinfo,
    is_ocr_required,
    ocr_engine_hocr,
    validate_pdfinfo_options,
)
from ocrmypdf._pipelines._common import (
    HOCRResult,
    manage_work_folder,
    process_page,
    set_thread_pageno,
    setup_pipeline,
    worker_init,
)
from ocrmypdf._plugin_manager import OcrmypdfPluginManager
from ocrmypdf._validation import (
    set_lossless_reconstruction,
)

log = logging.getLogger(__name__)


def _exec_page_hocr_sync(page_context: PageContext) -> HOCRResult:
    """Execute a pipeline for a single page hOCR."""
    set_thread_pageno(page_context.pageno + 1)

    if not is_ocr_required(page_context):
        return HOCRResult(pageno=page_context.pageno)

    ocr_image_out, pdf_page_from_image_out, orientation_correction = process_page(
        page_context
    )
    hocr_out, _ = ocr_engine_hocr(ocr_image_out, page_context)

    result = HOCRResult(
        pageno=page_context.pageno,
        pdf_page_from_image=pdf_page_from_image_out,
        hocr=hocr_out,
        orientation_correction=orientation_correction,
    )
    page_context.get_path('hocr.json').write_text(result.to_json())
    return result


def exec_pdf_to_hocr(context: PdfContext, executor: Executor) -> None:
    """Execute the OCR pipeline concurrently and output hOCR."""
    # Run exec_page_sync on every page
    options = context.options
    max_workers = min(len(context.pdfinfo), options.jobs)
    if max_workers > 1:
        log.info("Start processing %d pages concurrently", max_workers)

    executor(
        use_threads=options.use_threads,
        max_workers=max_workers,
        progress_kwargs=dict(
            total=(2 * len(context.pdfinfo)),
            desc='hOCR',
            unit='page',
            unit_scale=0.5,
            disable=not options.progress_bar,
        ),
        worker_initializer=partial(worker_init, PIL.Image.MAX_IMAGE_PIXELS),
        task=_exec_page_hocr_sync,
        task_arguments=context.get_page_context_args(),
    )


def run_hocr_pipeline(
    options: argparse.Namespace,
    *,
    plugin_manager: OcrmypdfPluginManager,
) -> None:
    """Run pipeline to output hOCR."""
    with manage_work_folder(
        work_folder=options.output_folder, retain=True, print_location=False
    ) as work_folder:
        executor = setup_pipeline(options, plugin_manager)
        shutil.copy2(options.input_file, work_folder / 'origin.pdf')

        # Gather pdfinfo and create context
        pdfinfo = get_pdfinfo(
            options.input_file,
            executor=executor,
            detailed_analysis=options.redo_ocr,
            progbar=options.progress_bar,
            max_workers=options.jobs,
            use_threads=options.use_threads,
            check_pages=options.pages,
        )
        context = PdfContext(
            options, work_folder, options.input_file, pdfinfo, plugin_manager
        )
        # Validate options are okay for this pdf
        set_lossless_reconstruction(options)
        validate_pdfinfo_options(context)
        exec_pdf_to_hocr(context, executor)
