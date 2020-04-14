# Copyright (C) 2019 Ian Alexander: https://github.com/ianalexander
# Copyright (C) 2020 James R Barlow: https://github.com/jbarlow83
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pikepdf
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import ocrmypdf

# pylint: disable=logging-format-interpolation

INPUT_DIRECTORY = os.getenv('OCR_INPUT_DIRECTORY', '/input')
OUTPUT_DIRECTORY = os.getenv('OCR_OUTPUT_DIRECTORY', '/output')
OUTPUT_DIRECTORY_YEAR_MONTH = bool(os.getenv('OCR_OUTPUT_DIRECTORY_YEAR_MONTH', False))
ON_SUCCESS_DELETE = bool(os.getenv('OCR_ON_SUCCESS_DELETE', False))
DESKEW = bool(os.getenv('OCR_DESKEW', False))
OCR_JSON_SETTINGS = json.loads(os.getenv('OCR_JSON_SETTINGS', '{}'))
POLL_NEW_FILE_SECONDS = os.getenv('OCR_POLL_NEW_FILE_SECONDS', 1)
LOGLEVEL = os.environ.get('OCR_LOGLEVEL', 'INFO').upper()
PATTERNS = ['*.pdf']

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
    if exit_code == 0 and ON_SUCCESS_DELETE:
        os.chmod(output_path, 0o664)
        log.info(f'OCR is done. Deleting: {file_path}')
        file_path.unlink()
    else:
        log.info('OCR is done')


class HandleObserverEvent(PatternMatchingEventHandler):
    def on_any_event(self, event):
        if event.event_type in ['created']:
            execute_ocrmypdf(event.src_path)


def main():
    ocrmypdf.configure_logging(
        verbosity=ocrmypdf.Verbosity.default, manage_root_logger=True
    )
    log.info(
        f"Starting OCRmyPDF watcher with config:\n"
        f"Input Directory: {INPUT_DIRECTORY}\n"
        f"Output Directory: {OUTPUT_DIRECTORY}\n"
        f"Output Directory Year & Month: {OUTPUT_DIRECTORY_YEAR_MONTH}"
    )
    log.debug(
        f"INPUT_DIRECTORY: {INPUT_DIRECTORY}\n"
        f"OUTPUT_DIRECTORY: {OUTPUT_DIRECTORY}\n"
        f"OUTPUT_DIRECTORY_YEAR_MONTH: {OUTPUT_DIRECTORY_YEAR_MONTH}\n"
        f"ON_SUCCESS_DELETE: {ON_SUCCESS_DELETE}\n"
        f"DESKEW: {DESKEW}\n"
        f"ARGS: {OCR_JSON_SETTINGS}\n"
        f"POLL_NEW_FILE_SECONDS: {POLL_NEW_FILE_SECONDS}\n"
        f"LOGLEVEL: {LOGLEVEL}\n"
    )

    if 'input_file' in OCR_JSON_SETTINGS or 'output_file' in OCR_JSON_SETTINGS:
        log.error('OCR_JSON_SETTINGS should not specify input file or output file')
        sys.exit(1)

    handler = HandleObserverEvent(patterns=PATTERNS)
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
