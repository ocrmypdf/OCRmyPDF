#!/usr/bin/env python3
# Reimplement ocrPage.sh as Python

import sys
import os.path
import fileinput
import re
from parse import parse

from subprocess import Popen, check_call, PIPE, CalledProcessError, \
    TimeoutExpired
try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')


from ruffus import transform, suffix, merge, active_if, regex, jobs_limit, \
    mkdir, formatter
import ruffus.cmdline as cmdline
from .hocrtransform import HocrTransform


basedir = os.path.dirname(os.path.realpath(__file__))

parser = cmdline.get_argparse(
    prog="ocrpage",
    description="Run OCR and related jobs on a single page of a PDF file")

parser.add_argument(
    'input_pdf',    # Implemented
    help="PDF file containing the page to be OCRed")
parser.add_argument(
    'page_info',    # Implemented
    help="Various characteristics of the page to be OCRed")
parser.add_argument(
    'num_pages',    # Unused
    help="Total number of page of the PDF file (required for logger)")
parser.add_argument(
    'tmp_fld',      # Implemented
    help="Folder where the temporary files should be placed")
parser.add_argument(
    'verbosity', type=int,      # Superseded
    help="Requested verbosity")
parser.add_argument(
    'language',     # Implemented
    help="Language of the file to be OCRed")
parser.add_argument(
    'keep_tmp', type=int,   # Not implemented
    help="Keep the temporary files after processing (helpful for debugging)")
parser.add_argument(
    'preprocess_deskew', type=int,          # Implemented
    help="Deskew the page to be OCRed")
parser.add_argument(
    'preprocess_clean', type=int,           # Implemented
    help="Clean the page to be OCRed")
parser.add_argument(
    'preprocess_cleantopdf', type=int,      # Implemented
    help="Put the cleaned paged in the OCRed PDF")
parser.add_argument(
    'oversampling_dpi', type=int,           # Not implmeneted
    help="Oversampling resolution in dpi")
parser.add_argument(
    'pdf_noimg', type=int,                  # implemented
    help="Generate debug PDF pages with only the OCRed text and no image")
parser.add_argument(
    'force_ocr', type=int,                  # Implemented
    help="Force to OCR, even if the page already contains fonts")
parser.add_argument(
    'skip_text', type=int,                  # Implemented
    help="Skip OCR on pages that contain fonts and include the page anyway")
parser.add_argument(
    'skip_big', type=int,
    help="Skip OCR for pages that are very large")
parser.add_argument(
    'tess_cfg_files', default='', nargs='*',    # Implemented
    help="Tesseract configuration")
parser.add_argument(
    '--deskew-provider', choices=['imagemagick', 'leptonica'],
    default='leptonica')
parser.add_argument(
    '--page-renderer', choices=['pdftoppm', 'ghostscript'],
    default='ghostscript')


options = parser.parse_args()

logger, logger_mutex = cmdline.setup_logging(__name__, options.log_file,
                                             options.verbose)


def pdf_get_pageinfo(infile, page, width_pt, height_pt):
    pageinfo = {}
    pageinfo['pageno'] = page
    pageinfo['width_inches'] = width_pt / 72.0
    pageinfo['height_inches'] = height_pt / 72.0
    pageinfo['images'] = []

    p_pdftotext = Popen(['pdftotext', '-f', str(page), '-l', str(page),
                        '-raw', '-nopgbrk', infile, '-'],
                        close_fds=True, stdout=PIPE, stderr=PIPE,
                        universal_newlines=True)
    text, _ = p_pdftotext.communicate()
    if len(text.strip()) > 0:
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
        # pdfimages calculates DPI as of 0.26.0, but adds +1 to dpi_h
        # apparent bug, so calculate explicitly
        image['dpi_w'] = image['width'] / pageinfo['width_inches']
        image['dpi_h'] = image['height'] / pageinfo['height_inches']
        image['dpi'] = (image['dpi_w'] * image['dpi_h']) ** 0.5
        pageinfo['images'].append(image)

    if pageinfo['images']:
        xres = max(image['dpi_w'] for image in pageinfo['images'])
        yres = max(image['dpi_h'] for image in pageinfo['images'])
        pageinfo['xres'], pageinfo['yres'] = xres, yres
        pageinfo['width_pixels'] = \
            int(round(xres * pageinfo['width_inches']))
        pageinfo['height_pixels'] = \
            int(round(yres * pageinfo['height_inches']))

    return pageinfo

pageno, width_pt, height_pt = map(int, options.page_info.split(' ', 3))
pageinfo = pdf_get_pageinfo(options.input_pdf, pageno, width_pt, height_pt)

with logger_mutex:
    if not pageinfo['images']:
        # If the page has no images, then it contains vector content or text
        # or both. It seems quite unlikely that one would find meaningful text
        # from rasterizing vector content. So skip the page.
        logger.info(
            "Page {0} has no images - skipping OCR".format(pageno)
        )
    elif pageinfo['has_text']:
        s = "Page {0} already has text! – {1}"

        if not options.force_ocr and not options.skip_text:
            logger.error(s.format(pageno,
                         "aborting (use -f or -s to force OCR)"))
            sys.exit(1)
        elif options.force_ocr:
            logger.info(s.format(pageno,
                        "rasterizing text and running OCR anyway"))
        elif options.skip_text:
            logger.info(s.format(pageno,
                        "skipping all processing on this page"))

