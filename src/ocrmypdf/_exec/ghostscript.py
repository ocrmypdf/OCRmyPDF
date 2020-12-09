# © 2017 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Interface to Ghostscript executable"""

import logging
import os
import re
from io import BytesIO
from os import fspath
from pathlib import Path
from shutil import which
from subprocess import PIPE, CalledProcessError
from typing import Optional

from PIL import Image

from ocrmypdf.exceptions import MissingDependencyError, SubprocessOutputError
from ocrmypdf.helpers import Resolution
from ocrmypdf.subprocess import get_version, run, run_polling_stderr

log = logging.getLogger(__name__)

missing_gs_error = """
---------------------------------------------------------------------
This error normally occurs when ocrmypdf find can't Ghostscript.
Please ensure Ghostscript is installed and its location is added to
the system PATH environment variable.

For details see:
    https://ocrmypdf.readthedocs.io/en/latest/installation.html
---------------------------------------------------------------------
"""

_gswin = None
if os.name == 'nt':
    _gswin = which('gswin64c')
    if not _gswin:
        _gswin = which('gswin32c')
        if not _gswin:
            raise MissingDependencyError(missing_gs_error)
    _gswin = Path(_gswin).stem

GS = _gswin if _gswin else 'gs'
del _gswin


def version():
    return get_version(GS)


def jpeg_passthrough_available() -> bool:
    """Returns True if the installed version of Ghostscript supports JPEG passthru

    Prior to 9.23, Ghostscript decoded and re-encoded JPEGs internally. In 9.23
    it gained the ability to keep JPEGs unmodified. However, the 9.23
    implementation was buggy and would deletes the last two bytes of images in
    some cases, as reported here.
    https://bugs.ghostscript.com/show_bug.cgi?id=699216

    The issue was fixed for 9.24, hence that is the first version we consider
    the feature available. (Ghostscript 9.24 has its own problems is blacklisted.)
    """
    return version() >= '9.24'


def _gs_error_reported(stream) -> bool:
    return True if re.search(r'error', stream, flags=re.IGNORECASE) else False


def rasterize_pdf(
    input_file: os.PathLike,
    output_file: os.PathLike,
    *,
    raster_device: str,
    raster_dpi: Resolution,
    pageno: int = 1,
    page_dpi: Optional[Resolution] = None,
    rotation: Optional[int] = None,
    filter_vector: bool = False,
):
    """Rasterize one page of a PDF at resolution raster_dpi in canvas units."""
    raster_dpi = raster_dpi.round(6)
    if not page_dpi:
        page_dpi = raster_dpi

    args_gs = (
        [
            GS,
            '-dQUIET',
            '-dSAFER',
            '-dBATCH',
            '-dNOPAUSE',
            f'-sDEVICE={raster_device}',
            f'-dFirstPage={pageno}',
            f'-dLastPage={pageno}',
            f'-r{raster_dpi.x:f}x{raster_dpi.y:f}',
        ]
        + (['-dFILTERVECTOR'] if filter_vector else [])
        + [
            '-o',
            '-',
            '-sstdout=%stderr',
            '-dAutoRotatePages=/None',  # Probably has no effect on raster
            '-f',
            fspath(input_file),
        ]
    )

    try:
        p = run(args_gs, stdout=PIPE, stderr=PIPE, check=True)
    except CalledProcessError as e:
        log.error(e.stderr.decode(errors='replace'))
        raise SubprocessOutputError('Ghostscript rasterizing failed')
    else:
        stderr = p.stderr.decode(errors='replace')
        if _gs_error_reported(stderr):
            log.error(stderr)

    with Image.open(BytesIO(p.stdout)) as im:
        if rotation is not None:
            log.debug("Rotating output by %i", rotation)
            # rotation is a clockwise angle and Image.ROTATE_* is
            # counterclockwise so this cancels out the rotation
            if rotation == 90:
                im = im.transpose(Image.ROTATE_90)
            elif rotation == 180:
                im = im.transpose(Image.ROTATE_180)
            elif rotation == 270:
                im = im.transpose(Image.ROTATE_270)
            if rotation % 180 == 90:
                page_dpi = page_dpi.flip_axis()
        im.save(fspath(output_file), dpi=page_dpi)


