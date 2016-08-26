#!/usr/bin/env python3
import sys
import os
import signal


VERSION_STRING = '''tesseract 3.04.00
 leptonica-1.72
  libjpeg 8d : libpng 1.6.19 : libtiff 4.0.6 : zlib 1.2.5
SPOOFED: CRASH ON OCR or -psm 0
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
    elif sys.argv[-1] == 'hocr':
        print("KABOOM! Tesseract failed for some reason", file=sys.stderr)
        sys.exit(128 + signal.SIGSEGV)
    elif sys.argv[-1] == 'pdf':
        print("KABOOM! Tesseract failed for some reason", file=sys.stderr)
        sys.exit(128 + signal.SIGSEGV)
    elif sys.argv[-1] == 'stdout':
        print("libc++abi.dylib: terminating with uncaught exception of type "
              "std::bad_alloc: std::bad_alloc", file=sys.stderr)
        sys.exit(128 + signal.SIGABRT)
    else:
        print("Spoof doesn't understand arguments", file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
