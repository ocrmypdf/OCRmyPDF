# © 2016 James R. Barlow: github.com/jbarlow83
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

"""Wrappers to manage subprocess calls"""

import os
import re
import sys
from subprocess import run, STDOUT, PIPE, CalledProcessError
from ..exceptions import MissingDependencyError, ExitCode
from collections.abc import Mapping


def get_version(program, *, version_arg='--version', regex=r'(\d+(\.\d+)*)'):
    "Get the version of the specified program"
    args_prog = [program, version_arg]
    try:
        proc = run(
            args_prog,
            close_fds=True,
            universal_newlines=True,
            stdout=PIPE,
            stderr=STDOUT,
            check=True,
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
    try:
        version = re.match(regex, output.strip()).group(1)
    except AttributeError as e:
        raise MissingDependencyError(
            f"The program '{program}' did not report its version. "
            f"Message was:\n{output}"
        )

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


def _get_platform():
    if sys.platform.startswith('freebsd'):
        return 'freebsd'
    elif sys.platform.startswith('linux'):
        return 'linux'
    return sys.platform


def _error_trailer(log, program, package, **kwargs):
    if isinstance(package, Mapping):
        package = package[_get_platform()]

    if _get_platform() == 'darwin':
        log.info(osx_install_advice.format(**locals()))
    elif _get_platform() == 'linux':
        log.info(linux_install_advice.format(**locals()))


def _error_missing_program(log, program, package, required_for, recommended):
    if required_for:
        log.error(missing_optional_program.format(**locals()))
    elif recommended:
        log.info(missing_recommend_program.format(**locals()))
    else:
        log.error(missing_program.format(**locals()))
    _error_trailer(**locals())


def _error_old_version(
    log, program, package, need_version, found_version, required_for
):
    if required_for:
        log.error(old_version_required_for.format(**locals()))
    else:
        log.error(old_version.format(**locals()))
    _error_trailer(**locals())


def check_external_program(
    *,
    log,
    program,
    package,
    version_checker,
    need_version,
    required_for=None,
    recommended=False,
):
    try:
        found_version = version_checker()
    except (CalledProcessError, FileNotFoundError, MissingDependencyError):
        _error_missing_program(log, program, package, required_for, recommended)
        if not recommended:
            sys.exit(ExitCode.missing_dependency)
        return

    if found_version < need_version:
        _error_old_version(
            log, program, package, need_version, found_version, required_for
        )
        if not recommended:
            sys.exit(ExitCode.missing_dependency)

    log.debug(f'Found {program} {found_version}')
