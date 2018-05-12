# © 2018 James R. Barlow: github.com/jbarlow83
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

from subprocess import CalledProcessError, run, PIPE
from functools import lru_cache
import sys
import os
import shutil

from . import get_version
from ..exceptions import ExitCode, MissingDependencyError


@lru_cache(maxsize=1)
def version():
    return get_version('jbig2', regex=r'jbig2enc (\d+(\.\d+)*).*')


@lru_cache(maxsize=1)
def available():
    try:
        version()
    except MissingDependencyError:
        return False
    return True


def convert_group(*, cwd, infiles, out_prefix):
    args = [
        'jbig2',
        '-b',
        out_prefix,
        '-s',
        '-p',
    ]
    args.extend(infiles)
    proc = run(args, cwd=cwd, stdout=PIPE, stderr=PIPE)
    proc.check_returncode()
    return proc