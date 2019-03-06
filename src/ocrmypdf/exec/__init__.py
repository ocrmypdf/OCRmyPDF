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
from ..exceptions import MissingDependencyError
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
        if e.returncode < 0:
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

unknown_version = '''
OCRmyPDF requires '{program}' {need_version} or higher.  Your system has
'{program}' but we cannot tell what version is installed.  Contact the
package maintainer.
'''

old_version = '''
OCRmyPDF requires '{program}' {need_version} or higher.  Your system appears
to have {found_version}.  Please update this program.
'''

okay_its_optional = '''
This program is OPTIONAL, so installation of OCRmyPDF can proceed, but
some functionality may be missing.
'''

not_okay_its_required = '''
This program is REQUIRED for OCRmyPDF to work.  Installation will abort.
'''

osx_install_advice = '''
If you have homebrew installed, try these command to install the missing
packages:
    brew update
    brew upgrade
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


def get_platform():
    if sys.platform.startswith('freebsd'):
        return 'freebsd'
    elif sys.platform.startswith('linux'):
        return 'linux'
    return sys.platform


def _error_trailer(log, program, package, optional, **kwargs):
    if optional:
        log.error(okay_its_optional.format(**locals()))
    else:
        log.error(not_okay_its_required.format(**locals()))

    if isinstance(package, Mapping):
        package = package[get_platform()]

    if get_platform() == 'darwin':
        log.error(osx_install_advice.format(**locals()))
    elif get_platform() == 'linux':
        log.error(linux_install_advice.format(**locals()))


def error_missing_program(log, program, package, optional):
    log.error(missing_program.format(**locals()))
    _error_trailer(**locals())


def error_unknown_version(log, program, package, optional, need_version):
    log.error(unknown_version.format(**locals()))
    _error_trailer(**locals())


def error_old_version(log, program, package, optional, need_version, found_version):
    log.error(old_version.format(**locals()))
    _error_trailer(**locals())


def check_external_program(
    log, program, package, version_checker, need_version, optional=False
):
    try:
        found_version = version_checker()
    except (CalledProcessError, FileNotFoundError, MissingDependencyError):
        error_missing_program(log, program, package, optional)
        if not optional:
            sys.exit(1)
        return

    if found_version < need_version:
        error_old_version(log, program, package, optional, need_version, found_version)

    log.debug(f'Found {program} {found_version}')
