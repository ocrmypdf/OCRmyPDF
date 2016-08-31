#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

import sys
import os
import re
import shutil
from functools import lru_cache
from . import ExitCode, get_program, page_number
from collections import namedtuple

from subprocess import Popen, PIPE, CalledProcessError, \
    TimeoutExpired, check_output, STDOUT, DEVNULL


OrientationConfidence = namedtuple(
    'OrientationConfidence',
    ('angle', 'confidence'))

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


def get_orientation(input_file, language: list, timeout: float, log):
    args_tesseract = [
        get_program('tesseract'),
        '-l', '+'.join(language),
        '-psm', '0',
        input_file,
        'stdout'
    ]

    try:
        stdout = check_output(
            args_tesseract, close_fds=True, stderr=STDOUT,
            universal_newlines=True, timeout=timeout)
    except TimeoutExpired:
        return OrientationConfidence(angle=0, confidence=0.0)
    except CalledProcessError as e:
        tesseract_log_output(log, e.output, input_file)
        if ('Too few characters. Skipping this page' in e.output or
                'Image too large' in e.output):
            return OrientationConfidence(0, 0)
        raise e from e
    else:
        osd = {}
        for line in stdout.splitlines():
            line = line.strip()
            parts = line.split(':', maxsplit=2)
            if len(parts) == 2:
                osd[parts[0].strip()] = parts[1].strip()

        angle = int(osd.get('Orientation in degrees', 0))
        if 'Orientation' in osd:
            # Tesseract < 3.04.01
            # reports "Orientation in degrees" as a counterclockwise angle
            # We keep it clockwise
            assert 'Rotate' not in osd
            angle = -angle % 360
        else:
            # Tesseract == 3.04.01, hopefully also Tesseract > 3.04.01
            # reports "Orientation in degrees" as a clockwise angle
            assert 'Rotate' in osd

        oc = OrientationConfidence(
            angle=angle,
            confidence=float(osd.get('Orientation confidence', 0)))
        return oc


def tesseract_log_output(log, stdout, input_file):
    lines = stdout.splitlines()
    prefix = "{0:4d}: [tesseract] ".format(page_number(input_file))
    for line in lines:
        if line.startswith("Tesseract Open Source"):
            continue
        elif line.startswith("Warning in pixReadMem"):
            continue
        elif 'diacritics' in line:
            log.warning(prefix + "lots of diacritics - possibly poor OCR")
        elif line.startswith('OSD: Weak margin'):
            log.warning(prefix + "unsure about page orientation")
        elif 'error' in line.lower() or 'exception' in line.lower():
            log.error(prefix + line.strip())
        else:
            log.info(prefix + line.strip())


def page_timedout(log, input_file):
    prefix = "{0:4d}: [tesseract] ".format(page_number(input_file))
    log.warning(prefix + " took too long to OCR - skipping")


def _generate_null_hocr(output_hocr, pageinfo):
    with open(output_hocr, 'w', encoding="utf-8") as f:
        f.write(HOCR_TEMPLATE.format(
            pageinfo['width_pixels'],
            pageinfo['height_pixels']))


def generate_hocr(input_file, output_hocr, language: list, tessconfig: list,
                  timeout: float, pageinfo_getter, pagesegmode: int, log):

    badxml = os.path.splitext(output_hocr)[0] + '.badxml'

    args_tesseract = [
        get_program('tesseract'),
        '-l', '+'.join(language)
    ]

    if pagesegmode is not None:
        args_tesseract.extend(['-psm', str(pagesegmode)])

    args_tesseract.extend([
        input_file,
        badxml,
        'hocr'
    ] + tessconfig)
    try:
        stdout = check_output(
            args_tesseract, close_fds=True, stderr=STDOUT,
            universal_newlines=True, timeout=timeout)
    except TimeoutExpired:
        # Generate a HOCR file with no recognized text if tesseract times out
        # Temporary workaround to hocrTransform not being able to function if
        # it does not have a valid hOCR file.
        page_timedout(log, input_file)
        _generate_null_hocr(output_hocr, pageinfo_getter())
    except CalledProcessError as e:
        tesseract_log_output(log, e.output, input_file)
        if 'Image too large' in e.output:
            _generate_null_hocr(output_hocr, pageinfo_getter())
            return

        raise e from e
    else:
        tesseract_log_output(log, stdout, input_file)
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
                 tessconfig: list, timeout: float, pagesegmode: int, log):
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
        '-l', '+'.join(language)
    ]

    if pagesegmode is not None:
        args_tesseract.extend(['-psm', str(pagesegmode)])

    args_tesseract.extend([
        input_image,
        os.path.splitext(output_pdf)[0],  # Tesseract appends suffix
        'pdf'
    ] + tessconfig)

    try:
        stdout = check_output(
            args_tesseract, close_fds=True, stderr=STDOUT,
            universal_newlines=True, timeout=timeout)
    except TimeoutExpired:
        page_timedout(log, input_image)
        shutil.copy(skip_pdf, output_pdf)
    except CalledProcessError as e:
        tesseract_log_output(log, e.output, input_image)
        if 'Image too large' in e.output:
            shutil.copy(skip_pdf, output_pdf)
            return
        raise e from e
    else:
        tesseract_log_output(log, stdout, input_image)
