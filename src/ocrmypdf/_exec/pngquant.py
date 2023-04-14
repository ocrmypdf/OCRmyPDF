# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to pngquant executable."""

from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from subprocess import PIPE

from PIL import Image

from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import get_version, run


def version():
    return get_version('pngquant', regex=r'(\d+(\.\d+)*).*')


def available():
    try:
        version()
    except MissingDependencyError:
        return False
    return True


@contextmanager
def input_as_png(input_file: Path):
    if not input_file.name.endswith('.png'):
        with Image.open(input_file) as im:
            bio = BytesIO()
            im.save(bio, format='png')
            bio.seek(0)
            yield bio
    else:
        with open(input_file, 'rb') as f:
            yield f


def quantize(input_file: Path, output_file: Path, quality_min: int, quality_max: int):
    with input_as_png(input_file) as input_stream:
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


def quantize_mp(args):
    return quantize(*args)
