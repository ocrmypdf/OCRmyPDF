#!/usr/bin/env python3

from subprocess import Popen, PIPE, CalledProcessError
import sys
import os
import re


def _version():
    args_tess = [
        'tesseract',
        '--version'
    ]
    p_tess = Popen(args_tess, close_fds=True, universal_newlines=True,
                   stdout=PIPE, stderr=PIPE)
    _, versions = p_tess.communicate(timeout=5)

    tesseract_version = re.match(r'tesseract\s(.+)', versions).group(1)
    return tesseract_version


def _languages():
    args_tess = [
        'tesseract',
        '--list-langs'
    ]
    p_tess = Popen(args_tess, close_fds=True, universal_newlines=True,
                   stdout=PIPE, stderr=PIPE)
    _, langs = p_tess.communicate(timeout=5)

    return set(lang.strip() for lang in langs.splitlines()[1:])

try:
    VERSION = _version()
    LANGUAGES = _languages()
except Exception as e:
    print(e)
    print("Could not find tesseract executable", file=sys.stderr)

    sys.exit(1)

HOCR_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title></title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name='ocr-system' content='tesseract 3.02.02' />
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
