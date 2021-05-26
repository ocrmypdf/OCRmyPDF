#!/usr/bin/env python3
# © 2015-17 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import locale
import logging
import os
import sys
import unicodedata
from pathlib import Path
from shutil import copyfileobj
from typing import List, Set, Tuple, Union

import pikepdf
import PIL

from ocrmypdf._exec import jbig2enc, pngquant, unpaper
from ocrmypdf._unicodefun import verify_python3_env
from ocrmypdf.exceptions import (
    BadArgsError,
    InputFileError,
    MissingDependencyError,
    OutputFileAccessError,
)
from ocrmypdf.helpers import (
    is_file_writable,
    is_iterable_notstr,
    monotonic,
    safe_symlink,
)
from ocrmypdf.subprocess import check_external_program

# -------------
# External dependencies

HOCR_OK_LANGS = frozenset(['eng', 'deu', 'spa', 'ita', 'por'])
DEFAULT_LANGUAGE = 'eng'  # Enforce English hegemony

log = logging.getLogger(__name__)


# --------
# Critical environment tests
verify_python3_env()


def check_platform():
    if os.name == 'nt' and sys.maxsize <= 2 ** 32:  # pragma: no cover
        # 32-bit interpreter on Windows
        log.error(
            "You are running OCRmyPDF in a 32-bit (x86) Python interpreter."
            "Please use a 64-bit (x86-64) version of Python."
        )


def check_options_languages(options, ocr_engine_languages):
    if not options.languages:
        options.languages = {DEFAULT_LANGUAGE}
        system_lang = locale.getlocale()[0]
        if system_lang and not system_lang.startswith('en'):
            log.debug("No language specified; assuming --language %s", DEFAULT_LANGUAGE)
    if not ocr_engine_languages:
        return
    if not options.languages.issubset(ocr_engine_languages):
        msg = (
            f"OCR engine does not have language data for the following "
            "requested languages: \n"
        )
        for lang in options.languages - ocr_engine_languages:
            msg += lang + '\n'
        raise MissingDependencyError(msg)


def check_options_output(options):
    is_latin = options.languages.issubset(HOCR_OK_LANGS)

    if options.pdf_renderer.startswith('hocr') and not is_latin:
        msg = (
            "The 'hocr' PDF renderer is known to cause problems with one "
            "or more of the languages in your document.  Use "
            "--pdf-renderer auto (the default) to avoid this issue."
        )
        log.warning(msg)

    lossless_reconstruction = False
    if not any(
        (
            options.deskew,
            options.clean_final,
            options.force_ocr,
            options.remove_background,
        )
    ):
        lossless_reconstruction = True
    options.lossless_reconstruction = lossless_reconstruction

    if not options.lossless_reconstruction and options.redo_ocr:
        raise BadArgsError(
            "--redo-ocr is not currently compatible with --deskew, "
            "--clean-final, and --remove-background"
        )


def check_options_sidecar(options):
    if options.sidecar == '\0':
        if options.output_file == '-':
            raise BadArgsError(
                "--sidecar filename must be specified when output file is stdout."
            )
        options.sidecar = options.output_file + '.txt'
    if options.sidecar == options.input_file or options.sidecar == options.output_file:
        raise BadArgsError(
            "--sidecar file must be different from the input and output files"
        )


def check_options_preprocessing(options):
    if options.clean_final:
        options.clean = True
    if options.unpaper_args and not options.clean:
        raise BadArgsError("--clean is required for --unpaper-args")
    if options.clean:
        check_external_program(
            program='unpaper',
            package='unpaper',
            version_checker=unpaper.version,
            need_version='6.1',
            required_for=['--clean, --clean-final'],
        )
        try:
            if options.unpaper_args:
                options.unpaper_args = unpaper.validate_custom_args(
                    options.unpaper_args
                )
        except Exception as e:
            raise BadArgsError("--unpaper-args: " + str(e)) from e


