#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2019 Ian Alexander <https://github.com/ianalexander>
# SPDX-FileCopyrightText: 2020 James R Barlow <https://github.com/jbarlow83>
# SPDX-License-Identifier: MIT

"""Watch a directory for new PDFs and OCR them."""

from __future__ import annotations

import datetime as dt
import fnmatch
import json
import logging
import os
import shutil
import sys
import time
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any

import cyclopts
import pikepdf
from dotenv import load_dotenv
from watchfiles import Change, DefaultFilter, watch

import ocrmypdf
from ocrmypdf._watcher_security import (
    WatcherConfigError,
    assert_data_dirs_isolated,
    assert_no_watch_loop,
    assert_plugins_safe,
    assert_settings_file_safe,
    is_safe_regular_file,
    is_safe_write_target,
    resolve_critical_paths,
)

# ``load_dotenv`` reads ``.env`` from the current working directory. The startup
# check in ``main`` guarantees the data directories are disjoint from the code
# zone (which includes the working directory), so ``.env`` remains trusted.
load_dotenv()


# pylint: disable=logging-format-interpolation
app = cyclopts.App(name="ocrmypdf-watcher")

log = logging.getLogger('ocrmypdf-watcher')


class LoggingLevelEnum(StrEnum):
    """Enum for logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OutputStructure(StrEnum):
    """Enum for the directory layout of the output and archive directories."""

    FLAT = "FLAT"
    YEAR_MONTH = "YEAR_MONTH"
    HIERARCHY = "HIERARCHY"


class ConflictPolicy(StrEnum):
    """Enum for what to do when a destination file already exists."""

    SKIP = "SKIP"
    OVERWRITE = "OVERWRITE"
    SUFFIX = "SUFFIX"


# Illegal in a Windows/SMB filename; a superset of what POSIX forbids.
_ILLEGAL_FILENAME_CHARS = frozenset('<>:"/\\|?*')

# Windows refuses these names whatever the extension.
_RESERVED_DEVICE_NAMES = frozenset(
    ['CON', 'PRN', 'AUX', 'NUL']
    + [f'COM{n}' for n in range(1, 10)]
    + [f'LPT{n}' for n in range(1, 10)]
)


def sanitize_filename_component(name: str) -> str:
    """Rewrite one path component so it can be created on any common filesystem.

    The output side is often a more restrictive filesystem than the input side --
    an SMB share, say -- so characters that are merely unusual on POSIX are
    replaced rather than passed through and left to fail at write time.
    """
    cleaned = ''.join(
        '_' if ch in _ILLEGAL_FILENAME_CHARS or ord(ch) < 32 else ch for ch in name
    )
    # Windows silently drops trailing dots and spaces, so the name we asked for
    # would not be the name on disk.
    cleaned = cleaned.rstrip('. ')
    if Path(cleaned).stem.upper() in _RESERVED_DEVICE_NAMES:
        cleaned = f'_{cleaned}'
    return cleaned or '_'


def get_output_path(
    root: Path,
    input_dir: Path,
    file_path: Path,
    structure: OutputStructure,
    *,
    force_pdf: bool = True,
) -> Path:
    """Build the destination path for ``file_path`` under ``root``.

    Every component is sanitized. ``force_pdf`` is for the output directory,
    where the result is always a PDF; the archive keeps the original suffix.
    This never creates directories -- the caller does that, after the
    destination has passed the safety check.
    """
    parts: list[str] = []
    if structure == OutputStructure.YEAR_MONTH:
        today = dt.datetime.today()
        parts = [str(today.year), f'{today.month:02d}']
    elif structure == OutputStructure.HIERARCHY:
        relative = os.path.relpath(file_path.parent, input_dir)
        parts = [p for p in Path(relative).parts if p not in ('.', '..')]

    # Sanitize before touching the suffix: an unsanitized name may contain
    # characters (':' above all) that Path parses as something other than a name.
    name = sanitize_filename_component(file_path.name)
    if force_pdf:
        name = Path(name).with_suffix('.pdf').name
    return root.joinpath(*(sanitize_filename_component(p) for p in parts), name)


def apply_conflict_policy(path: Path, policy: ConflictPolicy) -> Path | None:
    """Resolve a destination that may already be occupied.

    Returns the path to write to, or None if the file must be left alone.
    """
    if not path.exists():
        return path
    if policy == ConflictPolicy.OVERWRITE:
        return path
    if policy == ConflictPolicy.SKIP:
        return None
    # SUFFIX: the numbering Windows Explorer and macOS Finder both produce.
    counter = 1
    while True:
        candidate = path.with_name(f'{path.stem} ({counter}){path.suffix}')
        if not candidate.exists():
            return candidate
        counter += 1


def wait_for_file_ready(
    file_path: Path, poll_new_file_seconds: int, retries_loading_file: int
):
    # This loop waits to make sure that the file is completely loaded on
    # disk before attempting to read. Docker sometimes will publish the
    # watchdog event before the file is actually fully on disk, causing
    # pikepdf to fail.

    tries = retries_loading_file + 1
    while tries:
        try:
            with pikepdf.Pdf.open(file_path) as pdf:
                log.debug(f"{file_path} ready with {pdf.pages} pages")
                return True
        except pikepdf.PasswordError as e:
            # PasswordError derives from Exception, not PdfError, so it must be
            # caught explicitly. Waiting cannot produce the password, so give up
            # immediately rather than burning the retry budget.
            log.error(f"File {file_path} is password protected, skipping")
            log.debug("Exception was", exc_info=e)
            return False
        except (FileNotFoundError, OSError) as e:
            log.info(f"File {file_path} is not ready yet")
            log.debug("Exception was", exc_info=e)
            time.sleep(poll_new_file_seconds)
            tries -= 1
        except pikepdf.PdfError as e:
            log.info(f"File {file_path} is not full written yet")
            log.debug("Exception was", exc_info=e)
            time.sleep(poll_new_file_seconds)
            tries -= 1

    return False


def execute_ocrmypdf(
    *,
    file_path: Path,
    input_dir: Path,
    archive_dir: Path,
    output_dir: Path,
    ocrmypdf_kwargs: dict[str, Any],
    on_success_delete: bool,
    on_success_archive: bool,
    poll_new_file_seconds: int,
    retries_loading_file: int,
    output_structure: OutputStructure,
    on_conflict: ConflictPolicy,
):
    # Re-check right before use to shrink the TOCTOU window: reject symlinks and
    # non-regular files, and anything that resolves outside the watched tree.
    if not is_safe_regular_file(file_path, input_dir):
        log.warning(f'Ignoring {file_path}: not a regular file within {input_dir}')
        return

    log.info("-" * 20)

    # Settle the destination before waiting for the file: a skipped file should
    # cost neither the wait nor the OCR run.
    intended_output = get_output_path(
        output_dir, input_dir, file_path, output_structure
    )
    output_path = apply_conflict_policy(intended_output, on_conflict)
    if output_path is None:
        log.info(f'Skipping {file_path}: output {intended_output} already exists')
        return

    log.info(f'New file: {file_path}. Waiting until fully written...')
    if not wait_for_file_ready(file_path, poll_new_file_seconds, retries_loading_file):
        log.info(f"Gave up waiting for {file_path} to become ready")
        return

    if not is_safe_write_target(output_path, output_dir):
        log.error(
            f'Refusing to write output to {output_path}: destination is occupied '
            f'by a non-regular file or escapes {output_dir}'
        )
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log.info(f'Attempting to OCRmyPDF to: {output_path}')

    log.debug(
        f'OCRmyPDF input_file={file_path} output_file={output_path} '
        f'kwargs: {ocrmypdf_kwargs}'
    )
    exit_code = ocrmypdf.ocr(
        ocrmypdf.OcrOptions(
            input_file=file_path,
            output_file=output_path,
            **ocrmypdf_kwargs,
        )
    )
    if exit_code == 0:
        if on_success_delete:
            log.info(f'OCR is done. Deleting: {file_path}')
            file_path.unlink()
        elif on_success_archive:
            # Same structure and same conflict policy as the output directory.
            intended_archive = get_output_path(
                archive_dir,
                input_dir,
                file_path,
                output_structure,
                force_pdf=False,
            )
            archive_path = apply_conflict_policy(intended_archive, on_conflict)
            if archive_path is None:
                log.info(
                    f'Not archiving {file_path}: {intended_archive} already '
                    f'exists; leaving the original in {input_dir}'
                )
                return
            if not is_safe_write_target(archive_path, archive_dir):
                log.error(
                    f'Refusing to archive to {archive_path}: destination is '
                    f'occupied by a non-regular file or escapes {archive_dir}'
                )
                return
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            log.info(f'OCR is done. Archiving {file_path.name} to {archive_path}')
            shutil.move(file_path, archive_path)
        else:
            log.info('OCR is done')
    else:
        log.info('OCR is done')


def ocrmypdf_kwargs(json_settings: dict[str, Any], deskew: bool | None) -> dict:
    """Merge OCR_DESKEW into the OCR_JSON_SETTINGS arguments for ocrmypdf.ocr.

    OCR_DESKEW overrides the JSON settings only if it is set, so that
    "deskew" in the JSON settings is not silently turned off.
    """
    if deskew is None:
        return dict(json_settings)
    return json_settings | {'deskew': deskew}


class PdfFilter(DefaultFilter):
    """Only surface newly created files whose name matches a watched pattern."""

    def __init__(self, patterns):  # noqa: D107
        super().__init__()
        self._patterns = tuple(patterns)

    def __call__(self, change: Change, path: str) -> bool:
        if change is not Change.added:
            return False
        if not super().__call__(change, path):
            return False
        name = Path(path).name
        return any(fnmatch.fnmatch(name, pattern) for pattern in self._patterns)


@app.default
def main(
    input_dir: Annotated[
        Path,
        cyclopts.Parameter(
            env_var='OCR_INPUT_DIRECTORY',
        ),
    ] = Path('/input'),
    output_dir: Annotated[
        Path,
        cyclopts.Parameter(
            env_var='OCR_OUTPUT_DIRECTORY',
        ),
    ] = Path('/output'),
    archive_dir: Annotated[
        Path,
        cyclopts.Parameter(
            env_var='OCR_ARCHIVE_DIRECTORY',
        ),
    ] = Path('/processed'),
    *,
    output_structure: Annotated[
        OutputStructure | None,
        cyclopts.Parameter(
            env_var='OCR_OUTPUT_STRUCTURE',
            help='Layout of the output and archive directories: FLAT, YEAR_MONTH '
            '(a YYYY/MM subdirectory), or HIERARCHY (mirror the input directory '
            'tree)',
        ),
    ] = None,
    on_conflict: Annotated[
        ConflictPolicy,
        cyclopts.Parameter(
            env_var='OCR_ON_CONFLICT',
            help='What to do when the destination file already exists: SKIP, '
            'OVERWRITE, or SUFFIX (write "name (1).pdf" instead)',
        ),
    ] = ConflictPolicy.SUFFIX,
    output_dir_year_month: Annotated[
        bool,
        cyclopts.Parameter(
            env_var='OCR_OUTPUT_DIRECTORY_YEAR_MONTH',
            help='(deprecated) Create a subdirectory in the output directory for '
            'each year/month; use --output-structure YEAR_MONTH instead',
        ),
    ] = False,
    on_success_delete: Annotated[
        bool,
        cyclopts.Parameter(
            env_var='OCR_ON_SUCCESS_DELETE',
            help='Delete the input file after successful OCR',
        ),
    ] = False,
    on_success_archive: Annotated[
        bool,
        cyclopts.Parameter(
            env_var='OCR_ON_SUCCESS_ARCHIVE',
            help='Archive the input file after successful OCR',
        ),
    ] = False,
    deskew: Annotated[
        bool | None,
        cyclopts.Parameter(
            env_var='OCR_DESKEW',
            help='Deskew the input file before OCR. If set, overrides "deskew" '
            'in OCR_JSON_SETTINGS',
        ),
    ] = None,
    ocr_json_settings: Annotated[
        str | None,
        cyclopts.Parameter(
            env_var='OCR_JSON_SETTINGS',
            help='JSON settings to pass to OCRmyPDF (JSON string or file path)',
        ),
    ] = None,
    poll_new_file_seconds: Annotated[
        int,
        cyclopts.Parameter(
            env_var='OCR_POLL_NEW_FILE_SECONDS',
            help='Seconds to wait before polling a new file',
        ),
    ] = 1,
    use_polling: Annotated[
        bool,
        cyclopts.Parameter(
            env_var='OCR_USE_POLLING',
            help='Use polling instead of filesystem events',
        ),
    ] = False,
    retries_loading_file: Annotated[
        int,
        cyclopts.Parameter(
            env_var='OCR_RETRIES_LOADING_FILE',
            help='Number of times to retry loading a file before giving up',
        ),
    ] = 5,
    loglevel: Annotated[
        LoggingLevelEnum,
        cyclopts.Parameter(
            env_var='OCR_LOGLEVEL',
            help='Logging level',
        ),
    ] = LoggingLevelEnum.INFO,
    patterns: Annotated[
        str,
        cyclopts.Parameter(
            env_var='OCR_PATTERNS',
            help='File patterns to watch',
        ),
    ] = '*.pdf,*.PDF',
):
    ocrmypdf.configure_logging(
        verbosity=(
            ocrmypdf.Verbosity.default
            if loglevel != LoggingLevelEnum.DEBUG
            else ocrmypdf.Verbosity.debug
        ),
        manage_root_logger=True,
    )
    log.setLevel(loglevel.value)

    # Resolve the legacy boolean into the structure enum. Logging is configured
    # by now, so the deprecation notice reaches the ordinary startup log.
    if output_structure is None:
        if output_dir_year_month:
            log.warning(
                "OCR_OUTPUT_DIRECTORY_YEAR_MONTH is deprecated; use "
                "OCR_OUTPUT_STRUCTURE=YEAR_MONTH instead"
            )
            output_structure = OutputStructure.YEAR_MONTH
        else:
            output_structure = OutputStructure.FLAT
    elif output_dir_year_month:
        log.warning(
            "OCR_OUTPUT_DIRECTORY_YEAR_MONTH is deprecated and is ignored "
            "because OCR_OUTPUT_STRUCTURE is set"
        )

    log.info(
        f"Starting OCRmyPDF watcher with config:\n"
        f"Input Directory: {input_dir}\n"
        f"Output Directory: {output_dir}\n"
        f"Output Structure: {output_structure.value}\n"
        f"Archive Directory: {archive_dir}"
    )
    log.info(
        f"INPUT_DIRECTORY: {input_dir}\n"
        f"OUTPUT_DIRECTORY: {output_dir}\n"
        f"ARCHIVE_DIRECTORY: {archive_dir}\n"
        f"OUTPUT_STRUCTURE: {output_structure.value}\n"
        f"ON_CONFLICT: {on_conflict.value}\n"
        f"ON_SUCCESS_DELETE: {on_success_delete}\n"
        f"ON_SUCCESS_ARCHIVE: {on_success_archive}\n"
        f"DESKEW: {deskew}\n"
        f"ARGS: {ocr_json_settings}\n"
        f"POLL_NEW_FILE_SECONDS: {poll_new_file_seconds}\n"
        f"RETRIES_LOADING_FILE: {retries_loading_file}\n"
        f"USE_POLLING: {use_polling}\n"
        f"LOGLEVEL: {loglevel.value}"
    )

    data_dirs = [input_dir, output_dir, archive_dir]
    try:
        # Harvard architecture: the attacker-writable data directories must be
        # completely separate from the interpreter, virtual environment and $PATH,
        # so a less-privileged user cannot inject code that we would execute.
        assert_data_dirs_isolated(
            {'input': input_dir, 'output': output_dir, 'archive': archive_dir},
            resolve_critical_paths(),
        )

        # The input directory is watched recursively, so output/archive must not
        # live under it or OCR output would be reprocessed forever.
        assert_no_watch_loop(input_dir, output_dir, archive_dir)

        if ocr_json_settings and Path(ocr_json_settings).exists():
            settings_path = Path(ocr_json_settings)
            assert_settings_file_safe(settings_path, data_dirs)
            json_settings = json.loads(settings_path.read_text())
        else:
            json_settings = json.loads(ocr_json_settings or '{}')

        if 'input_file' in json_settings or 'output_file' in json_settings:
            raise WatcherConfigError(
                'OCR_JSON_SETTINGS (--ocr-json-settings) may not specify '
                'input/output file'
            )

        plugins = json_settings.get('plugins') or []
        if isinstance(plugins, (str, Path)):
            plugins = [plugins]
        assert_plugins_safe(plugins, data_dirs)
    except WatcherConfigError as e:
        log.error(str(e))
        sys.exit(e.exit_code)

    settings = {
        'input_dir': input_dir,
        'archive_dir': archive_dir,
        'output_dir': output_dir,
        'ocrmypdf_kwargs': ocrmypdf_kwargs(json_settings, deskew),
        'on_success_delete': on_success_delete,
        'on_success_archive': on_success_archive,
        'poll_new_file_seconds': poll_new_file_seconds,
        'retries_loading_file': retries_loading_file,
        'output_structure': output_structure,
        'on_conflict': on_conflict,
    }

    print(f"Watching {input_dir} for new PDFs. Press Ctrl+C to exit.")
    try:
        for changes in watch(
            input_dir,
            watch_filter=PdfFilter(patterns.split(',')),
            force_polling=use_polling,
            recursive=True,
        ):
            for _change, path in changes:
                try:
                    execute_ocrmypdf(file_path=Path(path), **settings)
                except Exception:  # noqa: BLE001
                    # A watched folder is unattended, so no single bad file may
                    # take the watcher down with it. Log and keep watching.
                    log.exception(f"Error while processing {path}, continuing")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app()
