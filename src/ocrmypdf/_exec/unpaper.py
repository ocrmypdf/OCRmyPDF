# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to unpaper executable."""

from __future__ import annotations

import logging
import os
import shlex
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from subprocess import PIPE, STDOUT
from tempfile import TemporaryDirectory

from packaging.version import Version
from PIL import Image

from ocrmypdf.exceptions import SubprocessOutputError
from ocrmypdf.subprocess import get_version, run

# unpaper documentation:
# https://github.com/Flameeyes/unpaper/blob/main/doc/basic-concepts.md


UNPAPER_IMAGE_PIXEL_LIMIT = 256 * 1024 * 1024

DecFloat = Decimal | float

log = logging.getLogger(__name__)


class UnpaperImageTooLargeError(Exception):
    """To capture details when an image is too large for unpaper."""

    def __init__(
        self,
        w,
        h,
        message="Image with size {}x{} is too large for cleaning with 'unpaper'.",
    ):
        self.w = w
        self.h = h
        self.message = message.format(w, h)
        super().__init__(self.message)


def version() -> Version:
    return Version(get_version('unpaper'))


@contextmanager
def _setup_unpaper_io(input_file: Path) -> Iterator[tuple[Path, Path, Path]]:
    with Image.open(input_file) as im:
        if im.width * im.height >= UNPAPER_IMAGE_PIXEL_LIMIT:
            raise UnpaperImageTooLargeError(w=im.width, h=im.height)

    with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        tmppath = Path(tmpdir)
        # No changes, PNG input, just use the file we already have
        input_png = input_file
        # unpaper can write .png too, but it seems to write them slowly
        # adds a few seconds to test suite - so just use pnm
        output_pnm = tmppath / 'output.pnm'
        yield input_png, output_pnm, tmppath


def run_unpaper(
    input_file: Path, output_file: Path, *, dpi: DecFloat, mode_args: list[str]
) -> None:
    args_unpaper = ['unpaper', '-v', '--dpi', str(round(dpi, 6))] + mode_args

    with _setup_unpaper_io(input_file) as (input_png, output_pnm, tmpdir):
        # To prevent any shenanigans from accepting arbitrary parameters in
        # --unpaper-args, we:
        # 1) run with cwd set to a tmpdir with only unpaper's files
        # 2) forbid the use of '/' in arguments, to prevent changing paths
        # 3) append absolute paths for the input and output file
        # This should ensure that a user cannot clobber some other file with
        # their unpaper arguments (whether intentionally or otherwise)
        args_unpaper.extend([os.fspath(input_png), os.fspath(output_pnm)])
        run(
            args_unpaper,
            close_fds=True,
            check=True,
            stderr=STDOUT,  # unpaper writes logging output to stdout and stderr
            stdout=PIPE,  # and cannot send file output to stdout
            cwd=tmpdir,
            logs_errors_to_stdout=True,
        )
        try:
            with Image.open(output_pnm) as imout:
                imout.save(output_file, dpi=(dpi, dpi))
        except OSError as e:
            raise SubprocessOutputError(
                "unpaper: failed to produce the expected output file. "
                + " Called with: "
                + str(args_unpaper)
            ) from e


def validate_custom_args(args: str) -> list[str]:
    unpaper_args = shlex.split(args)
    if any(('/' in arg or arg == '.' or arg == '..') for arg in unpaper_args):
        raise ValueError('No filenames allowed in --unpaper-args')
    return unpaper_args


def clean(
    input_file: Path,
    output_file: Path,
    *,
    dpi: DecFloat,
    unpaper_args: list[str] | None = None,
) -> Path:
    default_args = [
        '--layout',
        'none',
        '--mask-scan-size',
        '100',  # don't blank out narrow columns
        '--no-border-align',  # don't align visible content to borders
        '--no-mask-center',  # don't center visible content within page
        '--no-grayfilter',  # don't remove light gray areas
        '--no-blackfilter',  # don't remove solid black areas
        '--no-deskew',  # don't deskew
    ]
    if not unpaper_args:
        unpaper_args = default_args
    try:
        run_unpaper(input_file, output_file, dpi=dpi, mode_args=unpaper_args)
        return output_file
    except UnpaperImageTooLargeError as e:
        log.warning(str(e))
        return input_file
