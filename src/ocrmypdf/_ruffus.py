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

import os
import re
import sys
import atexit
from tempfile import mkdtemp
from ruffus import (
    Pipeline,
    formatter,
    regex,
    suffix,
    cmdline,
    proxy_logger,
    ruffus_exceptions
)
from .exec import qpdf
from ._jobcontext import JobContext, JobContextManager, cleanup_working_files
from ._weave import weave_layers
from ._pipeline import (
    triage,
    repair_and_parse_pdf,
    marker_pages,
    ocr_or_skip,
    rasterize_preview,
    orient_page,
    rasterize_with_ghostscript,
    preprocess_remove_background,
    preprocess_deskew,
    preprocess_clean,
    select_ocr_image,
    ocr_tesseract_hocr,
    select_visible_page_image,
    select_image_layer,
    render_hocr_page,
    ocr_tesseract_textonly_pdf,
    generate_postscript_stub,
    convert_to_pdfa,
    metadata_fixup,
    merge_sidecars,
    optimize_pdf,
    copy_final
)
from . import exceptions as ocrmypdf_exceptions
from .exceptions import (
    ExitCode,
    ExitCodeException,
)
from .helpers import available_cpu_count
from .pdfa import file_claims_pdfa
from ._validation import (
    check_closed_streams,
    preamble,
    check_options,
    check_dependency_versions,
    check_environ,
    check_input_file,
    check_requested_output_file,
    report_output_file_size,
    log_page_orientations,
    logging_factory,
)


def cleanup_ruffus_error_message(msg):
    msg = re.sub(r'\s+', r' ', msg)
    msg = re.sub(r"\((.+?)\)", r'\1', msg)
    msg = msg.strip()
    return msg


def do_ruffus_exception(ruffus_five_tuple, options, log):
    """Replace the elaborate ruffus stack trace with a user friendly
    description of the error message that occurred."""
    exit_code = None

    _task_name, _job_name, exc_name, exc_value, exc_stack = ruffus_five_tuple

    if isinstance(exc_name, type):
        # ruffus is full of mystery... sometimes (probably when the process
        # group leader is killed) exc_name is the class object of the exception,
        # rather than a str. So reach into the object and get its name.
        exc_name = exc_name.__name__

    if exc_name.startswith('ocrmypdf.exceptions.'):
        base_exc_name = exc_name.replace('ocrmypdf.exceptions.', '')
        exc_class = getattr(ocrmypdf_exceptions, base_exc_name)
        exit_code = getattr(exc_class, 'exit_code', ExitCode.other_error)
        try:
            if isinstance(exc_value, exc_class):
                exc_msg = str(exc_value)
            elif isinstance(exc_value, str):
                exc_msg = exc_value
            else:
                exc_msg = str(exc_class())
        except Exception:
            exc_msg = "Unknown"

    if exc_name in ('builtins.SystemExit', 'SystemExit'):
        match = re.search(r"\.(.+?)\)", exc_value)
        exit_code_name = match.groups()[0]
        exit_code = getattr(ExitCode, exit_code_name, 'other_error')
    elif exc_name == 'ruffus.ruffus_exceptions.MissingInputFileError':
        log.error(cleanup_ruffus_error_message(exc_value))
        exit_code = ExitCode.input_file
    elif exc_name in ('builtins.KeyboardInterrupt', 'KeyboardInterrupt'):
        # We have to print in this case because the log daemon might be toast
        print("Interrupted by user", file=sys.stderr)
        exit_code = ExitCode.ctrl_c
    elif exc_name == 'subprocess.CalledProcessError':
        # It's up to the subprocess handler to report something useful
        msg = "Error occurred while running this command:"
        log.error(msg + '\n' + exc_value)
        exit_code = ExitCode.child_process_error
    elif exc_name.startswith('ocrmypdf.exceptions.'):
        if exc_msg:
            log.error(exc_msg)
    elif exc_name == 'PIL.Image.DecompressionBombError':
        msg = cleanup_ruffus_error_message(exc_value)
        msg += (
            "\nUse the --max-image-mpixels argument to set increase the "
            "maximum number of megapixels to accept."
        )
        log.error(msg)
        exit_code = ExitCode.input_file

    if exit_code is not None:
        return exit_code

    if not options.verbose:
        log.error(exc_stack)
    return ExitCode.other_error


