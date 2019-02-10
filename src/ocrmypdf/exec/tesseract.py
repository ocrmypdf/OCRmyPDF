# © 2017 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import sys
from collections import namedtuple
from contextlib import suppress
from functools import lru_cache
from os import fspath
from subprocess import (
    PIPE,
    STDOUT,
    CalledProcessError,
    TimeoutExpired,
    check_output,
    run,
)
from textwrap import dedent

from . import get_version
from ..exceptions import MissingDependencyError, TesseractConfigError
from ..helpers import page_number

OrientationConfidence = namedtuple('OrientationConfidence', ('angle', 'confidence'))

HOCR_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title></title>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
  <meta name='ocr-system' content='tesseract 4.0.0' />
  <meta name='ocr-capabilities' content='ocr_page ocr_carea ocr_par ocr_line ocrx_word ocrp_wconf'/>
</head>
<body>
  <div class='ocr_page' id='page_1' title='image "_blank.png"; bbox 0 0 {0} {1}; ppageno 0'>
  </div>
 </body>
</html>
"""


@lru_cache(maxsize=1)
def version():
    return get_version('tesseract', regex=r'tesseract\s(.+)')


def v4():
    "Is this Tesseract v4.0?"
    return version() >= '4'


@lru_cache(maxsize=1)
def has_textonly_pdf():
    """Does Tesseract have textonly_pdf capability?

    Available in v4.00.00alpha since January 2017. Best to
    parse the parameter list
    """
    args_tess = ['tesseract', '--print-parameters', 'pdf']
    params = ''
    try:
        params = check_output(args_tess, universal_newlines=True, stderr=STDOUT)
    except CalledProcessError as e:
        print("Could not --print-parameters from tesseract", file=sys.stderr)
        raise MissingDependencyError from e
    if 'textonly_pdf' in params:
        return True
    return False


@lru_cache(maxsize=1)
def languages():
    def lang_error(output):
        msg = dedent(
            """Tesseract failed to report available languages.
        Output from Tesseract:
        -----------
        """
        )
        msg += output
        print(msg, file=sys.stderr)

    args_tess = ['tesseract', '--list-langs']
    try:
        proc = run(
            args_tess, universal_newlines=True, stdout=PIPE, stderr=STDOUT, check=True
        )
        output = proc.stdout
    except CalledProcessError as e:
        lang_error(e.output)
        raise MissingDependencyError from e

    header, *rest = output.splitlines()
    if not header.startswith('List of available languages'):
        lang_error(output)
        raise MissingDependencyError
    return set(lang.strip() for lang in rest)


def tess_base_args(langs, engine_mode):
    args = ['tesseract']
    if langs:
        args.extend(['-l', '+'.join(langs)])
    if engine_mode is not None and v4():
        args.extend(['--oem', str(engine_mode)])
    return args


def get_orientation(input_file, engine_mode, timeout: float, log):
    args_tesseract = tess_base_args(['osd'], engine_mode) + [
        '--psm',
        '0',
        fspath(input_file),
        'stdout',
    ]

    try:
        stdout = check_output(args_tesseract, stderr=STDOUT, timeout=timeout)
    except TimeoutExpired:
        return OrientationConfidence(angle=0, confidence=0.0)
    except CalledProcessError as e:
        tesseract_log_output(log, e.output, input_file)
        if (
            b'Too few characters. Skipping this page' in e.output
            or b'Image too large' in e.output
        ):
            return OrientationConfidence(0, 0)
        raise e from e
    else:
        osd = {}
        for line in stdout.decode().splitlines():
            line = line.strip()
            parts = line.split(':', maxsplit=2)
            if len(parts) == 2:
                osd[parts[0].strip()] = parts[1].strip()

        angle = int(osd.get('Orientation in degrees', 0))
        oc = OrientationConfidence(
            angle=angle, confidence=float(osd.get('Orientation confidence', 0))
        )
        return oc


def tesseract_log_output(log, stdout, input_file):
    prefix = f"{(page_number(input_file)):4d}: [tesseract] "

    try:
        text = stdout.decode()
    except UnicodeDecodeError:
        log.error(
            prefix
            + "command line output was not utf-8. "
            + "This usually means Tesseract's language packs do not match "
            "the installed version of Tesseract."
        )
        text = stdout.decode('utf-8', 'backslashreplace')

    lines = text.splitlines()
    for line in lines:
        if line.startswith("Tesseract Open Source"):
            continue
        elif line.startswith("Warning in pixReadMem"):
            continue
        elif 'diacritics' in line:
            log.warning(prefix + "lots of diacritics - possibly poor OCR")
        elif line.startswith('OSD: Weak margin'):
            log.warning(prefix + "unsure about page orientation")
        elif 'Error in pixScanForForeground' in line:
            pass  # Appears to be spurious/problem with nonwhite borders
        elif 'Error in boxClipToRectangle' in line:
            pass  # Always appears with pixScanForForeground message
        elif 'parameter not found: ' in line.lower():
            log.error(prefix + line.strip())
            problem = line.split('found: ')[1]
            raise TesseractConfigError(problem)
        elif 'error' in line.lower() or 'exception' in line.lower():
            log.error(prefix + line.strip())
        elif 'warning' in line.lower():
            log.warning(prefix + line.strip())
        elif 'read_params_file' in line.lower():
            log.error(prefix + line.strip())
        else:
            log.info(prefix + line.strip())


def page_timedout(log, input_file, timeout):
    if timeout == 0:
        return
    prefix = f"{(page_number(input_file)):4d}: [tesseract] "
    log.warning(prefix + " took too long to OCR - skipping")


def _generate_null_hocr(output_hocr, output_sidecar, image):
    """Produce a .hocr file that reports no text detected on a page that is
    the same size as the input image."""
    from PIL import Image

    im = Image.open(image)
    w, h = im.size

    with open(output_hocr, 'w', encoding="utf-8") as f:
        f.write(HOCR_TEMPLATE.format(w, h))
    with open(output_sidecar, 'w', encoding='utf-8') as f:
        f.write('[skipped page]')


def generate_hocr(
    input_file,
    output_files,
    language: list,
    engine_mode,
    tessconfig: list,
    timeout: float,
    pagesegmode: int,
    user_words,
    user_patterns,
    log,
):

    output_hocr = next(o for o in output_files if o.endswith('.hocr'))
    output_sidecar = next(o for o in output_files if o.endswith('.txt'))
    prefix = os.path.splitext(output_hocr)[0]

    args_tesseract = tess_base_args(language, engine_mode)

    if pagesegmode is not None:
        args_tesseract.extend(['--psm', str(pagesegmode)])

    if user_words:
        args_tesseract.extend(['--user-words', user_words])

    if user_patterns:
        args_tesseract.extend(['--user-patterns', user_patterns])

    # Reminder: test suite tesseract spoofers will break after any changes
    # to the number of order parameters here
    args_tesseract.extend([input_file, prefix, 'hocr', 'txt'] + tessconfig)
    try:
        log.debug(args_tesseract)
        stdout = check_output(args_tesseract, stderr=STDOUT, timeout=timeout)
    except TimeoutExpired:
        # Generate a HOCR file with no recognized text if tesseract times out
        # Temporary workaround to hocrTransform not being able to function if
        # it does not have a valid hOCR file.
        page_timedout(log, input_file, timeout)
        _generate_null_hocr(output_hocr, output_sidecar, input_file)
    except CalledProcessError as e:
        tesseract_log_output(log, e.output, input_file)
        if b'Image too large' in e.output:
            _generate_null_hocr(output_hocr, output_sidecar, input_file)
            return

        raise e from e
    else:
        tesseract_log_output(log, stdout, input_file)
        # The sidecar text file will get the suffix .txt; rename it to
        # whatever caller wants it named
        if os.path.exists(prefix + '.txt'):
            shutil.move(prefix + '.txt', output_sidecar)


def use_skip_page(text_only, skip_pdf, output_pdf, output_text):
    with open(output_text, 'w') as f:
        f.write('[skipped page]')

    if skip_pdf and not text_only:
        # Substitute a "skipped page"
        with suppress(FileNotFoundError):
            os.remove(output_pdf)  # In case it was partially created
        os.symlink(skip_pdf, output_pdf)
        return

    # Or normally, just write a 0 byte file to the output to indicate a skip
    with open(output_pdf, 'wb') as out:
        out.write(b'')


def generate_pdf(
    *,
    input_image,
    skip_pdf=None,
    output_pdf,
    output_text,
    language: list,
    engine_mode,
    text_only: bool,
    tessconfig: list,
    timeout: float,
    pagesegmode: int,
    user_words,
    user_patterns,
    log,
):
    '''Use Tesseract to render a PDF.

    input_image -- image to analyze
    skip_pdf -- if we time out, use this file as output
    output_pdf -- file to generate
    output_text -- OCR text file
    language -- list of languages to consider
    engine_mode -- engine mode argument for tess v4
    text_only -- enable tesseract text only mode?
    tessconfig -- tesseract configuration
    timeout -- timeout (seconds)
    log -- logger object
    '''

    args_tesseract = tess_base_args(language, engine_mode)

    if pagesegmode is not None:
        args_tesseract.extend(['--psm', str(pagesegmode)])

    if text_only and has_textonly_pdf():
        args_tesseract.extend(['-c', 'textonly_pdf=1'])

    if user_words:
        args_tesseract.extend(['--user-words', user_words])

    if user_patterns:
        args_tesseract.extend(['--user-patterns', user_patterns])

    prefix = os.path.splitext(output_pdf)[0]  # Tesseract appends suffixes

    # Reminder: test suite tesseract spoofers might break after any changes
    # to the number of order parameters here

    args_tesseract.extend([input_image, prefix, 'pdf', 'txt'] + tessconfig)

    try:
        log.debug(args_tesseract)
        stdout = check_output(args_tesseract, stderr=STDOUT, timeout=timeout)
        if os.path.exists(prefix + '.txt'):
            shutil.move(prefix + '.txt', output_text)
    except TimeoutExpired:
        page_timedout(log, input_image, timeout)
        use_skip_page(text_only, skip_pdf, output_pdf, output_text)
    except CalledProcessError as e:
        tesseract_log_output(log, e.output, input_image)
        if b'Image too large' in e.output:
            use_skip_page(text_only, skip_pdf, output_pdf, output_text)
            return
        raise e from e
    else:
        tesseract_log_output(log, stdout, input_image)
