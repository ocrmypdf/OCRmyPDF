# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Wrappers to manage subprocess calls"""

import logging
import os
import re
import sys
from collections.abc import Mapping
from contextlib import suppress
from distutils.version import LooseVersion, Version
from functools import lru_cache
from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError, CompletedProcess, Popen
from subprocess import run as subprocess_run
from typing import Callable, Optional, Type, Union

from ocrmypdf.exceptions import MissingDependencyError

# pylint: disable=logging-format-interpolation

log = logging.getLogger(__name__)


def run(args, *, env=None, logs_errors_to_stdout=False, **kwargs):
    """Wrapper around :py:func:`subprocess.run`

    The main purpose of this wrapper is to log subprocess output in an orderly
    fashion that indentifies the responsible subprocess. An additional
    task is that this function goes to greater lengths to find possible Windows
    locations of our dependencies when they are not on the system PATH.

    Arguments should be identical to ``subprocess.run``, except for following:

    Arguments:
        logs_errors_to_stdout: If True, indicates that the process writes its error
            messages to stdout rather than stderr, so stdout should be logged
            if there is an error. If False, stderr is logged. Could be used with
            stderr=STDOUT, stdout=PIPE for example.
    """
    args, env, process_log, _text = _fix_process_args(args, env, kwargs)

    stderr = None
    stderr_name = 'stderr' if not logs_errors_to_stdout else 'stdout'
    try:
        proc = subprocess_run(args, env=env, **kwargs)
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


def run_polling_stderr(args, *, callback, check=False, env=None, **kwargs):
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
            for msg in iter(proc.stderr.readline, ''):
                if process_log.isEnabledFor(logging.DEBUG):
                    process_log.debug(msg.strip())
                callback(msg)
                lines.append(msg)
        stderr = ''.join(lines)

        if check and proc.returncode != 0:
            raise CalledProcessError(proc.returncode, args, output=None, stderr=stderr)
        return CompletedProcess(args, proc.returncode, None, stderr=stderr)


def _fix_process_args(args, env, kwargs):
    assert 'universal_newlines' not in kwargs, "Use text= instead of universal_newlines"

    if not env:
        env = os.environ

    # Search in spoof path if necessary
    program = args[0]

    if os.name == 'nt':
        from ocrmypdf.subprocess._windows import fix_windows_args

        args = fix_windows_args(program, args, env)

    log.debug("Running: %s", args)
    process_log = log.getChild(os.path.basename(program))
    text = kwargs.get('text', False)
    if sys.version_info < (3, 7):
        if os.name == 'nt':
            # Can't use close_fds=True on Windows with Python 3.6 or older
            # https://bugs.python.org/issue19575, etc.
            kwargs['close_fds'] = False
        if 'text' in kwargs:
            # Convert run(...text=) to run(...universal_newlines=) for Python 3.6
            kwargs['universal_newlines'] = kwargs['text']
            del kwargs['text']
    return args, env, process_log, text


@lru_cache(maxsize=None)
def get_version(
    program: str, *, version_arg: str = '--version', regex=r'(\d+(\.\d+)*)', env=None
):
    """Get the version of the specified program

    Arguments:
        program: The program to version check.
        version_arg: The argument needed to ask for its version, e.g. ``--version``.
        regex: A regular expression to parse the program's output and obtain the
            version.
        env: Custom ``os.environ`` in which to run program.
    """
    args_prog = [program, version_arg]
    try:
        proc = run(
            args_prog,
            close_fds=True,
            text=True,
            stdout=PIPE,
            stderr=STDOUT,
            check=True,
            env=env,
        )
        output = proc.stdout
    except FileNotFoundError as e:
        raise MissingDependencyError(
            f"Could not find program '{program}' on the PATH"
        ) from e
    except CalledProcessError as e:
        if e.returncode != 0:
            raise MissingDependencyError(
                f"Ran program '{program}' but it exited with an error:\n{e.output}"
            ) from e
        raise MissingDependencyError(
            f"Could not find program '{program}' on the PATH"
        ) from e

    match = re.match(regex, output.strip())
    if not match:
        raise MissingDependencyError(
            f"The program '{program}' did not report its version. "
            f"Message was:\n{output}"
        )
    version = match.group(1)

    return version


