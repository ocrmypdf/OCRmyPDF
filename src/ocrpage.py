#!/usr/bin/env python3
# Reimplement ocrPage.sh as Python

import argparse
import logging
import sys
import os.path
from parse import parse

from subprocess import Popen, check_call, PIPE, CalledProcessError
try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

from tempfile import NamedTemporaryFile

from ruffus import transform, suffix, merge, active_if, regex, jobs_limit, \
    mkdir, formatter
import ruffus.cmdline as cmdline

basedir = os.path.dirname(os.path.realpath(__file__))

parser = cmdline.get_argparse(
    prog="ocrpage",
    description="Run OCR and related jobs on a single page of a PDF file")

parser.add_argument(
    'input_pdf',
    help="PDF file containing the page to be OCRed")
parser.add_argument(
    'page_info',
    help="Various characteristics of the page to be OCRed")
parser.add_argument(
    'num_pages',
    help="Total number of page of the PDF file (required for logger)")
parser.add_argument(
    'tmp_fld',
    help="Folder where the temporary files should be placed")
parser.add_argument(
    'verbosity', type=int,
    help="Requested verbosity")
parser.add_argument(
    'language',
    help="Language of the file to be OCRed")
parser.add_argument(
    'keep_tmp', type=int,
    help="Keep the temporary files after processing (helpful for debugging)")
parser.add_argument(
    'preprocess_deskew', type=int,
    help="Deskew the page to be OCRed")
parser.add_argument(
    'preprocess_clean', type=int,
    help="Clean the page to be OCRed")
parser.add_argument(
    'preprocess_cleantopdf', type=int,
    help="Put the cleaned paged in the OCRed PDF")
parser.add_argument(
    'oversampling_dpi', type=int,
    help="Oversampling resolution in dpi")
parser.add_argument(
    'pdf_noimg', type=int,
    help="Generate debug PDF pages with only the OCRed text and no image")
parser.add_argument(
    'force_ocr', type=int,
    help="Force to OCR, even if the page already contains fonts")
parser.add_argument(
    'skip_text', type=int,
    help="Skip OCR on pages that contain fonts and include the page anyway")
parser.add_argument(
    'tess_cfg_files', default='', nargs='*',
    help="Tesseract configuration")


options = parser.parse_args()

logger, logger_mutex = cmdline.setup_logging(__name__, options.log_file,
                                             options.verbose)


def pdf_get_pageinfo(infile, page, width_pt, height_pt):
    pageinfo = {}
    pageinfo['pageno'] = page
    pageinfo['width_inches'] = width_pt / 72.0
    pageinfo['height_inches'] = height_pt / 72.0
    pageinfo['images'] = []

    p_pdffonts = Popen(['pdffonts', '-f', str(page), '-l', str(page), infile],
                       close_fds=True, stdout=PIPE, stderr=PIPE,
                       universal_newlines=True)
    pdffonts, _ = p_pdffonts.communicate()
    if len(pdffonts.splitlines()) > 2:
        logger.info("Page already contains font data!")
        pageinfo['has_text'] = True
    else:
        pageinfo['has_text'] = False

    # pdfimages: get image dimensions
    p_pdfimages = Popen(['pdfimages', '-list', '-f', str(page), '-l',
                        str(page), str(infile)], close_fds=True, stdout=PIPE,
                        stderr=PIPE, universal_newlines=True)
    pdfimages, _ = p_pdfimages.communicate()
    for n, line in enumerate(pdfimages.splitlines()):
        if n <= 1:
            continue  # Skip first two lines

        r = parse('{page:1d} {num:1d} {imtype:>} {width:1d} {height:1d} ' +
                  '{color:>} {comp:1d} {bpc:1d} {enc:>} {interp:>} ' +
                  '{pdfobject:1d} {pdfid:1d} {bad_dpi_w:1d} {bad_dpi_h:1d} ' +
                  '{size:>} {ratio:>}', line)
        image = r.named
        # pdfimages calculates DPI as 0.26.0, but adds +1 to dpi_h
        # apparent bug, so calculate explicitly
        image['dpi_w'] = image['width'] / pageinfo['width_inches']
        image['dpi_h'] = image['height'] / pageinfo['height_inches']
        image['dpi'] = (image['dpi_w'] * image['dpi_h']) ** 0.5
        pageinfo['images'].append(image)

    xres = max(image['dpi_w'] for image in pageinfo['images'])
    yres = max(image['dpi_h'] for image in pageinfo['images'])
    pageinfo['xres'], pageinfo['yres'] = xres, yres
    pageinfo['width_pixels'] = int(round(xres * pageinfo['width_inches']))
    pageinfo['height_pixels'] = int(round(yres * pageinfo['height_inches']))

    return pageinfo

