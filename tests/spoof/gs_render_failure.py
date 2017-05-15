#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

import sys
import os

"""Replicate Ghostscript render failure while allowing rasterizing"""


def real_ghostscript(argv):
    gs_args = ['gs'] + argv[1:]
    os.execvp("gs", gs_args)
    return  # Not reachable


def main():
    if '--version' in sys.argv:
        print('9.20')
        print('SPOOFED: ' + os.path.basename(__filename__))
        sys.exit(0)

    # For any rasterize calls (device != pdfwrite) call real ghostscript
    if '-sDEVICE=pdfwrite' not in sys.argv:
        real_ghostscript(sys.argv)
        return

    # Fail
    print("ERROR: Casper is not a friendly ghost")
    sys.exit(1)


if __name__ == '__main__':
    main()
