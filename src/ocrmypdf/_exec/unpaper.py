# © 2015 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


# unpaper documentation:
# https://github.com/Flameeyes/unpaper/blob/master/doc/basic-concepts.md

"""Interface to unpaper executable"""

import logging
import os
import shlex
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from subprocess import PIPE, STDOUT
from tempfile import TemporaryDirectory
from typing import Iterator, List, Optional, Tuple, Union

from PIL import Image

from ocrmypdf.exceptions import MissingDependencyError, SubprocessOutputError
from ocrmypdf.subprocess import get_version, run

UNPAPER_IMAGE_PIXEL_LIMIT = 256 * 1024 * 1024

DecFloat = Union[Decimal, float]

log = logging.getLogger(__name__)


class UnpaperImageTooLargeError(Exception):
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


def version() -> str:
    return get_version('unpaper')


def _convert_image(im: Image.Image) -> Tuple[Image.Image, bool, str]:
    SUFFIXES = {'1': '.pbm', 'L': '.pgm', 'RGB': '.ppm'}
    im_modified = False

    if im.mode not in SUFFIXES:
        log.info("Converting image to other colorspace")
        try:
            if im.mode == 'P' and len(im.getcolors()) == 2:
                im = im.convert(mode='1')
            else:
                im = im.convert(mode='RGB')
        except OSError as e:
            raise MissingDependencyError(
                "Could not convert image with type " + im.mode
            ) from e
        else:
            im_modified = True
    try:
        suffix = SUFFIXES[im.mode]
    except KeyError:
        raise MissingDependencyError(
            "Failed to convert image to a supported format."
        ) from None
    return im, im_modified, suffix


@contextmanager
def _setup_unpaper_io(input_file: Path) -> Iterator[Tuple[Path, Path, Path]]:
    with Image.open(input_file) as im:
        if im.width * im.height >= UNPAPER_IMAGE_PIXEL_LIMIT:
            raise UnpaperImageTooLargeError(w=im.width, h=im.height)
        im, im_modified, suffix = _convert_image(im)

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            if im_modified or input_file.suffix != '.pnm':
                input_pnm = tmppath / 'input.pnm'
                im.save(input_pnm, format='PPM')
            else:
                # No changes, PNG input, just use the file we already have
                input_pnm = input_file

            output_pnm = tmppath / f'output{suffix}'
            yield input_pnm, output_pnm, tmppath


def run_unpaper(
    input_file: Path, output_file: Path, *, dpi: DecFloat, mode_args: List[str]
) -> None:
    args_unpaper = ['unpaper', '-v', '--dpi', str(round(dpi, 6))] + mode_args

    with _setup_unpaper_io(input_file) as (input_pnm, output_pnm, tmpdir):
        # To prevent any shenanigans from accepting arbitrary parameters in
        # --unpaper-args, we:
        # 1) run with cwd set to a tmpdir with only unpaper's files
        # 2) forbid the use of '/' in arguments, to prevent changing paths
        # 3) append absolute paths for the input and output file
        # This should ensure that a user cannot clobber some other file with
        # their unpaper arguments (whether intentionally or otherwise)
        args_unpaper.extend([os.fspath(input_pnm), os.fspath(output_pnm)])
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


def validate_custom_args(args: str) -> List[str]:
    unpaper_args = shlex.split(args)
    if any(('/' in arg or arg == '.' or arg == '..') for arg in unpaper_args):
        raise ValueError('No filenames allowed in --unpaper-args')
    return unpaper_args


def clean(
    input_file: Path,
    output_file: Path,
    *,
    dpi: DecFloat,
    unpaper_args: Optional[List[str]] = None,
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
