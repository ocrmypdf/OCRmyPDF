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

"""Interface to Tesseract executable"""

import logging
import os
import shutil
from collections import namedtuple
from os import fspath
from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError, TimeoutExpired
from typing import List

from PIL import Image

from ocrmypdf.exceptions import (
    MissingDependencyError,
    SubprocessOutputError,
    TesseractConfigError,
)
from ocrmypdf.subprocess import get_version, run

log = logging.getLogger(__name__)

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


class TesseractLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs['extra'] = self.extra
        return '[tesseract] %s' % (msg), kwargs


def version():
    return get_version('tesseract', regex=r'tesseract\s(.+)')


def has_textonly_pdf(langs=None):
    """Does Tesseract have textonly_pdf capability?

    Available in v4.00.00alpha since January 2017. Best to
    parse the parameter list.
    """
    args_tess = tess_base_args(langs, engine_mode=None) + ['--print-parameters', 'pdf']
    params = ''
    try:
        proc = run(args_tess, check=True, stdout=PIPE, stderr=STDOUT)
        params = proc.stdout
    except CalledProcessError as e:
        raise MissingDependencyError(
            "Could not --print-parameters from tesseract. This can happen if the "
            "TESSDATA_PREFIX environment is not set to a valid tessdata folder. "
        ) from e
    if b'textonly_pdf' in params:
        return True
    return False


def has_user_words():
    """Does Tesseract have --user-words capability?

    Not available in 4.0, but available in 4.1. Also available in 3.x, but
    we no longer support 3.x.
    """
    return version() >= '4.1'


def get_languages():
    def lang_error(output):
        msg = (
            "Tesseract failed to report available languages.\n"
            "Output from Tesseract:\n"
            "-----------\n"
        )
        msg += output
        return msg

    args_tess = ['tesseract', '--list-langs']
    try:
        proc = run(
            args_tess, universal_newlines=True, stdout=PIPE, stderr=STDOUT, check=True
        )
        output = proc.stdout
    except CalledProcessError as e:
        raise MissingDependencyError(lang_error(e.output)) from e

    for line in output.splitlines():
        if line.startswith('Error'):
            raise MissingDependencyError(lang_error(output))
    _header, *rest = output.splitlines()
    return set(lang.strip() for lang in rest)


def tess_base_args(langs: List[str], engine_mode) -> List[str]:
    args = ['tesseract']
    if langs:
        args.extend(['-l', '+'.join(langs)])
    if engine_mode is not None:
        args.extend(['--oem', str(engine_mode)])
    return args


def get_orientation(input_file: Path, engine_mode, timeout: float):
    args_tesseract = tess_base_args(['osd'], engine_mode) + [
        '--psm',
        '0',
        fspath(input_file),
        'stdout',
    ]

    try:
        p = run(args_tesseract, stdout=PIPE, stderr=STDOUT, timeout=timeout, check=True)
        stdout = p.stdout
    except TimeoutExpired:
        return OrientationConfidence(angle=0, confidence=0.0)
    except CalledProcessError as e:
        tesseract_log_output(e.stdout)
        tesseract_log_output(e.stderr)
        if (
            b'Too few characters. Skipping this page' in e.output
            or b'Image too large' in e.output
        ):
            return OrientationConfidence(0, 0)
        raise SubprocessOutputError() from e
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


def tesseract_log_output(stream):
    tlog = TesseractLoggerAdapter(
        log, extra=log.extra if hasattr(log, 'extra') else None
    )

    if not stream:
        return
    try:
        text = stream.decode()
    except UnicodeDecodeError:
        text = stream.decode('utf-8', 'ignore')

    lines = text.splitlines()
    for line in lines:
        if line.startswith("Tesseract Open Source"):
            continue
        elif line.startswith("Warning in pixReadMem"):
            continue
        elif 'diacritics' in line:
            tlog.warning("lots of diacritics - possibly poor OCR")
        elif line.startswith('OSD: Weak margin'):
            tlog.warning("unsure about page orientation")
        elif 'Error in pixScanForForeground' in line:
            pass  # Appears to be spurious/problem with nonwhite borders
        elif 'Error in boxClipToRectangle' in line:
            pass  # Always appears with pixScanForForeground message
        elif 'parameter not found: ' in line.lower():
            tlog.error(line.strip())
            problem = line.split('found: ')[1]
            raise TesseractConfigError(problem)
        elif 'error' in line.lower() or 'exception' in line.lower():
            tlog.error(line.strip())
        elif 'warning' in line.lower():
            tlog.warning(line.strip())
        elif 'read_params_file' in line.lower():
            tlog.error(line.strip())
        else:
            tlog.info(line.strip())


