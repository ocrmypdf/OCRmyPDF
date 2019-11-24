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
import os
import shutil
import sys


class PicklableLoggerMixin:
    def __init__(self):
        self._log = None

    @property
    def log(self):
        if not self._log:
            self._log = self.get_logger()
        return self._log

    def __getstate__(self):
        # Python 3.6 is incapable of pickling a logger and marshalling it to another
        # process (threading._RLock error), so we disconnect it before pickling,
        # and create a new logger in the worker process.
        state = self.__dict__.copy()
        state['_log'] = None
        return state


class PDFContext(PicklableLoggerMixin):
    """Holds our context for a particular run of the pipeline"""

    def __init__(self, options, work_folder, origin, pdfinfo):
        PicklableLoggerMixin.__init__(self)
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

    def get_logger(self):
        return make_logger(self.options, filename=self.name)

    def get_path(self, name):
        return os.path.join(self.work_folder, name)

    def get_page_contexts(self):
        npages = len(self.pdfinfo)
        for n in range(npages):
            yield PageContext(self, n)


class PageContext(PicklableLoggerMixin):
    """Holds our context for a page

    Must be pickable, so only store intrinsic/simple data elements
    """

    def __init__(self, pdf_context, pageno):
        PicklableLoggerMixin.__init__(self)
        self.work_folder = pdf_context.work_folder
        self.origin = pdf_context.origin
        self.options = pdf_context.options
        self.name = pdf_context.name
        self.pageno = pageno
        self.pageinfo = pdf_context.pdfinfo[pageno]
        self._log = None

    def get_logger(self):
        return make_logger(self.options, filename=self.name, page=self.pageno + 1)

    def get_path(self, name):
        return os.path.join(self.work_folder, "%06d_%s" % (self.pageno + 1, name))


def cleanup_working_files(work_folder, options):
    if options.keep_temporary_files:
        print(f"Temporary working files retained at:\n{work_folder}", file=sys.stderr)
    else:
        shutil.rmtree(work_folder, ignore_errors=True)


class LogNameAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        # return '[%s] %s' % (self.extra['input_filename'], msg), kwargs
        return '%s' % (msg,), kwargs


class LogNamePageAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return (
            #'[%s:%05u] %s' % (self.extra['input_filename'], self.extra['page'], msg),
            '%4u: %s' % (self.extra['page'], msg),
            kwargs,
        )


def make_logger(options=None, prefix='ocrmypdf', filename=None, page=None):
    log = logging.getLogger(prefix)
    if filename and page:
        adapter = LogNamePageAdapter(log, dict(input_filename=filename, page=page))
    elif filename:
        adapter = LogNameAdapter(log, dict(input_filename=filename))
    else:
        adapter = log
    return adapter
