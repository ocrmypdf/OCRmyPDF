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

import logging
import sys
import tempfile
from collections import defaultdict
from functools import partial
from os import fspath
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    MutableSet,
    NamedTuple,
    NewType,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import pikepdf
from pikepdf import Dictionary, Name, Object, Pdf, PdfImage
from PIL import Image
from tqdm import tqdm

from ocrmypdf import leptonica
from ocrmypdf._concurrent import exec_progress_pool
from ocrmypdf._exec import jbig2enc, pngquant
from ocrmypdf._jobcontext import PdfContext
from ocrmypdf.exceptions import OutputFileAccessError
from ocrmypdf.helpers import safe_symlink

log = logging.getLogger(__name__)

DEFAULT_JPEG_QUALITY = 75
DEFAULT_PNG_QUALITY = 70


Xref = NewType('Xref', int)


class XrefExt(NamedTuple):
    xref: Xref
    ext: str


def img_name(root: Path, xref: Xref, ext: str) -> Path:
    return root / f'{xref:08d}{ext}'


def png_name(root: Path, xref: Xref) -> Path:
    return img_name(root, xref, '.png')


def jpg_name(root: Path, xref: Xref) -> Path:
    return img_name(root, xref, '.jpg')


def tif_name(root: Path, xref: Xref) -> Path:
    return img_name(root, xref, '.tif')


def extract_image_filter(
    pike: Pdf, root: Path, image: Object, xref: Xref
) -> Optional[Tuple[PdfImage, Tuple[Name, Object]]]:
    if image.Subtype != Name.Image:
        return None
    if image.Length < 100:
        log.debug("Skipping small image, xref %s", xref)
        return None

    pim = PdfImage(image)

    if len(pim.filter_decodeparms) > 1:
        log.debug("Skipping multiply filtered, xref %s", xref)
        return None
    filtdp = pim.filter_decodeparms[0]

    if pim.bits_per_component > 8:
        return None  # Don't mess with wide gamut images

    if filtdp[0] == Name.JPXDecode:
        return None  # Don't do JPEG2000

    if Name.Decode in image:
        return None  # Don't mess with custom Decode tables

    return pim, filtdp


def extract_image_jbig2(
    *, pike: pikepdf.Pdf, root: Path, image: Object, xref: Xref, options
) -> Optional[XrefExt]:
    result = extract_image_filter(pike, root, image, xref)
    if result is None:
        return None
    pim, filtdp = result

    if (
        pim.bits_per_component == 1
        and filtdp[0] != Name.JBIG2Decode
        and jbig2enc.available()
    ):
        try:
            imgname = root / f'{xref:08d}'
            with imgname.open('wb') as f:
                ext = pim.extract_to(stream=f)
            imgname.rename(imgname.with_suffix(ext))
        except pikepdf.UnsupportedImageTypeError:
            return None
        return XrefExt(xref, ext)
    return None


def extract_image_generic(
    *, pike: Pdf, root: Path, image: PdfImage, xref: Xref, options
) -> Optional[XrefExt]:
    result = extract_image_filter(pike, root, image, xref)
    if result is None:
        return None
    pim, filtdp = result

    # Don't try to PNG-optimize 1bpp images, since JBIG2 does it better.
    if pim.bits_per_component == 1:
        return None

    try:
        pim.indexed  # pikepdf 1.6.3 can't handle [/Indexed [/Array...]]
    except NotImplementedError:
        return None

    if filtdp[0] == Name.DCTDecode and options.optimize >= 2:
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
            imgname = root / f'{xref:08d}'
            with imgname.open('wb') as f:
                ext = pim.extract_to(stream=f)
            imgname.rename(imgname.with_suffix(ext))
        except pikepdf.UnsupportedImageTypeError:
            return None
        return XrefExt(xref, ext)
    elif (
        pim.indexed
        and pim.colorspace in pim.SIMPLE_COLORSPACES
        and options.optimize >= 3
    ):
        # Try to improve on indexed images - these are far from low hanging
        # fruit in most cases
        pim.as_pil_image().save(png_name(root, xref))
        return XrefExt(xref, '.png')
    elif not pim.indexed and pim.colorspace in pim.SIMPLE_COLORSPACES:
        # An optimization opportunity here, not currently taken, is directly
        # generating a PNG from compressed data
        pim.as_pil_image().save(png_name(root, xref))
        return XrefExt(xref, '.png')
    elif (
        not pim.indexed
        and pim.colorspace == Name.ICCBased
        and pim.bits_per_component == 1
        and not options.jbig2_lossy
    ):
        # We can losslessly optimize 1-bit images to CCITT or JBIG2 without
        # paying any attention to the ICC profile, provided we're not doing
        # lossy JBIG2
        pim.as_pil_image().save(png_name(root, xref))
        return XrefExt(xref, '.png')

    return None


