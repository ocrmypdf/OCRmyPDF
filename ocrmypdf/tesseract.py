#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

import sys
import os
import re
import shutil
from functools import lru_cache
from . import ExitCode, get_program

from subprocess import Popen, PIPE, CalledProcessError, \
    TimeoutExpired, check_output, STDOUT
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


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


@lru_cache(maxsize=1)
def version():
    args_tess = [
        get_program('tesseract'),
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
        get_program('tesseract'),
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


def generate_hocr(input_file, output_hocr, language: list, tessconfig: list,
                  timeout: float, pageinfo_getter, log):

    badxml = os.path.splitext(output_hocr)[0] + '.badxml'

    args_tesseract = [
        get_program('tesseract'),
        '-l', '+'.join(language),
        input_file,
        badxml,
        'hocr'
    ] + tessconfig
    p = Popen(args_tesseract, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except TimeoutExpired:
        p.kill()
        stdout, stderr = p.communicate()
        # Generate a HOCR file with no recognized text if tesseract times out
        # Temporary workaround to hocrTransform not being able to function if
        # it does not have a valid hOCR file.
        with open(output_hocr, 'w', encoding="utf-8") as f:
            pageinfo = pageinfo_getter()
            f.write(HOCR_TEMPLATE.format(
                pageinfo['width_pixels'],
                pageinfo['height_pixels']))
    else:
        if stdout:
            log.info(stdout)
        if stderr:
            log.error(stderr)

        if p.returncode != 0:
            raise CalledProcessError(p.returncode, args_tesseract)

        if os.path.exists(badxml + '.html'):
            # Tesseract 3.02 appends suffix ".html" on its own (.badxml.html)
            shutil.move(badxml + '.html', badxml)
        elif os.path.exists(badxml + '.hocr'):
            # Tesseract 3.03 appends suffix ".hocr" on its own (.badxml.hocr)
            shutil.move(badxml + '.hocr', badxml)

        # Tesseract 3.03 inserts source filename into hocr file without
        # escaping it, creating invalid XML and breaking the parser.
        # As a workaround, rewrite the hocr file, replacing the filename
        # with a space.  Don't know if Tesseract 3.02 does the same.

        regex_nested_single_quotes = re.compile(
            r"""title='image "([^"]*)";""")
        with open(badxml, mode='r', encoding='utf-8') as f_in, \
                open(output_hocr, mode='w', encoding='utf-8') as f_out:
            for line in f_in:
                line = regex_nested_single_quotes.sub(
                    r"""title='image " ";""", line)
                f_out.write(line)


def generate_pdf(input_image, skip_pdf, output_pdf, language: list,
                 tessconfig: list, timeout: float, log):
    '''Use Tesseract to render a PDF.

    input_image -- image to analyze
    skip_pdf -- if we time out, use this file as output
    language -- list of languages to consider
    tessconfig -- tesseract configuration
    timeout -- timeout (seconds)
    log -- logger object
    '''

    args_tesseract = [
        get_program('tesseract'),
        '-l', '+'.join(language),
        input_image,
        os.path.splitext(output_pdf)[0],  # Tesseract appends suffix
        'pdf'
    ] + tessconfig
    p = Popen(args_tesseract, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)

    try:
        stdout, stderr = p.communicate(timeout=timeout)
        if stdout:
            log.info(stdout)
        if stderr:
            log.error(stderr)
    except TimeoutExpired:
        p.kill()
        log.info("Tesseract - page timed out")
        shutil.copy(skip_pdf, output_pdf)

