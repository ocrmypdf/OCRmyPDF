# SPDX-License-Identifier: MPL-2.0
"""Built-in plugin to implement OCR using RapidOCR."""

from __future__ import annotations

import argparse
import logging

from ocrmypdf import hookimpl
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.ocr_engine.rapidocr import (
    RAPIDOCR_AVAILABLE,
    IMPORT_ERROR_MESSAGE,
    RapidOcrEngine,
)

log = logging.getLogger(__name__)


@hookimpl
def add_options(parser):
    """Add RapidOCR specific command line arguments."""
    rapidocr_group = parser.add_argument_group("RapidOCR", "RapidOCR engine options")

    # Check if --ocr-engine already exists
    has_ocr_engine = False
    for action in parser._actions:
        if action.dest == 'ocr_engine':
            has_ocr_engine = True
            # Update choices if the option exists but doesn't include 'rapidocr'
            if 'rapidocr' not in action.choices:
                action.choices.append('rapidocr')
            break

    # Only add the argument if it doesn't exist yet
    if not has_ocr_engine:
        parser.add_argument(
            '--ocr-engine',
            choices=['tesseract', 'rapidocr'],
            default='tesseract',
            help="Choose OCR engine (default: tesseract)",
        )

    rapidocr_group.add_argument(
        '--rapidocr-use-angle-cls',
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable angle classification in RapidOCR to detect rotated text",
    )

    rapidocr_group.add_argument(
        '--rapidocr-lang',
        choices=['ch', 'en', 'french', 'german', 'korean', 'japan'],
        default='en',
        help="Language for RapidOCR recognition (default: en)",
    )


@hookimpl
def check_options(options):
    """Validate RapidOCR settings."""
    if hasattr(options, 'ocr_engine') and options.ocr_engine == 'rapidocr':
        log.info("RapidOCR engine selected in options")

        if not RAPIDOCR_AVAILABLE:
            log.error("RapidOCR engine requested but not available")
            error_msg = (
                "RapidOCR selected as OCR engine but rapidocr_onnxruntime could not be imported. "
                f"Error details: {IMPORT_ERROR_MESSAGE}\n"
                "Install it with: pip install rapidocr_onnxruntime"
            )
            raise MissingDependencyError(error_msg)
        else:
            # Force the option to be set again to make sure it's effective
            options.ocr_engine = 'rapidocr'
            log.info("RapidOCR engine confirmed as available")


@hookimpl
def get_ocr_engine():
    """Return the OCR engine to use."""
    # Add verbose logging
    if not RAPIDOCR_AVAILABLE:
        log.warning("get_ocr_engine(): RapidOCR not available, returning None")
        return None

    log.info("get_ocr_engine(): Returning RapidOCR engine")
    return RapidOcrEngine()