def _pages_from_ranges(ranges: str) -> Set[int]:
    if is_iterable_notstr(ranges):
        return set(ranges)
    pages: List[int] = []
    page_groups = ranges.replace(' ', '').split(',')
    for g in page_groups:
        if not g:
            continue
        try:
            start, end = g.split('-')
        except ValueError:
            pages.append(int(g) - 1)
        else:
            try:
                new_pages = list(range(int(start) - 1, int(end)))
                if not new_pages:
                    raise BadArgsError(f"invalid page subrange '{start}-{end}'")
                pages.extend(new_pages)
            except ValueError:
                raise BadArgsError("invalid page range") from None

    if not pages:
        raise BadArgsError(
            f"The string of page ranges '{ranges}' did not contain any recognizable "
            f"page ranges."
        )

    if not monotonic(pages):
        log.warning(
            "List of pages to process contains duplicate pages, or pages that are "
            "out of order"
        )
    if any(page < 0 for page in pages):
        raise BadArgsError("pages refers to a page number less than 1")

    log.debug("OCRing only these pages: %s", pages)
    return set(pages)


def check_options_ocr_behavior(options):
    exclusive_options = sum(
        [
            (1 if opt else 0)
            for opt in (options.force_ocr, options.skip_text, options.redo_ocr)
        ]
    )
    if exclusive_options >= 2:
        raise BadArgsError("Choose only one of --force-ocr, --skip-text, --redo-ocr.")
    if options.pages:
        options.pages = _pages_from_ranges(options.pages)


def check_options_optimizing(options):
    if options.optimize >= 2:
        check_external_program(
            program='pngquant',
            package='pngquant',
            version_checker=pngquant.version,
            need_version='2.0.1',
            required_for='--optimize {2,3}',
        )

    if options.optimize >= 2:
        # Although we use JBIG2 for optimize=1, don't nag about it unless the
        # user is asking for more optimization
        check_external_program(
            program='jbig2',
            package='jbig2enc',
            version_checker=jbig2enc.version,
            need_version='0.28',
            required_for='--optimize {2,3} | --jbig2-lossy',
            recommended=True if not options.jbig2_lossy else False,
        )

    if options.optimize == 0 and any(
        [options.jbig2_lossy, options.png_quality, options.jpeg_quality]
    ):
        log.warning(
            "The arguments --jbig2-lossy, --png-quality, and --jpeg-quality "
            "will be ignored because --optimize=0."
        )


def check_options_advanced(options):
    if options.pdfa_image_compression != 'auto' and not options.output_type.startswith(
        'pdfa'
    ):
        log.warning(
            "--pdfa-image-compression argument only applies when "
            "--output-type is one of 'pdfa', 'pdfa-1', or 'pdfa-2'"
        )


def check_options_metadata(options):
    docinfo = [options.title, options.author, options.keywords, options.subject]
    for s in (m for m in docinfo if m):
        for c in s:
            if unicodedata.category(c) == 'Co' or ord(c) >= 0x10000:
                raise ValueError(
                    "One of the metadata strings contains "
                    "an unsupported Unicode character: '{}' (U+{})".format(
                        c, hex(ord(c))[2:].upper()
                    )
                )


def check_options_pillow(options):
    PIL.Image.MAX_IMAGE_PIXELS = int(options.max_image_mpixels * 1_000_000)
    if PIL.Image.MAX_IMAGE_PIXELS == 0:
        PIL.Image.MAX_IMAGE_PIXELS = None


def _check_options(options, plugin_manager, ocr_engine_languages):
    check_platform()
    check_options_languages(options, ocr_engine_languages)
    check_options_metadata(options)
    check_options_output(options)
    check_options_sidecar(options)
    check_options_preprocessing(options)
    check_options_ocr_behavior(options)
    check_options_optimizing(options)
    check_options_advanced(options)
    check_options_pillow(options)
    plugin_manager.hook.check_options(options=options)


def check_options(options, plugin_manager):
    ocr_engine_languages = plugin_manager.hook.get_ocr_engine().languages(options)
    _check_options(options, plugin_manager, ocr_engine_languages)


def check_closed_streams(options):  # pragma: no cover
    """Work around Python issue with multiprocessing forking on closed streams

    https://bugs.python.org/issue28326

    Attempting to a fork/exec a new Python process when any of std{in,out,err}
    are closed or not flushable for some reason may raise an exception.
    Fix this by opening devnull if the handle seems to be closed.  Do this
    globally to avoid tracking places all places that fork.

    Seems to be specific to multiprocessing.Process not all Python process
    forkers.

    The error actually occurs when the stream object is not flushable,
    but replacing an open stream object that is not flushable with
    /dev/null is a bad idea since it will create a silent failure.  Replacing
    a closed handle with /dev/null seems safe.

    """

    if sys.version_info[0:3] >= (3, 6, 4):
        return True  # Issued fixed in Python 3.6.4+

    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

    if sys.stdin is None:
        if options.input_file == '-':
            log.error("Trying to read from stdin but stdin seems closed")
            return False
        sys.stdin = open(os.devnull, 'r')

    if sys.stdout is None:
        if options.output_file == '-':
            # Can't replace stdout if the user is piping
            # If this case can even happen, it must be some kind of weird
            # stream.
            log.error(
                "Output was set to stdout '-' but the stream attached to "
                "stdout does not support the flush() system call.  This "
                "will fail."
            )
            return False
        sys.stdout = open(os.devnull, 'w')

    return True


