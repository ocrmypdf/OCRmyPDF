# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to jbig2 executable."""

from __future__ import annotations

from subprocess import PIPE

from packaging.version import Version

from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import get_version, run


def version() -> Version:
    return Version(get_version('jbig2', regex=r'jbig2enc (\d+(\.\d+)*).*'))


def available():
    try:
        version()
    except MissingDependencyError:
        return False
    return True


def convert_group(cwd, infiles, out_prefix, threshold):
    args = [
        'jbig2',
        '-b',
        out_prefix,
        '--symbol-mode',  # symbol mode (lossy)
        '-t',
        str(threshold),  # threshold
        # '-r', # refinement mode (lossless symbol mode, currently disabled in
        # jbig2)
        '--pdf',
    ]
    args.extend(infiles)
    proc = run(args, cwd=cwd, stdout=PIPE, stderr=PIPE)
    proc.check_returncode()
    return proc


def convert_single(cwd, infile, outfile, threshold):
    args = ['jbig2', '--pdf', '-t', str(threshold), infile]
    with open(outfile, 'wb') as fstdout:
        proc = run(args, cwd=cwd, stdout=fstdout, stderr=PIPE)
    proc.check_returncode()
    return proc
