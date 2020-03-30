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
import multiprocessing
import os
import signal
import sys
import threading
from collections import namedtuple
from pathlib import Path
from tempfile import mkdtemp

import PIL
from tqdm import tqdm

from ._graft import OcrGrafter
from ._jobcontext import PDFContext, cleanup_working_files, make_logger
from ._pipeline import (
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
    ocr_tesseract_hocr,
    ocr_tesseract_textonly_pdf,
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
from ._validation import (
    check_requested_output_file,
    create_input_file,
    report_output_file_size,
)
from .exceptions import ExitCode, ExitCodeException
from .exec import qpdf
from .helpers import available_cpu_count
from .pdfa import file_claims_pdfa

PageResult = namedtuple(
    'PageResult', 'pageno, pdf_page_from_image, ocr, text, orientation_correction'
)


def preprocess(page_context, image, remove_background, deskew, clean):
    if remove_background:
        image = preprocess_remove_background(image, page_context)
    if deskew:
        image = preprocess_deskew(image, page_context)
    if clean:
        image = preprocess_clean(image, page_context)
    return image


def exec_page_sync(page_context):
    options = page_context.options
    orientation_correction = 0
    pdf_page_from_image_out = None
    ocr_out = None
    text_out = None
    if is_ocr_required(page_context):
        if options.rotate_pages:
            # Rasterize
            rasterize_preview_out = rasterize_preview(page_context.origin, page_context)
            orientation_correction = get_orientation_correction(
                rasterize_preview_out, page_context
            )

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
            ocr_image = preprocess(
                page_context,
                rasterize_ocr_out,
                options.remove_background,
                options.deskew,
                clean=options.clean,
            )

        ocr_image_out = create_ocr_image(ocr_image, page_context)

        pdf_page_from_image_out = None
        if not options.lossless_reconstruction:
            visible_image_out = preprocess_out
            if should_visible_page_image_use_jpg(page_context.pageinfo):
                visible_image_out = create_visible_page_jpg(
                    visible_image_out, page_context
                )
            pdf_page_from_image_out = create_pdf_page_from_image(
                visible_image_out, page_context
            )

        if options.pdf_renderer == 'hocr':
            (hocr_out, text_out) = ocr_tesseract_hocr(ocr_image_out, page_context)
            ocr_out = render_hocr_page(hocr_out, page_context)

        if options.pdf_renderer == 'sandwich':
            (ocr_out, text_out) = ocr_tesseract_textonly_pdf(
                ocr_image_out, page_context
            )

    return PageResult(
        pageno=page_context.pageno,
        pdf_page_from_image=pdf_page_from_image_out,
        ocr=ocr_out,
        text=text_out,
        orientation_correction=orientation_correction,
    )


def post_process(pdf_file, context):
    pdf_out = pdf_file
    if context.options.output_type.startswith('pdfa'):
        ps_stub_out = generate_postscript_stub(context)
        pdf_out = convert_to_pdfa(pdf_out, ps_stub_out, context)

    pdf_out = metadata_fixup(pdf_out, context)
    return optimize_pdf(pdf_out, context)


def worker_init(queue, max_pixels):
    """Initialize a process pool worker"""

    # Ignore SIGINT (our parent process will kill us gracefully)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Reconfigure the root logger for this process to send all messages to a queue
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(h)

    # In Windows, child process will not inherit our change to this value in
    # the parent process, so ensure workers get it set
    PIL.Image.MAX_IMAGE_PIXELS = max_pixels


def worker_thread_init(_queue, max_pixels):
    # This is probably not needed since threads should all see the same memory,
    # but done for consistency.
    PIL.Image.MAX_IMAGE_PIXELS = max_pixels


def log_listener(queue):
    """Listen to the worker processes and forward the messages to logging

    For simplicity this is a thread rather than a process. Only one process
    should actually write to sys.stderr or whatever we're using, so if this is
    made into a process the main application needs to be directed to it.

    See https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
    """

    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import traceback

            print("Logging problem", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def exec_concurrent(context):
    """Execute the pipeline concurrently"""

    # Run exec_page_sync on every page context
    max_workers = min(len(context.pdfinfo), context.options.jobs)
    if max_workers > 1:
        context.log.info("Start processing %d pages concurrently", max_workers)

    # Tesseract 4.x can be multithreaded, and we also run multiple workers. We want
    # to manage how many threads it uses to avoid creating total threads than cores.
    # Performance testing shows we're better off
    # parallelizing ocrmypdf and forcing Tesseract to be single threaded, which we
    # get by setting the envvar OMP_THREAD_LIMIT to 1. But if the page count of the
    # input file is small, then we allow Tesseract to use threads, subject to the
    # constraint: (ocrmypdf workers) * (tesseract threads) <= max_workers.
    # As of Tesseract 4.1, 3 threads is the most effective on a 4 core/8 thread system.
    tess_threads = min(3, context.options.jobs // max_workers)
    if context.options.tesseract_env is None:
        context.options.tesseract_env = os.environ.copy()
    context.options.tesseract_env.setdefault('OMP_THREAD_LIMIT', str(tess_threads))
    try:
        tess_threads = int(context.options.tesseract_env['OMP_THREAD_LIMIT'])
    except ValueError:  # OMP_THREAD_LIMIT initialized to non-numeric
        context.log.error("Environment variable OMP_THREAD_LIMIT is not numeric")
    if tess_threads > 1:
        context.log.info("Using Tesseract OpenMP thread limit %d", tess_threads)

    if context.options.use_threads:
        from multiprocessing.dummy import Pool

        initializer = worker_thread_init
    else:
        Pool = multiprocessing.Pool
        initializer = worker_init

    sidecars = [None] * len(context.pdfinfo)
    ocrgraft = OcrGrafter(context)

    log_queue = multiprocessing.Queue(-1)
    listener = threading.Thread(target=log_listener, args=(log_queue,))
    listener.start()
    with tqdm(
        total=(2 * len(context.pdfinfo)),
        desc='OCR',
        unit='page',
        unit_scale=0.5,
        disable=not context.options.progress_bar,
    ) as pbar:
        pool = Pool(
            processes=max_workers,
            initializer=initializer,
            initargs=(log_queue, PIL.Image.MAX_IMAGE_PIXELS),
        )
        try:
            results = pool.imap_unordered(exec_page_sync, context.get_page_contexts())
            while True:
                try:
                    page_result = results.next()
                    sidecars[page_result.pageno] = page_result.text
                    pbar.update()
                    ocrgraft.graft_page(page_result)
                    pbar.update()
                except StopIteration:
                    break
        except KeyboardInterrupt:
            # Terminate pool so we exit instantly
            pool.terminate()
            # Don't try listener.join() here, will deadlock
            raise
        except Exception:
            if not os.environ.get("PYTEST_CURRENT_TEST", ""):
                # Unless inside pytest, exit immediately because no one wants
                # to wait for child processes to finalize results that will be
                # thrown away. Inside pytest, we want child processes to exit
                # cleanly so that they output an error messages or coverage data
                # we need from them.
                pool.terminate()
            raise
        finally:
            # Terminate log listener
            log_queue.put_nowait(None)
            pool.close()
            pool.join()

    listener.join()

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


def samefile(f1, f2):
    if os.name == 'nt':
        return f1 == f2
    else:
        return os.path.samefile(f1, f2)


def configure_debug_logging(log_filename, prefix=''):
    log_file_handler = logging.FileHandler(log_filename, delay=True)
    log_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(asctime)s] - %(name)s - %(levelname)7s - %(message)s'
    )
    log_file_handler.setFormatter(formatter)
    logging.getLogger(prefix).addHandler(log_file_handler)
    return log_file_handler


def run_pipeline(options, api=False):
    log = make_logger(options, __name__)

    # Any changes to options will not take effect for options that are already
    # bound to function parameters in the pipeline. (For example
    # options.input_file, options.pdf_renderer are already bound.)
    if not options.jobs:
        options.jobs = available_cpu_count()

    work_folder = mkdtemp(prefix="com.github.ocrmypdf.")
    debug_log_handler = None
    if (options.keep_temporary_files or options.verbose >= 1) and not os.environ.get(
        'PYTEST_CURRENT_TEST', ''
    ):
        debug_log_handler = configure_debug_logging(Path(work_folder) / "debug.log")

    try:
        check_requested_output_file(options)
        start_input_file, original_filename = create_input_file(options, work_folder)

        # Triage image or pdf
        origin_pdf = triage(
            original_filename,
            start_input_file,
            os.path.join(work_folder, 'origin.pdf'),
            options,
            log,
        )

        # Gather pdfinfo and create context
        pdfinfo = get_pdfinfo(
            origin_pdf,
            detailed_page_analysis=options.redo_ocr,
            progbar=options.progress_bar,
        )

        context = PDFContext(options, work_folder, origin_pdf, pdfinfo)

        # Validate options are okay for this pdf
        validate_pdfinfo_options(context)

        # Execute the pipeline
        exec_concurrent(context)

        if options.output_file == '-':
            log.info("Output sent to stdout")
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
            if not qpdf.check(options.output_file, log):
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
    except (Exception if not api else NeverRaise) as e:
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
