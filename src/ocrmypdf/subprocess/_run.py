# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Low-level wrappers around :py:mod:`subprocess`.

These functions exist to give OCRmyPDF child processes uniform logging
behavior and to route through any platform-specific PATH fix-ups before
invocation. They are intended as drop-in replacements for
:py:func:`subprocess.run` in contexts where that routing is desirable
(for example, plugin-provided tools).
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, Popen
from subprocess import run as subprocess_run

log = logging.getLogger('ocrmypdf.subprocess')

Args = Sequence[Path | str]
Environ = Mapping[str, str] | os._Environ  # pylint: disable=protected-access


def run(
    args: Args,
    *,
    env: Environ | None = None,
    logs_errors_to_stdout: bool = False,
    check: bool = False,
    **kwargs,
) -> CompletedProcess:
    """Wrapper around :py:func:`subprocess.run`.

    The main purpose of this wrapper is to log subprocess output in an orderly
    fashion that identifies the responsible subprocess. An additional
    task is that this function goes to greater lengths to find possible Windows
    locations of our dependencies when they are not on the system PATH.

    Arguments should be identical to ``subprocess.run``, except for following:

    Args:
        args: Positional arguments to pass to ``subprocess.run``.
        env: A set of environment variables. If None, the OS environment is used.
        logs_errors_to_stdout: If True, indicates that the process writes its error
            messages to stdout rather than stderr, so stdout should be logged
            if there is an error. If False, stderr is logged. Could be used with
            stderr=STDOUT, stdout=PIPE for example.
        check: If True, raise an exception if the process exits with a non-zero
            status code. If False, the return value will indicate success or failure.
        kwargs: Additional arguments to pass to ``subprocess.run``.
    """
    args, env, process_log, _text = _fix_process_args(args, env, kwargs)

    stderr = None
    stderr_name = 'stderr' if not logs_errors_to_stdout else 'stdout'
    try:
        proc = subprocess_run(args, env=env, check=check, **kwargs)
    except CalledProcessError as e:
        stderr = getattr(e, stderr_name, None)
        raise
    else:
        stderr = getattr(proc, stderr_name, None)
    finally:
        if process_log.isEnabledFor(logging.DEBUG) and stderr:
            with suppress(AttributeError, UnicodeDecodeError):
                stderr = stderr.decode('utf-8', 'replace')
            if logs_errors_to_stdout:
                process_log.debug("stdout/stderr = %s", stderr)
            else:
                process_log.debug("stderr = %s", stderr)
    return proc


def run_polling_stderr(
    args: Args,
    *,
    callback: Callable[[str], None],
    check: bool = False,
    env: Environ | None = None,
    **kwargs,
) -> CompletedProcess:
    """Run a process like ``ocrmypdf.subprocess.run``, and poll stderr.

    Every line of produced by stderr will be forwarded to the callback function.
    The intended use is monitoring progress of subprocesses that output their
    own progress indicators. In addition, each line will be logged if debug
    logging is enabled.

    Requires stderr to be opened in text mode for ease of handling errors. In
    addition the expected encoding= and errors= arguments should be set. Note
    that if stdout is already set up, it need not be binary.
    """
    args, env, process_log, text = _fix_process_args(args, env, kwargs)
    assert text, "Must use text=True"

    with Popen(args, env=env, **kwargs) as proc:
        lines = []
        while proc.poll() is None:
            if proc.stderr is None:
                continue
            for msg in iter(proc.stderr.readline, ''):
                if process_log.isEnabledFor(logging.DEBUG):
                    process_log.debug(msg.strip())
                callback(msg)
                lines.append(msg)
        stderr = ''.join(lines)

        if check and proc.returncode != 0:
            raise CalledProcessError(proc.returncode, args, output=None, stderr=stderr)
        return CompletedProcess(args, proc.returncode, None, stderr=stderr)


def _fix_process_args(
    args: Args, env: Environ | None, kwargs
) -> tuple[Args, Environ, logging.Logger, bool]:
    if not env:
        env = os.environ

    # Search in spoof path if necessary
    program = str(args[0])

    if sys.platform == 'win32':
        # pylint: disable=import-outside-toplevel
        from ocrmypdf.subprocess._windows import fix_windows_args

        args = fix_windows_args(program, args, env)

    log.debug("Running: %s", args)
    process_log = log.getChild(os.path.basename(program))
    text = bool(kwargs.get('text', False))

    return args, env, process_log, text
