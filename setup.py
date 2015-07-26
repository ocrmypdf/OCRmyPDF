#!/usr/bin/env python3

from setuptools import setup

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
    classifiers = [
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
        'PyPDF2>=1.24'
    ],
    entry_points={
        'console_scripts': [
            'ocrmypdf = ocrmypdf.main:main'
        ],
    },
    include_package_data=True,
    zip_safe=False)
