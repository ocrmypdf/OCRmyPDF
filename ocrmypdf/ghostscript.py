#!/usr/bin/env python3
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE, check_call
from shutil import copy


def rasterize_pdf(input_file, output_file, xres, yres, raster_device, log):
    with NamedTemporaryFile(delete=True) as tmp:
        args_gs = [
            'gs',
            '-dBATCH', '-dNOPAUSE',
            '-sDEVICE=%s' % raster_device,
            '-o', tmp.name,
            '-r{0}x{1}'.format(str(xres), str(yres)),
            input_file
        ]

        p = Popen(args_gs, close_fds=True, stdout=PIPE, stderr=PIPE,
                  universal_newlines=True)
        stdout, stderr = p.communicate()
        if stdout:
            log.debug(stdout)
        if stderr:
            log.error(stderr)

        if p.returncode == 0:
            copy(tmp.name, output_file)
        else:
            log.error('Ghostscript rendering failed')


def generate_pdfa(pdf_pages, output_file):
    with NamedTemporaryFile(delete=True) as gs_pdf:
        args_gs = [
            "gs",
            "-dQUIET",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-sColorConversionStrategy=/RGB",
            "-sProcessColorModel=DeviceRGB",
            "-dPDFA",
            "-sPDFACompatibilityPolicy=2",
            "-sOutputICCProfile=srgb.icc",
            "-sOutputFile=" + gs_pdf.name,
        ]
        args_gs.extend(pdf_pages)
        check_call(args_gs)
        copy(gs_pdf.name, output_file)
