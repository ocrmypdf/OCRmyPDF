# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Logging support classes."""

from __future__ import annotations

import logging
from contextlib import suppress

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
