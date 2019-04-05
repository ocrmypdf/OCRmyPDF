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
import atexit
import concurrent.futures
from tqdm import tqdm
from tempfile import mkdtemp
from ._jobcontext import PDFContext, get_logger, cleanup_working_files
from ._weave import weave_layers
from ._pipeline import (
    get_pdfinfo,
    validate_pdfinfo_options,
    is_ocr_required,
    rasterize_preview,
    get_orientation_correction,
    rasterize,
    preprocess_remove_background,
    preprocess_deskew,
    preprocess_clean,
    create_ocr_image,
    ocr_tesseract_hocr,
    should_visible_page_image_use_jpg,
    create_visible_page_jpg,
    create_pdf_page_from_image,
    render_hocr_page,
    ocr_tesseract_textonly_pdf,
    generate_postscript_stub,
    convert_to_pdfa,
    metadata_fixup,
    merge_sidecars,
    optimize_pdf,
    copy_final,
)
from .exceptions import (
    ExitCode,
    ExitCodeException,
)
from .helpers import available_cpu_count
from ._validation import (
    check_closed_streams,
    preamble,
    check_options,
    check_dependency_versions,
    check_environ,
    check_requested_output_file,
    create_input_file,
    report_output_file_size,
)
from .pdfa import file_claims_pdfa
from .exec import qpdf


def exec_page_sync(page_context):
    options = page_context.options
    orientation_correction = 0
    pdf_page_from_image_out = None
    ocr_out = None
    text_out = None
    if is_ocr_required(page_context):
        if options.rotate_pages:
            # Rasterize
            rasterize_preview_out = rasterize_preview(page_context.pdf_context.origin, page_context)
            orientation_correction = get_orientation_correction(rasterize_preview_out, page_context)

        rasterize_out = rasterize(page_context.pdf_context.origin, page_context, correction=orientation_correction)
        page_context.tick()
        preprocess_out = rasterize_out
        if options.remove_background:
            preprocess_out = preprocess_remove_background(preprocess_out, page_context)

        if options.deskew:
            preprocess_out = preprocess_deskew(preprocess_out, page_context)

        if options.clean:
            preprocess_out = preprocess_clean(preprocess_out, page_context)

        ocr_image_out = create_ocr_image(preprocess_out, page_context)
        page_context.tick()
        pdf_page_from_image_out = None
        if not options.lossless_reconstruction:
            visible_image_out = preprocess_out
            if should_visible_page_image_use_jpg(page_context.pageinfo):
                visible_image_out = create_visible_page_jpg(visible_image_out, page_context)
            pdf_page_from_image_out = create_pdf_page_from_image(visible_image_out, page_context)

        if options.pdf_renderer == 'hocr':
            (hocr_out, text_out) = ocr_tesseract_hocr(ocr_image_out, page_context)
            ocr_out = render_hocr_page(hocr_out, page_context)

        if options.pdf_renderer == 'sandwich':
            (ocr_out, text_out) = ocr_tesseract_textonly_pdf(ocr_image_out, page_context)
        page_context.tick()
    else:
        page_context.tick(3)
    return (page_context.pageno, pdf_page_from_image_out, ocr_out, text_out, orientation_correction)


def post_process(pdf_file, context):
    pdf_out = pdf_file
    if context.options.output_type.startswith('pdfa'):
        ps_stub_out = generate_postscript_stub(context)
        pdf_out = convert_to_pdfa(pdf_out, ps_stub_out, context)

    pdf_out = metadata_fixup(pdf_out, context)
    return optimize_pdf(pdf_out, context)


def exec_sync(context):
    """Execute the pipeline single threaded"""

    # TODO: triage

    # Run exec_page_sync on every page context
    layers = map(exec_page_sync, context.get_page_contexts())

    # Output sidecar text
    if context.options.sidecar:
        sidecars = [layer[3] for layer in layers]
        text = merge_sidecars(sidecars, context)
        # Copy final text file to destination
        copy_final(text, context.options.sidecar, context)

    # Merge layers to one single pdf
    pdf = weave_layers(layers, context)

    # PDF/A and metadata
    pdf = post_process(pdf, context)

    # Copy final PDF file to destination
    copy_final(pdf, context.options.output_file, context)


def exec_concurrent(context):
    """Execute the pipeline concurrent"""

    # TODO: triage
    context.tick()
    # Run exec_page_sync on every page context
    max_workers = min(len(context.pdfinfo), context.options.jobs)
    context.log.info("Start processing %d pages concurrent" % max_workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        layers = executor.map(exec_page_sync, context.get_page_contexts())

    context.tick()
    # Output sidecar text
    if context.options.sidecar:
        sidecars = [layer[3] for layer in layers]
        text = merge_sidecars(sidecars, context)
        # Copy text file to destination
        copy_final(text, context.options.sidecar, context)

    # Merge layers to one single pdf
    pdf = weave_layers(layers, context)
    context.tick()
    # PDF/A and metadata
    pdf = post_process(pdf, context)
    context.tick()
    # Copy PDF file to destination
    copy_final(pdf, context.options.output_file, context)


def run_pipeline(options):
    if not check_closed_streams(options):
        return ExitCode.bad_args

    log = get_logger(options, 'Pipeline')
    preamble(log)
    check_code = check_options(options, log)
    if check_code != ExitCode.ok:
        return check_code
    check_dependency_versions(options, log)

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

    check_environ(options, log)
    if os.environ.get('PYTEST_CURRENT_TEST'):
        os.environ['_OCRMYPDF_TEST_INFILE'] = options.input_file

    work_folder = mkdtemp(prefix="com.github.ocrmypdf.")

    start_input_file = create_input_file(options, log, work_folder)
    check_requested_output_file(options, log)

    atexit.register(cleanup_working_files, work_folder, options)
    if hasattr(os, 'nice'):
        os.nice(5)

    try:
        # Gather pdfinfo and create context
        pdfinfo = get_pdfinfo(start_input_file)
        steps = 5 + len(pdfinfo) * 3
        t = tqdm(total=steps, bar_format='{l_bar}{bar}{n_fmt}/{total_fmt}')

        context = PDFContext(options, work_folder, start_input_file, pdfinfo, tick=lambda n: t.update(n))

        # Validate options are okey for this pdf
        validate_pdfinfo_options(context)

        # Execute the pipeline
        exec_concurrent(context)
        t.update()
        t.close()
    except ExitCodeException as e:
        return e.exit_code
    except Exception as e:
        log.error(str(e))
        return ExitCode.other_error

    if options.output_file == '-':
        log.info("Output sent to stdout")
    elif os.path.samefile(options.output_file, os.devnull):
        pass  # Say nothing when sending to dev null
    else:
        if options.output_type.startswith('pdfa'):
            pdfa_info = file_claims_pdfa(options.output_file)
            if pdfa_info['pass']:
                msg = f"Output file is a {pdfa_info['conformance']} (as expected)"
                log.info(msg)
            else:
                msg = f"Output file is okay but is not PDF/A (seems to be {pdfa_info['conformance']})"
                log.warning(msg)
                return ExitCode.pdfa_conversion_failed
        if not qpdf.check(options.output_file, log):
            log.warning('Output file: The generated PDF is INVALID')
            return ExitCode.invalid_output_pdf

        report_output_file_size(options, log, start_input_file, options.output_file)

    return ExitCode.ok
