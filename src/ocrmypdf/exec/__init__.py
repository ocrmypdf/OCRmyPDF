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


def get_version(program, *,
        version_arg='--version', regex=r'(\d+(\.\d+)*)'):
    "Get the version of the specified program"
    args_prog = [
        program,
        version_arg
    ]
    try:
        proc = run(
            args_prog, close_fds=True, universal_newlines=True,
            stdout=PIPE, stderr=STDOUT, check=True)
        output = proc.stdout
    except FileNotFoundError as e:
        raise MissingDependencyError(
            "Could not find program '{}' on the PATH".format(
                program)) from e
    except CalledProcessError as e:
        if e.returncode < 0:
            raise MissingDependencyError(
                "Ran program '{}' but it exited with an error:\n{}".format(
                    program, e.output)) from e
        raise MissingDependencyError(
            "Could not find program '{}' on the PATH".format(
                program)) from e
    try:
        version = re.match(regex, output.strip()).group(1)
    except AttributeError as e:
        raise MissingDependencyError(
            ("The program '{}' did not report its version. "
            "Message was:\n{}").format(program, output)
        )

    return version
