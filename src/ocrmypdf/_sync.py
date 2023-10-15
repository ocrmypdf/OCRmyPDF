# SPDX-FileCopyrightText: 2019-2022 James R. Barlow
# SPDX-FileCopyrightText: 2019 Martin Wind
# SPDX-License-Identifier: MPL-2.0

"""Implements the concurrent and page synchronous parts of the pipeline."""


from __future__ import annotations

import logging
import logging.handlers

from ocrmypdf._pipelines._common import (
    configure_debug_logging,
)
from ocrmypdf._pipelines.ocr import run_pipeline, run_pipeline_cli
from ocrmypdf._pipelines.pdf_to_hocr import run_hocr_pipeline

log = logging.getLogger(__name__)


__all__ = [
    'run_pipeline',
    'run_pipeline_cli',
    'run_hocr_pipeline',
    'configure_debug_logging',
]
