# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to verapdf executable."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from subprocess import PIPE
from typing import NamedTuple

from packaging.version import Version

from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import get_version, run

log = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    """Result of PDF/A validation."""

    valid: bool
    failed_rules: int
    message: str


def version() -> Version:
    """Get verapdf version."""
    return Version(get_version('verapdf', regex=r'veraPDF (\d+(\.\d+)*)'))


def available() -> bool:
    """Check if verapdf is available."""
    try:
        version()
    except MissingDependencyError:
        return False
    return True


def output_type_to_flavour(output_type: str) -> str:
    """Map OCRmyPDF output_type to verapdf flavour.

    Args:
        output_type: One of 'pdfa', 'pdfa-1', 'pdfa-2', 'pdfa-3'

    Returns:
        verapdf flavour string like '1b', '2b', '3b'
    """
    mapping = {
        'pdfa': '2b',
        'pdfa-1': '1b',
        'pdfa-2': '2b',
        'pdfa-3': '3b',
    }
    return mapping.get(output_type, '2b')


def validate(input_file: Path, flavour: str) -> ValidationResult:
    """Validate a PDF against a PDF/A profile.

    Args:
        input_file: Path to PDF file to validate
        flavour: verapdf flavour (1a, 1b, 2a, 2b, 2u, 3a, 3b, 3u)

    Returns:
        ValidationResult with validation status
    """
    args = [
        'verapdf',
        '--format',
        'json',
        '--flavour',
        flavour,
        str(input_file),
    ]

    try:
        proc = run(args, stdout=PIPE, stderr=PIPE, check=False)
    except FileNotFoundError as e:
        raise MissingDependencyError('verapdf') from e

    try:
        result = json.loads(proc.stdout)
        jobs = result.get('report', {}).get('jobs', [])
        if not jobs:
            return ValidationResult(False, -1, 'No validation jobs in result')
        validation_results = jobs[0].get('validationResult', [])
        if not validation_results:
            return ValidationResult(False, -1, 'No validation result in output')
        validation_result = validation_results[0]
        details = validation_result.get('details', {})
        failed_rules = details.get('failedRules', 0)

        if failed_rules == 0:
            return ValidationResult(True, 0, 'PDF/A validation passed')
        else:
            return ValidationResult(
                False,
                failed_rules,
                f'PDF/A validation failed with {failed_rules} rule violations',
            )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.debug('Failed to parse verapdf output: %s', e)
        return ValidationResult(False, -1, f'Failed to parse verapdf output: {e}')
