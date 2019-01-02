#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83
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

import signal
import sys

VERSION_STRING = '''tesseract 4.0.0
 leptonica-1.77.0
  libjpeg 9c : libpng 1.6.35 : libtiff 4.0.10 : zlib 1.2.11 : libopenjp2 2.3.0
 Found AVX2
 Found AVX
 Found SSE
SPOOFED: CRASH ON OCR or --psm 0
'''

"""Simulates a Tesseract crash when asked to run OCR

It isn't strictly necessary to crash the process and that has unwanted
side effects like triggering core dumps or error reporting, logging and such.
It's enough to dump some text to stderr and return an error code.

Follows the POSIX(?) convention of returning 128 + signal number.

"""


def main():
    if sys.argv[1] == '--version':
        print(VERSION_STRING, file=sys.stderr)
        sys.exit(0)
    elif sys.argv[1] == '--list-langs':
        print('List of available languages (1):\neng', file=sys.stderr)
        sys.exit(0)
    elif sys.argv[1] == '--print-parameters':
        print('A parameter list would go here\ntextonly_pdf 0\n', file=sys.stderr)
        sys.exit(0)
    elif sys.argv[-2] == 'hocr':
        print("KABOOM! Tesseract failed for some reason", file=sys.stderr)
        sys.exit(128 + signal.SIGSEGV)
    elif sys.argv[-2] == 'pdf':
        print("KABOOM! Tesseract failed for some reason", file=sys.stderr)
        sys.exit(128 + signal.SIGSEGV)
    elif sys.argv[-1] == 'stdout':
        print(
            "libc++abi.dylib: terminating with uncaught exception of type "
            "std::bad_alloc: std::bad_alloc",
            file=sys.stderr,
        )
        sys.exit(128 + signal.SIGABRT)
    else:
        print("Spoof doesn't understand arguments", file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