pageno, width_pt, height_pt = map(int, options.page_info.split(' ', 3))
pageinfo = pdf_get_pageinfo(options.input_pdf, pageno, width_pt, height_pt)


def re_symlink(input_file, soft_link_name, logger, logger_mutex):
    """
    Helper function: relinks soft symbolic link if necessary
    """
    # Guard against soft linking to oneself
    if input_file == soft_link_name:
        logger.debug("Warning: No symbolic link made. You are using " +
                     "the original data directory as the working directory.")
        return

    # Soft link already exists: delete for relink?
    if os.path.lexists(soft_link_name):
        # do not delete or overwrite real (non-soft link) file
        if not os.path.islink(soft_link_name):
            raise Exception("%s exists and is not a link" % soft_link_name)
        try:
            os.unlink(soft_link_name)
        except:
            with logger_mutex:
                logger.debug("Can't unlink %s" % (soft_link_name))
    with logger_mutex:
        logger.debug("os.symlink(%s, %s)" % (input_file, soft_link_name))

    # Create symbolic link using absolute path
    os.symlink(
        os.path.abspath(input_file),
        soft_link_name
    )


@jobs_limit(1)
@mkdir(options.tmp_fld)
@transform([options.input_pdf],
           formatter(),
           os.path.join(options.tmp_fld, "original{ext[0]}"))
def setup_working_directory(input_file, soft_link_name):
    with logger_mutex:
        logger.debug("Linking %(input_file)s -> %(soft_link_name)s" % locals())
    re_symlink(input_file, soft_link_name, logger, logger_mutex)


@transform(setup_working_directory,
           formatter(),
           "{path[0]}/%04i.pnm" % pageno)
def unpack_with_pdftoppm(
        input_file,
        output_file):
    force_ppm = True
    allow_jpeg = False

    colorspace = 'color'
    compression = 'deflate'
    output_format = 'tiff'
    if all(image['comp'] == 1 for image in pageinfo['images']):
        if all(image['bpc'] == 1 for image in pageinfo['images']):
            colorspace = 'mono'
            compression = 'deflate'
        elif not any(image['color'] == 'color'
                     for image in pageinfo['images']):
            colorspace = 'gray'

    if allow_jpeg and \
            all(image['enc'] == 'jpeg' for image in pageinfo['images']):
        output_format = 'jpeg'

    args_pdftoppm = [
        'pdftoppm',
        '-f', str(pageinfo['pageno']), '-l', str(pageinfo['pageno']),
        '-rx', str(pageinfo['xres']),
        '-ry', str(pageinfo['yres'])
    ]

    if not force_ppm:
        if output_format == 'tiff':
            args_pdftoppm.append('-tiff')
            if False and compression:
                args_pdftoppm.append('-tiffcompression')
                args_pdftoppm.append(compression)
        elif output_format == 'jpeg':
            args_pdftoppm.append('-jpeg')

    if colorspace == 'mono':
        args_pdftoppm.append('-mono')
    elif colorspace == 'gray':
        args_pdftoppm.append('-gray')

    args_pdftoppm.extend([str(input_file)])

    p = Popen(args_pdftoppm, close_fds=True, stdout=open(output_file, 'wb'),
              stderr=PIPE, universal_newlines=False)
    _, stderr = p.communicate()
    if stderr:
        from codecs import iterdecode
        with logger_mutex:
            logger.error(iterdecode(stderr, sys.getdefaultencoding(),
                                    errors='ignore'))
    if p.returncode != 0:
        raise CalledProcessError(p.returncode, args_pdftoppm)


