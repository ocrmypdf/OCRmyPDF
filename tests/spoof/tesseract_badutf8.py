#!/usr/bin/env python3
# © 2017 James R. Barlow: github.com/jbarlow83
import sys
import img2pdf
import PyPDF2 as pypdf
from PIL import Image


"""Tesseract bad utf8 spoof

In 'hocr' mode or 'pdf' mode, return error code 1 and some non-Unicode
text because tesseract seems to do that in some cases related to 
language pack version mismatches

"""


VERSION_STRING = '''tesseract 3.05.01
 leptonica-1.72
  libjpeg 8d : libpng 1.6.19 : libtiff 4.0.6 : zlib 1.2.5
SPOOFED
'''

# Japanese "Invalid UTF-8" encoded in Shift JIS
BAD_UTF8 = b'\x96\xb3\x8c\xf8\x82\xc8UTF-8\x0a'


def main():
    if sys.argv[1] == '--version':
        print(VERSION_STRING, file=sys.stderr)
        sys.exit(0)
    elif sys.argv[1] == '--list-langs':
        print('List of available languages (1):\neng', file=sys.stderr)
        sys.exit(0)
    elif sys.argv[1] == '--print-parameters':
        print("Some parameters", file=sys.stderr)
        print("textonly_pdf\t1\tSome help text")
        sys.exit(0)
    elif sys.argv[-2] in ('hocr', 'pdf'):
        sys.stdout.buffer.write(BAD_UTF8)
        sys.exit(1)
    elif sys.argv[-1] == 'stdout':
        # input file is at sys.argv[-2] but we don't look at it
        print("""Orientation: 0
Orientation in degrees: 0
Orientation confidence: 100.00
Script: 1
Script confidence: 100.00""", file=sys.stderr)
    else:
        print("Spoof doesn't understand arguments", file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