missing_program = '''
The program '{program}' could not be executed or was not found on your
system PATH.
'''

missing_optional_program = '''
The program '{program}' could not be executed or was not found on your
system PATH.  This program is required when you use the
{required_for} arguments.  You could try omitting these arguments, or install
the package.
'''

missing_recommend_program = '''
The program '{program}' could not be executed or was not found on your
system PATH.  This program is recommended when using the {required_for} arguments,
but not required, so we will proceed.  For best results, install the program.
'''

old_version = '''
OCRmyPDF requires '{program}' {need_version} or higher.  Your system appears
to have {found_version}.  Please update this program.
'''

old_version_required_for = '''
OCRmyPDF requires '{program}' {need_version} or higher when run with the
{required_for} arguments.  If you omit these arguments, OCRmyPDF may be able to
proceed.  For best results, install the program.
'''

osx_install_advice = '''
If you have homebrew installed, try these command to install the missing
package:
    brew install {package}
'''

linux_install_advice = '''
On systems with the aptitude package manager (Debian, Ubuntu), try these
commands:
    sudo apt-get update
    sudo apt-get install {package}

On RPM-based systems (Red Hat, Fedora), search for instructions on
installing the RPM for {program}.
'''

windows_install_advice = '''
If not already installed, install the Chocolatey package manager. Then use
a command prompt to install the missing package:
    choco install {package}
'''


def _get_platform():
    if sys.platform.startswith('freebsd'):
        return 'freebsd'
    elif sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('win'):
        return 'windows'
    return sys.platform


def _error_trailer(program, package, **kwargs):
    if isinstance(package, Mapping):
        package = package.get(_get_platform(), program)

    if _get_platform() == 'darwin':
        log.info(osx_install_advice.format(**locals()))
    elif _get_platform() == 'linux':
        log.info(linux_install_advice.format(**locals()))
    elif _get_platform() == 'windows':
        log.info(windows_install_advice.format(**locals()))


def _error_missing_program(program, package, required_for, recommended):
    if recommended:
        log.warning(missing_recommend_program.format(**locals()))
    elif required_for:
        log.error(missing_optional_program.format(**locals()))
    else:
        log.error(missing_program.format(**locals()))
    _error_trailer(**locals())


def _error_old_version(program, package, need_version, found_version, required_for):
    if required_for:
        log.error(old_version_required_for.format(**locals()))
    else:
        log.error(old_version.format(**locals()))
    _error_trailer(**locals())


def check_external_program(
    *,
    program: str,
    package: str,
    version_checker: Union[str, Callable],
    need_version: str,
    required_for: Optional[str] = None,
    recommended=False,
    version_parser: Type[Version] = LooseVersion,
):
    """Check for required version of external program and raise exception if not.

    Args:
        program: The name of the program to test.
        package: The name of a software package that typically supplies this program.
            Usually the same as program.
        version_check: A callable without arguments that retrieves the installed
            version of program.
        need_version: The minimum required version.
        required_for: The name of an argument of feature that requires this program.
        recommended: If this external program is recommended, instead of raising
            an exception, log a warning and allow execution to continue.
        version_parser: A class that should be used to parse and compare version
            numbers. Used when version numbers do not follow standard conventions.
    """

    try:
        if callable(version_checker):
            found_version = version_checker()
        else:
            found_version = version_checker
    except (CalledProcessError, FileNotFoundError, MissingDependencyError):
        _error_missing_program(program, package, required_for, recommended)
        if not recommended:
            raise MissingDependencyError(program)
        return

    def remove_leading_v(s):
        if s.startswith('v'):
            return s[1:]
        return s

    found_version = remove_leading_v(found_version)
    need_version = remove_leading_v(need_version)

    if found_version and version_parser(found_version) < version_parser(need_version):
        _error_old_version(program, package, need_version, found_version, required_for)
        if not recommended:
            raise MissingDependencyError(program)

    log.debug('Found %s %s', program, found_version)
