#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83

import sys
import os
import platform

pytest_plugins = ['helpers_namespace']

import pytest


if sys.version_info.major < 3:
    print("Requires Python 3.4+")
    sys.exit(1)


@pytest.helpers.register
def is_linux():
    return platform.system() == 'Linux'


@pytest.helpers.register
def running_in_docker():
    # Docker creates a file named /.dockerinit
    return os.path.exists('/.dockerinit')
