#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from tempfile import NamedTemporaryFile
from subprocess import run, PIPE, STDOUT, CalledProcessError
from shutil import copy
from functools import lru_cache
import re
import sys
from math import isclose
from . import get_program
from ..exceptions import SubprocessOutputError
from PIL import Image


@lru_cache(maxsize=1)
def version():
    args_gs = [
        get_program('gs'),
        '--version'
    ]
    try:
        version = check_output(
                args_gs, close_fds=True, universal_newlines=True,
                stderr=STDOUT)
    except CalledProcessError as e:
        print("Could not find Ghostscript executable on system PATH.",
              file=sys.stderr)
        raise MissingDependencyError from e

    return version.strip()


def _gs_error_reported(stream):
    return re.search(r'error', stream, flags=re.IGNORECASE)


def _correct_image_size(input_fp, output_file, res, int_res, log):
    # If the output size was reduced due to rounding DPI to an
    # integer, resize the image to its expected size
    input_fp.seek(0)
    with Image.open(input_fp) as im:
        expected_size = round(res[0] / int_res[0] * im.size[0]), \
                        round(res[1] / int_res[1] * im.size[1])
        log.info(im.size)
        log.info(expected_size)
        im.resize(expected_size).save(output_file)


def rasterize_pdf(input_file, output_file, xres, yres, raster_device, log,
                  pageno=1):
    res = xres, yres
    int_res = round(xres), round(yres)
    with NamedTemporaryFile(delete=True) as tmp:
        args_gs = [
            get_program('gs'),
            '-dQUIET',
            '-dSAFER',
            '-dBATCH',
            '-dNOPAUSE',
            '-sDEVICE=%s' % raster_device,
            '-dFirstPage=%i' % pageno,
            '-dLastPage=%i' % pageno,
            '-o', tmp.name,
            '-r{0}x{1}'.format(str(int_res[0]), str(int_res[1])),
            input_file
        ]

        p = run(args_gs, stdout=PIPE, stderr=STDOUT,
                universal_newlines=True)
        if _gs_error_reported(p.stdout):
            log.error(p.stdout)
        else:
            log.debug(p.stdout)

        if p.returncode == 0:
            if isclose(int_res[0], res[0], abs_tol=0.1) and \
                    isclose(int_res[1], res[1], abs_tol=0.1):
                copy(tmp.name, output_file)
            else:
                # If the output size was reduced due to rounding DPI to an
                # integer, resize the image to its expected size
                _correct_image_size(tmp, output_file, res, int_res, log)
        else:
            log.error('Ghostscript rasterizing failed')
            raise SubprocessOutputError()


def generate_pdfa(*, pdf_version, pdf_pages, output_file, compression, log,
                  threads=1):
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

    with NamedTemporaryFile(delete=True) as gs_pdf:
        args_gs = [
            get_program("gs"),
            "-dQUIET",
            "-dBATCH",
            "-dNOPAUSE",
            '-dCompatibilityLevel=' + str(pdf_version),
            '-dNumRenderingThreads=' + str(threads),
            "-sDEVICE=pdfwrite",
            "-dAutoRotatePages=/None",
            "-sColorConversionStrategy=/RGB",
            "-sProcessColorModel=DeviceRGB"
        ] + compression_args + [
            "-dJPEGQ=95",
            "-dPDFA=2",
            "-dPDFACompatibilityPolicy=1",
            "-sOutputFile=" + gs_pdf.name,
        ]
        args_gs.extend(pdf_pages)
        p = run(args_gs, stdout=PIPE, stderr=STDOUT,
                universal_newlines=True)

        if _gs_error_reported(p.stdout):
            log.error(p.stdout)
        elif 'overprint mode not set' in p.stdout:
            # Unless someone is going to print PDF/A documents on a
            # magical sRGB printer I can't see the removal of overprinting
            # being a problem....
            log.debug(
                "Ghostscript had to remove PDF 'overprinting' from the "
                "input file to complete PDF/A conversion. "
                )
        else:
            log.debug(p.stdout)

        if p.returncode == 0:
            # Ghostscript does not change return code when it fails to create
            # PDF/A - check PDF/A status elsewhere
            copy(gs_pdf.name, output_file)
        else:
            log.error('Ghostscript PDF/A rendering failed')
            raise SubprocessOutputError()