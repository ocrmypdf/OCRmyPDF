# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement OCR using Tesseract."""

from __future__ import annotations

import argparse
import logging
import os
from typing import Annotated

from PIL import Image
from pydantic import BaseModel, Field

from ocrmypdf import hookimpl
from ocrmypdf._exec import tesseract
from ocrmypdf._jobcontext import PageContext
from ocrmypdf.cli import numeric, str_to_int
from ocrmypdf.exceptions import BadArgsError, MissingDependencyError
from ocrmypdf.helpers import available_cpu_count, clamp
from ocrmypdf.imageops import calculate_downsample, downsample_image
from ocrmypdf.pluginspec import OcrEngine
from ocrmypdf.subprocess import check_external_program

log = logging.getLogger(__name__)


class TesseractOptions(BaseModel):
    """Options specific to Tesseract OCR engine."""

    config: Annotated[
        list[str], Field(description="Additional Tesseract configuration files")
    ] = []
    pagesegmode: Annotated[
        int | None,
        Field(ge=0, le=13, description="Set Tesseract page segmentation mode"),
    ] = None
    oem: Annotated[
        int | None, Field(ge=0, le=3, description="Set Tesseract OCR engine mode")
    ] = None
    thresholding: Annotated[
        int | None, Field(description="Set Tesseract input image thresholding mode")
    ] = None
    timeout: Annotated[
        float, Field(ge=0, description="Timeout for OCR operations in seconds")
    ] = 180.0
    non_ocr_timeout: Annotated[
        float, Field(ge=0, description="Timeout for non-OCR operations in seconds")
    ] = 180.0
    downsample_large_images: Annotated[
        bool, Field(description="Downsample large images before OCR")
    ] = True
    downsample_above: Annotated[
        int,
        Field(
            ge=100,
            le=32767,
            description="Downsample images larger than this pixel size",
        ),
    ] = 32767
    user_words: Annotated[
        str | None, Field(description="Path to Tesseract user words file")
    ] = None
    user_patterns: Annotated[
        str | None, Field(description="Path to Tesseract user patterns file")
    ] = None

    @classmethod
    def add_arguments_to_parser(cls, parser, namespace: str = 'tesseract'):
        """Add Tesseract-specific arguments to the argument parser.

        Args:
            parser: The argument parser to add arguments to
            namespace: The namespace prefix for argument names
        """
        tess = parser.add_argument_group(
            "Tesseract", "Advanced control of Tesseract OCR"
        )

        tess.add_argument(
            f'--{namespace}-config',
            action='append',
            metavar='CFG',
            default=[],
            dest=f'{namespace}_config',
            help="Additional Tesseract configuration files -- see documentation.",
        )

        tess.add_argument(
            f'--{namespace}-pagesegmode',
            action='store',
            type=int,
            metavar='PSM',
            choices=range(0, 14),
            dest=f'{namespace}_pagesegmode',
            help="Set Tesseract page segmentation mode (see tesseract --help).",
        )

        tess.add_argument(
            f'--{namespace}-oem',
            action='store',
            type=int,
            metavar='MODE',
            choices=range(0, 4),
            dest=f'{namespace}_oem',
            help=(
                "Set Tesseract 4+ OCR engine mode: "
                "0 - original Tesseract only; "
                "1 - neural nets LSTM only; "
                "2 - Tesseract + LSTM; "
                "3 - default."
            ),
        )

        tess.add_argument(
            f'--{namespace}-thresholding',
            action='store',
            type=str_to_int(tesseract.TESSERACT_THRESHOLDING_METHODS),
            default='auto',
            metavar='METHOD',
            dest=f'{namespace}_thresholding',
            help=(
                "Set Tesseract 5.0+ input image thresholding mode. This may improve OCR "
                "results on low quality images or those that contain high contrast color. "
                "legacy-otsu is the Tesseract default; adaptive-otsu is an improved Otsu "
                "algorithm with improved sort for background color changes; sauvola is "
                "based on local standard deviation."
            ),
        )

        tess.add_argument(
            f'--{namespace}-timeout',
            default=180.0,
            type=numeric(float, 0),
            metavar='SECONDS',
            dest=f'{namespace}_timeout',
            help=(
                "Give up on OCR after the timeout, but copy the preprocessed page "
                "into the final output. This timeout is only used when using Tesseract "
                "for OCR. When Tesseract is used for other operations such as "
                "deskewing and orientation, the timeout is controlled by "
                f"--{namespace}-non-ocr-timeout."
            ),
        )

        tess.add_argument(
            f'--{namespace}-non-ocr-timeout',
            default=180.0,
            type=numeric(float, 0),
            metavar='SECONDS',
            dest=f'{namespace}_non_ocr_timeout',
            help=(
                "Give up on non-OCR operations such as deskewing and orientation "
                f"after timeout. This is a separate timeout from --{namespace}-timeout "
                "because these operations are not as expensive as OCR."
            ),
        )

        tess.add_argument(
            f'--{namespace}-downsample-large-images',
            action=argparse.BooleanOptionalAction,
            default=True,
            dest=f'{namespace}_downsample_large_images',
            help=(
                "Downsample large images before OCR. Tesseract has an upper limit on the "
                "size images it will support. If this argument is given, OCRmyPDF will "
                "downsample large images to fit Tesseract. This may reduce OCR quality, "
                "on large images the most desirable text is usually larger. If this "
                "parameter is not supplied, Tesseract will error out and produce no OCR "
                "on the page in question. This argument should be used with a high value "
                f"of --{namespace}-timeout to ensure Tesseract has enough to time."
            ),
        )

        tess.add_argument(
            f'--{namespace}-downsample-above',
            action='store',
            type=numeric(int, 100, 32767),
            default=32767,
            dest=f'{namespace}_downsample_above',
            help=(
                "Downsample images larger than this size pixel size in either dimension "
                f"before OCR. --{namespace}-downsample-large-images downsamples only when "
                "an image exceeds Tesseract's internal limits. This argument causes "
                "downsampling to occur when an image exceeds the given size. This may "
                "reduce OCR quality, but on large images the most desirable text is "
                "usually larger."
            ),
        )

        tess.add_argument(
            '--user-words',
            metavar='FILE',
            dest='user_words',
            help="Specify the location of the Tesseract user words file. This is a "
            "list of words Tesseract should consider while performing OCR in "
            "addition to its standard language dictionaries. This can improve "
            "OCR quality especially for specialized and technical documents.",
        )
        tess.add_argument(
            '--user-patterns',
            metavar='FILE',
            dest='user_patterns',
            help="Specify the location of the Tesseract user patterns file.",
        )


