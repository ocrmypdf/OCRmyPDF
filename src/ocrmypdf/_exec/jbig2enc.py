# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to jbig2 executable."""

from __future__ import annotations

from subprocess import PIPE

from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import get_version, run


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


def convert_group_mp(args):
    return convert_group(cwd=args[0], infiles=args[1], out_prefix=args[2])


def convert_single(*, cwd, infile, outfile):
    args = ['jbig2', '-p', infile]
    with open(outfile, 'wb') as fstdout:
        proc = run(args, cwd=cwd, stdout=fstdout, stderr=PIPE)
    proc.check_returncode()
    return proc


def convert_single_mp(args):
    return convert_single(cwd=args[0], infile=args[1], outfile=args[2])
