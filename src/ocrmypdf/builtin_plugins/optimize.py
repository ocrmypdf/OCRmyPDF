# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement PDF page optimization."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from ocrmypdf import Executor, PdfContext, hookimpl
from ocrmypdf._exec import jbig2enc, pngquant
from ocrmypdf._pipeline import get_pdf_save_settings
from ocrmypdf.cli import numeric
from ocrmypdf.optimize import optimize
from ocrmypdf.subprocess import check_external_program

log = logging.getLogger(__name__)


@hookimpl
def add_options(parser):
    optimizing = parser.add_argument_group(
        "Optimization options", "Control how the PDF is optimized after OCR"
    )
    optimizing.add_argument(
        '-O',
        '--optimize',
        type=int,
        choices=range(0, 4),
        default=1,
        help=(
            "Control how PDF is optimized after processing:"
            "0 - do not optimize; "
            "1 - do safe, lossless optimizations (default); "
            "2 - do lossy JPEG and JPEG2000 optimizations; "
            "3 - do more aggressive lossy JPEG and JPEG2000 optimizations. "
            "To enable lossy JBIG2, see --jbig2-lossy."
        ),
    )
    optimizing.add_argument(
        '--jpeg-quality',
        type=numeric(int, 0, 100),
        default=0,
        metavar='Q',
        help=(
            "Adjust JPEG quality level for JPEG optimization. "
            "100 is best quality and largest output size; "
            "1 is lowest quality and smallest output; "
            "0 uses the default."
        ),
    )
    optimizing.add_argument(
        '--jpg-quality',
        type=numeric(int, 0, 100),
        default=0,
        metavar='Q',
        dest='jpeg_quality',
        help=argparse.SUPPRESS,  # Alias for --jpeg-quality
    )
    optimizing.add_argument(
        '--png-quality',
        type=numeric(int, 0, 100),
        default=0,
        metavar='Q',
        help=(
            "Adjust PNG quality level to use when quantizing PNGs. "
            "Values have same meaning as with --jpeg-quality"
        ),
    )
    optimizing.add_argument(
        '--jbig2-lossy',
        action='store_true',
        help=(
            "Enable JBIG2 lossy mode (better compression, not suitable for some "
            "use cases - see documentation). Only takes effect if --optimize 1 or "
            "higher is also enabled."
        ),
    )
    optimizing.add_argument(
        '--jbig2-page-group-size',
        type=numeric(int, 1, 10000),
        default=0,
        metavar='N',
        # Adjust number of pages to consider at once for JBIG2 compression
        help=argparse.SUPPRESS,
    )


@hookimpl
def check_options(options):
    if options.optimize >= 2:
        check_external_program(
            program='pngquant',
            package='pngquant',
            version_checker=pngquant.version,
            need_version='2.0.1',
            required_for='--optimize {2,3}',
        )

    if options.optimize >= 2:
        # Although we use JBIG2 for optimize=1, don't nag about it unless the
        # user is asking for more optimization
        check_external_program(
            program='jbig2',
            package='jbig2enc',
            version_checker=jbig2enc.version,
            need_version='0.28',
            required_for='--optimize {2,3} | --jbig2-lossy',
            recommended=True if not options.jbig2_lossy else False,
        )

    if options.optimize == 0 and any(
        [options.jbig2_lossy, options.png_quality, options.jpeg_quality]
    ):
        log.warning(
            "The arguments --jbig2-lossy, --png-quality, and --jpeg-quality "
            "will be ignored because --optimize=0."
        )


@hookimpl
def optimize_pdf(
    input_pdf: Path,
    output_pdf: Path,
    context: PdfContext,
    executor: Executor,
    linearize: bool,
) -> tuple[Path, Sequence[str]]:
    save_settings = dict(
        linearize=linearize,
        **get_pdf_save_settings(context.options.output_type),
    )
    result_path = optimize(input_pdf, output_pdf, context, save_settings, executor)
    messages = []
    if context.options.optimize == 0:
        messages.append("Optimization was disabled.")
    else:
        image_optimizers = {
            'jbig2': jbig2enc.available(),
            'pngquant': pngquant.available(),
        }
        for name, available in image_optimizers.items():
            if not available:
                messages.append(
                    f"The optional dependency '{name}' was not found, so some image "
                    f"optimizations could not be attempted."
                )
    return result_path, messages


@hookimpl
def is_optimization_enabled(context: PdfContext) -> bool:
    return context.options.optimize != 0