def traverse_ruffus_exception(exceptions, options, log):
    """Traverse a RethrownJobError and output the exceptions

    Ruffus presents exceptions as 5 element tuples. The RethrownJobException
    has a list of exceptions like
        e.job_exceptions = [(5-tuple), (5-tuple), ...]

    ruffus < 2.7.0 had a bug with exception marshalling that would give
    different output whether the main or child process raised the exception.
    We no longer support this.

    Attempting to log the exception itself will re-marshall it to the logger
    which is normally running in another process. It's better to avoid re-
    marshalling.

    The exit code will be based on this, even if multiple exceptions occurred
    at the same time."""

    exit_codes = []
    for exc in exceptions:
        exit_code = do_ruffus_exception(exc, options, log)
        exit_codes.append(exit_code)

    return exit_codes[0]  # Multiple codes are rare so take the first one


def build_pipeline(options, work_folder, log, context):
    main_pipeline = Pipeline.pipelines['main']

    # Triage
    task_triage = main_pipeline.transform(
        task_func=triage,
        input=os.path.join(work_folder, 'origin'),
        filter=formatter('(?i)'),
        output=os.path.join(work_folder, 'origin.pdf'),
        extras=[log, context],
    )

    task_repair_and_parse_pdf = main_pipeline.transform(
        task_func=repair_and_parse_pdf,
        input=task_triage,
        filter=suffix('.pdf'),
        output='.repaired.pdf',
        output_dir=work_folder,
        extras=[log, context],
    )

    # Split (kwargs for split seems to be broken, so pass plain args)
    task_marker_pages = main_pipeline.split(
        marker_pages,
        task_repair_and_parse_pdf,
        os.path.join(work_folder, '*.marker.pdf'),
        extras=[log, context],
    )

    task_ocr_or_skip = main_pipeline.split(
        ocr_or_skip,
        task_marker_pages,
        [
            os.path.join(work_folder, '*.ocr.page.pdf'),
            os.path.join(work_folder, '*.skip.page.pdf'),
        ],
        extras=[log, context],
    )

    # Rasterize preview
    task_rasterize_preview = main_pipeline.transform(
        task_func=rasterize_preview,
        input=task_ocr_or_skip,
        filter=suffix('.page.pdf'),
        output='.preview.jpg',
        output_dir=work_folder,
        extras=[log, context],
    )
    task_rasterize_preview.active_if(options.rotate_pages)

    # Orient
    task_orient_page = main_pipeline.collate(
        task_func=orient_page,
        input=[task_ocr_or_skip, task_rasterize_preview],
        filter=regex(r".*/(\d{6})(\.ocr|\.skip)(?:\.page\.pdf|\.preview\.jpg)"),
        output=os.path.join(work_folder, r'\1\2.oriented.pdf'),
        extras=[log, context],
    )

    # Rasterize actual
    task_rasterize_with_ghostscript = main_pipeline.transform(
        task_func=rasterize_with_ghostscript,
        input=task_orient_page,
        filter=suffix('.ocr.oriented.pdf'),
        output='.page.png',
        output_dir=work_folder,
        extras=[log, context],
    )

    # Preprocessing subpipeline
    task_preprocess_remove_background = main_pipeline.transform(
        task_func=preprocess_remove_background,
        input=task_rasterize_with_ghostscript,
        filter=suffix(".page.png"),
        output=".pp-background.png",
        extras=[log, context],
    )

    task_preprocess_deskew = main_pipeline.transform(
        task_func=preprocess_deskew,
        input=task_preprocess_remove_background,
        filter=suffix(".pp-background.png"),
        output=".pp-deskew.png",
        extras=[log, context],
    )

    task_preprocess_clean = main_pipeline.transform(
        task_func=preprocess_clean,
        input=task_preprocess_deskew,
        filter=suffix(".pp-deskew.png"),
        output=".pp-clean.png",
        extras=[log, context],
    )

    task_select_ocr_image = main_pipeline.collate(
        task_func=select_ocr_image,
        input=[task_preprocess_clean],
        filter=regex(r".*/(\d{6})(?:\.page|\.pp-.*)\.png"),
        output=os.path.join(work_folder, r"\1.ocr.png"),
        extras=[log, context],
    )

    # HOCR OCR
    task_ocr_tesseract_hocr = main_pipeline.transform(
        task_func=ocr_tesseract_hocr,
        input=task_select_ocr_image,
        filter=suffix(".ocr.png"),
        output=[".hocr", ".txt"],
        extras=[log, context],
    )
    task_ocr_tesseract_hocr.graphviz(fillcolor='"#00cc66"')
    task_ocr_tesseract_hocr.active_if(options.pdf_renderer == 'hocr')

    task_select_visible_page_image = main_pipeline.collate(
        task_func=select_visible_page_image,
        input=[
            task_rasterize_with_ghostscript,
            task_preprocess_remove_background,
            task_preprocess_deskew,
            task_preprocess_clean,
        ],
        filter=regex(r".*/(\d{6})(?:\.page|\.pp-.*)\.png"),
        output=os.path.join(work_folder, r'\1.image'),
        extras=[log, context],
    )
    task_select_visible_page_image.graphviz(shape='diamond')

    task_select_image_layer = main_pipeline.collate(
        task_func=select_image_layer,
        input=[task_select_visible_page_image, task_orient_page],
        filter=regex(r".*/(\d{6})(?:\.image|\.ocr\.oriented\.pdf)"),
        output=os.path.join(work_folder, r'\1.image-layer.pdf'),
        extras=[log, context],
    )
    task_select_image_layer.graphviz(fillcolor='"#00cc66"', shape='diamond')

    task_render_hocr_page = main_pipeline.transform(
        task_func=render_hocr_page,
        input=task_ocr_tesseract_hocr,
        filter=regex(r".*/(\d{6})(?:\.hocr)"),
        output=os.path.join(work_folder, r'\1.text.pdf'),
        extras=[log, context],
    )
    task_render_hocr_page.graphviz(fillcolor='"#00cc66"')
    task_render_hocr_page.active_if(options.pdf_renderer == 'hocr')

    # Tesseract OCR + text only PDF
    task_ocr_tesseract_textonly_pdf = main_pipeline.collate(
        task_func=ocr_tesseract_textonly_pdf,
        input=[task_select_ocr_image],
        filter=regex(r".*/(\d{6})(?:\.ocr.png)"),
        output=[
            os.path.join(work_folder, r'\1.text.pdf'),
            os.path.join(work_folder, r'\1.text.txt'),
        ],
        extras=[log, context],
    )
    task_ocr_tesseract_textonly_pdf.graphviz(fillcolor='"#ff69b4"')
    task_ocr_tesseract_textonly_pdf.active_if(options.pdf_renderer == 'sandwich')

    task_weave_layers = main_pipeline.collate(
        task_func=weave_layers,
        input=[
            task_repair_and_parse_pdf,
            task_render_hocr_page,
            task_ocr_tesseract_textonly_pdf,
            task_select_image_layer,
        ],
        filter=regex(
            r".*/((?:\d{6}(?:\.text\.pdf|\.image-layer\.pdf))|(?:origin\.repaired\.pdf))"
        ),
        output=os.path.join(work_folder, r'layers.rendered.pdf'),
        extras=[log, context],
    )
    task_weave_layers.graphviz(fillcolor='"#00cc66"')

    # PDF/A pdfmark
    task_generate_postscript_stub = main_pipeline.transform(
        task_func=generate_postscript_stub,
        input=task_repair_and_parse_pdf,
        filter=formatter(r'\.repaired\.pdf'),
        output=os.path.join(work_folder, 'pdfa.ps'),
        extras=[log, context],
    )
    task_generate_postscript_stub.active_if(options.output_type.startswith('pdfa'))

    # PDF/A conversion
    task_convert_to_pdfa = main_pipeline.merge(
        task_func=convert_to_pdfa,
        input=[task_generate_postscript_stub, task_weave_layers],
        output=os.path.join(work_folder, 'pdfa.pdf'),
        extras=[log, context],
    )
    task_convert_to_pdfa.active_if(options.output_type.startswith('pdfa'))

    task_metadata_fixup = main_pipeline.merge(
        task_func=metadata_fixup,
        input=[task_repair_and_parse_pdf, task_weave_layers, task_convert_to_pdfa],
        output=os.path.join(work_folder, 'metafix.pdf'),
        extras=[log, context],
    )

    task_merge_sidecars = main_pipeline.merge(
        task_func=merge_sidecars,
        input=[task_ocr_tesseract_hocr, task_ocr_tesseract_textonly_pdf],
        output=options.sidecar,
        extras=[log, context],
    )
    task_merge_sidecars.active_if(options.sidecar)

    # Optimize
    task_optimize_pdf = main_pipeline.transform(
        task_func=optimize_pdf,
        input=task_metadata_fixup,
        filter=suffix('.pdf'),
        output='.optimized.pdf',
        output_dir=work_folder,
        extras=[log, context],
    )

    # Finalize
    main_pipeline.merge(
        task_func=copy_final,
        input=[task_optimize_pdf],
        output=options.output_file,
        extras=[log, context],
    )


