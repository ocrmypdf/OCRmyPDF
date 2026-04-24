# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Interface to jbig2 executable."""

from __future__ import annotations

from subprocess import PIPE, CalledProcessError

from packaging.version import Version

from ocrmypdf._exec._probe import ToolProbe
from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import run

_PROBE = ToolProbe(program='jbig2', version_regex=r'jbig2enc (\d+(\.\d+)*).*')


def version() -> Version:
    try:
        return _PROBE.version()
    except CalledProcessError as e:
        # TeX Live for Windows provides an incompatible jbig2.EXE which may
        # be on the PATH.
        raise MissingDependencyError('jbig2enc') from e


def available() -> bool:
    try:
        version()
    except MissingDependencyError:
        return False
    return True


def convert_single(cwd, infile, outfile, threshold):
    args = ['jbig2', '--pdf', '-t', str(threshold), infile]
    with open(outfile, 'wb') as fstdout:
        proc = run(args, cwd=cwd, stdout=fstdout, stderr=PIPE)
    proc.check_returncode()
    return proc
