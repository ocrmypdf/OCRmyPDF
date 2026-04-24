# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Validate that required external programs are installed and new enough."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable, Mapping
from subprocess import CalledProcessError

from packaging.version import Version

from ocrmypdf.exceptions import MissingDependencyError

log = logging.getLogger('ocrmypdf.subprocess')


MISSING_PROGRAM = '''
The program '{program}' could not be executed or was not found on your
system PATH.
'''

MISSING_OPTIONAL_PROGRAM = '''
The program '{program}' could not be executed or was not found on your
system PATH.  This program is required when you use the
{required_for} arguments.  You could try omitting these arguments, or install
the package.
'''

MISSING_RECOMMEND_PROGRAM = '''
The program '{program}' could not be executed or was not found on your
system PATH.  This program is recommended when using the {required_for} arguments,
but not required, so we will proceed.  For best results, install the program.
'''

OLD_VERSION = '''
OCRmyPDF requires '{program}' {need_version} or higher.  Your system appears
to have {found_version}.  Please update this program.
'''

OLD_VERSION_REQUIRED_FOR = '''
OCRmyPDF requires '{program}' {need_version} or higher when run with the
{required_for} arguments.  {program} {found_version} is installed.

If you omit these arguments, OCRmyPDF may be able to
proceed.  For best results, update the program.
'''

OSX_INSTALL_ADVICE = '''
If you have homebrew installed, try these command to install the missing
package:
    brew install {package}
'''

LINUX_INSTALL_ADVICE = '''
On systems with the aptitude package manager (Debian, Ubuntu), try these
commands:
    sudo apt update
    sudo apt install {package}

On RPM-based systems (Red Hat, Fedora), try this command:
    sudo dnf install {package}
'''

WINDOWS_INSTALL_ADVICE = '''
If not already installed, install the Chocolatey package manager. Then use
a command prompt to install the missing package:
    choco install {package}
'''


def _get_platform() -> str:
    if sys.platform.startswith('freebsd'):
        return 'freebsd'
    elif sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('win'):
        return 'windows'
    return sys.platform


def _error_trailer(program: str, package: str | Mapping[str, str], **kwargs) -> None:
    del kwargs
    if isinstance(package, Mapping):
        package = package.get(_get_platform(), program)

    if _get_platform() == 'darwin':
        log.info(OSX_INSTALL_ADVICE.format(**locals()))
    elif _get_platform() == 'linux':
        log.info(LINUX_INSTALL_ADVICE.format(**locals()))
    elif _get_platform() == 'windows':
        log.info(WINDOWS_INSTALL_ADVICE.format(**locals()))


def _error_missing_program(
    program: str, package: str, required_for: str | None, recommended: bool
) -> None:
    # pylint: disable=unused-argument
    if recommended:
        log.warning(MISSING_RECOMMEND_PROGRAM.format(**locals()))
    elif required_for:
        log.error(MISSING_OPTIONAL_PROGRAM.format(**locals()))
    else:
        log.error(MISSING_PROGRAM.format(**locals()))
    _error_trailer(**locals())


def _error_old_version(
    program: str,
    package: str,
    need_version: str,
    found_version: str,
    required_for: str | None,
) -> None:
    # pylint: disable=unused-argument
    if required_for:
        log.error(OLD_VERSION_REQUIRED_FOR.format(**locals()))
    else:
        log.error(OLD_VERSION.format(**locals()))
    _error_trailer(**locals())


def check_external_program(
    *,
    program: str,
    package: str,
    version_checker: Callable[[], Version],
    need_version: str | Version,
    required_for: str | None = None,
    recommended: bool = False,
    version_parser: type[Version] = Version,
) -> None:
    """Check for required version of external program and raise exception if not.

    Args:
        program: The name of the program to test.
        package: The name of a software package that typically supplies this program.
            Usually the same as program.
        version_checker: A callable without arguments that retrieves the installed
            version of program.
        need_version: The minimum required version.
        required_for: The name of an argument of feature that requires this program.
        recommended: If this external program is recommended, instead of raising
            an exception, log a warning and allow execution to continue.
        version_parser: A class that should be used to parse and compare version
            numbers. Used when version numbers do not follow standard conventions.
    """
    if not isinstance(need_version, Version):
        need_version = version_parser(need_version)
    try:
        found_version = version_checker()
    except (CalledProcessError, FileNotFoundError) as e:
        _error_missing_program(program, package, required_for, recommended)
        if not recommended:
            raise MissingDependencyError(program) from e
        return
    except MissingDependencyError:
        _error_missing_program(program, package, required_for, recommended)
        if not recommended:
            raise
        return

    if found_version and found_version < need_version:
        _error_old_version(
            program, package, str(need_version), str(found_version), required_for
        )
        if not recommended:
            raise MissingDependencyError(program)

    log.debug('Found %s %s', program, found_version)
