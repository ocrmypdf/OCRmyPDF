# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement PDF page optimization."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from ocrmypdf import Executor, PdfContext, hookimpl
from ocrmypdf._exec import jbig2enc, pngquant
from ocrmypdf._pipeline import get_pdf_save_settings
from ocrmypdf.cli import numeric
from ocrmypdf.optimize import optimize
from ocrmypdf.subprocess import check_external_program

log = logging.getLogger(__name__)


class OptimizeOptions(BaseModel):
    """Options specific to PDF optimization."""

    level: Annotated[
        int,
        Field(
            ge=0,
            le=3,
            description="Optimization level (0=none, 1=safe, 2=lossy, 3=aggressive)",
        ),
    ] = 1
    jpeg_quality: Annotated[
        int, Field(ge=0, le=100, description="JPEG quality level for optimization")
    ] = 0
    png_quality: Annotated[
        int, Field(ge=0, le=100, description="PNG quality level for optimization")
    ] = 0
    jbig2_threshold: Annotated[
        float,
        Field(ge=0.4, le=0.9, description="JBIG2 symbol classification threshold"),
    ] = 0.85

    @classmethod
    def add_arguments_to_parser(cls, parser, namespace: str = 'optimize'):
        """Add optimization-specific arguments to the argument parser.

        Args:
            parser: The argument parser to add arguments to
            namespace: The namespace prefix for argument names
                (not used for optimize for backward compatibility)
        """
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
        # Deprecated arguments - kept for backward compatibility, emit warnings
        optimizing.add_argument(
            '--jbig2-lossy',
            action='store_true',
            help=argparse.SUPPRESS,  # Deprecated, hidden from help
        )
        optimizing.add_argument(
            '--jbig2-page-group-size',
            type=numeric(int, 1, 10000),
            default=0,
            metavar='N',
            help=argparse.SUPPRESS,  # Deprecated, hidden from help
        )
        optimizing.add_argument(
            '--jbig2-threshold',
            type=numeric(float, 0.4, 0.9),
            default=0.85,
            metavar='T',
            help=(
                "Adjust JBIG2 symbol code classification threshold "
                "(default 0.85), range 0.4 to 0.9."
            ),
        )

    @model_validator(mode='after')
    def validate_optimization_consistency(self):
        """Validate optimization options are consistent."""
        if self.level == 0 and any([self.png_quality > 0, self.jpeg_quality > 0]):
            log.warning(
                "The arguments --png-quality and --jpeg-quality "
                "will be ignored because --optimize=0."
            )
        return self

    def validate_with_context(
        self, external_programs_available: dict[str, bool]
    ) -> None:
        """Validate options that require external context.

        Args:
            external_programs_available: Dict of program name -> availability
        """
        if self.level >= 2:
            if not external_programs_available.get('pngquant', False):
                log.warning(
                    "pngquant is not available, so PNG optimization will be limited"
                )
            if not external_programs_available.get('jbig2enc', False):
                log.warning(
                    "jbig2enc is not available, so JBIG2 optimization will be limited"
                )


@hookimpl
def register_options():
    """Register optimization option model."""
    return {'optimize': OptimizeOptions}


@hookimpl
def add_options(parser):
    # Use the model's CLI generation method
    OptimizeOptions.add_arguments_to_parser(parser)


@hookimpl
def check_options(options):
    """Check external dependencies for optimization."""
    # Warn about deprecated options
    if getattr(options, 'jbig2_lossy', False):
        log.warning(
            "The --jbig2-lossy option is deprecated and will be ignored. "
            "Lossy JBIG2 compression has been removed due to risks of "
            "character substitution errors."
        )
    if getattr(options, 'jbig2_page_group_size', 0) not in (0, None):
        log.warning(
            "The --jbig2-page-group-size option is deprecated and will be ignored."
        )

    if options.optimize >= 2:
        check_external_program(
            program='pngquant',
            package='pngquant',
            version_checker=pngquant.version,
            need_version='2.12.2',
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
            required_for='--optimize {2,3}',
            recommended=True,
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
