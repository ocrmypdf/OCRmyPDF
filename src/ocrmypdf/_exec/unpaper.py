# © 2015 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

# unpaper documentation:
# https://github.com/Flameeyes/unpaper/blob/master/doc/basic-concepts.md

"""Interface to unpaper executable"""

import logging
import os
import shlex
from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError
from tempfile import TemporaryDirectory

from PIL import Image

from ocrmypdf.exceptions import MissingDependencyError, SubprocessOutputError
from ocrmypdf.subprocess import get_version
from ocrmypdf.subprocess import run as external_run

log = logging.getLogger(__name__)


def version():
    return get_version('unpaper')


def run(input_file, output_file, dpi, mode_args):
    args_unpaper = ['unpaper', '-v', '--dpi', str(dpi)] + mode_args

    SUFFIXES = {'1': '.pbm', 'L': '.pgm', 'RGB': '.ppm'}

    with TemporaryDirectory() as tmpdir, Image.open(input_file) as im:
        if im.mode not in SUFFIXES.keys():
            log.info("Converting image to other colorspace")
            try:
                if im.mode == 'P' and len(im.getcolors()) == 2:
                    im = im.convert(mode='1')
                else:
                    im = im.convert(mode='RGB')
            except IOError as e:
                im.close()
                raise MissingDependencyError(
                    "Could not convert image with type " + im.mode
                ) from e

        try:
            suffix = SUFFIXES[im.mode]
        except KeyError:
            raise MissingDependencyError(
                "Failed to convert image to a supported format."
            ) from e

        input_pnm = Path(tmpdir) / f'input{suffix}'
        output_pnm = Path(tmpdir) / f'output{suffix}'
        im.save(input_pnm, format='PPM')

        # To prevent any shenanigans from accepting arbitrary parameters in
        # --unpaper-args, we:
        # 1) run with cwd set to a tmpdir with only unpaper's files
        # 2) forbid the use of '/' in arguments, to prevent changing paths
        # 3) append absolute paths for the input and output file
        # This should ensure that a user cannot clobber some other file with
        # their unpaper arguments (whether intentionally or otherwise)
        args_unpaper.extend([os.fspath(input_pnm), os.fspath(output_pnm)])
        try:
            proc = external_run(
                args_unpaper,
                check=True,
                close_fds=True,
                universal_newlines=True,
                stderr=STDOUT,
                cwd=tmpdir,
                stdout=PIPE,
            )
        except CalledProcessError as e:
            log.debug(e.output)
            raise e from e
        else:
            log.debug(proc.stdout)
            # unpaper sets dpi to 72; fix this
            try:
                with Image.open(output_pnm) as imout:
                    imout.save(output_file, dpi=(dpi, dpi))
            except (FileNotFoundError, OSError):
                raise SubprocessOutputError(
                    "unpaper: failed to produce the expected output file. "
                    + " Called with: "
                    + str(args_unpaper)
                ) from None


def validate_custom_args(args: str):
    unpaper_args = shlex.split(args)
    if any('/' in arg for arg in unpaper_args):
        raise ValueError('No filenames allowed in --unpaper-args')
    return unpaper_args


def clean(input_file, output_file, dpi, unpaper_args=None):
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
    run(input_file, output_file, dpi, unpaper_args)
