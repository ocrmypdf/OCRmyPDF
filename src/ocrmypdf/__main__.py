#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""ocrmypdf command line entrypoint."""

from __future__ import annotations

import logging
import multiprocessing
import os
import signal
import sys
from contextlib import suppress

from ocrmypdf import __version__
from ocrmypdf._pipelines.ocr import run_pipeline_cli
from ocrmypdf._plugin_manager import get_parser_options_plugins
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
    """Handle SIGBUS signals.

    pikepdf, depending on configuration, may use mmap so SIGBUS is a
    possibility.
    """
    raise InputFileError("Lost access to the input file")


def run(args=None):
    """Run the ocrmypdf command line interface."""
    _parser, options, plugin_manager = get_parser_options_plugins(args=args)

    with suppress(AttributeError, PermissionError):
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

    with suppress(AttributeError, OSError):
        signal.signal(signal.SIGBUS, sigbus)

    result = run_pipeline_cli(options=options, plugin_manager=plugin_manager)
    return result


if __name__ == '__main__':
    multiprocessing.freeze_support()
    if os.name == 'posix':
        multiprocessing.set_start_method('forkserver')
    sys.exit(run())
