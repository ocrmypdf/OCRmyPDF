#!/usr/bin/env python3

from setuptools import setup
from subprocess import Popen, STDOUT, check_output, CalledProcessError
from string import Template
import re
import sys


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
installing the RPM for {package}.
'''


def _error_trailer(program, package, optional):
    if program == 'java':
        return  # You're fucked

    if optional:
        print(okay_its_optional.format(**locals()), file=sys.stderr)
    else:
        print(not_okay_its_required.format(**locals()), file=sys.stderr)
    if sys.platform.startswith('darwin'):
        print(osx_install_advice.format(**locals()), file=sys.stderr)
    elif sys.platform.startswith('linux'):
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
        optional
        ):
    print(unknown_version.format(**locals()), file=sys.stderr)
    _error_trailer(**locals())


def error_old_version(
        program,
        package,
        optional,
        need_version
        ):
    print(old_version.format(**locals()), file=sys.stderr)
    _error_trailer(**locals())


def check_external_program(
        program,
        minimum_version,
        package,
        version_check_args=['--version'],
        version_scrape_regex=re.compile(r'(\d+\.\d+(?:\.\d+)?)'),
        optional=False):

    print('Checking for {program} >= {minimum_version}...'.format(
            program=program, minimum_version=minimum_version))
    try:
        result = check_output(
                [program] + version_check_args,
                universal_newlines=True, stderr=STDOUT)
    except CalledProcessError:
        error_missing_program(program, package, optional)
        if not optional:
            sys.exit(1)

    try:
        version = version_scrape_regex.search(result).group(1)
    except AttributeError:
        error_unknown_version(program, package, optional, minimum_version)
        if not optional:
            sys.exit(1)

    if version < minimum_version:
        error_old_version(program, package, optional, minimum_version)

    print('Found {program} {version}'.format(
            program=program, version=version))

command = next((arg for arg in sys.argv[1:] if not arg.startswith('-')), '')

if command.startswith('install') or \
        command in ['check', 'test', 'nosetests', 'easy_install']:
    check_external_program(
        program='tesseract',
        minimum_version='3.02.02',
        package='tesseract'
    )
    check_external_program(
        program='gs',
        minimum_version='9.14',
        package='ghostscript'
    )
    check_external_program(
        program='unpaper',
        minimum_version='6.1',
        package='unpaper',
        optional=True
    )
    # Deprecated
    check_external_program(
        program='pdfseparate',
        minimum_version='0.29.0',
        package='poppler',
        version_check_args=['-v']
    )
    check_external_program(
        program='java',
        minimum_version='1.5.0',
        package='Java Runtime Environment',
        version_check_args=['-version']
    )
    check_external_program(
        program='mutool',
        minimum_version='1.7a',
        version_check_args=['-v'],
        version_scrape_regex=re.compile(r'(\d+\.\d+[a-z]+)'),
        package='mupdf-tools'
    )

setup(
    name='ocrmypdf',
    version='3.0rc1',
    description='OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched',
    url='https://github.com/fritz-hh/OCRmyPDF',
    author='J. R. Barlow',
    author_email='jim@purplerock.ca',
    license='Public Domain',
    packages=['ocrmypdf'],
    keywords=['PDF', 'OCR', 'optical character recognition', 'PDF/A', 'scanning'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: Public Domain",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Text Processing :: Linguistic",
        ],
    install_requires=[
        'ruffus>=2.6.3',
        'Pillow>=2.7.0',
        'lxml>=3.4.2',
        'reportlab>=3.1.44',
        'PyPDF2>=1.25.1'
    ],
    entry_points={
        'console_scripts': [
            'ocrmypdf = ocrmypdf.main:run_pipeline'
        ],
    },
    eager_resources=[
        'ocrmypdf/jhove/bin/*.jar',
        'ocrmypdf/jhove/conf/*.conf',
        'ocrmypdf/jhove/lib/*.jar'
    ],
    include_package_data=True,
    zip_safe=False)
