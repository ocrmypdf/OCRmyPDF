# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Logging support classes."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler


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
