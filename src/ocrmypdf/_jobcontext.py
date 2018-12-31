# © 2018 James R. Barlow: github.com/jbarlow83
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

import shutil
import sys
from contextlib import suppress
from multiprocessing.managers import SyncManager

from .pdfinfo import PdfInfo


class JobContext:
    """Holds our context for a particular run of the pipeline

    A multiprocessing manager effectively creates a separate process
    that keeps the master job context object.  Other threads access
    job context via multiprocessing proxy objects.

    While this would naturally lend itself @property's it seems to make
    a little more sense to use functions to make it explicitly that the
    invocation requires marshalling data across a process boundary.

    """

    def __init__(self):
        self.pdfinfo = None
        self.options = None
        self.work_folder = None
        self.rotations = {}

    def generate_pdfinfo(self, infile):
        self.pdfinfo = PdfInfo(infile)

    def get_pdfinfo(self):
        "What we know about the input PDF"
        return self.pdfinfo

    def set_pdfinfo(self, pdfinfo):
        self.pdfinfo = pdfinfo

    def get_options(self):
        return self.options

    def set_options(self, options):
        self.options = options

    def get_work_folder(self):
        return self.work_folder

    def set_work_folder(self, work_folder):
        self.work_folder = work_folder

    def get_rotation(self, pageno):
        return self.rotations.get(pageno, 0)

    def set_rotation(self, pageno, value):
        self.rotations[pageno] = value


class JobContextManager(SyncManager):
    pass


def cleanup_working_files(work_folder, options):
    if options.keep_temporary_files:
        print(f"Temporary working files saved at:\n{work_folder}", file=sys.stderr)
    else:
        with suppress(FileNotFoundError):
            shutil.rmtree(work_folder)
