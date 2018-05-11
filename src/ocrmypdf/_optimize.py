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
from subprocess import CalledProcessError
import concurrent.futures
from collections import defaultdict
import struct
from io import BytesIO
from PIL import Image

from .lib import fitz
import pikepdf

from . import leptonica
from .helpers import re_symlink
from .exec import pngquant, jbig2enc

PAGE_GROUP_SIZE = 10
SIMPLE_COLORSPACES = ('/DeviceRGB', '/DeviceGray', '/CalRGB', '/CalGray')


def filter_decodeparms(obj):
    """
    PDF has a lot of optional data structures concerning /Filter and 
    /DecodeParms. /Filter can be absent or a name or an array, /DecodeParms
    can be absent or a dictionary (if /Filter is a name) or an array (if
    /Filter is an array). When both are arrays the lengths match.
    
    Normalize this into:
    [(/FilterName, {/DecodeParmName: Value, ...}), ...]

    If there are no filters then the return is
    [('', {})]

    The order of /Filter matters as indicates the encoding/decoding sequence.

    """
    normalized = []
    filters = []
    filt = obj.get('/Filter', None)
    if filt is None:
        return [('', {})]
    if filt.type_code == pikepdf.ObjectType.array:
        filters.extend(filt)
    elif filt.type_code == pikepdf.ObjectType.name:
        filters.append(filt)

    decodeparms = obj.get('/DecodeParms', pikepdf.Array([]))
    if decodeparms.type_code == pikepdf.ObjectType.dictionary:
        decodeparms = pikepdf.Array([decodeparms])

    for n, dp in enumerate(decodeparms):
        filt_parm = (filters[n], dp)
        normalized.append(filt_parm)
    if len(normalized) == 0:
        for filt in filters:
            filt_parm = (filt, {})
            normalized.append(filt_parm)

    if len(normalized) == 0:
        return [('', {})]
    return normalized


def generate_ccitt_header(data, w, h, decode_parms):
    # https://stackoverflow.com/questions/2641770/
    # https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf

    if not decode_parms:
        raise ValueError("/CCITTFaxDecode without /DecodeParms")

    if decode_parms.get("/K", 1) < 0:
        ccitt_group = 4  # Pure two-dimensional encoding (Group 4)
    else:
        ccitt_group = 3

    img_size = len(data)
    tiff_header_struct = '<' + '2s' + 'H' + 'L' + 'H' + 'HHLL' * 8 + 'L'
    tiff_header = struct.pack(
            tiff_header_struct,
            b'II',  # Byte order indication: Little endian
            42,  # Version number (always 42)
            8,  # Offset to first IFD
            8,  # Number of tags in IFD
            256, 4, 1, w,  # ImageWidth, LONG, 1, width
            257, 4, 1, h,  # ImageLength, LONG, 1, length
            258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
            259, 3, 1, ccitt_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
            262, 3, 1, 0,  # Thresholding, SHORT, 1, 0 = WhiteIsZero
            273, 4, 1, struct.calcsize(tiff_header_struct),  # StripOffsets, LONG, 1, length of header
            278, 4, 1, h,  # RowsPerStrip, LONG, 1, length
            279, 4, 1, img_size,  # StripByteCounts, LONG, 1, size of image
            0  # last IFD
            )

    return tiff_header


def make_img_name(root, xref):
    return str(root / '{:08d}.png'.format(xref))


def extract_image(*, doc, pike, root, log, image, xref, jbig2s, 
                  pngs, jpegs, options):
    if image.Subtype != '/Image':
        return False
    if image.Length < 100:
        log.debug("Skipping small image, xref {}".format(xref))
        return False

    bpc = image.get('/BitsPerComponent', 8)
    cs = image.get('/ColorSpace', '')
    w = int(image.Width)
    h = int(image.Height)
    filtdps = filter_decodeparms(image)
    if len(filtdps) > 1:
        log.debug("Skipping multiply filtered, xref {}".format(xref))
        return False
    filtdp = filtdps[0]

    if bpc == 1 and filtdp[0] != '/JBIG2Decode' and jbig2enc.available():
        if filtdp[0] == '/CCITTFaxDecode':
            data = image.read_raw_bytes()
            try:
                header = generate_ccitt_header(data, w, h, filtdp[1])
            except ValueError as e:
                log.info(e)
                return False
            stream = BytesIO()
            stream.write(header)
            stream.write(data)
            stream.seek(0)
            with Image.open(stream) as im:
                im.save(make_img_name(root, xref))
        else:
            return False        
        jbig2s.append(xref)
    elif filtdp[0] == '/JPXDecode':
        return False
    elif filtdp[0] == '/DCTDecode' \
            and cs in SIMPLE_COLORSPACES \
            and options.optimize >= 2:
        raw_jpeg = pike._get_object_id(xref, 0)
        color_transform = filtdp[1].get('/ColorTransform', 1)
        if color_transform != 1:
            return False  # Don't mess with JPEGs other than YUV

        # This is a simple heuristic derived from some training data, that has
        # about a 70% chance of guessing whether the JPEG is high quality,
        # and possibly recompressible, or not. The number itself doesn't mean
        # anything.
        # bytes_per_pixel = int(raw_jpeg.Length) / (w * h)
        # jpeg_quality_estimate = 117.0 * (bytes_per_pixel ** 0.213)
        # if jpeg_quality_estimate < 65:
        #     return False

        raw_jpeg_data = raw_jpeg.read_raw_bytes()
        (root / '{:08d}.jpg'.format(xref)).write_bytes(raw_jpeg_data)
        jpegs.append(xref)
    elif cs in SIMPLE_COLORSPACES and fitz:
        # For any 'inferior' filter including /FlateDecode we extract
        # and recode as /FlateDecode
        # raw_png = pike._get_object_id(xref, 0)
        # raw_png_data = raw_png.read_raw_bytes()
        # (root / '{:08d}.png'.format(xref)).write_bytes(raw_png_data)
        pix = fitz.Pixmap(doc, xref)
        pix.writePNG(make_img_name(root, xref), savealpha=False)
        pngs.append(xref)
    else:
        return False
    
    return True