def extract_images(
    pike: Pdf, root: Path, options, extract_fn: Callable[..., Optional[XrefExt]],
) -> Iterator[Tuple[int, XrefExt]]:
    """Extract image using extract_fn

    Enumerate images on each page, lookup their xref/ID number in the PDF.
    Exclude images that are soft masks (i.e. alpha transparency related).
    Record the page number on which an image is first used, since images may be
    used on multiple pages (or multiple times on the same page).

    Current we do not check Form XObjects or other objects that may contain
    images, and we don't evaluate alternate images or thumbnails.

    extract_fn must decide if wants to extract the image in this context. If
    it does a tuple should be returned: (xref, ext) where .ext is the file
    extension. extract_fn must also extract the file it finds interesting.
    """

    include_xrefs: MutableSet[Xref] = set()
    exclude_xrefs: MutableSet[Xref] = set()
    pageno_for_xref = {}
    errors = 0
    for pageno, page in enumerate(pike.pages):
        try:
            xobjs = page.Resources.XObject
        except AttributeError:
            continue
        for _imname, image in dict(xobjs).items():
            if image.objgen[1] != 0:
                continue  # Ignore images in an incremental PDF
            xref = Xref(image.objgen[0])
            if hasattr(image, 'SMask'):
                # Ignore soft masks
                smask_xref = Xref(image.SMask.objgen[0])
                exclude_xrefs.add(smask_xref)
            include_xrefs.add(xref)
            if xref not in pageno_for_xref:
                pageno_for_xref[xref] = pageno

    working_xrefs = include_xrefs - exclude_xrefs
    for xref in working_xrefs:
        image = pike.get_object((xref, 0))
        try:
            result = extract_fn(
                pike=pike, root=root, image=image, xref=xref, options=options
            )
        except Exception as e:  # pylint: disable=broad-except
            log.debug("Image xref %s, error %s", xref, repr(e))
            errors += 1
        else:
            if result:
                _, ext = result
                yield pageno_for_xref[xref], XrefExt(xref, ext)


def extract_images_generic(
    pike: Pdf, root: Path, options
) -> Tuple[List[Xref], List[Xref]]:
    """Extract any >=2bpp image we think we can improve"""

    jpegs = []
    pngs = []
    for _, xref_ext in extract_images(pike, root, options, extract_image_generic):
        log.debug('%s', xref_ext)
        if xref_ext.ext == '.png':
            pngs.append(xref_ext.xref)
        elif xref_ext.ext == '.jpg':
            jpegs.append(xref_ext.xref)
    log.debug("Optimizable images: JPEGs: %s PNGs: %s", len(jpegs), len(pngs))
    return jpegs, pngs


def extract_images_jbig2(pike: Pdf, root: Path, options) -> Dict[int, List[XrefExt]]:
    """Extract any bitonal image that we think we can improve as JBIG2"""

    jbig2_groups = defaultdict(list)
    for pageno, xref_ext in extract_images(pike, root, options, extract_image_jbig2):
        group = pageno // options.jbig2_page_group_size
        jbig2_groups[group].append(xref_ext)

    # Elide empty groups
    jbig2_groups = {
        group: xrefs for group, xrefs in jbig2_groups.items() if len(xrefs) > 0
    }
    log.debug("Optimizable images: JBIG2 groups: %s", (len(jbig2_groups),))
    return jbig2_groups