def create_input_file(options, work_folder: Path) -> Tuple[Path, str]:
    if options.input_file == '-':
        # stdin
        log.info('reading file from standard input')
        target = work_folder / 'stdin'
        with open(target, 'wb') as stream_buffer:
            copyfileobj(sys.stdin.buffer, stream_buffer)
        return target, "stdin"
    elif hasattr(options.input_file, 'readable'):
        if not options.input_file.readable():
            raise InputFileError("Input file stream is not readable")
        log.info('reading file from input stream')
        target = work_folder / 'stream'
        with open(target, 'wb') as stream_buffer:
            copyfileobj(options.input_file, stream_buffer)
        return target, "stream"
    else:
        try:
            target = work_folder / 'origin'
            safe_symlink(options.input_file, target)
            return target, os.fspath(options.input_file)
        except FileNotFoundError:
            msg = f"File not found - {options.input_file}"
            if Path('/.dockerenv').exists():  # pragma: no cover
                msg += (
                    "\nDocker cannot your working directory unless you "
                    "explicitly share it with the Docker container and set up"
                    "permissions correctly.\n"
                    "You may find it easier to use stdin/stdout:"
                    "\n"
                    "\tdocker run -i --rm jbarlow83/ocrmypdf - - <input.pdf >output.pdf\n"
                )
            raise InputFileError(msg)


def check_requested_output_file(options):
    if options.output_file == '-':
        if sys.stdout.isatty():
            raise BadArgsError(
                "Output was set to stdout '-' but it looks like stdout "
                "is connected to a terminal.  Please redirect stdout to a "
                "file."
            )
    elif hasattr(options.output_file, 'writable'):
        if not options.output_file.writable():
            raise OutputFileAccessError("Output stream is not writable")
    elif not is_file_writable(options.output_file):
        raise OutputFileAccessError(
            f"Output file location ({options.output_file}) is not a writable file."
        )


def report_output_file_size(options, input_file, output_file):
    try:
        output_size = Path(output_file).stat().st_size
        input_size = Path(input_file).stat().st_size
    except FileNotFoundError:
        return  # Outputting to stream or something
    with pikepdf.open(output_file) as p:
        # Overhead constants obtained by estimating amount of data added by OCR
        # PDF/A conversion, and possible XMP metadata addition, with compression
        FILE_OVERHEAD = 4000
        OCR_PER_PAGE_OVERHEAD = 3000
        reasonable_overhead = FILE_OVERHEAD + OCR_PER_PAGE_OVERHEAD * len(p.pages)
    ratio = output_size / input_size
    reasonable_ratio = output_size / (input_size + reasonable_overhead)
    if reasonable_ratio < 1.35 or input_size < 25000:
        return  # Seems fine

    reasons = []
    image_preproc = {
        'deskew',
        'clean_final',
        'remove_background',
        'oversample',
        'force_ocr',
    }
    for arg in image_preproc:
        if getattr(options, arg, False):
            reasons.append(
                f"The argument --{arg.replace('_', '-')} was issued, causing transcoding."
            )

    if options.optimize == 0:
        reasons.append("Optimization was disabled.")
    else:
        image_optimizers = {
            'jbig2': jbig2enc.available(),
            'pngquant': pngquant.available(),
        }
        for name, available in image_optimizers.items():
            if not available:
                reasons.append(
                    f"The optional dependency '{name}' was not found, so some image "
                    f"optimizations could not be attempted."
                )
    if options.output_type.startswith('pdfa'):
        reasons.append("PDF/A conversion was enabled. (Try `--output-type pdf`.)")
    if options.plugins:
        reasons.append("Plugins were used.")

    if reasons:
        explanation = "Possible reasons for this include:\n" + '\n'.join(reasons) + "\n"
    else:
        explanation = "No reason for this increase is known.  Please report this issue."

    log.warning(
        f"The output file size is {ratio:.2f}× larger than the input file.\n"
        f"{explanation}"
    )
