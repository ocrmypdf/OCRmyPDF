# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Extract version strings from external programs."""

from __future__ import annotations

import logging
import re
from subprocess import PIPE, STDOUT, CalledProcessError

from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess._run import Environ

log = logging.getLogger('ocrmypdf.subprocess')


def get_version(
    program: str,
    *,
    version_arg: str = '--version',
    regex=r'(\d+(\.\d+)*)',
    env: Environ | None = None,
) -> str:
    """Get the version of the specified program.

    Arguments:
        program: The program to version check.
        version_arg: The argument needed to ask for its version, e.g. ``--version``.
        regex: A regular expression to parse the program's output and obtain the
            version.
        env: Custom ``os.environ`` in which to run program.
    """
    # Late import of the public ``run`` so that tests patching
    # ``ocrmypdf.subprocess.run`` affect this function. Binding ``run`` at
    # module load time would capture the real implementation and bypass the
    # patch.
    from ocrmypdf import subprocess as _sp

    args_prog = [program, version_arg]
    try:
        proc = _sp.run(
            args_prog,
            close_fds=True,
            text=True,
            stdout=PIPE,
            stderr=STDOUT,
            check=True,
            env=env,
        )
        output: str = proc.stdout
    except FileNotFoundError as e:
        raise MissingDependencyError(
            f"Could not find program '{program}' on the PATH"
        ) from e
    except CalledProcessError as e:
        if e.returncode != 0:
            log.exception(e)
            raise MissingDependencyError(
                f"Ran program '{program}' but it exited with an error:\n{e.output}"
            ) from e
        raise MissingDependencyError(
            f"Could not find program '{program}' on the PATH"
        ) from e

    match = re.match(regex, output.strip())
    if not match:
        raise MissingDependencyError(
            f"The program '{program}' did not report its version. "
            f"Message was:\n{output}"
        )
    version = match.group(1)

    return version
