# © 2018 James R. Barlow: github.com/jbarlow83
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

from pathlib import Path
import concurrent.futures
from collections import defaultdict, namedtuple
import logging
import sys

from PIL import Image

import pikepdf

from ._jobcontext import JobContext
from . import leptonica
from .helpers import re_symlink, fspath
from .exec import pngquant, jbig2enc

PAGE_GROUP_SIZE = 10
DEFAULT_JPEG_QUALITY = 75
DEFAULT_PNG_QUALITY = (65, 75)


def img_name(root, xref, ext):
    return fspath(root / '{:08d}{}'.format(xref, ext))


def png_name(root, xref):
    return img_name(root, xref, '.png')


def jpg_name(root, xref):
    return img_name(root, xref, '.jpg')


def tif_name(root, xref):
    return img_name(root, xref, '.tif')


def extract_image(*, pike, root, log, image, xref, jbig2s,
                  pngs, jpegs, options):
    if image.Subtype != '/Image':
        return False
    if image.Length < 100:
        log.debug("Skipping small image, xref {}".format(xref))
        return False

    pim = pikepdf.PdfImage(image)

    if len(pim.filter_decodeparms) > 1:
        log.debug("Skipping multiply filtered, xref {}".format(xref))
        return False
    filtdp = pim.filter_decodeparms[0]

    if pim.bits_per_component > 8:
        return False  # Don't mess with wide gamut images

    if filtdp[0] == '/JPXDecode':
        return False  # Don't do JPEG2000

    if pim.bits_per_component == 1 \
            and filtdp != '/JBIG2Decode' \
            and jbig2enc.available():
        try:
            imgname = Path(root / '{:08d}'.format(xref))
            with imgname.open('wb') as f:
                ext = pim.extract_to(stream=f)
            imgname.rename(imgname.with_suffix(ext))
        except pikepdf.UnsupportedImageTypeError:
            return False
        jbig2s.append((xref, ext))
    elif filtdp[0] == '/DCTDecode' \
            and options.optimize >= 2:
        # This is a simple heuristic derived from some training data, that has
        # about a 70% chance of guessing whether the JPEG is high quality,
        # and possibly recompressible, or not. The number itself doesn't mean
        # anything.
        # bytes_per_pixel = int(raw_jpeg.Length) / (w * h)
        # jpeg_quality_estimate = 117.0 * (bytes_per_pixel ** 0.213)
        # if jpeg_quality_estimate < 65:
        #     return False

        # We could get the ICC profile here, but there's no need to look at it
        # for quality transcoding
        # if icc:
        #     stream = BytesIO(raw_jpeg.read_raw_bytes())
        #     iccbytes = icc.read_bytes()
        #     with Image.open(stream) as im:
        #         im.save(jpg_name(root, xref), icc_profile=iccbytes)
        try:
            imgname = Path(root / '{:08d}'.format(xref))
            with imgname.open('wb') as f:
                ext = pim.extract_to(stream=f)
            imgname.rename(imgname.with_suffix(ext))
        except pikepdf.UnsupportedImageTypeError:
            return False
        jpegs.append(xref)
    elif pim.indexed \
            and pim.colorspace in pim.SIMPLE_COLORSPACES \
            and options.optimize >= 3:
        # Try to improve on indexed images - these are far from low hanging
        # fruit in most cases
        pim.as_pil_image().save(png_name(root, xref))
        pngs.append(xref)
    elif not pim.indexed and pim.colorspace in pim.SIMPLE_COLORSPACES:
        # An optimization opportunity here, not currently taken, is directly
        # generating a PNG from compressed data
        pim.as_pil_image().save(png_name(root, xref))
        pngs.append(xref)
    else:
        return False

    return True


