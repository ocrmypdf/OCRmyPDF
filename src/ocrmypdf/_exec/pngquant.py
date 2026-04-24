# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to pngquant executable."""

from __future__ import annotations

from pathlib import Path
from subprocess import PIPE

from ocrmypdf._exec._probe import ToolProbe
from ocrmypdf.subprocess import run

PROBE = ToolProbe(program='pngquant', version_regex=r'(\d+(\.\d+)*).*')
version = PROBE.version
available = PROBE.available


def quantize(input_file: Path, output_file: Path, quality_min: int, quality_max: int):
    """Quantize a PNG image using pngquant.

    Args:
        input_file: Input PNG image
        output_file: Output PNG image
        quality_min: Minimum quality to use
        quality_max: Maximum quality to use
    """
    with open(input_file, 'rb') as input_stream:
        args = [
            'pngquant',
            '--force',
            '--skip-if-larger',
            '--quality',
            f'{quality_min}-{quality_max}',
            '--',  # pngquant: stop processing arguments
            '-',  # pngquant: stream input and output
        ]
        result = run(args, stdin=input_stream, stdout=PIPE, stderr=PIPE, check=False)

    if result.returncode == 0:
        # input_file could be the same as output_file, so we defer the write
        output_file.write_bytes(result.stdout)
