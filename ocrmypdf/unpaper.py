#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83
# unpaper documentation:
# https://github.com/Flameeyes/unpaper/blob/master/doc/basic-concepts.md

from subprocess import CalledProcessError, STDOUT, check_output, check_call
from tempfile import NamedTemporaryFile
import sys
import os
from functools import lru_cache
from . import ExitCode, get_program


@lru_cache(maxsize=1)
def version():
    args_unpaper = [
        get_program('unpaper'),
        '--version'
    ]
    version = check_output(
        args_unpaper, close_fds=True, universal_newlines=True,
        stderr=STDOUT, timeout=5)
    return version.strip()


try:
    from PIL import Image
except ImportError:
    print("Could not find Python3 imaging library", file=sys.stderr)
    raise


def run(input_file, output_file, dpi, log, mode_args):
    args_unpaper = [
        get_program('unpaper'),
        '-v',
        '--dpi', str(dpi)
    ] + mode_args

    SUFFIXES = {'1': '.pbm', 'L': '.pgm', 'RGB': '.ppm'}

    im = Image.open(input_file)
    if im.mode not in SUFFIXES.keys():
        log.info("Converting image to other colorspace")
        try:
            if im.mode == 'P' and len(im.getcolors()) == 2:
                im = im.convert(mode='1')
            else:
                im = im.convert(mode='RGB')
        except IOError:
            log.error(
                    "Could not convert image with type " + im.mode)
            sys.exit(ExitCode.missing_dependency)

    try:
        suffix = SUFFIXES[im.mode]
    except KeyError:
        log.error(
                "Failed to convert image to a supported format.")
        sys.exit(ExitCode.missing_dependency)

    with NamedTemporaryFile(suffix=suffix) as input_pnm, \
            NamedTemporaryFile(suffix=suffix, mode="r+b") as output_pnm:
        im.save(input_pnm, format='PPM')
        im.close()

        os.unlink(output_pnm.name)

        args_unpaper.extend([input_pnm.name, output_pnm.name])
        try:
            stdout = check_output(
                args_unpaper, close_fds=True,
                universal_newlines=True, stderr=STDOUT,
                )
        except CalledProcessError as e:
            log.debug(e.output)
            raise e from e
        else:
            log.debug(stdout)
            Image.open(output_pnm.name).save(output_file)


def deskew(input_file, output_file, dpi, log):
    run(input_file, output_file, dpi, log, [
        '--mask-scan-size', '100',  # don't blank out narrow columns
        '--no-border-align',  # don't align visible content to borders
        '--no-mask-center',   # don't center visible content within page
        '--no-grayfilter',    # don't remove light gray areas
        '--no-blackfilter',   # don't remove solid black areas
        '--no-noisefilter',   # don't remove salt and pepper noise
        '--no-blurfilter'     # don't remove blurry objects/debris
    ])


def clean(input_file, output_file, dpi, log):
    run(input_file, output_file, dpi, log, [
        '--mask-scan-size', '100',  # don't blank out narrow columns
        '--no-border-align',  # don't align visible content to borders
        '--no-mask-center',   # don't center visible content within page
        '--no-grayfilter',    # don't remove light gray areas
        '--no-blackfilter',   # don't remove solid black areas
        '--no-deskew',        # don't deskew
    ])
