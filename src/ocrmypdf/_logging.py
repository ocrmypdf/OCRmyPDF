# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Logging support classes."""

from __future__ import annotations

import logging

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


class PageNumberFilter(logging.Filter):
    """Insert PDF page number that emitted log message to log record."""

    def filter(self, record):
        pageno = getattr(record, 'pageno', None)
        if isinstance(pageno, int):
            record.pageno = f'{pageno:5d} '
        elif pageno is None:
            record.pageno = ''
        return True


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
            desc,
            total=total * self.unit_scale
            if total is not None and self.unit_scale is not None
            else None,
            unit=unit,
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
