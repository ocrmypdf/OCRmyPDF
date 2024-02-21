#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2019 Ian Alexander <https://github.com/ianalexander>
# SPDX-FileCopyrightText: 2020 James R Barlow <https://github.com/jbarlow83>
# SPDX-License-Identifier: MIT

"""Watch a directory for new PDFs and OCR them."""

# Do not enable annotations!
# https://github.com/tiangolo/typer/discussions/598

import json
import logging
import shutil
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import pikepdf
import typer
from dotenv import load_dotenv
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

import ocrmypdf

load_dotenv()


# pylint: disable=logging-format-interpolation
app = typer.Typer(name="ocrmypdf-watcher")

log = logging.getLogger('ocrmypdf-watcher')


class LoggingLevelEnum(str, Enum):
    """Enum for logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def get_output_dir(root: Path, basename: str, output_dir_year_month: bool) -> Path:
    if output_dir_year_month:
        today = datetime.today()
        output_directory_year_month = root / str(today.year) / f'{today.month:02d}'
        if not output_directory_year_month.exists():
            output_directory_year_month.mkdir(parents=True, exist_ok=True)
        output_path = Path(output_directory_year_month) / basename
    else:
        output_path = root / basename
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
    output_path = get_output_dir(output_dir, file_path.name, output_dir_year_month)

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
        input_file=file_path,
        output_file=output_path,
        **ocrmypdf_kwargs,
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
        settings={},
    ):
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self._settings = settings

    def on_any_event(self, event):
        if event.event_type in ['created']:
            execute_ocrmypdf(file_path=Path(event.src_path), **self._settings)


@app.command()
def main(
    input_dir: Annotated[
        Path,
        typer.Argument(
            envvar='OCR_INPUT_DIRECTORY',
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ] = '/input',
    output_dir: Annotated[
        Path,
        typer.Argument(
            envvar='OCR_OUTPUT_DIRECTORY',
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = '/output',
    archive_dir: Annotated[
        Path,
        typer.Argument(
            envvar='OCR_ARCHIVE_DIRECTORY',
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = '/processed',
    output_dir_year_month: Annotated[
        bool,
        typer.Option(
            envvar='OCR_OUTPUT_DIRECTORY_YEAR_MONTH',
            help='Create a subdirectory in the output directory for each year/month',
        ),
    ] = False,
    on_success_delete: Annotated[
        bool,
        typer.Option(
            envvar='OCR_ON_SUCCESS_DELETE',
            help='Delete the input file after successful OCR',
        ),
    ] = False,
    on_success_archive: Annotated[
        bool,
        typer.Option(
            envvar='OCR_ON_SUCCESS_ARCHIVE',
            help='Archive the input file after successful OCR',
        ),
    ] = False,
    deskew: Annotated[
        bool,
        typer.Option(
            envvar='OCR_DESKEW',
            help='Deskew the input file before OCR',
        ),
    ] = False,
    ocr_json_settings: Annotated[
        str,
        typer.Option(
            envvar='OCR_JSON_SETTINGS',
            help='JSON settings to pass to OCRmyPDF (JSON string or file path)',
        ),
    ] = None,
    poll_new_file_seconds: Annotated[
        int,
        typer.Option(
            envvar='OCR_POLL_NEW_FILE_SECONDS',
            help='Seconds to wait before polling a new file',
            min=0,
        ),
    ] = 1,
    use_polling: Annotated[
        bool,
        typer.Option(
            envvar='OCR_USE_POLLING',
            help='Use polling instead of filesystem events',
        ),
    ] = False,
    retries_loading_file: Annotated[
        int,
        typer.Option(
            envvar='OCR_RETRIES_LOADING_FILE',
            help='Number of times to retry loading a file before giving up',
            min=0,
        ),
    ] = 5,
    loglevel: Annotated[
        LoggingLevelEnum,
        typer.Option(
            envvar='OCR_LOGLEVEL',
            help='Logging level',
        ),
    ] = LoggingLevelEnum.INFO,
    patterns: Annotated[
        str,
        typer.Option(
            envvar='OCR_PATTERNS',
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
    log.debug(
        f"INPUT_DIRECTORY: {input_dir}\n"
        f"OUTPUT_DIRECTORY: {output_dir}\n"
        f"OUTPUT_DIRECTORY_YEAR_MONTH: {output_dir_year_month}\n"
        f"ARCHIVE_DIRECTORY: {archive_dir}\n"
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
    if use_polling:
        observer = PollingObserver()
    else:
        observer = Observer()
    observer.schedule(handler, input_dir, recursive=True)
    observer.start()
    typer.echo(f"Watching {input_dir} for new PDFs. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    app()
