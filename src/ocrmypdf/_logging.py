# © 2020 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import logging
import sys
from contextlib import suppress

from tqdm import tqdm


class PageNumberFilter(logging.Filter):
    def filter(self, record):
        pageno = getattr(record, 'pageno', None)
        if pageno is not None:
            record.pageno = f'{pageno:5d} '
        else:
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
