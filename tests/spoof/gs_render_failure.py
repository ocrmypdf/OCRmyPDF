#!/usr/bin/env python3
# © 2016-18 James R. Barlow: github.com/jbarlow83
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Replicate Ghostscript render failure while allowing rasterizing"""

import os
import sys


def real_ghostscript(argv):
    gs_args = ['gs'] + argv[1:]
    os.execvp("gs", gs_args)
    return  # Not reachable


def main():
    os.environ['PATH'] = os.environ['_OCRMYPDF_SAVE_PATH']
    if '--version' in sys.argv:
        print('9.20')
        print('SPOOFED: ' + os.path.basename(__file__))
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
