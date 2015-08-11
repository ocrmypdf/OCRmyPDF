#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import STDOUT, CalledProcessError, check_output
import sys
import os
import re
from functools import lru_cache
from . import ExitCode


@lru_cache(maxsize=1)
def version():
    args_tess = [
        'tesseract',
        '--version'
    ]
    try:
        versions = check_output(
                args_tess, close_fds=True, universal_newlines=True,
                stderr=STDOUT)
    except CalledProcessError:
        print("Could not find Tesseract executable on system PATH.")
        sys.exit(ExitCode.missing_dependency)

    tesseract_version = re.match(r'tesseract\s(.+)', versions).group(1)
    return tesseract_version


@lru_cache(maxsize=1)
def languages():
    args_tess = [
        'tesseract',
        '--list-langs'
    ]
    try:
        langs = check_output(
                args_tess, close_fds=True, universal_newlines=True,
                stderr=STDOUT)
    except CalledProcessError as e:
        print("Tesseract failed to report available languages.")
        print("Output from Tesseract:")
        print("-" * 40)
        print(e.output)
        sys.exit(ExitCode.missing_dependency)
    return set(lang.strip() for lang in langs.splitlines()[1:])


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
