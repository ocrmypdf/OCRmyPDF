# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import sys
from contextlib import suppress

from tqdm import tqdm


class PageNumberFilter(logging.Filter):
    def filter(self, record):
        pageno = getattr(record, 'pageno', None)
        if isinstance(pageno, int):
            record.pageno = f'{pageno:5d} '
        elif pageno is None:
            record.pageno = ''
        return True


class TqdmConsole:
    """Wrapper to log messages in a way that is compatible with tqdm progress bar

    This routes log messages through tqdm so that it can print them above the
    progress bar, and then refresh the progress bar, rather than overwriting
    it which looks messy.

    For some reason Python 3.6 prints extra empty messages from time to time,
    so we suppress those.
    """

    def __init__(self, file):
        self.file = file
        self.py36 = sys.version_info[0:2] == (3, 6)

    def write(self, msg):
        # When no progress bar is active, tqdm.write() routes to print()
        if self.py36:
            if msg.strip() != '':
                tqdm.write(msg.rstrip(), end='\n', file=self.file)
        else:
            tqdm.write(msg.rstrip(), end='\n', file=self.file)

    def flush(self):
        with suppress(AttributeError):
            self.file.flush()
