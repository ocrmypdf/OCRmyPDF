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

"""Interface to Ghostscript executable"""

import logging
import os
import re
from io import BytesIO
from os import fspath
from pathlib import Path
from shutil import which
from subprocess import PIPE, CalledProcessError

from PIL import Image

from ocrmypdf.exceptions import MissingDependencyError, SubprocessOutputError
from ocrmypdf.helpers import Resolution
from ocrmypdf.subprocess import get_version, run

log = logging.getLogger(__name__)

GS = 'gs'
if os.name == 'nt':
    GS = which('gswin64c')
    if not GS:
        GS = which('gswin32c')
        if not GS:
            raise MissingDependencyError(
                """
                ---------------------------------------------------------------------
                This error normally occurs when ocrmypdf can't Ghostscript.  Please
                ensure Ghostscript is installed and its location is added to the
                system PATH environment variable.

                For details see:
                    https://ocrmypdf.readthedocs.io/en/latest/installation.html
                ---------------------------------------------------------------------
                """
            )
    GS = Path(GS).stem


def version():
    return get_version(GS)


def jpeg_passthrough_available() -> bool:
    """Returns True if the installed version of Ghostscript supports JPEG passthru

    Prior to 9.23, Ghostscript decode and re-encoded JPEGs internally. In 9.23
    it gained the ability to keep JPEGs unmodified. However, the 9.23
    implementation was buggy and would deletes the last two bytes of images in
    some cases, as reported here.
    https://bugs.ghostscript.com/show_bug.cgi?id=699216

    The issue was fixed for 9.24, hence that is the first version we consider
    the feature available. (However, we don't use 9.24 at all, so the first
    version that allows JPEG passthrough is 9.25.

    """
    return version() >= '9.24'


def _gs_error_reported(stream) -> bool:
    return re.search(r'error', stream, flags=re.IGNORECASE)


def rasterize_pdf(
    input_file: os.PathLike,
    output_file: os.PathLike,
    *,
    raster_device: str,
    raster_dpi: Resolution,
    pageno: int = 1,
    page_dpi: Resolution = None,
    rotation: int = None,
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
        elif stderr:
            log.debug(stderr)

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


def generate_pdfa(
    pdf_pages,
    output_file: os.PathLike,
    compression: str,
    pdf_version: str = '1.5',
    pdfa_part: str = '2',
):
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

    # Older versions of Ghostscript expect a leading slash in
    # sColorConversionStrategy, newer ones should not have it. See Ghostscript
    # git commit fe1c025d.
    strategy = 'RGB' if version() >= '9.19' else '/RGB'

    if version() == '9.23':
        # 9.23: new feature JPEG passthrough is broken in some cases, best to
        # disable it always
        # https://bugs.ghostscript.com/show_bug.cgi?id=699216
        compression_args.append('-dPassThroughJPEGImages=false')

    # nb no need to specify ProcessColorModel when ColorConversionStrategy
    # is set; see:
    # https://bugs.ghostscript.com/show_bug.cgi?id=699392
    args_gs = (
        [
            GS,
            "-dQUIET",
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
            p = run(args_gs, stdout=output, stderr=PIPE, check=True)
    except CalledProcessError as e:
        # Ghostscript does not change return code when it fails to create
        # PDF/A - check PDF/A status elsewhere
        log.error(e.stderr.decode(errors='replace'))
        raise SubprocessOutputError('Ghostscript PDF/A rendering failed')
    else:
        stderr = p.stderr.decode('utf-8', errors='replace')
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
        elif 'overprint mode not set' in stderr:
            # Unless someone is going to print PDF/A documents on a
            # magical sRGB printer I can't see the removal of overprinting
            # being a problem....
            log.debug(
                "Ghostscript had to remove PDF 'overprinting' from the "
                "input file to complete PDF/A conversion. "
            )
