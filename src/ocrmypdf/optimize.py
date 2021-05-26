# © 2018 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import sys
import tempfile
from collections import defaultdict
from os import fspath
from pathlib import Path
from typing import (
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
)

import img2pdf
import pikepdf
from pikepdf import Dictionary, Name, Object, Pdf, PdfImage
from PIL import Image

from ocrmypdf import leptonica
from ocrmypdf._concurrent import Executor, SerialExecutor
from ocrmypdf._exec import jbig2enc, pngquant
from ocrmypdf._jobcontext import PdfContext
from ocrmypdf.exceptions import OutputFileAccessError
from ocrmypdf.helpers import safe_symlink

log = logging.getLogger(__name__)

DEFAULT_JPEG_QUALITY = 75
DEFAULT_PNG_QUALITY = 70


Xref = NewType('Xref', int)


class XrefExt(NamedTuple):  # pylint: disable=inherit-non-class
    xref: Xref
    ext: str


def img_name(root: Path, xref: Xref, ext: str) -> Path:
    return root / f'{xref:08d}{ext}'


def png_name(root: Path, xref: Xref) -> Path:
    return img_name(root, xref, '.png')


def jpg_name(root: Path, xref: Xref) -> Path:
    return img_name(root, xref, '.jpg')


def extract_image_filter(
    pike: Pdf, root: Path, image: Object, xref: Xref
) -> Optional[Tuple[PdfImage, Tuple[Name, Object]]]:
    del pike  # unused args
    del root

    if image.Subtype != Name.Image:
        return None
    if image.Length < 100:
        log.debug(f"Skipping small image, xref {xref}")
        return None
    if image.Width < 8 or image.Height < 8:  # Issue 732
        log.debug(f"Skipping oddly sized image, xref {xref}")
        return None

    pim = PdfImage(image)

    if len(pim.filter_decodeparms) > 1:
        log.debug(f"Skipping multiply filtered image, xref {xref}")
        return None
    filtdp = pim.filter_decodeparms[0]

    if pim.bits_per_component > 8:
        log.debug(f"Skipping wide gamut image, xref {xref}")
        return None  # Don't mess with wide gamut images

    if filtdp[0] == Name.JPXDecode:
        log.debug(f"Skipping JPEG2000 iamge, xref {xref}")
        return None  # Don't do JPEG2000

    if filtdp[0] == Name.CCITTFaxDecode and filtdp[1].get('/K', 0) >= 0:
        log.debug(f"Skipping CCITT Group 3 image, xref {xref}")
        return None  # pikepdf doesn't support Group 3 yet

    if Name.Decode in image:
        log.debug(f"Skipping image with Decode table, xref {xref}")
        return None  # Don't mess with custom Decode tables

    return pim, filtdp


def extract_image_jbig2(
    *, pike: pikepdf.Pdf, root: Path, image: Object, xref: Xref, options
) -> Optional[XrefExt]:
    del options  # unused arg

    result = extract_image_filter(pike, root, image, xref)
    if result is None:
        return None
    pim, filtdp = result

    if (
        pim.bits_per_component == 1
        and filtdp[0] != Name.JBIG2Decode
        and jbig2enc.available()
    ):
        # Save any colorspace associated with the image, so that we
        # will export a pure 1-bit PNG with no palette or ICC profile.
        # Showing the palette or ICC to jbig2enc will cause it to perform
        # colorspace transform to 1bpp, which will conflict the palette or
        # ICC if it exists.
        colorspace = pim.obj.get(pikepdf.Name.ColorSpace, None)
        if colorspace is not None or pim.image_mask:
            try:
                # Set to DeviceGray temporarily; we already in 1 bpc.
                pim.obj.ColorSpace = pikepdf.Name.DeviceGray
                imgname = root / f'{xref:08d}'
                with imgname.open('wb') as f:
                    ext = pim.extract_to(stream=f)
                imgname.rename(imgname.with_suffix(ext))
            except pikepdf.UnsupportedImageTypeError:
                return None
            finally:
                # Restore image colorspace after temporarily setting it to DeviceGray
                if colorspace is not None:
                    pim.obj.ColorSpace = colorspace
                else:
                    del pim.obj.ColorSpace
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
    pike: Pdf,
    root: Path,
    options,
    extract_fn: Callable[..., Optional[XrefExt]],
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
                log.debug(f"Skipping image {smask_xref} because it is an SMask")
            include_xrefs.add(xref)
            log.debug(f"Treating {xref} as an optimization candidate")
            if xref not in pageno_for_xref:
                pageno_for_xref[xref] = pageno

    working_xrefs = include_xrefs - exclude_xrefs
    for xref in working_xrefs:
        image = pike.get_object((xref, 0))
        try:
            result = extract_fn(
                pike=pike, root=root, image=image, xref=xref, options=options
            )
        except Exception:  # pylint: disable=broad-except
            log.exception(f"While extracting image xref {xref}, an error occurred")
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

    log.debug("Optimizable images: JBIG2 groups: %s", (len(jbig2_groups),))
    return jbig2_groups


