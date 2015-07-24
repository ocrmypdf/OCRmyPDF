#!/usr/bin/env python3

from subprocess import Popen, PIPE, CalledProcessError
import sys
import os
import re


def _version():
    args_tess = [
        'tesseract',
        '--version'
    ]
    p_tess = Popen(args_tess, close_fds=True, universal_newlines=True,
                   stdout=PIPE, stderr=PIPE)
    _, versions = p_tess.communicate(timeout=5)

    tesseract_version = re.match(r'tesseract\s(.+)', versions).group(1)
    return tesseract_version


def _languages():
    args_tess = [
        'tesseract',
        '--list-langs'
    ]
    p_tess = Popen(args_tess, close_fds=True, universal_newlines=True,
                   stdout=PIPE, stderr=PIPE)
    _, langs = p_tess.communicate(timeout=5)

    return set(lang.strip() for lang in langs.splitlines()[1:])

try:
    VERSION = _version()
    LANGUAGES = _languages()
except Exception as e:
    print(e)
    print("Could not find tesseract executable", file=sys.stderr)

    sys.exit(1)
