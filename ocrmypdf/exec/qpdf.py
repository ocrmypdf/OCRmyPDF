#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import CalledProcessError, STDOUT, PIPE, run, check_output
from functools import lru_cache
import sys
import os
import re

from ..exceptions import InputFileError, SubprocessOutputError, \
    MissingDependencyError, EncryptedPdfError
from . import get_program


@lru_cache(maxsize=1)
def version():
    args_qpdf = [
        get_program('qpdf'),
        '--version'
    ]
    try:
        p = run(args_qpdf, universal_newlines=True, stderr=STDOUT,
                stdout=PIPE)
    except CalledProcessError as e:
        print("Could not find qpdf executable on system PATH.",
              file=sys.stderr)
        raise MissingDependencyError() from e

    qpdf_version = re.match(r'qpdf version (.+)', p.stdout).group(1)
    return qpdf_version


def check(input_file, log=None):
    args_qpdf = [
        get_program('qpdf'),
        '--check',
        input_file
    ]

    if log is None:
        import logging as log

    try:
        check_output(args_qpdf, stderr=STDOUT, universal_newlines=True)
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
        get_program('qpdf'), input_file, output_file
    ]
    try:
        check_output(args_qpdf, stderr=STDOUT, universal_newlines=True)
    except CalledProcessError as e:
        if e.returncode == 3 and e.output.find("operation succeeded"):
            log.debug('qpdf found and fixed errors: ' + e.output)
            log.debug(e.output)
            return

        if _probably_encrypted(e):
            log.error("{0}: this PDF is password-protected - password must "
                      "be removed for OCR".format(input_file))
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


def get_npages(input_file, log):
    try:
        pages = check_output(
            [get_program('qpdf'), '--show-npages', input_file],
             universal_newlines=True, close_fds=True)
    except CalledProcessError as e:
        if e.returncode == 2 and e.output.find('No such file'):
            log.error(e.output)
            raise InputFileError() from e
    return int(pages)


def split_pages(input_file, work_folder, npages):
    """Split multipage PDF into individual pages.

    Incredibly enough, this multiple process approach is about 70 times
    faster than using Ghostscript.
    """
    for n in range(int(npages)):
        args_qpdf = [
            get_program('qpdf'), input_file,
            '--pages', input_file, '{0}'.format(n + 1), '--',
            os.path.join(work_folder, '{0:06d}.page.pdf'.format(n + 1))
        ]
        run(args_qpdf, check=True)


def merge(input_files, output_file, min_version=None):
    """Merge the list of input files (all filenames) into the output file.

    The input files may contain one or more pages.
    """
    version_arg = ['--min-version={}'.format(min_version)] \
                  if min_version else []

    args_qpdf = [
        get_program('qpdf')
    ] + version_arg + [
        input_files[0], '--pages'
    ] + input_files + ['--', output_file]
    run(args_qpdf, check=True)

