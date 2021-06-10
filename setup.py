#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © 2021 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from setuptools import setup

# Minimal setup to support older setuptools/setuptools_scm
setup(
    setup_requires=[  # can be removed whenever we can drop pip 9 support
        'cffi >= 1.9.1',  # to build the leptonica module
        'setuptools_scm',  # so that version will work
        'setuptools_scm_git_archive',  # enable version from github tarballs
    ],
    use_scm_version={'version_scheme': 'post-release'},
    cffi_modules=['src/ocrmypdf/lib/compile_leptonica.py:ffibuilder'],
)
