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
from collections import defaultdict
import logging
import sys

from PIL import Image

import pikepdf

from ._jobcontext import JobContext
from . import leptonica
from .helpers import re_symlink, fspath
from .exec import pngquant, jbig2enc

DEFAULT_JPEG_QUALITY = 75
DEFAULT_PNG_QUALITY = 70


def img_name(root, xref, ext):
    return fspath(root / '{:08d}{}'.format(xref, ext))


def png_name(root, xref):
    return img_name(root, xref, '.png')


def jpg_name(root, xref):
    return img_name(root, xref, '.jpg')


def tif_name(root, xref):
    return img_name(root, xref, '.tif')


def extract_image_filter(pike, root, log, image, xref):
    if image.Subtype != '/Image':
        return None
    if image.Length < 100:
        log.debug("Skipping small image, xref %s", xref)
        return None

    pim = pikepdf.PdfImage(image)

    if len(pim.filter_decodeparms) > 1:
        log.debug("Skipping multiply filtered, xref %s", xref)
        return None
    filtdp = pim.filter_decodeparms[0]

    if pim.bits_per_component > 8:
        return None  # Don't mess with wide gamut images

    if filtdp[0] == '/JPXDecode':
        return None  # Don't do JPEG2000

    return pim, filtdp


def extract_image_jbig2(*, pike, root, log, image, xref, options):
    result = extract_image_filter(pike, root, log, image, xref)
    if result is None:
        return None
    pim, filtdp = result

    if pim.bits_per_component == 1 \
            and filtdp != '/JBIG2Decode' \
            and jbig2enc.available():
        try:
            imgname = Path(root / '{:08d}'.format(xref))
            with imgname.open('wb') as f:
                ext = pim.extract_to(stream=f)
            imgname.rename(imgname.with_suffix(ext))
        except pikepdf.UnsupportedImageTypeError:
            return None
        return xref, ext
    return None


def extract_image_generic(*, pike, root, log, image, xref, options):
    result = extract_image_filter(pike, root, log, image, xref)
    if result is None:
        return None
    pim, filtdp = result

    if filtdp[0] == '/DCTDecode' \
            and options.optimize >= 2:
        # This is a simple heuristic derived from some training data, that has
        # about a 70% chance of guessing whether the JPEG is high quality,
        # and possibly recompressible, or not. The number itself doesn't mean
        # anything.
        # bytes_per_pixel = int(raw_jpeg.Length) / (w * h)
        # jpeg_quality_estimate = 117.0 * (bytes_per_pixel ** 0.213)
        # if jpeg_quality_estimate < 65:
        #     return None

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
            return None
        return xref, ext
    elif pim.indexed \
            and pim.colorspace in pim.SIMPLE_COLORSPACES \
            and options.optimize >= 3:
        # Try to improve on indexed images - these are far from low hanging
        # fruit in most cases
        pim.as_pil_image().save(png_name(root, xref))
        return xref, '.png'
    elif not pim.indexed and pim.colorspace in pim.SIMPLE_COLORSPACES:
        # An optimization opportunity here, not currently taken, is directly
        # generating a PNG from compressed data
        pim.as_pil_image().save(png_name(root, xref))
        return xref, '.png'

    return None



def extract_images(pike, root, log, options, extract_fn):
    """Extract image using extract_fn

    extract_fn decides where the image is interesting in this case
    """

    include_xrefs = set()
    exclude_xrefs = set()
    errors = 0
    for pageno, page in enumerate(pike.pages):
        try:
            xobjs = page.Resources.XObject
        except AttributeError:
            continue
        for _imname, image in dict(xobjs).items():
            if image.objgen[1] != 0:
                continue  # Ignore images in an incremental PDF
            xref = image.objgen[0]
            if hasattr(image, 'SMask'):
                # Ignore soft masks
                smask_xref = image.SMask.objgen[0]
                exclude_xrefs.add(smask_xref)
            include_xrefs.add(xref)

    working_xrefs = include_xrefs - exclude_xrefs
    for xref in working_xrefs:
        image = pike.get_object((xref, 0))
        try:
            result = extract_fn(
                pike=pike, root=root, log=log, image=image,
                xref=xref, options=options
            )
        except Exception as e:
            log.debug("Image xref %s", xref)
            log.debug(repr(e))
            errors += 1
        else:
            if result:
                _, ext = result
                yield pageno, xref, ext


def extract_images_generic(pike, root, log, options):
    """Extract any >=2bpp image we think we can improve"""

    jpegs = []
    pngs = []
    for _, xref, ext in extract_images(
            pike, root, log, options, extract_image_generic):
        log.debug('xref = %s ext = %s', xref, ext)
        if ext == '.png':
            pngs.append(xref)
        elif ext == '.jpg':
            jpegs.append(xref)
    log.debug(
        "Optimizable images: "
        "JPEGs: %s PNGs: %s", len(jpegs), len(pngs)
    )
    return jpegs, pngs


def extract_images_jbig2(pike, root, log, options):
    """Extract any bitonal image that we think we can improve as JBIG2"""

    jbig2_groups = defaultdict(list)
    for pageno, xref, ext in extract_images(
            pike, root, log, options, extract_image_jbig2):
        group = pageno // options.jbig2_page_group_size
        jbig2_groups[group].append((xref, ext))

    # Elide empty groups
    jbig2_groups = {group: xrefs for group, xrefs in jbig2_groups.items()
                    if len(xrefs) > 0}
    log.debug(
        "Optimizable images: "
        "JBIG2 groups: %s", (len(jbig2_groups),)
    )
    return jbig2_groups