def extract_images(pike, root, log, options):
    # Extract images we can improve
    changed_xrefs = set()
    jbig2_groups = defaultdict(lambda: [])
    jpegs = []
    pngs = []
    errors = 0
    for pageno, page in enumerate(pike.pages):
        group, _ = divmod(pageno, PAGE_GROUP_SIZE)
        try:
            xobjs = page.Resources.XObject
        except AttributeError:
            continue
        for imname, image in dict(xobjs).items():
            if image.objgen[1] != 0:
                continue  # Ignore images in an incremental PDF
            xref = image.objgen[0]
            if xref in changed_xrefs:
                continue  # Don't improve same image twice
            try:
                result = extract_image(
                    pike=pike, root=root, log=log, image=image,
                    xref=xref, jbig2s=jbig2_groups[group], pngs=pngs,
                    jpegs=jpegs, options=options
                )
                if result:
                    changed_xrefs.add(xref)
            except Exception as e:
                log.debug("Image {} xref {}".format(imname, xref))
                log.debug(repr(e))
                errors += 1

    # Elide empty groups
    jbig2_groups = {group: xrefs for group, xrefs in jbig2_groups.items()
                    if len(xrefs) > 0}
    log.debug(
        "Optimizable images: "
        "JBIG2 groups: {} JPEGs: {} PNGs: {} Errors: {}".format(
            len(jbig2_groups), len(jpegs), len(pngs), errors
    ))

    return jbig2_groups, jpegs, pngs


def convert_to_jbig2(pike, jbig2_groups, root, log, options):
    """
    Convert a group of JBIG2 images and insert into PDF.

    We use a group because JBIG2 works best with a symbol dictionary that spans
    multiple pages. When inserted back into the PDF, each JBIG2 must reference
    the symbol dictionary it is associated with. So convert a group at a time,
    and replace their streams with a parameter set that points to the
    appropriate dictionary.

    If too many pages shared the same dictionary JBIG2 encoding becomes more
    expensive and less efficient.

    """
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=options.jobs) as executor:
        futures = []
        for group, xref_exts in jbig2_groups.items():
            prefix = 'group{:08d}'.format(group)
            future = executor.submit(
                jbig2enc.convert_group,
                cwd=fspath(root),
                infiles=(img_name(root, xref, ext) for xref, ext in xref_exts),
                out_prefix=prefix
            )
            futures.append(future)
        for future in concurrent.futures.as_completed(futures):
            proc = future.result()
            log.debug(proc.stderr.decode())

    for group, xref_exts in jbig2_groups.items():
        prefix = 'group{:08d}'.format(group)
        jbig2_globals_data = (root / (prefix + '.sym')).read_bytes()
        jbig2_globals = pikepdf.Stream(pike, jbig2_globals_data)

        for n, xref_ext in enumerate(xref_exts):
            xref, _ = xref_ext
            jbig2_im_file = root / (prefix + '.{:04d}'.format(n))
            jbig2_im_data = jbig2_im_file.read_bytes()
            im_obj = pike.get_object(xref, 0)
            im_obj.write(
                jbig2_im_data, pikepdf.Name('/JBIG2Decode'),
                pikepdf.Dictionary({
                    '/JBIG2Globals': jbig2_globals
                })
            )


def transcode_jpegs(pike, jpegs, root, log, options):
    for xref in jpegs:
        in_jpg = Path(jpg_name(root, xref))
        opt_jpg = in_jpg.with_suffix('.opt.jpg')

        # This produces a debug warning from PIL
        # DEBUG:PIL.Image:Error closing: 'NoneType' object has no attribute
        # 'close'.  Seems to be mostly harmless
        # https://github.com/python-pillow/Pillow/issues/1144
        with Image.open(fspath(in_jpg)) as im:
            im.save(fspath(opt_jpg),
                    optimize=True,
                    quality=options.jpeg_quality)
        # pylint: disable=E1101
        if opt_jpg.stat().st_size > in_jpg.stat().st_size:
            log.debug("xref {}, jpeg, made larger - skip".format(xref))
            continue

        compdata = leptonica.CompressedData.open(opt_jpg)
        im_obj = pike.get_object(xref, 0)
        im_obj.write(
            compdata.read(), pikepdf.Name('/DCTDecode'),
            pikepdf.Null()
        )


