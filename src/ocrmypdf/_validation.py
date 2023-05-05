#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Validate a work order from API or command line."""

from __future__ import annotations

import locale
import logging
import os
import sys
import unicodedata
from argparse import Namespace
from pathlib import Path
from shutil import copyfileobj
from typing import Sequence

import pikepdf
import PIL
from pluggy import PluginManager

from ocrmypdf._exec import unpaper
from ocrmypdf.exceptions import (
    BadArgsError,
    InputFileError,
    MissingDependencyError,
    OutputFileAccessError,
)
from ocrmypdf.helpers import is_file_writable, monotonic, safe_symlink
from ocrmypdf.hocrtransform import HOCR_OK_LANGS
from ocrmypdf.subprocess import check_external_program

# -------------
# External dependencies

DEFAULT_LANGUAGE = 'eng'  # Enforce English hegemony

log = logging.getLogger(__name__)


# --------


def check_platform() -> None:
    if os.name == 'nt' and sys.maxsize <= 2**32:  # pragma: no cover
        # 32-bit interpreter on Windows
        log.error(
            "You are running OCRmyPDF in a 32-bit (x86) Python interpreter."
            "Please use a 64-bit (x86-64) version of Python."
        )


def check_options_languages(options: Namespace, ocr_engine_languages: set[str]) -> None:
    if not options.languages:
        options.languages = {DEFAULT_LANGUAGE}
        system_lang = locale.getlocale()[0]
        if system_lang and not system_lang.startswith('en'):
            log.debug("No language specified; assuming --language %s", DEFAULT_LANGUAGE)
    if not ocr_engine_languages:
        return
    missing_languages = options.languages - ocr_engine_languages
    if missing_languages:
        lang_text = '\n'.join(lang for lang in missing_languages)
        msg = (
            "OCR engine does not have language data for the following "
            "requested languages: \n"
            f"{lang_text}\n"
            "Please install the appropriate language data for your OCR engine.\n"
            "\n"
            "See the online documentation for instructions:\n"
            "    https://ocrmypdf.readthedocs.io/en/latest/languages.html\n"
            "\n"
            "Note: most languages are identified by a 3-digit ISO 639-2 Code.\n"
            "For example, English is 'eng', German is 'deu', and Spanish is 'spa'."
            "\n"
        )
        raise MissingDependencyError(msg)


def check_options_output(options: Namespace) -> None:
    is_latin = options.languages.issubset(HOCR_OK_LANGS)

    if options.pdf_renderer.startswith('hocr') and not is_latin:
        log.warning(
            "The 'hocr' PDF renderer is known to cause problems with one "
            "or more of the languages in your document.  Use "
            "`--pdf-renderer auto` (the default) to avoid this issue."
        )

    if options.output_type == 'none' and options.output_file not in (os.devnull, '-'):
        raise BadArgsError(
            "Since you specified `--output-type none`, the output file "
            f"{options.output_file} cannot be produced. Set the output file to "
            f"`-` to suppress this message."
        )

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


def check_options_sidecar(options: Namespace) -> None:
    if options.sidecar == '\0':
        if options.output_file == '-':
            raise BadArgsError("--sidecar filename needed when output file is stdout.")
        elif options.output_file == os.devnull:
            raise BadArgsError(
                "--sidecar filename needed when output file is /dev/null or NUL."
            )
        options.sidecar = options.output_file + '.txt'
    if options.sidecar == options.input_file or options.sidecar == options.output_file:
        raise BadArgsError(
            "--sidecar file must be different from the input and output files"
        )


def check_options_preprocessing(options: Namespace) -> None:
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
            required_for="--clean, --clean-final",  # Problem arguments
        )
        try:
            if options.unpaper_args:
                options.unpaper_args = unpaper.validate_custom_args(
                    options.unpaper_args
                )
        except Exception as e:
            raise BadArgsError("--unpaper-args: " + str(e)) from e