ocr_required = pageinfo['images'] and \
    (options.force_ocr or
        (not (pageinfo['has_text'] and options.skip_text)))

if ocr_required and options.skip_big:
    area = pageinfo['width_inches'] * pageinfo['height_inches']
    pixel_count = pageinfo['width_pixels'] * pageinfo['height_pixels']
    if area > (11.0 * 17.0) or pixel_count > (300.0 * 300.0 * 11 * 17):
        ocr_required = False
        logger.info(
            "Page {0} is very large; skipping due to -b".format(pageno))


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

    if not os.path.exists(input_file):
        raise Exception("trying to create a broken symlink to %s" % input_file)

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
    try:
        re_symlink(input_file, soft_link_name, logger, logger_mutex)
    except FileExistsError:
        pass


@active_if(not ocr_required)
@transform(setup_working_directory,
           formatter(),
           os.path.join(options.tmp_fld, '%04i.skip.pdf' % pageno))
def skip_ocr(
        input_file,
        output_file):
    args_pdfseparate = [
        'pdfseparate',
        '-f', str(pageinfo['pageno']), '-l', str(pageinfo['pageno']),
        input_file,
        output_file
    ]
    check_call(args_pdfseparate)


@active_if(ocr_required)
@active_if(options.page_renderer == 'pdftoppm')
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

    # Ask pdftoppm to write the binary output to stdout; therefore set
    # universal_newlines=False
    p = Popen(args_pdftoppm, close_fds=True, stdout=open(output_file, 'wb'),
              stderr=PIPE, universal_newlines=False)
    _, stderr = p.communicate()
    if stderr:
        # Because universal_newlines=False, stderr is bytes(), so we must
        # manually convert it to str for logging
        from codecs import decode
        with logger_mutex:
            logger.error(decode(stderr, sys.getdefaultencoding(), 'ignore'))
    if p.returncode != 0:
        raise CalledProcessError(p.returncode, args_pdftoppm)


@active_if(ocr_required)
@transform(unpack_with_pdftoppm, suffix(".pnm"), ".png")
def convert_to_png(input_file, output_file):
    args_convert = [
        'convert',
        input_file,
        output_file
    ]
    check_call(args_convert)


@active_if(ocr_required)
@active_if(options.page_renderer == 'ghostscript')
@transform(setup_working_directory,
           formatter(),
           "{path[0]}/%04i.png" % pageno)
