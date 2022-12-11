#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2019 Ian Alexander <https://github.com/ianalexander>
# SPDX-FileCopyrightText: 2020 James R Barlow <https://github.com/jbarlow83>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import pikepdf
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

import ocrmypdf

# pylint: disable=logging-format-interpolation


def getenv_bool(name: str, default: str = 'False'):
    return os.getenv(name, default).lower() in ('true', 'yes', 'y', '1')


INPUT_DIRECTORY = os.getenv('OCR_INPUT_DIRECTORY', '/input')
OUTPUT_DIRECTORY = os.getenv('OCR_OUTPUT_DIRECTORY', '/output')
ARCHIVE_DIRECTORY = os.getenv('OCR_ARCHIVE_DIRECTORY', '/processed')
OUTPUT_DIRECTORY_YEAR_MONTH = getenv_bool('OCR_OUTPUT_DIRECTORY_YEAR_MONTH')
ON_SUCCESS_DELETE = getenv_bool('OCR_ON_SUCCESS_DELETE')
ON_SUCCESS_ARCHIVE = getenv_bool('OCR_ON_SUCCESS_ARCHIVE')
DESKEW = getenv_bool('OCR_DESKEW')
OCR_JSON_SETTINGS = json.loads(os.getenv('OCR_JSON_SETTINGS', '{}'))
POLL_NEW_FILE_SECONDS = int(os.getenv('OCR_POLL_NEW_FILE_SECONDS', '1'))
USE_POLLING = getenv_bool('OCR_USE_POLLING')
LOGLEVEL = os.getenv('OCR_LOGLEVEL', 'INFO')
PATTERNS = ['*.pdf', '*.PDF']

log = logging.getLogger('ocrmypdf-watcher')


def get_output_dir(root, basename):
    if OUTPUT_DIRECTORY_YEAR_MONTH:
        today = datetime.today()
        output_directory_year_month = (
            Path(root) / str(today.year) / f'{today.month:02d}'
        )
        if not output_directory_year_month.exists():
            output_directory_year_month.mkdir(parents=True, exist_ok=True)
        output_path = Path(output_directory_year_month) / basename
    else:
        output_path = Path(OUTPUT_DIRECTORY) / basename
    return output_path


def wait_for_file_ready(file_path):
    # This loop waits to make sure that the file is completely loaded on
    # disk before attempting to read. Docker sometimes will publish the
    # watchdog event before the file is actually fully on disk, causing
    # pikepdf to fail.

    retries = 5
    while retries:
        try:
            pdf = pikepdf.open(file_path)
        except (FileNotFoundError, pikepdf.PdfError) as e:
            log.info(f"File {file_path} is not ready yet")
            log.debug("Exception was", exc_info=e)
            time.sleep(POLL_NEW_FILE_SECONDS)
            retries -= 1
        else:
            pdf.close()
            return True

    return False


def execute_ocrmypdf(file_path):
    file_path = Path(file_path)
    output_path = get_output_dir(OUTPUT_DIRECTORY, file_path.name)

    log.info("-" * 20)
    log.info(f'New file: {file_path}. Waiting until fully loaded...')
    if not wait_for_file_ready(file_path):
        log.info(f"Gave up waiting for {file_path} to become ready")
        return
    log.info(f'Attempting to OCRmyPDF to: {output_path}')
    exit_code = ocrmypdf.ocr(
        input_file=file_path,
        output_file=output_path,
        deskew=DESKEW,
        **OCR_JSON_SETTINGS,
    )
    if exit_code == 0:
        if ON_SUCCESS_DELETE:
            log.info(f'OCR is done. Deleting: {file_path}')
            file_path.unlink()
        elif ON_SUCCESS_ARCHIVE:
            log.info(f'OCR is done. Archiving {file_path.name} to {ARCHIVE_DIRECTORY}')
            shutil.move(file_path, f'{ARCHIVE_DIRECTORY}/{file_path.name}')
        else:
            log.info('OCR is done')
    else:
        log.info('OCR is done')


class HandleObserverEvent(PatternMatchingEventHandler):
    def on_any_event(self, event):
        if event.event_type in ['created']:
            execute_ocrmypdf(event.src_path)


def main():
    ocrmypdf.configure_logging(
        verbosity=(
            ocrmypdf.Verbosity.default
            if LOGLEVEL != 'DEBUG'
            else ocrmypdf.Verbosity.debug
        ),
        manage_root_logger=True,
    )
    log.setLevel(LOGLEVEL)
    log.info(
        f"Starting OCRmyPDF watcher with config:\n"
        f"Input Directory: {INPUT_DIRECTORY}\n"
        f"Output Directory: {OUTPUT_DIRECTORY}\n"
        f"Output Directory Year & Month: {OUTPUT_DIRECTORY_YEAR_MONTH}\n"
        f"Archive Directory: {ARCHIVE_DIRECTORY}"
    )
    log.debug(
        f"INPUT_DIRECTORY: {INPUT_DIRECTORY}\n"
        f"OUTPUT_DIRECTORY: {OUTPUT_DIRECTORY}\n"
        f"OUTPUT_DIRECTORY_YEAR_MONTH: {OUTPUT_DIRECTORY_YEAR_MONTH}\n"
        f"ARCHIVE_DIRECTORY: {ARCHIVE_DIRECTORY}\n"
        f"ON_SUCCESS_DELETE: {ON_SUCCESS_DELETE}\n"
        f"ON_SUCCESS_ARCHIVE: {ON_SUCCESS_ARCHIVE}\n"
        f"DESKEW: {DESKEW}\n"
        f"ARGS: {OCR_JSON_SETTINGS}\n"
        f"POLL_NEW_FILE_SECONDS: {POLL_NEW_FILE_SECONDS}\n"
        f"USE_POLLING: {USE_POLLING}\n"
        f"LOGLEVEL: {LOGLEVEL}"
    )

    if 'input_file' in OCR_JSON_SETTINGS or 'output_file' in OCR_JSON_SETTINGS:
        log.error('OCR_JSON_SETTINGS should not specify input file or output file')
        sys.exit(1)

    handler = HandleObserverEvent(patterns=PATTERNS)
    if USE_POLLING:
        observer = PollingObserver()
    else:
        observer = Observer()
    observer.schedule(handler, INPUT_DIRECTORY, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
