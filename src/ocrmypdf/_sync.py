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
# import re
# import sys
import atexit
from tempfile import mkdtemp
from ._jobcontext import cleanup_working_files
from ._weave import weave_layers
from ._pipeline_simple import (
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
)


class Logger:
    def __init__(self, prefix):
        self.prefix = prefix

    def debug(self, *argv):
        print(self.prefix, *argv)

    def info(self, *argv):
        print(self.prefix, *argv)

    def warn(self, *argv):
        print(self.prefix, *argv)

    def error(self, *argv):
        print(self.prefix, *argv)


class PageContext:
    def __init__(self, pdf_context, pageno):
        self.pdf_context = pdf_context
        self.options = pdf_context.options
        self.pageno = pageno
        self.pageinfo = pdf_context.pdfinfo[pageno]
        self.log = Logger('%s Page %d: ' % (os.path.basename(pdf_context.origin), pageno + 1))

    def get_path(self, name):
        return os.path.join(self.pdf_context.work_folder, "page_%d_%s" % (self.pageno, name))


class PDFContext:
    def __init__(self, options, work_folder, origin, pdfinfo):
        self.options = options
        self.work_folder = work_folder
        self.origin = origin
        self.pdfinfo = pdfinfo
        self.log = Logger('%s: ' % os.path.basename(origin))

    def get_path(self, name):
        return os.path.join(self.work_folder, name)

    def get_page_contexts(self):
        npages = len(self.pdfinfo)
        for n in range(npages):
            yield PageContext(self, n)


def _exec_pipeline(options, work_folder, origin):
    # Gather info of pdf
    pdfinfo = get_pdfinfo(origin)
    context = PDFContext(options, work_folder, origin, pdfinfo)

    # Validate options are okey for this pdf
    validate_pdfinfo_options(context)

    # For every page in the pdf
    layers = []
    for page_context in context.get_page_contexts():
        # Check if OCR is required
        ocr_required = is_ocr_required(page_context)
        if not ocr_required:
            continue

        orientation_correction = 0
        if options.rotate_pages:
            # Rasterize
            rasterize_preview_out = rasterize_preview(origin, page_context)
            orientation_correction = get_orientation_correction(rasterize_preview_out, page_context)

        rasterize_out = rasterize(origin, page_context, correction=orientation_correction)

        preprocess_out = rasterize_out
        if options.remove_background:
            preprocess_out = preprocess_remove_background(preprocess_out, page_context)

        if options.deskew:
            preprocess_out = preprocess_deskew(preprocess_out, page_context)

        if options.clean:
            preprocess_out = preprocess_clean(preprocess_out, page_context)

        ocr_image_out = create_ocr_image(preprocess_out, page_context)

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

        layers.append((page_context.pageno, pdf_page_from_image_out, ocr_out, text_out, orientation_correction))

    weave_layers_out = weave_layers(layers, context)

    pdf_out = weave_layers_out
    if options.output_type.startswith('pdfa'):
        ps_stub_out = generate_postscript_stub(context)
        pdf_out = convert_to_pdfa(pdf_out, ps_stub_out, context)

    pdf_out = metadata_fixup(pdf_out, context)

    if options.sidecar:
        sidecars = [layer[3] for layer in layers]
        sidecar_out = merge_sidecars(sidecars, context)
        copy_final(sidecar_out, context.options.sidecar, context)

    pdf_out = optimize_pdf(pdf_out, context)
    copy_final(pdf_out, context.options.output_file, context)


def run_pipeline(options):
    if not check_closed_streams(options):
        return ExitCode.bad_args

    log = Logger('Pipeline')
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

    _exec_pipeline(options, work_folder, start_input_file)

    return ExitCode.ok


"""
    try:
        # build_pipeline(options, work_folder, log, context)
        atexit.register(cleanup_working_files, work_folder, options)
        if hasattr(os, 'nice'):
            os.nice(5)
    except Exception as e:
        log.error(str(e))
        return ExitCode.other_error

    if options.flowchart:
        log.info(f"Flowchart saved to {options.flowchart}")
        return ExitCode.ok
    elif options.output_file == '-':
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

    # pdfinfo = context.get_pdfinfo()
    # if options.verbose:
    #    from pprint import pformat
    #    log.debug(pformat(pdfinfo))

    # log_page_orientations(pdfinfo, log)

    return ExitCode.ok
"""
