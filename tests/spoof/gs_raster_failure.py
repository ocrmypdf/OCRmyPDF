#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

import sys
import os

"""Replicate Ghostscript raster failure while allowing rendering"""


def real_ghostscript(argv):
    gs_args = ['gs'] + argv[1:]
    os.execvp("gs", gs_args)
    return  # Not reachable


def main():
    if '--version' in sys.argv:
        print('9.20')
        print('SPOOFED: ' + os.path.basename(__filename__))
        sys.exit(0)

    # For any rendering calls (device == pdfwrite) call real ghostscript
    if '-sDEVICE=pdfwrite' in sys.argv:
        real_ghostscript(sys.argv)
        return

    # Fail
    print("ERROR: Ghost story archive not found")
    sys.exit(1)


if __name__ == '__main__':
    main()
