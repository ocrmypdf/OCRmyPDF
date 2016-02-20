#!/usr/bin/env python3
import sys


VERSION_STRING = '''tesseract 3.04.00
 leptonica-1.72
  libjpeg 8d : libpng 1.6.19 : libtiff 4.0.6 : zlib 1.2.5
SPOOFED: return error claiming image too big
'''

"""Simulates a Tesseract crash

It isn't strictly necessary to crash the process and that has unwanted
side effects like triggering core dumps or error reporting, logging and such.
It's enough to dump some text to stderr and return an error code.

Follows the POSIX? convention of returning 128 + signal number.

"""


def main():
    if sys.argv[1] == '--version':
        print(VERSION_STRING, file=sys.stderr)
        sys.exit(0)
    elif sys.argv[1] == '--list-langs':
        print('List of available languages (1):\neng', file=sys.stderr)
        sys.exit(0)
    elif sys.argv[-1] == 'hocr':
        print("Image too large: (33830, 14959)\n"
              "Error during processing.", file=sys.stderr)
        sys.exit(1)
    elif sys.argv[-1] == 'pdf':
        print("Image too large: (33830, 14959)\n"
              "Error during processing.", file=sys.stderr)
        sys.exit(1)
    elif sys.argv[-1] == 'stdout':
        print("Image too large: (33830, 14959)\n"
              "Error during processing.", file=sys.stderr)
        sys.exit(1)
    else:
        print("Spoof doesn't understand arguments", file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
