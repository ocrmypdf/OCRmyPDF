#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © 2015 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 6):
    print("Python 3.6 or newer is required", file=sys.stderr)
    sys.exit(1)

if 'upload' in sys.argv[1:]:
    print('Use twine to upload the package - setup.py upload is insecure')
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
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
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
        'pytest-runner',  # to enable python setup.py test
        'setuptools_scm',  # so that version will work
        'setuptools_scm_git_archive',  # enable version from github tarballs
    ],
    use_scm_version={'version_scheme': 'post-release'},
    cffi_modules=['src/ocrmypdf/lib/compile_leptonica.py:ffibuilder'],
    install_requires=[
        'cffi >= 1.9.1',  # must be a setup and install requirement
        'coloredlogs >= 14.0',  # strictly optional
        'img2pdf >= 0.3.0, < 0.4',  # pure Python, so track HEAD closely
        'pdfminer.six >= 20191110, <= 20200517',
        'pikepdf >= 1.14.0, < 2',
        'Pillow >= 7.0.0',
        'pluggy >= 0.13.0',
        'reportlab >= 3.3.0',  # oldest released version with sane image handling
        'tqdm >= 4',
    ],
    tests_require=tests_require,
    entry_points={'console_scripts': ['ocrmypdf = ocrmypdf.__main__:run']},
    package_data={'ocrmypdf': ['data/sRGB.icc']},
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Documentation': 'https://ocrmypdf.readthedocs.io/',
        'Source': 'https://github.com/jbarlow83/ocrmypdf',
        'Tracker': 'https://github.com/jbarlow83/ocrmypdf/issues',
    },
)
