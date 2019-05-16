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

import logging
import shutil
import sys
import os
from contextlib import suppress


class PDFContext:
    """Holds our context for a particular run of the pipeline"""

    def __init__(self, options, work_folder, origin, pdfinfo):
        self.options = options
        self.work_folder = work_folder
        self.origin = origin
        self.pdfinfo = pdfinfo
        if options:
            self.name = os.path.basename(options.input_file)
        else:
            self.name = 'origin.pdf'
        if self.name == '-':
            self.name = 'stdin'
        self.log = get_logger(options, filename=self.name)

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
        self.log = get_logger(
            pdf_context.options, filename=self.pdf_context.name, page=(self.pageno + 1)
        )

    def get_path(self, name):
        return os.path.join(
            self.pdf_context.work_folder, "%06d_%s" % (self.pageno + 1, name)
        )


def cleanup_working_files(work_folder, options):
    if options.keep_temporary_files:
        print(f"Temporary working files saved at:\n{work_folder}", file=sys.stderr)
    else:
        with suppress(FileNotFoundError):
            shutil.rmtree(work_folder)


class LogNameAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        # return '[%s] %s' % (self.extra['filename'], msg), kwargs
        return '%s' % (msg,), kwargs


class LogNamePageAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return (
            #'[%s:%05u] %s' % (self.extra['filename'], self.extra['page'], msg),
            '%4u: %s' % (self.extra['page'], msg),
            kwargs,
        )


def get_logger(options=None, prefix='ocrmypdf', filename=None, page=None):
    log = logging.getLogger(prefix)
    if filename and page:
        adapter = LogNamePageAdapter(log, dict(filename=filename, page=page))
    elif filename:
        adapter = LogNameAdapter(log, dict(filename=filename))
    else:
        adapter = log
    adapter.setLevel(logging.DEBUG)
    return adapter