@hookimpl
def register_options():
    """Register Tesseract option model."""
    return {'tesseract': TesseractOptions}


@hookimpl
def add_options(parser):
    # Use the model's CLI generation method - it now handles all Tesseract options
    TesseractOptions.add_arguments_to_parser(parser)


@hookimpl
def check_options(options):
    check_external_program(
        program='tesseract',
        package={'linux': 'tesseract-ocr'},
        version_checker=tesseract.version,
        need_version='4.1.1',  # Ubuntu 22.04 version (also 20.04)
        version_parser=tesseract.TesseractVersion,
    )
    tess_version = tesseract.version()
    if tess_version == tesseract.TesseractVersion('5.4.0'):
        raise MissingDependencyError(
            "Tesseract 5.4.0 is not supported due to regressions in this version. "
            "Please upgrade to a newer or supported older version."
        )

    # Validate Tesseract-specific options using the new model
    # For now, we still access options directly for backward compatibility
    if not tesseract.has_thresholding() and options.tesseract_thresholding != 0:
        log.warning(
            "The installed version of Tesseract does not support changes to its "
            "thresholding method. The --tesseract-threshold argument will be "
            "ignored."
        )
    if options.tesseract_pagesegmode in (0, 2):
        log.warning(
            "The --tesseract-pagesegmode argument you select will disable OCR. "
            "This may cause processing to fail."
        )
    DENIED_LANGUAGES = {'equ', 'osd'}
    if DENIED_LANGUAGES & set(options.languages):
        raise BadArgsError(
            "The following languages for Tesseract's internal use and should not "
            "be issued explicitly: "
            f"{', '.join(DENIED_LANGUAGES & set(options.languages))}\n"
            "Remove them from the -l/--language argument."
        )


