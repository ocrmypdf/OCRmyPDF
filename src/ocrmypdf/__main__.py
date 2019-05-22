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

from . import __version__
from .cli import parser
from .api import configure_logging
from ._jobcontext import make_logger
from ._sync import run_pipeline
from ._validation import check_closed_streams, check_options
from .exceptions import ExitCode, BadArgsError, MissingDependencyError


def main(args=None):
    options = parser.parse_args(args=args)

    if not check_closed_streams(options):
        return ExitCode.bad_args

    if os.environ.get('PYTEST_CURRENT_TEST'):
        os.environ['_OCRMYPDF_TEST_INFILE'] = options.input_file
    if hasattr(os, 'nice'):
        os.nice(5)

    verbosity = options.verbose
    if options.quiet:
        verbosity = -1
        options.progress_bar = False
    configure_logging(
        verbosity, progress_bar_friendly=options.progress_bar, manage_root_logger=True
    )
    log = make_logger('ocrmypdf')
    log.debug('ocrmypdf ' + __version__)
    try:
        check_options(options)
    except ValueError as e:
        log.error(e)
        return ExitCode.bad_args
    except BadArgsError as e:
        log.error(e)
        return e.exit_code
    except MissingDependencyError as e:
        log.error(e)
        return ExitCode.missing_dependency

    result = run_pipeline(options=options)
    return result


if __name__ == '__main__':
    sys.exit(main())
