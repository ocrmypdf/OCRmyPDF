#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

import sys
import os

"""Replicate Ghostscript PDF/A conversion failure by suppressing some
arguments"""


def real_ghostscript(argv):
    gs_args = ['gs'] + argv[1:]
    os.execvp("gs", gs_args)
    return  # Not reachable


def main():
    if '--version' in sys.argv:
        print('9.20')
        print('SPOOFED: ' + os.path.basename(__filename__))
        sys.exit(0)

    # Unless some argument is calling for PDFA generation, forward to
    # real ghostscript
    if not any(arg.startswith('-dPDFA') for arg in sys.argv):
        real_ghostscript(sys.argv)
        return

    # Remove the two arguments that tell ghostscript to create a PDF/A
    # Does not remove the Postscript definition file - not necessary
    # to cause PDF/A creation failure
    argv = []
    for arg in sys.argv:
        if arg.startswith('-dPDFA'):
            continue
        elif arg.startswith('-dPDFACompatibilityPolicy'):
            continue
        argv.append(arg)

    real_ghostscript(argv)


if __name__ == '__main__':
    main()
