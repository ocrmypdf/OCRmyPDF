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

"""Tesseract no-op spoof

To quickly run tests where getting OCR output is not necessary.

In 'hocr' mode, create a .hocr file that specifies no text found.

In 'pdf' mode, convert the image to PDF using another program.

In orientation check mode, report the orientation is upright.
"""

import sys

import img2pdf
import PyPDF2 as pypdf
from PIL import Image

VERSION_STRING = '''tesseract 4.0.0
 leptonica-1.77.0
  libjpeg 9c : libpng 1.6.35 : libtiff 4.0.10 : zlib 1.2.11 : libopenjp2 2.3.0
 Found AVX2
 Found AVX
 Found SSE
SPOOFED
'''

HOCR_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title></title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name='ocr-system' content='tesseract 4.0.0' />
  <meta name='ocr-capabilities' content='ocr_page ocr_carea ocr_par ocr_line ocrx_word'/>
 </head>
 <body>
  <div class='ocr_page' id='page_1' title='image "x.tif"; bbox 0 0 {0} {1}; ppageno 0'>
   <div class='ocr_carea' id='block_1_1' title="bbox 0 1 {0} {1}">
    <p class='ocr_par' dir='ltr' id='par_1' title="bbox 0 1 {0} {1}">
     <span class='ocr_line' id='line_1' title="bbox 0 1 {0} {1}"><span class='ocrx_word' id='word_1' title="bbox 0 1 {0} {1}"> </span>
     </span>
    </p>
   </div>
  </div>
 </body>
</html>'''


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
    elif sys.argv[-2] == 'hocr':
        inputf = sys.argv[-4]
        output = sys.argv[-3]
        with Image.open(inputf) as im, open(
            output + '.hocr', 'w', encoding='utf-8'
        ) as f:
            w, h = im.size
            f.write(HOCR_TEMPLATE.format(str(w), str(h)))
        with open(output + '.txt', 'w') as f:
            f.write('')
    elif sys.argv[-2] == 'pdf':
        if 'textonly_pdf=1' in sys.argv:
            inputf = sys.argv[-4]
            output = sys.argv[-3]
            with Image.open(inputf) as im:
                dpi = im.info['dpi']
                pagesize = im.size[0] / dpi[0], im.size[1] / dpi[1]
                ptsize = pagesize[0] * 72, pagesize[1] * 72

            pdf_out = pypdf.PdfFileWriter()
            pdf_out.addBlankPage(ptsize[0], ptsize[1])
            with open(output + '.pdf', 'wb') as f:
                pdf_out.write(f)
            with open(output + '.txt', 'w') as f:
                f.write('')
        else:
            inputf = sys.argv[-4]
            output = sys.argv[-3]
            pdf_bytes = img2pdf.convert([inputf], dpi=300)
            with open(output + '.pdf', 'wb') as f:
                f.write(pdf_bytes)
            with open(output + '.txt', 'w') as f:
                f.write('')
    elif sys.argv[-1] == 'stdout':
        inputf = sys.argv[-2]
        print(
            """Orientation: 0
Orientation in degrees: 0
Orientation confidence: 100.00
Script: 1
Script confidence: 100.00""",
            file=sys.stderr,
        )
    else:
        print("Spoof doesn't understand arguments", file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
