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


import sys

VERSION_STRING = '''tesseract 4.0.0
 leptonica-1.77.0
  libjpeg 9c : libpng 1.6.35 : libtiff 4.0.10 : zlib 1.2.11 : libopenjp2 2.3.0
 Found AVX2
 Found AVX
 Found SSE
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
        print(
            "Image too large: (33830, 14959)\n" "Error during processing.",
            file=sys.stderr,
        )
        sys.exit(1)
    elif sys.argv[-2] == 'pdf':
        print(
            "Image too large: (33830, 14959)\n" "Error during processing.",
            file=sys.stderr,
        )
        sys.exit(1)
    elif sys.argv[-1] == 'stdout':
        print(
            "Image too large: (33830, 14959)\n" "Error during processing.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("Spoof doesn't understand arguments", file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
