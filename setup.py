#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © 2015 James R. Barlow: github.com/jbarlow83

from __future__ import print_function, unicode_literals

import sys
if sys.version_info < (3, 4):
    print("Python 3.4 or newer is required", file=sys.stderr)
    sys.exit(1)

from setuptools import setup  # nopep8
from subprocess import STDOUT, check_output, CalledProcessError  # nopep8
from collections.abc import Mapping  # nopep8
import re  # nopep8


missing_program = '''
The program '{program}' could not be executed or was not found on your
system PATH.
'''

unknown_version = '''
OCRmyPDF requires '{program}' {need_version} or higher.  Your system has
'{program}' but we cannot tell what version is installed.  Contact the
package maintainer.
'''

old_version = '''
OCRmyPDF requires '{program}' {need_version} or higher.  Your system appears
to have {found_version}.  Please update this program.
'''

okay_its_optional = '''
This program is OPTIONAL, so installation of OCRmyPDF can proceed, but
some functionality may be missing.
'''

not_okay_its_required = '''
This program is REQUIRED for OCRmyPDF to work.  Installation will abort.
'''

osx_install_advice = '''
If you have homebrew installed, try these command to install the missing
packages:
    brew update
    brew upgrade
    brew install {package}
'''

linux_install_advice = '''
On systems with the aptitude package manager (Debian, Ubuntu), try these
commands:
    sudo apt-get update
    sudo apt-get install {package}

On RPM-based systems (Red Hat, Fedora), search for instructions on
installing the RPM for {program}.
'''


def get_platform():
    if sys.platform.startswith('freebsd'):
        return 'freebsd'
    elif sys.platform.startswith('linux'):
        return 'linux'
    return sys.platform


def _error_trailer(program, package, optional, **kwargs):
    if optional:
        print(okay_its_optional.format(**locals()), file=sys.stderr)
    else:
        print(not_okay_its_required.format(**locals()), file=sys.stderr)

    if isinstance(package, Mapping):
        package = package[get_platform()]

    if get_platform() == 'darwin':
        print(osx_install_advice.format(**locals()), file=sys.stderr)
    elif get_platform() == 'linux':
        print(linux_install_advice.format(**locals()), file=sys.stderr)


def error_missing_program(
        program,
        package,
        optional
        ):
    print(missing_program.format(**locals()), file=sys.stderr)
    _error_trailer(**locals())


def error_unknown_version(
        program,
        package,
        optional,
        need_version
        ):
    print(unknown_version.format(**locals()), file=sys.stderr)
    _error_trailer(**locals())


def error_old_version(
        program,
        package,
        optional,
        need_version,
        found_version
        ):
    print(old_version.format(**locals()), file=sys.stderr)
    _error_trailer(**locals())


def check_external_program(
        program,
        need_version,
        package,
        version_check_args=['--version'],
        version_scrape_regex=re.compile(r'(\d+\.\d+(?:\.\d+)?)'),
        optional=False):

    print('Checking for {program} >= {need_version}...'.format(
            program=program, need_version=need_version))
    try:
        result = check_output(
                [program] + version_check_args,
                universal_newlines=True, stderr=STDOUT)
    except (CalledProcessError, FileNotFoundError):
        error_missing_program(program, package, optional)
        if not optional:
            sys.exit(1)
        print('Continuing install without {program}'.format(program=program))
        return

    try:
        found_version = version_scrape_regex.search(result).group(1)
    except AttributeError:
        error_unknown_version(program, package, optional, need_version)
        sys.exit(1)

    if found_version < need_version:
        error_old_version(program, package, optional, need_version,
                          found_version)

    print('Found {program} {found_version}'.format(
            program=program, found_version=found_version))


command = next((arg for arg in sys.argv[1:] if not arg.startswith('-')), '')


if command.startswith('install') or \
        command in ['check', 'test', 'nosetests', 'easy_install']:
    check_external_program(
        program='tesseract',
        need_version='3.03',  # limited by Travis CI / Ubuntu 12.04 backports
        package={'darwin': 'tesseract', 'linux': 'tesseract-ocr'}
    )
    check_external_program(
        program='gs',
        need_version='9.15',  # limited by Travis CI / Ubuntu 12.04 backports
        package='ghostscript'
    )
    check_external_program(
        program='unpaper',
        need_version='6.1',   # latest sane version
        package='unpaper',
        optional=True
    )
    check_external_program(
        program='qpdf',
        need_version='5.0.0',   # limited by Travis CI / Ubuntu 12.04 backports
        package='qpdf',
        version_check_args=['--version']
    )


if 'upload' in sys.argv[1:]:
    print('Use twine to upload the package - setup.py upload is insecure')
    sys.exit(1)

tests_require = open('test_requirements.txt').read().splitlines()

setup(
    name='ocrmypdf',
    description='OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched',
    url='https://github.com/jbarlow83/OCRmyPDF',
    author='James R. Barlow',
    author_email='jim@purplerock.ca',
    license='Public Domain',
    packages=['ocrmypdf'],
    keywords=['PDF', 'OCR', 'optical character recognition', 'PDF/A', 'scanning'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Text Processing :: Linguistic",
        ],
    setup_requires=[
        'setuptools_scm',
        'cffi>=1.5.0',
        'pytest-runner'
    ],
    use_scm_version={'version_scheme': 'post-release'},
    cffi_modules=[
        'ocrmypdf/lib/compile_leptonica.py:ffi'
    ],
    install_requires=[
        'ruffus==2.6.3',        # pinned - ocrmypdf implements a 2.6.3 workaround
        'Pillow>=3.1.0',        # Pillow is pretty stable
        'reportlab>=3.2.0',     # oldest released version with sane image handling
        'PyPDF2>=1.26',         # pure Python, so track HEAD closely
        'img2pdf>=0.2.1',       # pure Python, so track HEAD closely
        'cffi>=1.5.0'           # oldest version ever tested
    ],
    tests_require=tests_require,
    entry_points={
        'console_scripts': [
            'ocrmypdf = ocrmypdf.__main__:run_pipeline'
        ],
    },
    package_data={'ocrmypdf': ['data/sRGB.icc']},
    include_package_data=True,
    zip_safe=False)
