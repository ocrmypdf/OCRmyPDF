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

import logging
import os
import re
import shutil
import sys
from collections.abc import Mapping
from distutils.version import LooseVersion
from functools import lru_cache
from subprocess import PIPE, STDOUT, CalledProcessError
from subprocess import run as subprocess_run

from ..exceptions import ExitCode, MissingDependencyError

log = logging.getLogger(__name__)


def _get_program(args, env=None):
    program = args[0]
    test_path = env.get('_OCRMYPDF_TEST_PATH', '')
    if test_path:
        program = shutil.which(program, path=test_path)
    return program


def run(args, *, env=None, **kwargs):
    """Wrapper around subprocess.run()

    The main purpose of this wrapper is to allow us to substitute the main program
    for a spoof in the test suite. The hidden variable _OCRMYPDF_TEST_PATH replaces
    the main PATH as a location to check for programs to run.

    Secondly we have to account for behavioral differences in Windows in particular.
    Creating symbolic links in Windows requires administrator privileges and
    may not work if for some reason we're using a FAT file system or the temporary
    folder is on a different drive from the working folder. The test suite
    works around this by creating shim Python scripts that perform the same function
    as a symbolic link, but those shims require support on this side, to ensure
    we call them with Python.

    """
    if not env:
        env = os.environ

    # Search in spoof path if necessary
    program = _get_program(args, env)

    # If we are running a .py on Windows, ensure we call it with this Python
    # (to support test suite shims)
    if os.name == 'nt' and program.lower().endswith('.py'):
        args = [sys.executable, program] + args[1:]
    else:
        args = [program] + args[1:]

    if os.name == 'nt':
        paths = os.pathsep.join(os.get_exec_path(env))
        if not shutil.which(args[0], path=paths):
            shimmed_path = shim_paths_with_program_files(env)
            new_args0 = shutil.which(args[0], path=shimmed_path)
            if new_args0:
                args[0] = new_args0

    process_log = log.getChild(os.path.basename(program))
    process_log.debug("Running: %s", args)
    if sys.version_info < (3, 7) and os.name == 'nt':
        # Can't use close_fds=True on Windows with Python 3.6 or older
        # https://bugs.python.org/issue19575, etc.
        kwargs['close_fds'] = False
    proc = subprocess_run(args, env=env, **kwargs)
    if process_log.isEnabledFor(logging.DEBUG):
        try:
            stderr = proc.stderr.decode('utf-8', 'replace')
        except AttributeError:
            stderr = proc.stderr
        if stderr:
            process_log.debug("stderr = %s", stderr)
    return proc


def get_version(program, *, version_arg='--version', regex=r'(\d+(\.\d+)*)', env=None):
    """Get the version of the specified program"""
    args_prog = [program, version_arg]
    try:
        proc = run(
            args_prog,
            close_fds=True,
            universal_newlines=True,
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
    try:
        version = re.match(regex, output.strip()).group(1)
    except AttributeError as e:
        raise MissingDependencyError(
            f"The program '{program}' did not report its version. "
            f"Message was:\n{output}"
        )

    return version


def shim_paths_with_program_files(env=None):
    if not env:
        env = os.environ
    program_files = env.get('PROGRAMFILES', '')
    if not program_files:
        return env.get('PATH', '')
    paths = []
    try:
        for dirname in os.listdir(program_files):
            if dirname.lower() == 'tesseract-ocr':
                paths.append(os.path.join(program_files, dirname))
            elif dirname.lower() == 'gs':
                try:
                    latest_gs = max(
                        os.listdir(os.path.join(program_files, dirname)),
                        key=lambda d: float(d[2:]),
                    )
                except (FileNotFoundError, NotADirectoryError):
                    continue
                paths.append(os.path.join(program_files, dirname, latest_gs, 'bin'))
    except EnvironmentError:
        pass
    paths.extend(path for path in os.get_exec_path(env) if path not in set(paths))
    return os.pathsep.join(paths)


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
    if required_for:
        log.error(missing_optional_program.format(**locals()))
    elif recommended:
        log.info(missing_recommend_program.format(**locals()))
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
    program,
    package,
    version_checker,
    need_version,
    required_for=None,
    recommended=False,
    **kwargs,  # To consume log parameter
):
    if kwargs:
        if not 'log' in kwargs:
            log.warning('check_external_program(log=...) is deprecated')
    try:
        found_version = version_checker()
    except (CalledProcessError, FileNotFoundError, MissingDependencyError):
        _error_missing_program(program, package, required_for, recommended)
        if not recommended:
            raise MissingDependencyError()
        return

    def remove_leading_v(s):
        if s.startswith('v'):
            return s[1:]
        return s

    found_version = remove_leading_v(found_version)
    need_version = remove_leading_v(need_version)

    if LooseVersion(found_version) < LooseVersion(need_version):
        _error_old_version(program, package, need_version, found_version, required_for)
        if not recommended:
            raise MissingDependencyError()

    log.debug('Found %s %s', program, found_version)