@transform(unpack_with_pdftoppm, suffix(".pnm"), ".tif")
def convert_to_tiff(input_file, output_file):
    args_convert = [
        'convert',
        input_file,
        output_file
    ]
    check_call(args_convert)


@active_if(options.preprocess_deskew != 0)
@transform(convert_to_tiff, suffix(".tif"), ".deskewed.tif")
def deskew_imagemagick(input_file, output_file):
    args_convert = [
        'convert',
        input_file,
        '-deskew', '40%',
        '-gravity', 'center',
        '-extent', '{width_pixels}x{height_pixels}'.format(**pageinfo),
        '+repage',
        output_file
    ]

    p = Popen(args_convert, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    stdout, stderr = p.communicate()

    with logger_mutex:
        if stdout:
            logger.info(stdout)
        if stderr:
            logger.error(stderr)

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, args_convert)


def clean_unpaper(pageinfo, infile, prefix, output_folder):
    args_unpaper = [
        'unpaper',
        '--dpi', int(round((pageinfo['xres'] * pageinfo['yres']) ** 0.5)),
        '--mask-scan-size', '100',
        '--no-deskew',
        '--no-grayfilter',
        '--no-blackfilter',
        '--no-mask-center',
        '--no-border-align',
        infile
    ]

    with NamedTemporaryFile(prefix=prefix + "%04i.pnm" % pageinfo['pageno'],
                            suffix='.pnm', dir=output_folder,
                            delete=False) as tmpfile:
        args_unpaper.append(tmpfile.name)
        check_call(args_unpaper, close_fds=True)
        return tmpfile.name


@merge([convert_to_tiff, deskew_imagemagick],
       os.path.join(options.tmp_fld, "%04i.for_ocr.tif" % pageno))
def select_ocr_image(infiles, output_file):
    re_symlink(infiles[-1], output_file, logger, logger_mutex)


@transform(select_ocr_image, suffix(".for_ocr.tif"), ".hocr")
def ocr_tesseract(
        input_file,
        output_file):

    args_tesseract = [
        'tesseract',
        '-l', options.language,
        input_file,
        output_file,
        'hocr',
        options.tess_cfg_files
    ]
    p = Popen(args_tesseract, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    stdout, stderr = p.communicate()

    with logger_mutex:
        if stdout:
            logger.info(stdout)
        if stderr:
            logger.error(stderr)

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, args_tesseract)

    # Tesseract appends suffix ".html" on its own
    re_symlink(output_file + ".html", output_file, logger, logger_mutex)


@merge([ocr_tesseract, select_ocr_image],
       os.path.join(options.tmp_fld, '%04i.ocred.pdf' % pageno))
def render_page(infiles, output_file):
    # Call python in a subprocess because:
    #  -That is python2 and this is python3
    #  -It is written as a standalone script; not meant for import yet
    args_hocrTransform = [
        'python2',
        os.path.join(basedir, 'hocrTransform.py'),
        '-r', str(round(max(pageinfo['xres'], pageinfo['yres']))),
        '-i', infiles[1],
        infiles[0],
        output_file
    ]
    p = Popen(args_hocrTransform, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    stdout, stderr = p.communicate()

    with logger_mutex:
        if stdout:
            logger.info(stdout)
        if stderr:
            logger.error(stderr)

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, args_hocrTransform)


cmdline.run(options)

# parser.add_argument(
#     'tess_cfg_files',
#     help="Specific configuration files to be used by Tesseract during OCRing")


def main():
    args = parser.parse_args()

    pageno, width_pt, height_pt = map(int, args.page_info.split(' ', 3))

    logger.name += '(page=%i)' % pageno

    logger.info("Processing page %i / %i", pageno, args.num_pages)

    pageinfo = pdf_get_pageinfo(args.input_pdf, pageno, width_pt, height_pt)

