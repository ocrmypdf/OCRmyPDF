# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Logging support classes."""

from __future__ import annotations

import logging
from contextlib import suppress

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Column
from tqdm import tqdm


class PageNumberFilter(logging.Filter):
    """Insert PDF page number that emitted log message to log record."""

    def filter(self, record):
        pageno = getattr(record, 'pageno', None)
        if isinstance(pageno, int):
            record.pageno = f'{pageno:5d} '
        elif pageno is None:
            record.pageno = ''
        return True


class TqdmConsole:
    """Wrapper to log messages in a way that is compatible with tqdm progress bar.

    This routes log messages through tqdm so that it can print them above the
    progress bar, and then refresh the progress bar, rather than overwriting
    it which looks messy.
    """

    def __init__(self, file):
        self.file = file

    def write(self, msg):
        # When no progress bar is active, tqdm.write() routes to print()
        tqdm.write(msg.rstrip(), end='\n', file=self.file)

    def flush(self):
        with suppress(AttributeError):
            self.file.flush()


class RichLoggingHandler(RichHandler):
    def __init__(self, console: Console, **kwargs):
        super().__init__(
            console=console, show_level=False, show_time=False, markup=True, **kwargs
        )


class RichTqdmProgressAdapter:
    """Adapt tqdm API to rich progress bar."""

    def __init__(
        self,
        *,
        console: Console,
        desc: str,
        total: float | None = None,
        unit: str | None = None,
        unit_scale: float | None = 1.0,
        disable: bool = False,
        **kwargs,
    ):
        self.progress = Progress(
            TextColumn(
                "[progress.description]{task.description}",
                table_column=Column(min_width=20),
            ),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
            auto_refresh=True,
            redirect_stderr=True,
            redirect_stdout=False,
            disable=disable,
            **kwargs,
        )
        self.unit_scale = unit_scale
        self.progress_bar = self.progress.add_task(
            desc, total=total * self.unit_scale, unit=unit
        )

    def __enter__(self):
        self.progress.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.progress.refresh()
        self.progress.stop()
        return False

    def update(self, value=None):
        advance = self.unit_scale if value is None else value
        self.progress.update(self.progress_bar, advance=advance)
