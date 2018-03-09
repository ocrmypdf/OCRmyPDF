# © 2017 James R. Barlow: github.com/jbarlow83

from subprocess import CalledProcessError, STDOUT, PIPE, run
from functools import lru_cache
import sys
import os
import re
import resource

from ..exceptions import InputFileError, SubprocessOutputError, \
    MissingDependencyError, EncryptedPdfError
from . import get_program, get_version
from ..helpers import re_symlink


@lru_cache(maxsize=1)
def version():
    return get_version('qpdf', regex=r'qpdf version (.+)')    


def check(input_file, log=None):
    args_qpdf = [
        get_program('qpdf'),
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
        get_program('qpdf'), input_file, output_file
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


def get_npages(input_file, log):
    try:
        pages = run(
            [get_program('qpdf'), '--show-npages', input_file],
            universal_newlines=True, check=True, stdout=PIPE, stderr=STDOUT)
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


def _merge_inner(input_files, output_file, min_version=None, log=None):
    """Merge the list of input files (all filenames) into the output file.

    The input files may contain one or more pages.
    """

    # Single page 'merges' should still be attempted to that the same error
    # checking is applied to single page case

    version_arg = ['--min-version={}'.format(min_version)] \
                  if min_version else []

    if log is None:
        import logging as log

    args_qpdf = [
        get_program('qpdf')
    ] + version_arg + [
        input_files[0], '--pages'
    ] + input_files + ['--', output_file]

    try:
        run(args_qpdf, check=True, stderr=PIPE, universal_newlines=True)
    except CalledProcessError as e:
        if e.returncode == 3 and \
                e.stderr.find("unknown token while reading object") and \
                e.stderr.find("operation succeeded"):
            # Only whitelist the 'unknown token' problem (decimal/string issue)
            # qpdf issue #165
            log.warning('qpdf found and fixed errors: ' + e.stderr)
            return
        raise e from e


def merge(input_files, output_file, min_version=None, log=None, max_files=None):
    """Merge the list of input files (all filenames) into the output file.

    The input files may contain one or more pages.

    """
    # qpdf requires that every file that contributes to the output has a file 
    # descriptor that remains open. That means, given our approach of one 
    # intermediate PDF per, we can practically hit the number of file 
    # descriptors. 

    if max_files is None or max_files < 2:
        # Find out how many open file descriptors we can get away with
        ulimits = resource.getrlimit(resource.RLIMIT_NOFILE)
        max_open_files = ulimits[0]
        max_files = max_open_files // 2  # Conservative guess

    # We'll write things alongside the output file
    output_dir = os.path.dirname(output_file)

    import random
    import string    

    def randstr():
        return ''.join(random.sample(string.ascii_lowercase, 6))

    # How many files to grab at once, merging all their contents
    step_size = max_files

    workqueue = input_files.copy()
    counter = 1
    next_workqueue = []
    while len(workqueue) > 1 or len(next_workqueue) > 0:
        # Take n files out of the queue
        n = min(step_size, len(workqueue))
        job = workqueue[0:n]
        del workqueue[0:n]
        log.debug('merging ' + repr(job))

        # Merge them into 1 file, which will contain n^depth pages
        merge_file = os.path.join(
            output_dir, "merge-{:06d}-{}.pdf".format(counter, randstr()))
        counter += 1
        _merge_inner(job, merge_file, min_version=min_version, log=log)

        # On the next 
        next_workqueue.append(merge_file)
        log.debug('next_workqueue ' + repr(next_workqueue))

        # If we're out of things to do in this queue, move on to the next
        # queue. On the counter-th pass of the workqueue we can chew through
        # (step_size)**N pages, so on most systems the second pass finishes
        # the job.
        if len(workqueue) == 0:
            workqueue = next_workqueue
            next_workqueue = []

    re_symlink(workqueue.pop(), output_file, log)


