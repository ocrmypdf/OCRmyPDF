#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

import sys
import os
from subprocess import check_call

"""Replicate one type of Ghostscript feature elision warning during
PDF/A creation."""


def real_ghostscript(argv):
    gs_args = ['gs'] + argv[1:]
    os.execvp("gs", gs_args)
    return  # Not reachable


elision_warning = """GPL Ghostscript 9.20: Setting Overprint Mode to 1
not permitted in PDF/A-2, overprint mode not set"""


def main():
    if '--version' in sys.argv:
        print('9.20')
        print('SPOOFED: ' + os.path.basename(__filename__))
        sys.exit(0)

    gs_args = ['gs'] + sys.argv[1:]
    check_call(gs_args)

    if '-sDEVICE=pdfwrite' in sys.argv[1:]:
        print(elision_warning)

    sys.exit(0)

if __name__ == '__main__':
    main()
