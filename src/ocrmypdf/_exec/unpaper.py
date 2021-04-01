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
from decimal import Decimal
from pathlib import Path
from subprocess import PIPE, STDOUT
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple, Union

from PIL import Image

from ocrmypdf.exceptions import MissingDependencyError, SubprocessOutputError
from ocrmypdf.subprocess import get_version
from ocrmypdf.subprocess import run as external_run

DecFloat = Union[Decimal, float]

log = logging.getLogger(__name__)


def version() -> str:
    return get_version('unpaper')


def _setup_unpaper_io(tmpdir: Path, input_file: Path) -> Tuple[Path, Path]:
    SUFFIXES = {'1': '.pbm', 'L': '.pgm', 'RGB': '.ppm'}
    with Image.open(input_file) as im:
        im_modified = False
        if im.mode not in SUFFIXES:
            log.info("Converting image to other colorspace")
            try:
                if im.mode == 'P' and len(im.getcolors()) == 2:
                    im = im.convert(mode='1')
                else:
                    im = im.convert(mode='RGB')
            except IOError as e:
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

        if im_modified or input_file.suffix != '.pnm':
            input_pnm = tmpdir / 'input.pnm'
            im.save(input_pnm, format='PPM')
        else:
            # No changes, PNG input, just use the file we already have
            input_pnm = input_file
        output_pnm = tmpdir / f'output{suffix}'
    return input_pnm, output_pnm


def run(
    input_file: Path, output_file: Path, *, dpi: DecFloat, mode_args: List[str]
) -> None:
    args_unpaper = ['unpaper', '-v', '--dpi', str(round(dpi, 6))] + mode_args

    with TemporaryDirectory() as tmpdir:
        input_pnm, output_pnm = _setup_unpaper_io(Path(tmpdir), input_file)

        # To prevent any shenanigans from accepting arbitrary parameters in
        # --unpaper-args, we:
        # 1) run with cwd set to a tmpdir with only unpaper's files
        # 2) forbid the use of '/' in arguments, to prevent changing paths
        # 3) append absolute paths for the input and output file
        # This should ensure that a user cannot clobber some other file with
        # their unpaper arguments (whether intentionally or otherwise)
        args_unpaper.extend([os.fspath(input_pnm), os.fspath(output_pnm)])
        external_run(
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
        except (FileNotFoundError, OSError):
            raise SubprocessOutputError(
                "unpaper: failed to produce the expected output file. "
                + " Called with: "
                + str(args_unpaper)
            ) from None


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
):
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
    run(input_file, output_file, dpi=dpi, mode_args=unpaper_args)
