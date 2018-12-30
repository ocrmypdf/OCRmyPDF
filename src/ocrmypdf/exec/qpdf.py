# © 2017 James R. Barlow: github.com/jbarlow83
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
from os import fspath
from subprocess import PIPE, STDOUT, CalledProcessError, run

from . import get_version


@lru_cache(maxsize=1)
def version():
    return get_version('qpdf', regex=r'qpdf version (.+)')


def check(input_file, log=None):
    args_qpdf = ['qpdf', '--check', fspath(input_file)]

    if log is None:
        import logging as log

    try:
        run(args_qpdf, stderr=STDOUT, stdout=PIPE, universal_newlines=True, check=True)
    except CalledProcessError as e:
        if e.returncode == 2:
            log.error("%s: not a valid PDF, and could not repair it.", input_file)
            log.error("Details:")
            log.error(e.output)
        elif e.returncode == 3:
            log.info("qpdf --check returned warnings:")
            log.info(e.output)
        else:
            log.warning(e.output)
        return False
    return True
