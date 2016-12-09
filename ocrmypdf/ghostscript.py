#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE, STDOUT, check_call
from shutil import copy
from . import get_program
from .pdfa import SRGB_ICC_PROFILE


def rasterize_pdf(input_file, output_file, xres, yres, raster_device, log,
                  pageno=1):
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
            '-r{0}x{1}'.format(str(round(xres)), str(round(yres))),
            input_file
        ]

        p = Popen(args_gs, close_fds=True, stdout=PIPE, stderr=STDOUT,
                  universal_newlines=True)
        stdout, _ = p.communicate()
        if 'error' in stdout:
            log.error(stdout)  # Ghostscript puts errors in stdout
        else:
            log.debug(stdout)

        if p.returncode == 0:
            copy(tmp.name, output_file)
        else:
            log.error('Ghostscript rendering failed')


def generate_pdfa(pdf_pages, output_file, log, threads=1):
    with NamedTemporaryFile(delete=True) as gs_pdf:
        args_gs = [
            get_program("gs"),
            "-dQUIET",
            "-dBATCH",
            "-dNOPAUSE",
            '-dNumRenderingThreads=' + str(threads),
            "-sDEVICE=pdfwrite",
            "-dAutoRotatePages=/None",
            "-sColorConversionStrategy=/RGB",
            "-sProcessColorModel=DeviceRGB",
            "-dJPEGQ=95",
            "-dPDFA=2",
            "-dPDFACompatibilityPolicy=1",
            "-sOutputFile=" + gs_pdf.name,
        ]
        args_gs.extend(pdf_pages)
        p = Popen(args_gs, close_fds=True, stdout=PIPE, stderr=STDOUT,
                  universal_newlines=True)
        stdout, _ = p.communicate()

        if 'error' in stdout:
            log.error(stdout)
        elif 'overprint mode not set' in stdout:
            # Unless someone is going to print PDF/A documents on a
            # magical sRGB printer I can't see the removal of overprinting
            # being a problem....
            log.debug(
                "Ghostscript had to remove PDF 'overprinting' from the "
                "input file to complete PDF/A conversion. "
                )
        else:
            log.debug(stdout)

        if p.returncode == 0:
            # Ghostscript does not change return code when it fails to create
            # PDF/A - check PDF/A status elsewhere
            copy(gs_pdf.name, output_file)
        else:
            log.error('Ghostscript PDF/A failed')