def _pages_from_ranges(ranges: str) -> set[int]:
    pages: list[int] = []
    page_groups = ranges.replace(' ', '').split(',')
    for group in page_groups:
        if not group:
            continue
        try:
            start, end = group.split('-')
        except ValueError:
            pages.append(int(group) - 1)
        else:
            try:
                new_pages = list(range(int(start) - 1, int(end)))
                if not new_pages:
                    raise BadArgsError(
                        f"invalid page subrange '{start}-{end}'"
                    ) from None
                pages.extend(new_pages)
            except ValueError:
                raise BadArgsError(f"invalid page subrange '{group}'") from None

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


def check_options_ocr_behavior(options: Namespace) -> None:
    exclusive_options = sum(
        (1 if opt else 0)
        for opt in (options.force_ocr, options.skip_text, options.redo_ocr)
    )
    if exclusive_options >= 2:
        raise BadArgsError("Choose only one of --force-ocr, --skip-text, --redo-ocr.")
    if options.pages:
        options.pages = _pages_from_ranges(options.pages)


def check_options_advanced(options: Namespace) -> None:
    if options.pdfa_image_compression != 'auto' and not options.output_type.startswith(
        'pdfa'
    ):
        log.warning(
            "--pdfa-image-compression argument only applies when "
            "--output-type is one of 'pdfa', 'pdfa-1', or 'pdfa-2'"
        )


def check_options_metadata(options: Namespace) -> None:
    docinfo = [options.title, options.author, options.keywords, options.subject]
    for s in (m for m in docinfo if m):
        for char in s:
            if unicodedata.category(char) == 'Co' or ord(char) >= 0x10000:
                hexchar = hex(ord(char))[2:].upper()
                raise ValueError(
                    "One of the metadata strings contains "
                    "an unsupported Unicode character: "
                    f"{char} (U+{hexchar})"
                )


def check_options_pillow(options: Namespace) -> None:
    PIL.Image.MAX_IMAGE_PIXELS = int(options.max_image_mpixels * 1_000_000)
    if PIL.Image.MAX_IMAGE_PIXELS == 0:
        PIL.Image.MAX_IMAGE_PIXELS = None  # type: ignore


def _check_plugin_invariant_options(options: Namespace) -> None:
    check_platform()
    check_options_metadata(options)
    check_options_output(options)
    check_options_sidecar(options)
    check_options_preprocessing(options)
    check_options_ocr_behavior(options)
    check_options_advanced(options)
    check_options_pillow(options)


def _check_plugin_options(options: Namespace, plugin_manager: PluginManager) -> None:
    plugin_manager.hook.check_options(options=options)
    ocr_engine_languages = plugin_manager.hook.get_ocr_engine().languages(options)
    check_options_languages(options, ocr_engine_languages)


def check_options(options: Namespace, plugin_manager: PluginManager) -> None:
    _check_plugin_invariant_options(options)
    _check_plugin_options(options, plugin_manager)


def create_input_file(options: Namespace, work_folder: Path) -> tuple[Path, str]:
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
        except FileNotFoundError as e:
            msg = f"File not found - {options.input_file}"
            if Path('/.dockerenv').exists():  # pragma: no cover
                msg += (
                    "\nDocker cannot your working directory unless you "
                    "explicitly share it with the Docker container and set up"
                    "permissions correctly.\n"
                    "You may find it easier to use stdin/stdout:"
                    "\n"
                    "\tdocker run -i --rm jbarlow83/ocrmypdf - - <input.pdf >output.pdf"
                    "\n"
                )
            raise InputFileError(msg) from e


def check_requested_output_file(options: Namespace) -> None:
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


def report_output_file_size(
    options: Namespace,
    input_file: Path,
    output_file: Path,
    optimize_messages: Sequence[str] | None = None,
    file_overhead: int = 4000,
    page_overhead: int = 3000,
) -> None:
    if optimize_messages is None:
        optimize_messages = []
    try:
        output_size = Path(output_file).stat().st_size
        input_size = Path(input_file).stat().st_size
    except FileNotFoundError:
        return  # Outputting to stream or something
    with pikepdf.open(output_file) as p:
        # Overhead constants obtained by estimating amount of data added by OCR
        # PDF/A conversion, and possible XMP metadata addition, with compression
        reasonable_overhead = file_overhead + page_overhead * len(p.pages)
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
                f"--{arg.replace('_', '-')} was issued, causing transcoding."
            )

    reasons.extend(optimize_messages)

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
