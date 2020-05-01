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


class PDFContext:
    """Holds our context for a particular run of the pipeline"""

    def __init__(self, options, work_folder, origin, pdfinfo, plugin_manager):
        self.options = options
        self.work_folder = work_folder
        self.origin = origin
        self.pdfinfo = pdfinfo
        self.plugin_manager = plugin_manager
        if options:
            self.name = os.path.basename(options.input_file)
        else:
            self.name = 'origin.pdf'
        if self.name == '-':
            self.name = 'stdin'

    def get_path(self, name):
        return os.path.join(self.work_folder, name)

    def get_page_contexts(self):
        npages = len(self.pdfinfo)
        for n in range(npages):
            yield PageContext(self, n)


class PageContext:
    """Holds our context for a page

    Must be pickable, so only store intrinsic/simple data elements
    """

    def __init__(self, pdf_context, pageno):
        self.work_folder = pdf_context.work_folder
        self.origin = pdf_context.origin
        self.options = pdf_context.options
        self.name = pdf_context.name
        self.pageno = pageno
        self.pageinfo = pdf_context.pdfinfo[pageno]

    def get_path(self, name):
        return os.path.join(self.work_folder, "%06d_%s" % (self.pageno + 1, name))


def cleanup_working_files(work_folder, options):
    if options.keep_temporary_files:
        print(f"Temporary working files retained at:\n{work_folder}", file=sys.stderr)
    else:
        shutil.rmtree(work_folder, ignore_errors=True)
