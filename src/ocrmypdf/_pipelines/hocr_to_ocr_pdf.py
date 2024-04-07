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

import PIL

from ocrmypdf._concurrent import Executor
from ocrmypdf._graft import OcrGrafter
from ocrmypdf._jobcontext import PageContext, PdfContext
from ocrmypdf._pipeline import (
    copy_final,
    get_pdfinfo,
    render_hocr_page,
)
from ocrmypdf._pipelines._common import (
    HOCRResult,
    manage_work_folder,
    postprocess,
    report_output_pdf,
    set_thread_pageno,
    setup_pipeline,
    worker_init,
)
from ocrmypdf._plugin_manager import OcrmypdfPluginManager
from ocrmypdf._progressbar import ProgressBar
from ocrmypdf.exceptions import ExitCode

log = logging.getLogger(__name__)


def _exec_hocrtransform_sync(page_context: PageContext) -> HOCRResult:
    """Process each page."""
    hocr_json = page_context.get_path('hocr.json')
    if not hocr_json.exists():
        # No hOCR file, so no OCR was performed on this page.
        return HOCRResult(pageno=page_context.pageno)
    hocr_result = HOCRResult.from_json(hocr_json.read_text())
    hocr_result.textpdf = render_hocr_page(
        page_context.get_path('ocr_hocr.hocr'), page_context
    )
    return hocr_result


def exec_hocr_to_ocr_pdf(context: PdfContext, executor: Executor) -> Sequence[str]:
    """Convert hOCR files to OCR PDF."""
    # Run exec_page_sync on every page
    options = context.options
    max_workers = min(len(context.pdfinfo), options.jobs)
    if max_workers > 1:
        log.info("Continue processing %d pages concurrently", max_workers)

    ocrgraft = OcrGrafter(context)

    def graft_page(result: HOCRResult, pbar: ProgressBar):
        """Graft text only PDF on to main PDF's page."""
        try:
            set_thread_pageno(result.pageno + 1)
            pbar.update()
            ocrgraft.graft_page(
                pageno=result.pageno,
                image=result.pdf_page_from_image,
                textpdf=result.textpdf,
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
            desc='Grafting hOCR to PDF',
            unit='page',
            unit_scale=0.5,
            disable=not options.progress_bar,
        ),
        worker_initializer=partial(worker_init, PIL.Image.MAX_IMAGE_PIXELS),
        task=_exec_hocrtransform_sync,
        task_arguments=context.get_page_context_args(),
        task_finished=graft_page,
    )

    pdf = ocrgraft.finalize()
    messages: Sequence[str] = []
    if options.output_type != 'none':
        # PDF/A and metadata
        log.info("Postprocessing...")
        pdf, messages = postprocess(pdf, context, executor)

        # Copy PDF file to destination (we don't know the input PDF file name)
        copy_final(pdf, options.output_file, None)
    return messages


def run_hocr_to_ocr_pdf_pipeline(
    options: argparse.Namespace,
    *,
    plugin_manager: OcrmypdfPluginManager,
) -> ExitCode:
    """Run pipeline to convert hOCR to final output PDF."""
    with manage_work_folder(
        work_folder=options.work_folder, retain=True, print_location=False
    ) as work_folder:
        executor = setup_pipeline(options, plugin_manager)
        origin_pdf = work_folder / 'origin.pdf'

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
        plugin_manager.hook.check_options(options=options)
        optimize_messages = exec_hocr_to_ocr_pdf(context, executor)

        return report_output_pdf(options, origin_pdf, optimize_messages)
