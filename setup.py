#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © 2015 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from __future__ import print_function, unicode_literals

import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 6):
    print("Python 3.6 or newer is required", file=sys.stderr)
    sys.exit(1)

tests_require = open('requirements/test.txt', encoding='utf-8').read().splitlines()


def readme():
    with open('README.md', encoding='utf-8') as f:
        return f.read()


setup(
    name='ocrmypdf',
    description='OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/jbarlow83/OCRmyPDF',
    author='James R. Barlow',
    author_email='james@purplerock.ca',
    packages=find_packages('src', exclude=["tests", "tests.*"]),
    package_dir={'': 'src'},
    keywords=['PDF', 'OCR', 'optical character recognition', 'PDF/A', 'scanning'],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=' >= 3.6',
    setup_requires=[  # can be removed whenever we can drop pip 9 support
        'cffi >= 1.9.1',  # to build the leptonica module
        'setuptools_scm',  # so that version will work
        'setuptools_scm_git_archive',  # enable version from github tarballs
    ],
    use_scm_version={'version_scheme': 'post-release'},
    cffi_modules=['src/ocrmypdf/lib/compile_leptonica.py:ffibuilder'],
    install_requires=[
        'cffi >= 1.9.1',  # must be a setup and install requirement
        'coloredlogs >= 14.0',  # strictly optional
        'img2pdf >= 0.3.0, < 0.5',  # pure Python, so track HEAD closely
        'pdfminer.six >= 20191110, != 20200720, <= 20201018',
        "pikepdf >= 2.10.0",
        'Pillow >= 8.1.2',
        'pluggy >= 0.13.0, < 1.0',
        'reportlab >= 3.5.66',
        'setuptools',
        'tqdm >= 4',
    ],
    tests_require=tests_require,
    entry_points={'console_scripts': ['ocrmypdf = ocrmypdf.__main__:run']},
    package_data={'ocrmypdf': ['data/sRGB.icc', 'py.typed']},
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Documentation': 'https://ocrmypdf.readthedocs.io/',
        'Source': 'https://github.com/jbarlow83/ocrmypdf',
        'Tracker': 'https://github.com/jbarlow83/ocrmypdf/issues',
    },
)