def page_timedout(timeout):
    if timeout == 0:
        return
    log.warning("[tesseract] took too long to OCR - skipping")


def _generate_null_hocr(output_hocr, output_text, image):
    """Produce a .hocr file that reports no text detected on a page that is
    the same size as the input image."""
    with Image.open(image) as im:
        w, h = im.size

    output_hocr.write_text(HOCR_TEMPLATE.format(w, h), encoding='utf-8')
    output_text.write_text('[skipped page]', encoding='utf-8')


def generate_hocr(
    input_file: Path,
    output_hocr: Path,
    output_text: Path,
    languages: list,
    engine_mode,
    tessconfig: list,
    timeout: float,
    pagesegmode: int,
    user_words,
    user_patterns,
):
    prefix = output_hocr.with_suffix('')

    args_tesseract = tess_base_args(languages, engine_mode)

    if pagesegmode is not None:
        args_tesseract.extend(['--psm', str(pagesegmode)])

    if user_words:
        args_tesseract.extend(['--user-words', user_words])

    if user_patterns:
        args_tesseract.extend(['--user-patterns', user_patterns])

    # Reminder: test suite tesseract test plugins will break after any changes
    # to the number of order parameters here
    args_tesseract.extend([input_file, prefix, 'hocr', 'txt'] + tessconfig)
    try:
        p = run(args_tesseract, stdout=PIPE, stderr=STDOUT, timeout=timeout, check=True)
        stdout = p.stdout
    except TimeoutExpired:
        # Generate a HOCR file with no recognized text if tesseract times out
        # Temporary workaround to hocrTransform not being able to function if
        # it does not have a valid hOCR file.
        page_timedout(timeout)
        _generate_null_hocr(output_hocr, output_text, input_file)
    except CalledProcessError as e:
        tesseract_log_output(e.output)
        if b'Image too large' in e.output:
            _generate_null_hocr(output_hocr, output_text, input_file)
            return

        raise SubprocessOutputError() from e
    else:
        tesseract_log_output(stdout)
        # The sidecar text file will get the suffix .txt; rename it to
        # whatever caller wants it named
        if prefix.with_suffix('.txt').exists():
            shutil.move(prefix.with_suffix('.txt'), output_text)


def use_skip_page(output_pdf, output_text):
    output_text.write_text('[skipped page]', encoding='utf-8')

    # A 0 byte file to the output to indicate a skip
    output_pdf.write_bytes(b'')


def generate_pdf(
    *,
    input_file: Path,
    output_pdf: Path,
    output_text: Path,
    languages: List[str],
    engine_mode,
    tessconfig: List[str],
    timeout: float,
    pagesegmode: int,
    user_words,
    user_patterns,
):
    """Use Tesseract to render a PDF.

    input_file -- image to analyze
    output_pdf -- file to generate
    output_text -- OCR text file
    languages -- list of languages to consider
    engine_mode -- engine mode argument for tess v4
    tessconfig -- tesseract configuration
    timeout -- timeout (seconds)
    """

    args_tesseract = tess_base_args(languages, engine_mode)

    if pagesegmode is not None:
        args_tesseract.extend(['--psm', str(pagesegmode)])

    args_tesseract.extend(['-c', 'textonly_pdf=1'])

    if user_words:
        args_tesseract.extend(['--user-words', user_words])

    if user_patterns:
        args_tesseract.extend(['--user-patterns', user_patterns])

    prefix = os.path.splitext(output_pdf)[0]  # Tesseract appends suffixes

    # Reminder: test suite tesseract test plugins might break after any changes
    # to the number of order parameters here

    args_tesseract.extend([input_file, prefix, 'pdf', 'txt'] + tessconfig)
    try:
        p = run(args_tesseract, stdout=PIPE, stderr=STDOUT, timeout=timeout, check=True)
        stdout = p.stdout
        if os.path.exists(prefix + '.txt'):
            shutil.move(prefix + '.txt', output_text)
    except TimeoutExpired:
        page_timedout(timeout)
        use_skip_page(output_pdf, output_text)
    except CalledProcessError as e:
        tesseract_log_output(e.output)
        if b'Image too large' in e.output:
            use_skip_page(output_pdf, output_text)
            return
        raise SubprocessOutputError() from e
    else:
        tesseract_log_output(stdout)