@hookimpl
def validate(pdfinfo, options):
    # Tesseract 4.x can be multithreaded, and we also run multiple workers. We want
    # to manage how many threads it uses to avoid creating total threads than cores.
    # Performance testing shows we're better off
    # parallelizing ocrmypdf and forcing Tesseract to be single threaded, which we
    # get by setting the envvar OMP_THREAD_LIMIT to 1. But if the page count of the
    # input file is small, then we allow Tesseract to use threads, subject to the
    # constraint: (ocrmypdf workers) * (tesseract threads) <= max_workers.
    # As of Tesseract 4.1, 3 threads is the most effective on a 4 core/8 thread system.
    if not os.environ.get('OMP_THREAD_LIMIT', '').isnumeric():
        jobs = options.jobs or available_cpu_count()
        tess_threads = clamp(jobs // len(pdfinfo), 1, 3)
        os.environ['OMP_THREAD_LIMIT'] = str(tess_threads)
    else:
        tess_threads = int(os.environ['OMP_THREAD_LIMIT'])
    log.debug("Using Tesseract OpenMP thread limit %d", tess_threads)

    if (
        options.tesseract_downsample_above != 32767
        and not options.tesseract_downsample_large_images
    ):
        log.warning(
            "The --tesseract-downsample-above argument will have no effect unless "
            "--tesseract-downsample-large-images is also given."
        )


@hookimpl
def filter_ocr_image(page: PageContext, image: Image.Image) -> Image.Image:
    """Filter the image before OCR.

    Tesseract cannot handle images with more than 32767 pixels in either axis,
    or more than 2**31 bytes. This function resizes the image to fit within
    those limits.
    """
    threshold = min(page.options.tesseract_downsample_above, 32767)

    options = page.options
    if options.tesseract_downsample_large_images:
        size = calculate_downsample(
            image, max_size=(threshold, threshold), max_bytes=(2**31) - 1
        )
        image = downsample_image(image, size)
    return image


class TesseractOcrEngine(OcrEngine):
    """Implements OCR with Tesseract."""

    @staticmethod
    def version():
        return str(tesseract.version())

    @staticmethod
    def _determine_renderer(options):
        """Determine the PDF renderer to use based on options and languages."""
        if options.pdf_renderer == 'auto':
            if {'ara', 'heb', 'fas', 'per'} & set(options.languages):
                log.info("Using sandwich renderer since there is an RTL language")
                return 'sandwich'
            else:
                return 'hocr'
        return options.pdf_renderer

    @staticmethod
    def creator_tag(options):
        renderer = TesseractOcrEngine._determine_renderer(options)
        tag = '-PDF' if renderer == 'sandwich' else '-hOCR'
        return f"Tesseract OCR{tag} {TesseractOcrEngine.version()}"

    def __str__(self):
        return f"Tesseract OCR {TesseractOcrEngine.version()}"

    @staticmethod
    def languages(options):
        return tesseract.get_languages()

    @staticmethod
    def get_orientation(input_file, options):
        return tesseract.get_orientation(
            input_file,
            engine_mode=options.tesseract_oem,
            timeout=options.tesseract_non_ocr_timeout,
        )

    @staticmethod
    def get_deskew(input_file, options) -> float:
        return tesseract.get_deskew(
            input_file,
            languages=options.languages,
            engine_mode=options.tesseract_oem,
            timeout=options.tesseract_non_ocr_timeout,
        )

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        tesseract.generate_hocr(
            input_file=input_file,
            output_hocr=output_hocr,
            output_text=output_text,
            languages=options.languages,
            engine_mode=options.tesseract_oem,
            tessconfig=options.tesseract_config,
            timeout=options.tesseract_timeout,
            pagesegmode=options.tesseract_pagesegmode,
            thresholding=options.tesseract_thresholding,
            user_words=options.user_words,
            user_patterns=options.user_patterns,
        )

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        tesseract.generate_pdf(
            input_file=input_file,
            output_pdf=output_pdf,
            output_text=output_text,
            languages=options.languages,
            engine_mode=options.tesseract_oem,
            tessconfig=options.tesseract_config,
            timeout=options.tesseract_timeout,
            pagesegmode=options.tesseract_pagesegmode,
            thresholding=options.tesseract_thresholding,
            user_words=options.user_words,
            user_patterns=options.user_patterns,
        )


@hookimpl
def get_ocr_engine():
    return TesseractOcrEngine()