def unpack_with_ghostscript(
        input_file,
        output_file):
    device = 'png16m'  # 24-bit
    if all(image['comp'] == 1 for image in pageinfo['images']):
        if all(image['bpc'] == 1 for image in pageinfo['images']):
            device = 'pngmono'
        elif not any(image['color'] == 'color'
                     for image in pageinfo['images']):
            device = 'pnggray'

    args_gs = [
        'gs',
        '-dBATCH', '-dNOPAUSE',
        '-dFirstPage=%i' % pageno,
        '-dLastPage=%i' % pageno,
        '-sDEVICE=%s' % device,
        '-o', output_file,
        '-r{0}x{1}'.format(str(pageinfo['xres']), str(pageinfo['yres'])),
        input_file
    ]

    p = Popen(args_gs, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    stdout, stderr = p.communicate()
    with logger_mutex:
        if stdout:
            logger.info(stdout)
        if stderr:
            logger.error(stderr)

    try:
        f = open(output_file)
    except FileNotFoundError:
        raise
    else:
        f.close()


@active_if(ocr_required)
@active_if(options.preprocess_deskew != 0
           and options.deskew_provider == 'imagemagick')
@transform(convert_to_png, suffix(".png"), ".deskewed.png")
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


@active_if(ocr_required)
@active_if(options.preprocess_deskew != 0
           and options.deskew_provider == 'leptonica')
@transform(convert_to_png, suffix(".png"), ".deskewed.png")
def deskew_leptonica(input_file, output_file):
    from .leptonica import deskew
    with logger_mutex:
        deskew(input_file, output_file,
               min(pageinfo['xres'], pageinfo['yres']))


@active_if(ocr_required)
@active_if(options.preprocess_clean != 0)
@merge([unpack_with_pdftoppm, unpack_with_ghostscript,
        deskew_imagemagick, deskew_leptonica],
       os.path.join(options.tmp_fld, "%04i.for_clean.pnm" % pageno))
def select_image_for_cleaning(infiles, output_file):
    input_file = infiles[-1]
    args_convert = [
        'convert',
        input_file,
        output_file
    ]
    check_call(args_convert)


@active_if(ocr_required)
@active_if(options.preprocess_clean != 0)
@transform(select_image_for_cleaning, suffix(".pnm"), ".cleaned.pnm")
def clean_unpaper(input_file, output_file):
    args_unpaper = [
        'unpaper',
        '--dpi', str(int(round((pageinfo['xres'] * pageinfo['yres']) ** 0.5))),
        '--mask-scan-size', '100',
        '--no-deskew',
        '--no-grayfilter',
        '--no-blackfilter',
        '--no-mask-center',
        '--no-border-align',
        input_file,
        output_file
    ]

    p = Popen(args_unpaper, close_fds=True, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    stdout, stderr = p.communicate()

    with logger_mutex:
        if stdout:
            logger.info(stdout)
        if stderr:
            logger.error(stderr)

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, args_unpaper)


@active_if(ocr_required)
@transform(clean_unpaper, suffix(".cleaned.pnm"), ".cleaned.png")
def cleaned_to_png(input_file, output_file):
    args_convert = [
        'convert',
        input_file,
        output_file
    ]
    check_call(args_convert)


@active_if(ocr_required)
@merge([unpack_with_ghostscript, convert_to_png, deskew_imagemagick,
        deskew_leptonica, cleaned_to_png],
       os.path.join(options.tmp_fld, "%04i.for_ocr.png" % pageno))
def select_ocr_image(infiles, output_file):
    re_symlink(infiles[-1], output_file, logger, logger_mutex)


hocr_template = '''<?xml version="1.0" encoding="UTF-8"?>
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


@active_if(ocr_required)
@transform(select_ocr_image, suffix(".for_ocr.png"), ".hocr")
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
    try:
        stdout, stderr = p.communicate(timeout=180)
    except TimeoutExpired:
        p.kill()
        stdout, stderr = p.communicate()
        # Generate a HOCR file with no recognized text if tesseract times out
        # Temporary workaround to hocrTransform not being able to function if
        # it does not have a valid hOCR file.
        with open(output_file, 'w', encoding="utf-8") as f:
            f.write(hocr_template.format(pageinfo['width_pixels'],
                                         pageinfo['height_pixels']))
    else:
        with logger_mutex:
            if stdout:
                logger.info(stdout)
            if stderr:
                logger.error(stderr)

        if p.returncode != 0:
            raise CalledProcessError(p.returncode, args_tesseract)

        if os.path.exists(output_file + '.html'):
            # Tesseract 3.02 appends suffix ".html" on its own
            re_symlink(output_file + ".html", output_file,
                       logger, logger_mutex)
        elif os.path.exists(output_file + '.hocr'):
            # Tesseract 3.03 appends suffix ".hocr" on its own
            re_symlink(output_file + ".hocr", output_file,
                       logger, logger_mutex)

            # The filename gets inserted to hocr
            # but Tesseract does not verify that it is escaped XML
            # it's not necessary so strip it out
            regex_nested_single_quotes = re.compile(
                r"""title='image "([^"]*)";""")
            with fileinput.input(files=(output_file,), inplace=True) as f:
                for line in f:
                    line = regex_nested_single_quotes.sub(
                        r"""title='image " ";""", line)
                    print(line, end='')  # stdout is redirected here


@active_if(ocr_required)
@merge([unpack_with_ghostscript, convert_to_png,
        deskew_imagemagick, deskew_leptonica, cleaned_to_png],
       os.path.join(options.tmp_fld, "%04i.image_for_pdf" % pageno))
def select_image_for_pdf(infiles, output_file):
    if options.preprocess_clean != 0 and options.preprocess_cleantopdf != 0:
        input_file = infiles[-1]
    elif options.preprocess_deskew != 0 and options.preprocess_clean != 0:
        input_file = infiles[-2]
    elif options.preprocess_deskew != 0 and options.preprocess_clean == 0:
        input_file = infiles[-1]
    else:
        input_file = infiles[0]

    if all(image['enc'] == 'jpeg' for image in pageinfo['images']):
        # If all images were JPEGs originally, produce a JPEG as output
        check_call(['convert', input_file, 'jpg:' + output_file])
    else:
        re_symlink(input_file, output_file, logger, logger_mutex)


@active_if(ocr_required)
@merge([ocr_tesseract, select_image_for_pdf],
       os.path.join(options.tmp_fld, '%04i.rendered.pdf' % pageno))
def render_page(infiles, output_file):
    hocr, image = infiles[0], infiles[1]

    dpi = round(max(pageinfo['xres'], pageinfo['yres']))

    hocrtransform = HocrTransform(hocr, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=image,
                         showBoundingboxes=False, invisibleText=True)


@active_if(ocr_required and options.pdf_noimg)
@transform(ocr_tesseract, suffix(".hocr"), ".ocred.todebug.pdf")
def render_text_output_page(input_file, output_file):
    dpi = round(max(pageinfo['xres'], pageinfo['yres']))

    hocrtransform = HocrTransform(input_file, dpi)
    hocrtransform.to_pdf(output_file, imageFileName=None,
                         showBoundingboxes=True, invisibleText=False)


@merge([render_page, skip_ocr],
       os.path.join(options.tmp_fld, '%04i.ocred.pdf' % pageno))
def select_final_page(infiles, output_file):
    re_symlink(infiles[-1], output_file, logger, logger_mutex)


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