def transcode_pngs(pike, pngs, root, log, options):
    if options.optimize >= 2:
        png_quality = (
            max(10, options.png_quality - 10),
            min(100, options.png_quality + 10)
        )
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=options.jobs) as executor:
            for xref in pngs:
                executor.submit(
                    pngquant.quantize,
                    png_name(root, xref), png_name(root, xref),
                    png_quality[0], png_quality[1])

    for xref in pngs:
        im_obj = pike.get_object(xref, 0)

        # Open, transcode (!), package for PDF
        try:
            pix = leptonica.Pix.open(png_name(root, xref))
            if pix.depth == 1:
                pix = pix.invert()  # PDF assumes 1 is black for monochrome
            compdata = pix.generate_pdf_ci_data(
                leptonica.lept.L_FLATE_ENCODE, 0
            )
        except leptonica.LeptonicaError as e:
            log.error(e)
            continue

        # This is what we should be doing: open the compressed data without
        # transcoding. However this shifts each pixel row by one for some
        # reason.
        #compdata = leptonica.CompressedData.open(png_name(root, xref))
        if len(compdata) > int(im_obj.stream_dict.Length):
            continue  # If we produced a larger image, don't use

        predictor = pikepdf.Null()
        if compdata.predictor > 0:
            predictor = pikepdf.Dictionary({'/Predictor': compdata.predictor})

        im_obj.BitsPerComponent = compdata.bps
        im_obj.Width = compdata.w
        im_obj.Height = compdata.h

        if compdata.ncolors > 0:
            palette_pdf_string = compdata.get_palette_pdf_string()
            palette_data = pikepdf.Object.parse(palette_pdf_string)
            palette_stream = pikepdf.Stream(pike, bytes(palette_data))
            palette = [pikepdf.Name('/Indexed'), pikepdf.Name('/DeviceRGB'),
                       compdata.ncolors - 1, palette_stream]
            cs = palette
        else:
            if compdata.spp == 1:
                cs = pikepdf.Name('/DeviceGray')
            elif compdata.spp == 3:
                cs = pikepdf.Name('/DeviceRGB')
            elif compdata.spp == 4:
                cs = pikepdf.Name('/DeviceCMYK')
        im_obj.ColorSpace = cs
        im_obj.write(compdata.read(), pikepdf.Name('/FlateDecode'), predictor)


def optimize(
    input_file,
    output_file,
    log,
    context):

    options = context.get_options()
    if options.optimize == 0:
        re_symlink(input_file, output_file, log)
        return

    if options.jpeg_quality == 0:
        options.jpeg_quality = \
                DEFAULT_JPEG_QUALITY if options.optimize < 3 else 40
    if options.png_quality == 0:
        options.png_quality = \
                DEFAULT_PNG_QUALITY if options.optimize < 3 else 30

    pike = pikepdf.Pdf.open(input_file)

    root = Path(output_file).parent / 'images'
    root.mkdir(exist_ok=True)  # pylint: disable=E1101
    jbig2_groups, jpegs, pngs = extract_images(
        pike, root, log, options)

    convert_to_jbig2(pike, jbig2_groups, root, log, options)
    transcode_jpegs(pike, jpegs, root, log, options)
    transcode_pngs(pike, pngs, root, log, options)

    # Not object_stream_mode + preserve_pdfa generates noncompliant PDFs
    target_file = Path(output_file).with_suffix('.opt.pdf')
    pike.save(target_file, preserve_pdfa=True)

    input_size = Path(input_file).stat().st_size
    output_size = Path(target_file).stat().st_size
    ratio = input_size / output_size
    savings = 1 - output_size / input_size
    log.info("Optimize ratio: {:.2f} savings: {:.1f}%".format(
        ratio, 100 * savings))

    if savings < 0:
        log.info("Optimize did not improve the file - discarded")
        re_symlink(input_file, output_file, log)
    else:
        re_symlink(target_file, output_file, log)


def main(infile, outfile, level, jobs=1):
    from tempfile import TemporaryDirectory
    from shutil import copy

    class OptimizeOptions:
        """Emulate ocrmypdf's options"""

        def __init__(self, jobs, optimize, jpeg_quality, png_quality):
            self.jobs = jobs
            self.optimize = optimize
            self.jpeg_quality = jpeg_quality
            self.png_quality = png_quality

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger()

    ctx = JobContext()
    options = OptimizeOptions(
        jobs=jobs,
        optimize=int(level),
        jpeg_quality=0,  # Use default
        png_quality=0
    )
    ctx.set_options(options)

    with TemporaryDirectory() as td:
        tmpout = Path(td) / 'out.pdf'
        optimize(infile, tmpout, log, ctx)
        copy(fspath(tmpout), fspath(outfile))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
