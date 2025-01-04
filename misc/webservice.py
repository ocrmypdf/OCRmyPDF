#!/usr/bin/env python
# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Run the OCRmyPDF web service."""

import os
import sys

try:
    import streamlit  # noqa: F401
except ImportError:
    raise ImportError(
        'You need to install streamlit in the Python environment '
        'to run the web service.\n'
    )

if __name__ == '__main__':
    os.execvp(
        sys.executable,
        [
            sys.executable,
            '-m',
            'streamlit',
            'run',
            'misc/_webservice.py',
            *sys.argv[1:],
        ],
    )
