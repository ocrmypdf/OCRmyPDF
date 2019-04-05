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
import os
from contextlib import suppress

ERROR = 40
WARN = 30
INFO = 20
DEBUG = 10


class PDFContext:
    """Holds our context for a particular run of the pipeline"""

    def __init__(self, options, work_folder, origin, pdfinfo):
        self.options = options
        self.work_folder = work_folder
        self.origin = origin
        self.pdfinfo = pdfinfo
        self.log = get_logger(options, '%s: ' % os.path.basename(origin))

    def get_path(self, name):
        return os.path.join(self.work_folder, name)

    def get_page_contexts(self):
        npages = len(self.pdfinfo)
        for n in range(npages):
            yield PageContext(self, n)


class PageContext:
    """Holds our context for a page"""

    def __init__(self, pdf_context, pageno):
        self.pdf_context = pdf_context
        self.options = pdf_context.options
        self.pageno = pageno
        self.pageinfo = pdf_context.pdfinfo[pageno]
        self.log = get_logger(pdf_context.options, '%s Page %d: ' % (os.path.basename(pdf_context.origin), pageno + 1))

    def get_path(self, name):
        return os.path.join(self.pdf_context.work_folder, "%06d_%s" % (self.pageno + 1, name))


def cleanup_working_files(work_folder, options):
    if options.keep_temporary_files:
        print(f"Temporary working files saved at:\n{work_folder}", file=sys.stderr)
    else:
        with suppress(FileNotFoundError):
            shutil.rmtree(work_folder)


def get_logger(options=None, prefix=''):
    level = ERROR  # TODO: add option
    if options is not None and options.output_file == '-' or options.sidecar == '-':
        return NullLogger()
    return Logger(prefix, level)


class Logger:
    def __init__(self, prefix, level=DEBUG):
        self.prefix = prefix
        self.level = level

    def debug(self, *args, **kwargs):
        if self.level <= DEBUG:
            print('DEBUG', self.prefix, end='')
            print(*args, **kwargs)

    def info(self, *args, **kwargs):
        if self.level <= INFO:
            print('INFO', self.prefix, end='')
            print(*args, **kwargs)

    def warning(self, *args, **kwargs):
        self.warn(*args, **kwargs)

    def warn(self, *args, **kwargs):
        if self.level <= WARN:
            print('WARN', self.prefix, end='')
            print(*args, **kwargs)

    def error(self, *args, **kwargs):
        if self.level <= ERROR:
            print('ERROR', self.prefix, end='')
            print(*args, **kwargs)


class NullLogger:
    def debug(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def warn(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass
