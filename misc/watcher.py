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


def get_output_path(root: Path, basename: str, output_dir_year_month: bool) -> Path:
    assert '/' not in basename, "basename must not contain '/'"
    if output_dir_year_month:
        today = dt.datetime.today()
        output_directory_year_month = root / str(today.year) / f'{today.month:02d}'
        if not output_directory_year_month.exists():
            output_directory_year_month.mkdir(parents=True, exist_ok=True)
        output_path = Path(output_directory_year_month) / Path(basename).with_suffix(
            '.pdf'
        )
    else:
        output_path = root / Path(basename).with_suffix('.pdf')
    return output_path


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
    output_dir_year_month: bool,
):
    # Re-check right before use to shrink the TOCTOU window: reject symlinks and
    # non-regular files, and anything that resolves outside the watched tree.
    if not is_safe_regular_file(file_path, input_dir):
        log.warning(f'Ignoring {file_path}: not a regular file within {input_dir}')
        return

    output_path = get_output_path(output_dir, file_path.name, output_dir_year_month)

    log.info("-" * 20)
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
            archive_path = archive_dir / file_path.name
            if not is_safe_write_target(archive_path, archive_dir):
                log.error(
                    f'Refusing to archive to {archive_path}: destination is '
                    f'occupied by a non-regular file or escapes {archive_dir}'
                )
                return
            log.info(f'OCR is done. Archiving {file_path.name} to {archive_dir}')
            shutil.move(file_path, archive_path)
        else:
            log.info('OCR is done')
    else:
        log.info('OCR is done')


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
    output_dir_year_month: Annotated[
        bool,
        cyclopts.Parameter(
            env_var='OCR_OUTPUT_DIRECTORY_YEAR_MONTH',
            help='Create a subdirectory in the output directory for each year/month',
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
        bool,
        cyclopts.Parameter(
            env_var='OCR_DESKEW',
            help='Deskew the input file before OCR',
        ),
    ] = False,
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
    log.info(
        f"Starting OCRmyPDF watcher with config:\n"
        f"Input Directory: {input_dir}\n"
        f"Output Directory: {output_dir}\n"
        f"Output Directory Year & Month: {output_dir_year_month}\n"
        f"Archive Directory: {archive_dir}"
    )
    log.info(
        f"INPUT_DIRECTORY: {input_dir}\n"
        f"OUTPUT_DIRECTORY: {output_dir}\n"
        f"ARCHIVE_DIRECTORY: {archive_dir}\n"
        f"OUTPUT_DIRECTORY_YEAR_MONTH: {output_dir_year_month}\n"
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
        'ocrmypdf_kwargs': json_settings | {'deskew': deskew},
        'on_success_delete': on_success_delete,
        'on_success_archive': on_success_archive,
        'poll_new_file_seconds': poll_new_file_seconds,
        'retries_loading_file': retries_loading_file,
        'output_dir_year_month': output_dir_year_month,
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