def _produce_jbig2_images(
    jbig2_groups: Dict[int, List[XrefExt]], root: Path, options
) -> None:
    """Produce JBIG2 images from their groups"""

    def jbig2_group_args(root: Path, groups: Dict[int, List[XrefExt]]):
        for group, xref_exts in groups.items():
            prefix = f'group{group:08d}'
            yield dict(
                cwd=fspath(root),
                infiles=(img_name(root, xref, ext) for xref, ext in xref_exts),
                out_prefix=prefix,
            )

    def jbig2_single_args(root, groups: Dict[int, List[XrefExt]]):
        for group, xref_exts in groups.items():
            prefix = f'group{group:08d}'
            # Second loop is to ensure multiple images per page are unpacked
            for n, xref_ext in enumerate(xref_exts):
                xref, ext = xref_ext
                yield dict(
                    cwd=fspath(root),
                    infile=img_name(root, xref, ext),
                    outfile=root / f'{prefix}.{n:04d}',
                )

    def convert_generic(fn, kwargs_dict):
        return fn(**kwargs_dict)

    if options.jbig2_page_group_size > 1:
        jbig2_args = jbig2_group_args
        jbig2_convert = partial(convert_generic, jbig2enc.convert_group)
    else:
        jbig2_args = jbig2_single_args
        jbig2_convert = partial(convert_generic, jbig2enc.convert_single)

    exec_progress_pool(
        use_threads=True,
        max_workers=options.jobs,
        tqdm_kwargs=dict(
            total=len(jbig2_groups),
            desc="JBIG2",
            unit='item',
            disable=not options.progress_bar,
        ),
        task=jbig2_convert,
        task_arguments=jbig2_args(root, jbig2_groups),
    )


def convert_to_jbig2(
    pike: Pdf, jbig2_groups: Dict[int, List[XrefExt]], root: Path, options
) -> None:
    """Convert images to JBIG2 and insert into PDF.

    When the JBIG2 page group size is > 1 we do several JBIG2 images at once
    and build a symbol dictionary that will span several pages. Each JBIG2
    image must reference to its symbol dictionary. If too many pages shared the
    same dictionary JBIG2 encoding becomes more expensive and less efficient.
    The default value of 10 was determined through testing. Currently this
    must be lossy encoding since jbig2enc does not support refinement coding.

    When the JBIG2 symbolic coder is not used, each JBIG2 stands on its own
    and needs no dictionary. Currently this must be lossless JBIG2.
    """

    _produce_jbig2_images(jbig2_groups, root, options)

    for group, xref_exts in jbig2_groups.items():
        prefix = f'group{group:08d}'
        jbig2_symfile = root / (prefix + '.sym')
        if jbig2_symfile.exists():
            jbig2_globals_data = jbig2_symfile.read_bytes()
            jbig2_globals = pikepdf.Stream(pike, jbig2_globals_data)
            jbig2_globals_dict = Dictionary(JBIG2Globals=jbig2_globals)
        elif options.jbig2_page_group_size == 1:
            jbig2_globals_dict = None
        else:
            raise FileNotFoundError(jbig2_symfile)

        for n, xref_ext in enumerate(xref_exts):
            xref, _ = xref_ext
            jbig2_im_file = root / (prefix + f'.{n:04d}')
            jbig2_im_data = jbig2_im_file.read_bytes()
            im_obj = pike.get_object(xref, 0)
            im_obj.write(
                jbig2_im_data, filter=Name.JBIG2Decode, decode_parms=jbig2_globals_dict
            )


def transcode_jpegs(pike: Pdf, jpegs: Sequence[Xref], root: Path, options) -> None:
    for xref in tqdm(
        jpegs, desc="JPEGs", unit='image', disable=not options.progress_bar
    ):
        in_jpg = jpg_name(root, xref)
        opt_jpg = in_jpg.with_suffix('.opt.jpg')

        # This produces a debug warning from PIL
        # DEBUG:PIL.Image:Error closing: 'NoneType' object has no attribute
        # 'close'.  Seems to be mostly harmless
        # https://github.com/python-pillow/Pillow/issues/1144
        with Image.open(in_jpg) as im:
            im.save(opt_jpg, optimize=True, quality=options.jpeg_quality)

        if opt_jpg.stat().st_size > in_jpg.stat().st_size:
            log.debug("xref %s, jpeg, made larger - skip", xref)
            continue

        compdata = leptonica.CompressedData.open(opt_jpg)
        im_obj = pike.get_object(xref, 0)
        im_obj.write(compdata.read(), filter=Name.DCTDecode)