def run_pipeline(options):
    options.verbose_abbreviated_path = 1
    if os.environ.get('_OCRMYPDF_THREADS'):
        options.use_threads = True

    if not check_closed_streams(options):
        return ExitCode.bad_args

    logger_args = {'verbose': options.verbose, 'quiet': options.quiet}

    _log, _log_mutex = proxy_logger.make_shared_logger_and_proxy(
        logging_factory, __name__, logger_args
    )
    preamble(_log)
    check_code = check_options(options, _log)
    if check_code != ExitCode.ok:
        return check_code
    check_dependency_versions(options, _log)

    # Any changes to options will not take effect for options that are already
    # bound to function parameters in the pipeline. (For example
    # options.input_file, options.pdf_renderer are already bound.)
    if not options.jobs:
        options.jobs = available_cpu_count()

    # Performance is improved by setting Tesseract to single threaded. In tests
    # this gives better throughput than letting a smaller number of Tesseract
    # jobs run multithreaded. Same story for pngquant. Tess <4 ignores this
    # variable, but harmless to set if ignored.
    os.environ.setdefault('OMP_THREAD_LIMIT', '1')

    check_environ(options, _log)
    if os.environ.get('PYTEST_CURRENT_TEST'):
        os.environ['_OCRMYPDF_TEST_INFILE'] = options.input_file

    try:
        work_folder = mkdtemp(prefix="com.github.ocrmypdf.")
        options.history_file = os.path.join(work_folder, 'ruffus_history.sqlite')
        start_input_file = os.path.join(work_folder, 'origin')

        check_input_file(options, _log, start_input_file)
        check_requested_output_file(options, _log)

        manager = JobContextManager()
        manager.register('JobContext', JobContext)  # pylint: disable=no-member
        manager.start()

        context = manager.JobContext()  # pylint: disable=no-member
        context.set_options(options)
        context.set_work_folder(work_folder)

        build_pipeline(options, work_folder, _log, context)
        atexit.register(cleanup_working_files, work_folder, options)
        if hasattr(os, 'nice'):
            os.nice(5)
        cmdline.run(options)
    except ruffus_exceptions.RethrownJobError as e:
        if options.verbose:
            _log.debug(str(e))  # stringify exception so logger doesn't have to
        exceptions = e.job_exceptions
        exitcode = traverse_ruffus_exception(exceptions, options, _log)
        if exitcode is None:
            _log.error("Unexpected ruffus exception: " + str(e))
            _log.error(repr(e))
            return ExitCode.other_error
        return exitcode
    except ExitCodeException as e:
        return e.exit_code
    except Exception as e:
        _log.error(str(e))
        return ExitCode.other_error

    if options.flowchart:
        _log.info(f"Flowchart saved to {options.flowchart}")
        return ExitCode.ok
    elif options.output_file == '-':
        _log.info("Output sent to stdout")
    elif os.path.samefile(options.output_file, os.devnull):
        pass  # Say nothing when sending to dev null
    else:
        if options.output_type.startswith('pdfa'):
            pdfa_info = file_claims_pdfa(options.output_file)
            if pdfa_info['pass']:
                msg = f"Output file is a {pdfa_info['conformance']} (as expected)"
                _log.info(msg)
            else:
                msg = f"Output file is okay but is not PDF/A (seems to be {pdfa_info['conformance']})"
                _log.warning(msg)
                return ExitCode.pdfa_conversion_failed
        if not qpdf.check(options.output_file, _log):
            _log.warning('Output file: The generated PDF is INVALID')
            return ExitCode.invalid_output_pdf

        report_output_file_size(options, _log, start_input_file, options.output_file)

    pdfinfo = context.get_pdfinfo()
    if options.verbose:
        from pprint import pformat

        _log.debug(pformat(pdfinfo))

    log_page_orientations(pdfinfo, _log)

    return ExitCode.ok
