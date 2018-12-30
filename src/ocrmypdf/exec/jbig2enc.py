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

from functools import lru_cache
from subprocess import PIPE, run

from . import get_version
from ..exceptions import MissingDependencyError


@lru_cache(maxsize=1)
def version():
    return get_version('jbig2', regex=r'jbig2enc (\d+(\.\d+)*).*')


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
        '-s',  # symbol mode (lossy)
        # '-r', # refinement mode (lossless symbol mode, currently disabled in
        # jbig2)
        '-p',
    ]
    args.extend(infiles)
    proc = run(args, cwd=cwd, stdout=PIPE, stderr=PIPE)
    proc.check_returncode()
    return proc


def convert_single(*, cwd, infile, outfile):
    args = ['jbig2', '-p', infile]
    with open(outfile, 'wb') as fstdout:
        proc = run(args, cwd=cwd, stdout=fstdout, stderr=PIPE)
    proc.check_returncode()
    return proc
