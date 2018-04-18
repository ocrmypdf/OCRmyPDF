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
from subprocess import run, PIPE
import concurrent.futures
from collections import defaultdict
import struct
from io import BytesIO
from PIL import Image

from .lib import fitz
import pikepdf

from . import leptonica
from .helpers import re_symlink
from .exec import pngquant

PAGE_GROUP_SIZE = 10
SIMPLE_COLORSPACES = ('/DeviceRGB', '/DeviceGray', '/CalRGB', '/CalGray')


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


def extract_images(doc, pike, root, log):
    # Extract images we can improve
    changed_xrefs = set()
    jbig2_groups = defaultdict(lambda: [])
    jpegs = []
    pngs = []
    for pageno, page in enumerate(pike.pages):
        group, index = divmod(pageno, PAGE_GROUP_SIZE)
        try:
            xobjs = page.Resources.XObject
        except AttributeError:
            continue
        for imname, image in dict(xobjs).items():
            if image.Subtype != '/Image':
                continue

            xref = image._objgen[0]
            if xref in changed_xrefs:
                continue  # Don't improve same image twice

            bpc = image.get('/BitsPerComponent', 8)
            filt = image.get('/Filter', pikepdf.Array([]))
            cs = image.get('/ColorSpace', '')
            w = int(image.Width)
            h = int(image.Height)
            if filt.type_code == pikepdf.ObjectType.array:
                if len(filt) > 1:
                    log.debug("Skipping multiply filtered {}".format(filt))
                    continue  # Not supported: multiple filters 
                elif len(filt) == 1:
                    filt = filt[0]
                else:
                    filt = ''
            if bpc == 1 and filt != '/JBIG2Decode':
                decode_parms = image.get('/DecodeParms')
                if filt == '/CCITTFaxDecode':
                    data = image.read_raw_bytes()
                    try:
                        header = generate_ccitt_header(data, w, h, decode_parms)
                    except ValueError as e:
                        log.info(e)
                        continue
                    stream = BytesIO()
                    stream.write(header)
                    stream.write(data)
                    stream.seek(0)
                    with Image.open(stream) as im:
                        im.save(make_img_name(root, xref))
                else:
                    continue
                
                changed_xrefs.add(xref)
                jbig2_groups[group].append(xref)
            elif filt == '/JPXDecode':
                continue
            elif filt == '/DCTDecode' and cs in SIMPLE_COLORSPACES:
                raw_jpeg = pike._get_object_id(xref, 0)
                dp = raw_jpeg.get('/DecodeParms', None)
                color_transform = None
                try:
                    color_transform = dp[0].get('/ColorTransform', 1)
                except ValueError:
                    try:
                        color_transform = dp.get('/ColorTransform', 1)
                    except ValueError:
                        pass
                if color_transform is not None and color_transform != 1:
                    continue  # Don't mess with JPEGs other than YUV
                raw_jpeg_data = raw_jpeg.read_raw_bytes()
                (root / '{:08d}.jpg'.format(xref)).write_bytes(raw_jpeg_data)
                changed_xrefs.add(xref)
                jpegs.append(xref)
            elif cs in SIMPLE_COLORSPACES:
                # For any 'inferior' filter include /FlateDecode we extract
                # and recode as /FlateDecode
                # raw_png = pike._get_object_id(xref, 0)
                # raw_png_data = raw_png.read_raw_bytes()
                # (root / '{:08d}.png'.format(xref)).write_bytes(raw_png_data)
                pix = fitz.Pixmap(doc, xref)
                try:
                    pix.writePNG(make_img_name(root, xref), savealpha=False)
                except RuntimeError as e:
                    log.error('page {} xref {}'.format(pageno, xref))
                    log.error(e)
                    continue    
                changed_xrefs.add(xref)
                pngs.append(xref)
    return changed_xrefs, jbig2_groups, jpegs, pngs


def convert_to_jbig2(pike, jbig2_groups, root, log, options):
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=options.jobs) as executor:
        futures = []
        for group, xrefs in jbig2_groups.items():
            prefix = 'group{:08d}'.format(group)
            cmd = ['jbig2', '-b', prefix, '-s', '-p']
            cmd.extend(make_img_name(root, xref) for xref in xrefs)
            future = executor.submit(
                run, cmd, cwd=str(root), stdout=PIPE, stderr=PIPE)
            futures.append(future)
        for future in concurrent.futures.as_completed(futures):
            proc = future.result()
            proc.check_returncode()
            log.debug(proc.stderr)

    for group, xrefs in jbig2_groups.items():
        prefix = 'group{:08d}'.format(group)
        jbig2_globals_data = (root / (prefix + '.sym')).read_bytes()
        jbig2_globals = pikepdf.Stream(pike, jbig2_globals_data)

        for n, xref in enumerate(xrefs):
            jbig2_im_file = root / (prefix + '.{:04d}'.format(n))
            jbig2_im_data = jbig2_im_file.read_bytes()
            im_obj = pike._get_object_id(xref, 0)
            log.debug(xref)
            log.debug(repr(im_obj))

            im_obj.write(
                jbig2_im_data, pikepdf.Name('/JBIG2Decode'), 
                pikepdf.Dictionary({
                    '/JBIG2Globals': jbig2_globals
                })
            )
            log.debug(repr(im_obj))


def transcode_jpegs(pike, jpegs, root):
    for xref in jpegs:
        pix = leptonica.Pix.read((root / '{:08d}.jpg'.format(xref)))
        compdata = pix.generate_pdf_ci_data(leptonica.lept.L_JPEG_ENCODE, 75)
        im_obj = pike._get_object_id(xref, 0)
        im_obj.write(
            compdata.read(), pikepdf.Name('/DCTDecode'),
            pikepdf.Null()
        )


def transcode_pngs(pike, pngs, root, options):

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=options.jobs) as executor:
        for xref in pngs:
            executor.submit(
                pngquant.quantize, 
                make_img_name(root, xref), make_img_name(root, xref), 65, 80)

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

    if not fitz:
        re_symlink(input_file, output_file)
        return

    options = context.get_options()
    doc = fitz.open(input_file)
    pike = pikepdf.Pdf.open(input_file)

    root = Path(output_file).parent / 'images'
    root.mkdir()
    changed_xrefs, jbig2_groups, jpegs, pngs = extract_images(
        doc, pike, root, log)

    convert_to_jbig2(pike, jbig2_groups, root, log, options)

    transcode_jpegs(pike, jpegs, root)

    transcode_pngs(pike, pngs, root, options)

    # Not object_stream_mode + preserve_pdfa generates noncompliant PDFs
    pike.save(output_file, preserve_pdfa=True)

    input_size = Path(input_file).stat().st_size
    output_size = Path(output_file).stat().st_size
    improvement = input_size / output_size
    log.info("Optimize reduced size by {:.3f}".format(improvement))    
