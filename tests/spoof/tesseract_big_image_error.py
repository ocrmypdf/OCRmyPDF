#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

import sys


VERSION_STRING = '''tesseract 3.05.01
 leptonica-1.74.4
  libjpeg 9b : libpng 1.6.32 : libtiff 4.0.8 : zlib 1.2.8
SPOOFED: return error claiming image too big
'''

"""Simulates an error of Tesseract failing on attempts to process large images

"""


def main():
    if sys.argv[1] == '--version':
        print(VERSION_STRING, file=sys.stderr)
        sys.exit(0)
    elif sys.argv[1] == '--list-langs':
        print('List of available languages (1):\neng\n', file=sys.stderr)
        sys.exit(0)
    elif sys.argv[1] == '--print-parameters':
        print('A parameter list would go here\ntextonly_pdf 0\n', file=sys.stderr)
        sys.exit(0)
    elif sys.argv[-2] == 'hocr':
        print("Image too large: (33830, 14959)\n"
              "Error during processing.", file=sys.stderr)
        sys.exit(1)
    elif sys.argv[-2] == 'pdf':
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
