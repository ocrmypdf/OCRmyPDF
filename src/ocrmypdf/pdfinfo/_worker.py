# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""PDF page info worker process handling."""

from __future__ import annotations

import atexit
import logging
from collections.abc import Container, Sequence
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from pikepdf import Pdf

from ocrmypdf._concurrent import Executor
from ocrmypdf._progressbar import ProgressBar
from ocrmypdf.exceptions import InputFileError
from ocrmypdf.helpers import available_cpu_count, pikepdf_enable_mmap

if TYPE_CHECKING:
    from ocrmypdf.pdfinfo.info import PageInfo
    from ocrmypdf.pdfinfo.layout import PdfMinerState

logger = logging.getLogger()

worker_pdf = None  # pylint: disable=invalid-name


def _pdf_pageinfo_sync_init(pdf: Pdf, infile: Path, pdfminer_loglevel):
    global worker_pdf  # pylint: disable=global-statement,invalid-name
    pikepdf_enable_mmap()

    logging.getLogger('pdfminer').setLevel(pdfminer_loglevel)

    # If the pdf is not opened, open a copy for our worker process to use
    if pdf is None:
        worker_pdf = Pdf.open(infile)

        def on_process_close():
            worker_pdf.close()

        # Close when this process exits
        atexit.register(on_process_close)


@contextmanager
def _pdf_pageinfo_sync_pdf(thread_pdf: Pdf | None, infile: Path):
    if thread_pdf is not None:
        yield thread_pdf
    elif worker_pdf is not None:
        yield worker_pdf
    else:
        with Pdf.open(infile) as pdf:
            yield pdf


def _pdf_pageinfo_sync(
    pageno: int,
    thread_pdf: Pdf | None,
    infile: Path,
    check_pages: Container[int],
    detailed_analysis: bool,
    miner_state: PdfMinerState | None,
) -> PageInfo:
    # Import here to avoid circular import - info.py imports this module,
    # but PageInfo is defined in info.py
    from ocrmypdf.pdfinfo.info import PageInfo

    with _pdf_pageinfo_sync_pdf(thread_pdf, infile) as pdf:
        return PageInfo(
            pdf, pageno, infile, check_pages, detailed_analysis, miner_state
        )


def _pdf_pageinfo_concurrent(
    pdf,
    executor: Executor,
    max_workers: int,
    use_threads: bool,
    infile,
    progbar,
    check_pages,
    detailed_analysis: bool = False,
    miner_state: PdfMinerState | None = None,
) -> Sequence[PageInfo | None]:
    pages: list[PageInfo | None] = [None] * len(pdf.pages)

    def update_pageinfo(page: PageInfo, pbar: ProgressBar):
        if not page:
            raise InputFileError("Could read a page in the PDF")
        pages[page.pageno] = page
        pbar.update()

    if max_workers is None:
        max_workers = available_cpu_count()

    total = len(pdf.pages)

    n_workers = min(1 + len(pages) // 4, max_workers)
    if n_workers == 1:
        # If we decided on only one worker, there is no point in using
        # a separate process.
        use_threads = True

    if use_threads and n_workers > 1:
        # If we are using threads, there is no point in using more than one
        # worker thread - they will just fight over the GIL.
        n_workers = 1

    # If we use a thread, we can pass the already-open Pdf for them to use
    # If we use processes, we pass a None which tells the init function to open its
    # own
    initial_pdf = pdf if use_threads else None

    contexts = (
        (n, initial_pdf, infile, check_pages, detailed_analysis, miner_state)
        for n in range(total)
    )
    assert n_workers == 1 if use_threads else n_workers >= 1, "Not multithreadable"
    logger.debug(
        f"Gathering info with {n_workers} "
        + ('thread' if use_threads else 'process')
        + " workers"
    )
    executor(
        use_threads=use_threads,
        max_workers=n_workers,
        progress_kwargs=dict(
            total=total, desc="Scanning contents", unit='page', disable=not progbar
        ),
        worker_initializer=partial(
            _pdf_pageinfo_sync_init,
            initial_pdf,
            infile,
            logging.getLogger('pdfminer').level,
        ),
        task=_pdf_pageinfo_sync,
        task_arguments=contexts,
        task_finished=update_pageinfo,
    )
    return pages