def _produce_jbig2_images(jbig2_groups, root, log, options):
    """Produce JBIG2 images from their groups"""

    def jbig2_group_futures(executor, root, groups):
        for group, xref_exts in groups.items():
            prefix = 'group{:08d}'.format(group)
            future = executor.submit(
                jbig2enc.convert_group,
                cwd=fspath(root),
                infiles=(img_name(root, xref, ext) for xref, ext in xref_exts),
                out_prefix=prefix
            )
            yield future

    def jbig2_single_futures(executor, root, groups):
        for group, xref_exts in groups.items():
            prefix = 'group{:08d}'.format(group)
            # Second loop is to ensure multiple images per page are unpacked
            for n, xref_ext in enumerate(xref_exts):
                xref, ext = xref_ext
                future = executor.submit(
                    jbig2enc.convert_single,
                    cwd=fspath(root),
                    infile=img_name(root, xref, ext),
                    outfile=root / ('{}.{:04d}'.format(prefix, n))
                )
                yield future

    if options.jbig2_page_group_size > 1:
        jbig2_futures = jbig2_group_futures
    else:
        jbig2_futures = jbig2_single_futures

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=options.jobs) as executor:
        futures = jbig2_futures(executor, root, jbig2_groups)
        for future in concurrent.futures.as_completed(futures):
            proc = future.result()
            log.debug(proc.stderr.decode())


def convert_to_jbig2(pike, jbig2_groups, root, log, options):
    """Convert images to JBIG2 and insert into PDF.

    When the JBIG2 page group size is > 1 we do several JBIG2 images at once
    and build a symbol dictionary that will span several pages. Each JBIG2
    image must reference to its symbol dictionary. If too many pages shared the
    same dictionary JBIG2 encoding becomes more expensive and less efficient.
    The default value of 10 was determined through testing. Currently this
    must be lossy encoding since jbig2enc does not support refinement coding.

    When the JBIG2 symbolic coder is not used, each JBIG2 stands on its own
    and needs no dictionary. Currently this is must be lossless JBIG2.
    """

    _produce_jbig2_images(jbig2_groups, root, log, options)

    for group, xref_exts in jbig2_groups.items():
        prefix = 'group{:08d}'.format(group)
        jbig2_symfile = root / (prefix + '.sym')
        if jbig2_symfile.exists():
            jbig2_globals_data = jbig2_symfile.read_bytes()
            jbig2_globals = pikepdf.Stream(pike, jbig2_globals_data)
            jbig2_globals_dict = pikepdf.Dictionary({
                    '/JBIG2Globals': jbig2_globals
            })
        elif options.jbig2_page_group_size == 1:
            jbig2_globals_dict = None
        else:
            raise FileNotFoundError(jbig2_symfile)

        for n, xref_ext in enumerate(xref_exts):
            xref, _ = xref_ext
            jbig2_im_file = root / (prefix + '.{:04d}'.format(n))
            jbig2_im_data = jbig2_im_file.read_bytes()
            im_obj = pike.get_object(xref, 0)
            im_obj.write(
                jbig2_im_data, pikepdf.Name('/JBIG2Decode'),
                jbig2_globals_dict
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
        # pylint: disable=no-member
        if opt_jpg.stat().st_size > in_jpg.stat().st_size:
            log.debug("xref %s, jpeg, made larger - skip", xref)
            continue

        compdata = leptonica.CompressedData.open(opt_jpg)
        im_obj = pike.get_object(xref, 0)
        im_obj.write(
            compdata.read(), filter=pikepdf.Name('/DCTDecode')
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

        predictor = None
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
        im_obj.write(
            compdata.read(),
            filter=pikepdf.Name('/FlateDecode'), decode_parms=predictor
        )


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
    if options.jbig2_page_group_size == 0:
        options.jbig2_page_group_size = \
                10 if options.jbig2_lossy else 1

    pike = pikepdf.Pdf.open(input_file)

    root = Path(output_file).parent / 'images'
    root.mkdir(exist_ok=True)  # pylint: disable=no-member

    jpegs, pngs = extract_images_generic(pike, root, log, options)
    transcode_jpegs(pike, jpegs, root, log, options)
    transcode_pngs(pike, pngs, root, log, options)

    jbig2_groups = extract_images_jbig2(pike, root, log, options)
    convert_to_jbig2(pike, jbig2_groups, root, log, options)

    target_file = Path(output_file).with_suffix('.opt.pdf')
    pike.remove_unreferenced_resources()
    pike.save(target_file, preserve_pdfa=True,
              object_stream_mode=pikepdf.ObjectStreamMode.generate)

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

        def __init__(
                self, jobs, optimize, jpeg_quality, png_quality, jb2lossy):
            self.jobs = jobs
            self.optimize = optimize
            self.jpeg_quality = jpeg_quality
            self.png_quality = png_quality
            self.jbig2_page_group_size = 0
            self.jbig2_lossy = jb2lossy

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger()

    ctx = JobContext()
    options = OptimizeOptions(
        jobs=jobs,
        optimize=int(level),
        jpeg_quality=0,  # Use default
        png_quality=0,
        jb2lossy=False
    )
    ctx.set_options(options)

    with TemporaryDirectory() as td:
        tmpout = Path(td) / 'out.pdf'
        optimize(infile, tmpout, log, ctx)
        copy(fspath(tmpout), fspath(outfile))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