def _produce_jbig2_images(
    jbig2_groups: Dict[int, List[XrefExt]], root: Path, options, executor: Executor
) -> None:
    """Produce JBIG2 images from their groups"""

    def jbig2_group_args(root: Path, groups: Dict[int, List[XrefExt]]):
        for group, xref_exts in groups.items():
            prefix = f'group{group:08d}'
            yield (
                fspath(root),  # =cwd
                (img_name(root, xref, ext) for xref, ext in xref_exts),  # =infiles
                prefix,  # =out_prefix
            )

    def jbig2_single_args(root, groups: Dict[int, List[XrefExt]]):
        for group, xref_exts in groups.items():
            prefix = f'group{group:08d}'
            # Second loop is to ensure multiple images per page are unpacked
            for n, xref_ext in enumerate(xref_exts):
                xref, ext = xref_ext
                yield (
                    fspath(root),
                    img_name(root, xref, ext),
                    root / f'{prefix}.{n:04d}',
                )

    if options.jbig2_page_group_size > 1:
        jbig2_args = jbig2_group_args
        jbig2_convert = jbig2enc.convert_group_mp
    else:
        jbig2_args = jbig2_single_args
        jbig2_convert = jbig2enc.convert_single_mp

    executor(
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
    pike: Pdf,
    jbig2_groups: Dict[int, List[XrefExt]],
    root: Path,
    options,
    executor: Executor,
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

    _produce_jbig2_images(jbig2_groups, root, options, executor)

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


def _optimize_jpeg(args):
    xref, in_jpg, opt_jpg, jpeg_quality = args

    # This may produce a debug warning from PIL
    # DEBUG:PIL.Image:Error closing: 'NoneType' object has no attribute
    # 'close'.  Seems to be mostly harmless
    # https://github.com/python-pillow/Pillow/issues/1144
    with Image.open(in_jpg) as im:
        im.save(opt_jpg, optimize=True, quality=jpeg_quality)

    if opt_jpg.stat().st_size > in_jpg.stat().st_size:
        log.debug("xref %s, jpeg, made larger - skip", xref)
        opt_jpg.unlink()
        opt_jpg = None
    return xref, opt_jpg


def transcode_jpegs(
    pike: Pdf, jpegs: Sequence[Xref], root: Path, options, executor
) -> None:
    def jpeg_args():
        for xref in jpegs:
            in_jpg = jpg_name(root, xref)
            opt_jpg = in_jpg.with_suffix('.opt.jpg')
            yield xref, in_jpg, opt_jpg, options.jpeg_quality

    def finish_jpeg(result, pbar):
        xref, opt_jpg = result
        if opt_jpg:
            compdata = leptonica.CompressedData.open(opt_jpg)
            im_obj = pike.get_object(xref, 0)
            im_obj.write(compdata.read(), filter=Name.DCTDecode)
        pbar.update()

    executor(
        use_threads=True,  # Processes are significantly slower at this task
        max_workers=options.jobs,
        tqdm_kwargs=dict(
            desc="JPEGs",
            total=len(jpegs),
            unit='image',
            disable=not options.progress_bar,
        ),
        task=_optimize_jpeg,
        task_arguments=jpeg_args(),
        task_finished=finish_jpeg,
    )


def _transcode_png(pike: Pdf, filename: Path, xref: Xref) -> bool:
    output = filename.with_suffix('.png.pdf')
    with output.open('wb') as f:
        img2pdf.convert(fspath(filename), outputstream=f)

    with pikepdf.open(output) as pdf_image:
        foreign_image = next(pdf_image.pages[0].images.values())
        local_image = pike.copy_foreign(foreign_image)

        im_obj = pike.get_object(xref, 0)
        im_obj.write(
            local_image.read_raw_bytes(),
            filter=local_image.Filter,
            decode_parms=local_image.DecodeParms,
        )

        # Don't copy keys from the new image...
        del_keys = set(im_obj.keys()) - set(local_image.keys())
        # ...except for the keep_fields, which are essential to displaying
        # the image correctly and preserving its metadata. (/Decode arrays
        # and /SMaskInData are implicitly discarded prior to this point.)
        keep_fields = {
            '/ID',
            '/Intent',
            '/Interpolate',
            '/Mask',
            '/Metadata',
            '/OC',
            '/OPI',
            '/SMask',
            '/StructParent',
        }
        del_keys -= keep_fields
        for key in local_image.keys():
            if key != Name.Length and str(key) not in keep_fields:
                im_obj[key] = local_image[key]
        for key in del_keys:
            del im_obj[key]
    return True


def transcode_pngs(
    pike: Pdf,
    images: Sequence[Xref],
    image_name_fn: Callable[[Path, Xref], Path],
    root: Path,
    options,
    executor,
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

        executor(
            use_threads=True,
            max_workers=options.jobs,
            tqdm_kwargs=dict(
                desc="PNGs",
                total=len(images),
                unit='image',
                disable=not options.progress_bar,
            ),
            task=pngquant.quantize_mp,
            task_arguments=pngquant_args(),
        )

    for xref in modified:
        filename = png_name(root, xref)
        _transcode_png(pike, filename, xref)


def optimize(
    input_file: Path,
    output_file: Path,
    context,
    save_settings,
    executor: Executor = SerialExecutor(),
) -> None:
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
        transcode_jpegs(pike, jpegs, root, options, executor)
        # if options.optimize >= 2:
        # Try pngifying the jpegs
        #    transcode_pngs(pike, jpegs, jpg_name, root, options)
        transcode_pngs(pike, pngs, png_name, root, options, executor)

        jbig2_groups = extract_images_jbig2(pike, root, options)
        convert_to_jbig2(pike, jbig2_groups, root, options, executor)

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
    log.info(f"Optimize ratio: {ratio:.2f} savings: {(savings):.1%}")

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