def transcode_pngs(
    pike: Pdf,
    images: Sequence[Xref],
    image_name_fn: Callable[[Path, Xref], Path],
    root: Path,
    options,
) -> None:
    modified: MutableSet[Xref] = set()
    if options.optimize >= 2:
        png_quality = (
            max(10, options.png_quality - 10),
            min(100, options.png_quality + 10),
        )

        def pngquant_args():
            for xref in images:
                log.debug(image_name_fn(root, xref))
                yield (
                    image_name_fn(root, xref),
                    png_name(root, xref),
                    png_quality[0],
                    png_quality[1],
                )
                modified.add(xref)

        def pngquant_fn(args):
            pngquant.quantize(*args)

        exec_progress_pool(
            use_threads=True,
            max_workers=options.jobs,
            tqdm_kwargs=dict(
                desc="PNGs",
                total=len(images),
                unit='image',
                disable=not options.progress_bar,
            ),
            task=pngquant_fn,
            task_arguments=pngquant_args(),
        )

    for xref in modified:
        im_obj = pike.get_object(xref, 0)
        try:
            pix = leptonica.Pix.open(png_name(root, xref))
            if pix.mode == '1':
                compdata = pix.generate_pdf_ci_data(leptonica.lept.L_G4_ENCODE, 0)
            else:
                compdata = leptonica.CompressedData.open(png_name(root, xref))
        except leptonica.LeptonicaError as e:
            # Most likely this means file not found, i.e. quantize did not
            # produce an improved version
            log.error(e)
            continue

        # If re-coded image is larger don't use it - we test here because
        # pngquant knows the size of the temporary output file but not the actual
        # object in the PDF
        if len(compdata) > int(im_obj.stream_dict.Length):
            log.debug(
                f"pngquant: pngquant did not improve over original image "
                f"{len(compdata)} > {int(im_obj.stream_dict.Length)}"
            )
            continue
        if compdata.type == leptonica.lept.L_FLATE_ENCODE:
            rewrite_png(pike, im_obj, compdata)
        elif compdata.type == leptonica.lept.L_G4_ENCODE:
            rewrite_png_as_g4(pike, im_obj, compdata)


def rewrite_png_as_g4(pike: Pdf, im_obj: Object, compdata) -> None:
    im_obj.BitsPerComponent = 1
    im_obj.Width = compdata.w
    im_obj.Height = compdata.h

    im_obj.write(compdata.read())

    log.debug(f"PNG to G4 {im_obj.objgen}")
    if Name.Predictor in im_obj:
        del im_obj.Predictor
    if Name.DecodeParms in im_obj:
        del im_obj.DecodeParms
    im_obj.DecodeParms = Dictionary(
        K=-1, BlackIs1=bool(compdata.minisblack), Columns=compdata.w
    )

    im_obj.Filter = Name.CCITTFaxDecode
    return


def rewrite_png(pike: Pdf, im_obj: Object, compdata) -> None:
    # When a PNG is inserted into a PDF, we more or less copy the IDAT section from
    # the PDF and transfer the rest of the PNG headers to PDF image metadata.
    # One thing we have to do is tell the PDF reader whether a predictor was used
    # on the image before Flate encoding. (Typically one is.)
    # According to Leptonica source, PDF readers don't actually need us
    # to specify the correct predictor, they just need a value of either:
    #   1 - no predictor
    #   10-14 - there is a predictor
    # Leptonica's compdata->predictor only tells TRUE or FALSE
    # 10-14 means the actual predictor is specified in the data, so for any
    # number >= 10 the PDF reader will use whatever the PNG data specifies.
    # In practice Leptonica should use Paeth, 14, but 15 seems to be the
    # designated value for "optimal". So we will use 15.
    # See:
    #   - PDF RM 7.4.4.4 Table 10
    #   - https://github.com/DanBloomberg/leptonica/blob/master/src/pdfio2.c#L757
    predictor = 15 if compdata.predictor > 0 else 1
    dparms = Dictionary(Predictor=predictor)
    if predictor > 1:
        dparms.BitsPerComponent = compdata.bps  # Yes, this is redundant
        dparms.Colors = compdata.spp
        dparms.Columns = compdata.w

    im_obj.BitsPerComponent = compdata.bps
    im_obj.Width = compdata.w
    im_obj.Height = compdata.h

    log.debug(
        f"PNG {im_obj.objgen}: palette={compdata.ncolors} spp={compdata.spp} bps={compdata.bps}"
    )
    if compdata.ncolors > 0:
        # .ncolors is the number of colors in the palette, not the number of
        # colors used in a true color image. The palette string is always
        # given as RGB tuples even when the image is grayscale; see
        # https://github.com/DanBloomberg/leptonica/blob/master/src/colormap.c#L2067
        palette_pdf_string = compdata.get_palette_pdf_string()
        palette_data = pikepdf.Object.parse(palette_pdf_string)
        palette_stream = pikepdf.Stream(pike, bytes(palette_data))
        palette = [Name.Indexed, Name.DeviceRGB, compdata.ncolors - 1, palette_stream]
        cs = palette
    else:
        # ncolors == 0 means we are using a colorspace without a palette
        if compdata.spp == 1:
            cs = Name.DeviceGray
        elif compdata.spp == 3:
            cs = Name.DeviceRGB
        elif compdata.spp == 4:
            cs = Name.DeviceCMYK
    im_obj.ColorSpace = cs
    im_obj.write(compdata.read(), filter=Name.FlateDecode, decode_parms=dparms)