class GhostscriptFollower:
    re_process = re.compile(r"Processing pages \d+ through (\d+).")
    re_page = re.compile(r"Page (\d+)")

    def __init__(self, progressbar_class):
        self.count = 0
        self.progressbar_class = progressbar_class
        self.progressbar = None

    def __call__(self, line):
        if not self.progressbar_class:
            return
        if not self.progressbar:
            m = self.re_process.match(line.strip())
            if m:
                self.count = int(m.group(1))
                self.progressbar = self.progressbar_class(
                    total=self.count, desc="PDF/A conversion", unit='page'
                )
                return
        else:
            m = self.re_page.match(line.strip())
            if m:
                self.progressbar.update()


def generate_pdfa(
    pdf_pages,
    output_file: os.PathLike,
    *,
    compression: str,
    pdf_version: str = '1.5',
    pdfa_part: str = '2',
    progressbar_class=None,
):
    # Ghostscript's compression is all or nothing. We can either force all images
    # to JPEG, force all to Flate/PNG, or let it decide how to encode the images.
    # In most case it's best to let it decide.
    compression_args = []
    if compression == 'jpeg':
        compression_args = [
            "-dAutoFilterColorImages=false",
            "-dColorImageFilter=/DCTEncode",
            "-dAutoFilterGrayImages=false",
            "-dGrayImageFilter=/DCTEncode",
        ]
    elif compression == 'lossless':
        compression_args = [
            "-dAutoFilterColorImages=false",
            "-dColorImageFilter=/FlateEncode",
            "-dAutoFilterGrayImages=false",
            "-dGrayImageFilter=/FlateEncode",
        ]
    else:
        compression_args = [
            "-dAutoFilterColorImages=true",
            "-dAutoFilterGrayImages=true",
        ]

    strategy = 'LeaveColorUnchanged'
    # Older versions of Ghostscript expect a leading slash in
    # sColorConversionStrategy, newer ones should not have it. See Ghostscript
    # git commit fe1c025d.
    strategy = ('/' + strategy) if version() < '9.19' else strategy

    if version() == '9.23':
        # 9.23: added JPEG passthrough as a new feature, but with a bug that
        # incorrectly formats some images. Fixed as of 9.24. So we disable this
        # feature for 9.23.
        # https://bugs.ghostscript.com/show_bug.cgi?id=699216
        compression_args.append('-dPassThroughJPEGImages=false')

    # nb no need to specify ProcessColorModel when ColorConversionStrategy
    # is set; see:
    # https://bugs.ghostscript.com/show_bug.cgi?id=699392
    args_gs = (
        [
            GS,
            "-dBATCH",
            "-dNOPAUSE",
            "-dSAFER",
            "-dCompatibilityLevel=" + str(pdf_version),
            "-sDEVICE=pdfwrite",
            "-dAutoRotatePages=/None",
            "-sColorConversionStrategy=" + strategy,
        ]
        + compression_args
        + [
            "-dJPEGQ=95",
            "-dPDFA=" + pdfa_part,
            "-dPDFACompatibilityPolicy=1",
            "-o",
            "-",
            "-sstdout=%stderr",
        ]
    )
    args_gs.extend(fspath(s) for s in pdf_pages)  # Stringify Path objs

    try:
        with Path(output_file).open('wb') as output:
            p = run_polling_stderr(
                args_gs,
                stdout=output,
                stderr=PIPE,
                check=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                callback=GhostscriptFollower(progressbar_class),
            )
    except CalledProcessError as e:
        # Ghostscript does not change return code when it fails to create
        # PDF/A - check PDF/A status elsewhere
        log.error(e.stderr)
        raise SubprocessOutputError('Ghostscript PDF/A rendering failed') from e
    else:
        stderr = p.stderr
        # If there is an error we log the whole stderr, except for filtering
        # duplicates.
        if _gs_error_reported(stderr):
            last_part = None
            repcount = 0
            for part in stderr.split('****'):
                if part != last_part:
                    if repcount > 1:
                        log.error(f"(previous error message repeated {repcount} times)")
                        repcount = 0
                    log.error(part)
                else:
                    repcount += 1
                last_part = part
