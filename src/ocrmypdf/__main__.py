#!/usr/bin/env python3
# © 2015-19 James R. Barlow: github.com/jbarlow83
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
import sys

from .cli import parser
from .api import configure_logging, run as api_run
from ._validation import check_closed_streams
from .exceptions import ExitCode


def run(args=None):
    options = parser.parse_args(args=args)

    if not check_closed_streams(options):
        return ExitCode.bad_args

    if os.environ.get('PYTEST_CURRENT_TEST'):
        os.environ['_OCRMYPDF_TEST_INFILE'] = options.input_file
    if hasattr(os, 'nice'):
        os.nice(5)

    configure_logging(options, manage_root_logger=True)
    result = api_run(options=options)
    return result


if __name__ == '__main__':
    sys.exit(run())