def optimize(input_file: Path, output_file: Path, context, save_settings) -> None:
    options = context.options
    if options.optimize == 0:
        safe_symlink(input_file, output_file)
        return

    if options.jpeg_quality == 0:
        options.jpeg_quality = DEFAULT_JPEG_QUALITY if options.optimize < 3 else 40
    if options.png_quality == 0:
        options.png_quality = DEFAULT_PNG_QUALITY if options.optimize < 3 else 30
    if options.jbig2_page_group_size == 0:
        options.jbig2_page_group_size = 10 if options.jbig2_lossy else 1

    with pikepdf.Pdf.open(input_file) as pike:
        root = output_file.parent / 'images'
        root.mkdir(exist_ok=True)

        jpegs, pngs = extract_images_generic(pike, root, options)
        transcode_jpegs(pike, jpegs, root, options)
        # if options.optimize >= 2:
        # Try pngifying the jpegs
        #    transcode_pngs(pike, jpegs, jpg_name, root, options)
        transcode_pngs(pike, pngs, png_name, root, options)

        jbig2_groups = extract_images_jbig2(pike, root, options)
        convert_to_jbig2(pike, jbig2_groups, root, options)

        target_file = output_file.with_suffix('.opt.pdf')
        pike.remove_unreferenced_resources()
        pike.save(target_file, **save_settings)

    input_size = input_file.stat().st_size
    output_size = target_file.stat().st_size
    if output_size == 0:
        raise OutputFileAccessError(
            f"Output file not created after optimizing. We probably ran "
            f"out of disk space in the temporary folder: {tempfile.gettempdir()}."
        )
    ratio = input_size / output_size
    savings = 1 - output_size / input_size
    log.info(f"Optimize ratio: {ratio:.2f} savings: {(100 * savings):.1f}%")

    if savings < 0:
        log.info("Image optimization did not improve the file - discarded")
        # We still need to save the file
        with pikepdf.open(input_file) as pike:
            pike.remove_unreferenced_resources()
            pike.save(output_file, **save_settings)
    else:
        safe_symlink(target_file, output_file)


def main(infile, outfile, level, jobs=1):
    from shutil import copy  # pylint: disable=import-outside-toplevel
    from tempfile import TemporaryDirectory  # pylint: disable=import-outside-toplevel

    class OptimizeOptions:
        """Emulate ocrmypdf's options"""

        def __init__(
            self, input_file, jobs, optimize_, jpeg_quality, png_quality, jb2lossy
        ):
            self.input_file = input_file
            self.jobs = jobs
            self.optimize = optimize_
            self.jpeg_quality = jpeg_quality
            self.png_quality = png_quality
            self.jbig2_page_group_size = 0
            self.jbig2_lossy = jb2lossy
            self.quiet = True
            self.progress_bar = False

    infile = Path(infile)
    options = OptimizeOptions(
        input_file=infile,
        jobs=jobs,
        optimize_=int(level),
        jpeg_quality=0,  # Use default
        png_quality=0,
        jb2lossy=False,
    )

    with TemporaryDirectory() as td:
        context = PdfContext(options, td, infile, None, None)
        tmpout = Path(td) / 'out.pdf'
        optimize(
            infile,
            tmpout,
            context,
            dict(
                compress_streams=True,
                preserve_pdfa=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            ),
        )
        copy(fspath(tmpout), fspath(outfile))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
