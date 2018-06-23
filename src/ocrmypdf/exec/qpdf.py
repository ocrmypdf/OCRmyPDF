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

from subprocess import CalledProcessError, STDOUT, PIPE, run
from functools import lru_cache
import sys
import os
import re
import resource

from ..exceptions import InputFileError, SubprocessOutputError, \
    MissingDependencyError, EncryptedPdfError
from . import  get_version
from ..helpers import re_symlink


@lru_cache(maxsize=1)
def version():
    return get_version('qpdf', regex=r'qpdf version (.+)')


def check(input_file, log=None):
    args_qpdf = [
        'qpdf',
        '--check',
        input_file
    ]

    if log is None:
        import logging as log

    try:
        run(args_qpdf, stderr=STDOUT, stdout=PIPE, universal_newlines=True,
            check=True)
    except CalledProcessError as e:
        if e.returncode == 2:
            log.error("{0}: not a valid PDF, and could not repair it.".format(
                input_file))
            log.error("Details:")
            log.error(e.output)
        elif e.returncode == 3:
            log.info("qpdf --check returned warnings:")
            log.info(e.output)
        else:
            log.warning(e.output)
        return False
    return True


def _probably_encrypted(e):
    """qpdf can report a false positive "file is encrypted" message for damaged
    files - suppress this"""
    return e.returncode == 2 and \
        'invalid password' in e.output and \
        'file is damaged' not in e.output


def repair(input_file, output_file, log):
    args_qpdf = [
        'qpdf', input_file, output_file
    ]
    try:
        run(args_qpdf, stderr=STDOUT, stdout=PIPE, universal_newlines=True,
            check=True)
    except CalledProcessError as e:
        if e.returncode == 3 and e.output.find("operation succeeded"):
            log.debug('qpdf found and fixed errors: ' + e.output)
            return

        if _probably_encrypted(e):
            raise EncryptedPdfError() from e
        elif e.returncode == 2:
            log.error("{0}: not a valid PDF, and could not repair it.".format(
                      input_file))
            log.error("Details: " + e.output)
            raise InputFileError() from e
        else:
            log.error("{0}: unknown error".format(
                      input_file))
            log.error(e.output)
            raise SubprocessOutputError() from e


def extract_page(input_file, output_file, pageno):
    args_qpdf = [
        'qpdf', input_file,
        '--pages', input_file, '{0}'.format(pageno + 1), '--',
        output_file
    ]
    run(args_qpdf, check=True)
