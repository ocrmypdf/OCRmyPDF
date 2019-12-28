# Copyright (C) 2019 Ian Alexander: https://github.com/ianalexander
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

import os
import time
from datetime import datetime
from pathlib import Path

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import ocrmypdf

INPUT_DIRECTORY = os.getenv('OCR_INPUT_DIRECTORY', '/input')
OUTPUT_DIRECTORY = os.getenv('OCR_OUTPUT_DIRECTORY', '/output')
OUTPUT_DIRECTORY_YEAR_MONTH = bool(os.getenv('OCR_OUTPUT_DIRECTORY_YEAR_MONTH', False))
PATTERNS = ['*.pdf']


def execute_ocrmypdf(file_path):
    filename = Path(file_path).name
    if OUTPUT_DIRECTORY_YEAR_MONTH:
        today = datetime.today()
        output_directory_year_month = Path(
            f'{OUTPUT_DIRECTORY}/{today.year}/{today.month}'
        )
        if not output_directory_year_month.exists():
            output_directory_year_month.mkdir(parents=True, exist_ok=True)
        output_path = Path(output_directory_year_month) / filename
    else:
        output_path = Path(OUTPUT_DIRECTORY) / filename
    print(f'New file: {file_path}.\nAttempting to OCRmyPDF to: {output_path}')
    ocrmypdf.ocr(file_path, output_path)


class HandleObserverEvent(PatternMatchingEventHandler):
    def on_any_event(self, event):
        if event.event_type in ['created', 'modified']:
            execute_ocrmypdf(event.src_path)


if __name__ == "__main__":
    print(
        f"Starting OCRmyPDF watcher with config:\n"
        f"Input Directory: {INPUT_DIRECTORY}\n"
        f"Output Directory: {OUTPUT_DIRECTORY}\n"
        f"Output Directory Year & Month: {OUTPUT_DIRECTORY_YEAR_MONTH}"
    )
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
