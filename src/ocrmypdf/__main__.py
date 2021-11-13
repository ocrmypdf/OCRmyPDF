#!/usr/bin/env python3
# © 2015-19 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import os
import signal
import sys
from multiprocessing import set_start_method

from ocrmypdf import __version__
from ocrmypdf._plugin_manager import get_parser_options_plugins
from ocrmypdf._sync import run_pipeline
from ocrmypdf._validation import check_options
from ocrmypdf.api import Verbosity, configure_logging
from ocrmypdf.exceptions import (
    BadArgsError,
    ExitCode,
    InputFileError,
    MissingDependencyError,
)

log = logging.getLogger('ocrmypdf')


def sigbus(*args):
    raise InputFileError("Lost access to the input file")


def run(args=None):
    _parser, options, plugin_manager = get_parser_options_plugins(args=args)

    if hasattr(os, 'nice'):
        os.nice(5)

    verbosity = options.verbose
    if not os.isatty(sys.stderr.fileno()):
        options.progress_bar = False
    if options.quiet:
        verbosity = Verbosity.quiet
        options.progress_bar = False
    configure_logging(
        verbosity,
        progress_bar_friendly=options.progress_bar,
        manage_root_logger=True,
        plugin_manager=plugin_manager,
    )
    log.debug('ocrmypdf %s', __version__)
    try:
        check_options(options, plugin_manager)
    except ValueError as e:
        log.error(e)
        return ExitCode.bad_args
    except BadArgsError as e:
        log.error(e)
        return e.exit_code
    except MissingDependencyError as e:
        log.error(e)
        return ExitCode.missing_dependency

    if hasattr(signal, 'SIGBUS'):
        signal.signal(signal.SIGBUS, sigbus)

    result = run_pipeline(options=options, plugin_manager=plugin_manager)
    return result


if __name__ == '__main__':
    if sys.platform == 'darwin' and sys.version_info < (3, 8):
        set_start_method('spawn')  # see python bpo-33725
    sys.exit(run())
