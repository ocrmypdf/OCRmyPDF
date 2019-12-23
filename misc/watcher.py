import sys
import time
import os
import ntpath
from pathlib import Path
from datetime import datetime
import ocrmypdf
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, PatternMatchingEventHandler

INPUT_DIRECTORY = os.getenv('OCR_INPUT_DIRECTORY', '/input')
OUTPUT_DIRECTORY = os.getenv('OCR_OUTPUT_DIRECTORY', '/output')
OUTPUT_DIRECTORY_YEAR_MONTH = \
    bool(os.getenv('OCR_OUTPUT_DIRECTORY_YEAR_MONTH', False))
PATTERNS = ['*.pdf']


def execute_ocrmypdf(file_path):
    filename = Path(file_path).name
    if OUTPUT_DIRECTORY_YEAR_MONTH:
        today = datetime.today()
        output_directory_year_month = \
            f'{OUTPUT_DIRECTORY}/{today.year}/{today.month}'
        if not Path(output_directory_year_month).exists():
            Path(output_directory_year_month).mkdir(parents=True, exist_ok=True)
        output_path = f'{output_directory_year_month}/{filename}'
    else:
        output_path = f'{OUTPUT_DIRECTORY}/{filename}'
    print(f'New file: {file_path}.\nAttempting to OCRmyPDF to: {output_path}')
    ocrmypdf.ocr(
        file_path,
        output_path
    )


class HandleObserverEvent(PatternMatchingEventHandler):
    def on_any_event(self, event):
        if event.event_type in ['created', 'modified']:
            execute_ocrmypdf(event.src_path)


if __name__ == "__main__":
    print(f"Starting OCRmyPDF watcher with config:\n"
          f"Input Directory: {INPUT_DIRECTORY}\n"
          f"Output Directory: {OUTPUT_DIRECTORY}\n"
          f"Output Directory Year & Month: {OUTPUT_DIRECTORY_YEAR_MONTH}")
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