def extract_images(doc, pike, root, log, options):
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
            xref = image._objgen[0]
            if xref in changed_xrefs:
                continue  # Don't improve same image twice
            try:
                result = extract_image(
                    doc=doc, pike=pike, root=root, log=log, image=image, 
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

    return changed_xrefs, jbig2_groups, jpegs, pngs


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
        for group, xrefs in jbig2_groups.items():
            prefix = 'group{:08d}'.format(group)
            future = executor.submit(
                jbig2enc.convert_group, 
                cwd=str(root),
                infiles=(make_img_name(root, xref) for xref in xrefs),
                out_prefix=prefix
            )
            futures.append(future)
        for future in concurrent.futures.as_completed(futures):
            proc = future.result()
            log.debug(proc.stderr)

    for group, xrefs in jbig2_groups.items():
        prefix = 'group{:08d}'.format(group)
        jbig2_globals_data = (root / (prefix + '.sym')).read_bytes()
        jbig2_globals = pikepdf.Stream(pike, jbig2_globals_data)

        for n, xref in enumerate(xrefs):
            jbig2_im_file = root / (prefix + '.{:04d}'.format(n))
            jbig2_im_data = jbig2_im_file.read_bytes()
            im_obj = pike._get_object_id(xref, 0)
            im_obj.write(
                jbig2_im_data, pikepdf.Name('/JBIG2Decode'), 
                pikepdf.Dictionary({
                    '/JBIG2Globals': jbig2_globals
                })
            )


def transcode_jpegs(pike, jpegs, root, log, options):
    for xref in jpegs:
        in_jpg = root / '{:08d}.jpg'.format(xref)
        opt_jpg = root / '{:08d}_opt.jpg'.format(xref)
        with Image.open(str(in_jpg)) as im:
            im.save(str(opt_jpg), 
                    optimize=True,
                    quality=70)
        if opt_jpg.stat().st_size > in_jpg.stat().st_size:
            log.debug("xref {}, jpeg, made larger - skip".format(xref))
            continue

        compdata = leptonica.CompressedData.open(opt_jpg)
        im_obj = pike._get_object_id(xref, 0)
        im_obj.write(
            compdata.read(), pikepdf.Name('/DCTDecode'),
            pikepdf.Null()
        )


def transcode_pngs(pike, pngs, root, options):
    if options.optimize >= 2:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=options.jobs) as executor:
            for xref in pngs:
                executor.submit(
                    pngquant.quantize, 
                    make_img_name(root, xref), make_img_name(root, xref), 
                    65, 80)

    for xref in pngs:
        im_obj = pike._get_object_id(xref, 0)
        pix = leptonica.Pix.read(make_img_name(root, xref))
        compdata = pix.generate_pdf_ci_data(leptonica.lept.L_FLATE_ENCODE, 0)
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

    if fitz:
        doc = fitz.open(input_file)
    else:
        doc = None
    pike = pikepdf.Pdf.open(input_file)

    root = Path(output_file).parent / 'images'
    root.mkdir(exist_ok=True)
    changed_xrefs, jbig2_groups, jpegs, pngs = extract_images(
        doc, pike, root, log, options)

    convert_to_jbig2(pike, jbig2_groups, root, log, options)

    transcode_jpegs(pike, jpegs, root, log, options)

    transcode_pngs(pike, pngs, root, options)

    # Not object_stream_mode + preserve_pdfa generates noncompliant PDFs
    target_file = output_file + '_opt.pdf'
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
        

if __name__ == '__main__':
    import logging
    import sys
    from .pipeline import JobContext
    from collections import namedtuple
    Options = namedtuple('Options', 'jobs')

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger()

    ctx = JobContext()
    options = Options(jobs=4)
    ctx.set_options(options)

    optimize(sys.argv[1], sys.argv[2], log, ctx)