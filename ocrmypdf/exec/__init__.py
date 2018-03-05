# © 2016 James R. Barlow: github.com/jbarlow83

"""Wrappers to manage subprocess calls"""

import os
import re
import sys
from subprocess import run, STDOUT, PIPE, CalledProcessError
from ..exceptions import MissingDependencyError


def get_program(name):
    "Check environment variables for overrides to this program"
    envvar = 'OCRMYPDF_' + name.upper()
    return os.environ.get(envvar, name)


def get_version(program, *, 
        version_arg='--version', regex=r'(\d+(\.\d+)*)'):
    "Get the version of the specified program, "
    args_prog = [
        get_program(program),
        version_arg
    ]
    try:
        proc = run(
            args_prog, close_fds=True, universal_newlines=True,
            stdout=PIPE, stderr=STDOUT, check=True)
        output = proc.stdout
    except CalledProcessError as e:
        if get_program(program) == program:
            raise MissingDependencyError(
                "Could not find program '{}' on the PATH".format(
                    program)) from e
        else:
            raise MissingDependencyError(
                "Could not find program '{}'".format(
                    get_program(program))) from e            

    try:
        version = re.match(regex, output.strip()).group(1)
    except AttributeError as e:
        raise MissingDependencyError(
            ("The program '{}' did not report its version. "
            "Message was:\n{}").format(program, output)
        )

    return version
