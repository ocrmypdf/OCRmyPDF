# © 2020 James R. Barlow: github.com/jbarlow83
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

"""Tesseract no-op plugin

To quickly run tests where getting OCR output is not necessary.

In 'hocr' mode, create a .hocr file that specifies no text found.

In 'pdf' mode, convert the image to PDF using another program.

In orientation check mode, report the orientation is upright.
"""

import pikepdf
from PIL import Image

from ocrmypdf import OcrEngine, OrientationConfidence, hookimpl

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


class NoopOcrEngine(OcrEngine):
    @staticmethod
    def version():
        return '4.0.0'

    @staticmethod
    def creator_tag(options):
        tag = '-PDF' if options.pdf_renderer == 'sandwich' else ''
        return f"NO-OP {tag} {NoopOcrEngine.version()}"

    def __str__(self):
        return f"NO-OP {NoopOcrEngine.version()}"

    @staticmethod
    def languages(options):
        return {'eng'}

    @staticmethod
    def get_orientation(input_file, options):
        return OrientationConfidence(angle=0, confidence=0.0)

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        with Image.open(input_file) as im, open(
            output_hocr, 'w', encoding='utf-8'
        ) as f:
            w, h = im.size
            f.write(HOCR_TEMPLATE.format(str(w), str(h)))
        with open(output_text, 'w') as f:
            f.write('')

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        with Image.open(input_file) as im:
            dpi = im.info['dpi']
            pagesize = im.size[0] / dpi[0], im.size[1] / dpi[1]
        ptsize = pagesize[0] * 72, pagesize[1] * 72
        pdf = pikepdf.new()
        pdf.add_blank_page(page_size=ptsize)
        pdf.save(output_pdf, static_id=True)
        output_text.write_text('')


@hookimpl
def get_ocr_engine():
    return NoopOcrEngine()
