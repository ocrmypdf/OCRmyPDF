#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2019 Ian Alexander <https://github.com/ianalexander>
# SPDX-FileCopyrightText: 2020 James R Barlow <https://github.com/jbarlow83>
# SPDX-License-Identifier: MIT

"""Watch a directory for new PDFs and OCR them."""

from __future__ import annotations

import datetime as dt
import json
import logging
import shutil
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import cyclopts
import pikepdf
from dotenv import load_dotenv
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
import re
import os

import ocrmypdf

load_dotenv()


# pylint: disable=logging-format-interpolation
app = cyclopts.App(name="ocrmypdf-watcher")

log = logging.getLogger('ocrmypdf-watcher')


class LoggingLevelEnum(str, Enum):
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
    archive_dir: Path,
    output_dir: Path,
    ocrmypdf_kwargs: dict[str, Any],
    on_success_delete: bool,
    on_success_archive: bool,
    poll_new_file_seconds: int,
    retries_loading_file: int,
    output_dir_year_month: bool,
):
    output_path = get_output_path(output_dir, file_path.name, output_dir_year_month)

    log.info("-" * 20)
    log.info(f'New file: {file_path}. Waiting until fully written...')
    if not wait_for_file_ready(file_path, poll_new_file_seconds, retries_loading_file):
        log.info(f"Gave up waiting for {file_path} to become ready")
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
            log.info(f'OCR is done. Archiving {file_path.name} to {archive_dir}')
            shutil.move(file_path, f'{archive_dir}/{file_path.name}')
        else:
            log.info('OCR is done')
    else:
        log.info('OCR is done')


class HandleObserverEvent(PatternMatchingEventHandler):
    def __init__(  # noqa: D107
        self,
        patterns=None,
        ignore_patterns=None,
        ignore_directories=False,
        case_sensitive=False,
        settings=None,
    ):
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self._settings = settings if settings else {}

    def on_any_event(self, event):
        if event.event_type in ['created']:
            try:
                execute_ocrmypdf(file_path=Path(event.src_path), **self._settings)
            except Exception as e:
                # 1. Extract error message and truncate at the first hyphen (as requested)
                raw_error = str(e).split('-')[0].strip()

                # 2. Remove invalid filename characters and limit length
                safe_reason = re.sub(r'[^\w\s-]', '', raw_error)
                if len(safe_reason) > 60:
                    safe_reason = safe_reason[:57] + "..."

                # 3. Apply the exact same output directory logic as successful processing
                original_path = Path(event.src_path)
                basename = original_path.name
                output_dir = self._settings.get('output_dir', Path('/output'))
                use_year_month = self._settings.get('output_dir_year_month', False)

                if use_year_month:
                    today = dt.datetime.today()
                    target_dir = output_dir / str(today.year) / f'{today.month:02d}'
                    target_dir.mkdir(parents=True, exist_ok=True)
                else:
                    target_dir = output_dir

                # 4. Construct new filename with error reason appended before extension
                stem = original_path.stem
                suffix = original_path.suffix
                new_name = f"{stem}_{safe_reason}{suffix}"
                target_path = target_dir / new_name

                # 5. Avoid overwriting (append a counter if file already exists)
                counter = 1
                while target_path.exists():
                    new_name = f"{stem}_{safe_reason}_{counter}{suffix}"
                    target_path = target_dir / new_name
                    counter += 1

                # 6. Move file to output directory and log the event
                try:
                    time.sleep(2)  # Allow SMB/Windows Explorer cache to propagate before move
                    shutil.move(str(original_path), str(target_path))
                    os.utime(target_path)                  # updates mtime/atime → forces SMB client refresh
                    log.warning(f"Moved failed OCR file {original_path.name} -> {target_path.name}: {safe_reason}")
                except Exception as move_err:
                    log.error(f"Failed to move file {original_path.name} to output directory: {move_err}")

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

    if ocr_json_settings and Path(ocr_json_settings).exists():
        json_settings = json.loads(Path(ocr_json_settings).read_text())
    else:
        json_settings = json.loads(ocr_json_settings or '{}')

    if 'input_file' in json_settings or 'output_file' in json_settings:
        log.error(
            'OCR_JSON_SETTINGS (--ocr-json-settings) may not specify input/output file'
        )
        sys.exit(1)

    handler = HandleObserverEvent(
        patterns=patterns.split(','),
        settings={
            'archive_dir': archive_dir,
            'output_dir': output_dir,
            'ocrmypdf_kwargs': json_settings | {'deskew': deskew},
            'on_success_delete': on_success_delete,
            'on_success_archive': on_success_archive,
            'poll_new_file_seconds': poll_new_file_seconds,
            'retries_loading_file': retries_loading_file,
            'output_dir_year_month': output_dir_year_month,
        },
    )
    observer = PollingObserver() if use_polling else Observer()
    observer.schedule(handler, input_dir, recursive=True)
    observer.start()
    print(f"Watching {input_dir} for new PDFs. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    app()
