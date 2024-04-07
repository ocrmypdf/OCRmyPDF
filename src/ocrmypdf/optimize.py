# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Post-processing image optimization of OCR PDFs."""

from __future__ import annotations

import logging
import sys
import tempfile
import threading
from collections import defaultdict
from collections.abc import Callable, Iterator, MutableSet, Sequence
from os import fspath
from pathlib import Path
from typing import Any, NamedTuple, NewType
from zlib import compress

import img2pdf
from pikepdf import (
    Dictionary,
    Name,
    Object,
    ObjectStreamMode,
    Pdf,
    PdfError,
    PdfImage,
    Stream,
    UnsupportedImageTypeError,
)
from PIL import Image

from ocrmypdf._concurrent import Executor, SerialExecutor
from ocrmypdf._exec import jbig2enc, pngquant
from ocrmypdf._jobcontext import PdfContext
from ocrmypdf._progressbar import ProgressBar
from ocrmypdf.exceptions import OutputFileAccessError
from ocrmypdf.helpers import IMG2PDF_KWARGS, safe_symlink

log = logging.getLogger(__name__)

DEFAULT_JPEG_QUALITY = 75
DEFAULT_PNG_QUALITY = 70


Xref = NewType('Xref', int)


class XrefExt(NamedTuple):
    """A PDF xref and image extension pair."""

    xref: Xref
    ext: str


def img_name(root: Path, xref: Xref, ext: str) -> Path:
    """Return the name of an image file for a given xref and extension."""
    return root / f'{xref:08d}{ext}'


def png_name(root: Path, xref: Xref) -> Path:
    """Return the name of a PNG file for a given xref."""
    return img_name(root, xref, '.png')


def jpg_name(root: Path, xref: Xref) -> Path:
    """Return the name of a JPEG file for a given xref."""
    return img_name(root, xref, '.jpg')


def extract_image_filter(
    image: Stream, xref: Xref
) -> tuple[PdfImage, tuple[Name, Object]] | None:
    """Determine if an image is extractable."""
    if image.Subtype != Name.Image:
        return None
    if image.Length < 100:
        log.debug(f"xref {xref}: skipping image with small stream size")
        return None
    if image.Width < 8 or image.Height < 8:  # Issue 732
        log.debug(f"xref {xref}: skipping image with unusually small dimensions")
        return None

    pim = PdfImage(image)

    if len(pim.filter_decodeparms) > 1:
        first_filtdp = pim.filter_decodeparms[0]
        second_filtdp = pim.filter_decodeparms[1]
        if (
            len(pim.filter_decodeparms) == 2
            and first_filtdp[0] == Name.FlateDecode
            and first_filtdp[1] is not None
            and first_filtdp[1].get(Name.Predictor, 1) == 1
            and second_filtdp[0] == Name.DCTDecode
            and not second_filtdp[1]
        ):
            log.debug(
                f"xref {xref}: found image compressed as /FlateDecode /DCTDecode, "
                "marked for JPEG optimization"
            )
            filtdp = pim.filter_decodeparms[1]
        else:
            log.debug(f"xref {xref}: skipping image with multiple compression filters")
            return None
    else:
        filtdp = pim.filter_decodeparms[0]

    if pim.bits_per_component > 8:
        log.debug(f"xref {xref}: skipping wide gamut image")
        return None  # Don't mess with wide gamut images

    if filtdp[0] == Name.JPXDecode:
        log.debug(f"xref {xref}: skipping JPEG2000 image")
        return None  # Don't do JPEG2000

    if filtdp[0] == Name.CCITTFaxDecode and filtdp[1].get('/K', 0) >= 0:
        log.debug(f"xref {xref}: skipping CCITT Group 3 image")
        return None  # pikepdf doesn't support Group 3 yet

    if Name.Decode in image:
        log.debug(f"xref {xref}: skipping image with Decode table")
        return None  # Don't mess with custom Decode tables

    return pim, filtdp


def extract_image_jbig2(
    *, pdf: Pdf, root: Path, image: Stream, xref: Xref, options
) -> XrefExt | None:
    """Extract an image, saving it as a JBIG2 file."""
    del options  # unused arg

    result = extract_image_filter(image, xref)
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
        colorspace = pim.obj.get(Name.ColorSpace, None)
        if colorspace is not None or pim.image_mask:
            try:
                # Set to DeviceGray temporarily; we already in 1 bpc.
                pim.obj.ColorSpace = Name.DeviceGray
                imgname = root / f'{xref:08d}'
                with imgname.open('wb') as f:
                    ext = pim.extract_to(stream=f)
                imgname.rename(imgname.with_suffix(ext))
            except NotImplementedError as e:
                if '/Decode' in str(e):
                    log.debug(
                        f"xref {xref}: skipping image with unsupported Decode table"
                    )
                    return None
                raise
            except UnsupportedImageTypeError:
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
    *, pdf: Pdf, root: Path, image: Stream, xref: Xref, options
) -> XrefExt | None:
    """Generic image extraction."""
    result = extract_image_filter(image, xref)
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
        try:
            imgname = root / f'{xref:08d}'
            with imgname.open('wb') as f:
                ext = pim.extract_to(stream=f)
            imgname.rename(imgname.with_suffix(ext))
        except UnsupportedImageTypeError:
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
        try:
            pim.as_pil_image().save(png_name(root, xref))
        except NotImplementedError:
            log.warning("PDF contains an atypical image that cannot be optimized.")
            return None
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


def _find_image_xrefs_container(
    pdf: Pdf,
    container: Object,
    pageno: int,
    include_xrefs: MutableSet[Xref],
    exclude_xrefs: MutableSet[Xref],
    pageno_for_xref: dict[Xref, int],
    depth: int = 0,
):
    """Find all image XRefs or Form XObject and add to the include/exclude sets."""
    if depth > 10:
        log.warning("Recursion depth exceeded in _find_image_xrefs_page")
        return
    try:
        xobjs = container.Resources.XObject
    except AttributeError:
        return
    for _imname, image in dict(xobjs).items():
        if image.objgen[1] != 0:
            continue  # Ignore images in an incremental PDF
        if Name.Subtype in image and image.Subtype == Name.Form:
            # Recurse into Form XObjects
            log.debug(f"Recursing into Form XObject {_imname} in page {pageno}")
            _find_image_xrefs_container(
                pdf,
                image,
                pageno,
                include_xrefs,
                exclude_xrefs,
                pageno_for_xref,
                depth + 1,
            )
            continue
        xref = Xref(image.objgen[0])
        if Name.SMask in image:
            # Ignore soft masks
            smask_xref = Xref(image.SMask.objgen[0])
            exclude_xrefs.add(smask_xref)
            log.debug(f"xref {smask_xref}: skipping image because it is an SMask")
        include_xrefs.add(xref)
        log.debug(f"xref {xref}: treating as an optimization candidate")
        if xref not in pageno_for_xref:
            pageno_for_xref[xref] = pageno


def _find_image_xrefs(pdf: Pdf):
    include_xrefs: MutableSet[Xref] = set()
    exclude_xrefs: MutableSet[Xref] = set()
    pageno_for_xref: dict[Xref, int] = {}

    for pageno, page in enumerate(pdf.pages):
        _find_image_xrefs_container(
            pdf, page.obj, pageno, include_xrefs, exclude_xrefs, pageno_for_xref
        )

    working_xrefs = include_xrefs - exclude_xrefs
    return working_xrefs, pageno_for_xref


def extract_images(
    pdf: Pdf,
    root: Path,
    options,
    extract_fn: Callable[..., XrefExt | None],
) -> Iterator[tuple[int, XrefExt]]:
    """Extract image using extract_fn.

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
    errors = 0
    working_xrefs, pageno_for_xref = _find_image_xrefs(pdf)
    for xref in working_xrefs:
        image = pdf.get_object((xref, 0))
        try:
            result = extract_fn(
                pdf=pdf, root=root, image=image, xref=xref, options=options
            )
        except Exception:  # pylint: disable=broad-except
            log.exception(
                f"xref {xref}: While extracting this image, an error occurred"
            )
            errors += 1
        else:
            if result:
                _, ext = result
                yield pageno_for_xref[xref], XrefExt(xref, ext)


def extract_images_generic(
    pdf: Pdf, root: Path, options
) -> tuple[list[Xref], list[Xref]]:
    """Extract any >=2bpp image we think we can improve."""
    jpegs = []
    pngs = []
    for _, xref_ext in extract_images(pdf, root, options, extract_image_generic):
        log.debug('%s', xref_ext)
        if xref_ext.ext == '.png':
            pngs.append(xref_ext.xref)
        elif xref_ext.ext == '.jpg':
            jpegs.append(xref_ext.xref)
    log.debug(f"Optimizable images: JPEGs: {len(jpegs)} PNGs: {len(pngs)}")
    return jpegs, pngs


def extract_images_jbig2(pdf: Pdf, root: Path, options) -> dict[int, list[XrefExt]]:
    """Extract any bitonal image that we think we can improve as JBIG2."""
    jbig2_groups = defaultdict(list)
    for pageno, xref_ext in extract_images(pdf, root, options, extract_image_jbig2):
        group = pageno // options.jbig2_page_group_size
        jbig2_groups[group].append(xref_ext)

    log.debug(f"Optimizable images: JBIG2 groups: {len(jbig2_groups)}")
    return jbig2_groups


def _produce_jbig2_images(
    jbig2_groups: dict[int, list[XrefExt]], root: Path, options, executor: Executor
) -> None:
    """Produce JBIG2 images from their groups."""

    def jbig2_group_args(root: Path, groups: dict[int, list[XrefExt]]):
        for group, xref_exts in groups.items():
            prefix = f'group{group:08d}'
            yield (
                fspath(root),  # =cwd
                (img_name(root, xref, ext) for xref, ext in xref_exts),  # =infiles
                prefix,  # =out_prefix
                options.jbig2_threshold,
            )

    def jbig2_single_args(root: Path, groups: dict[int, list[XrefExt]]):
        for group, xref_exts in groups.items():
            prefix = f'group{group:08d}'
            # Second loop is to ensure multiple images per page are unpacked
            for n, xref_ext in enumerate(xref_exts):
                xref, ext = xref_ext
                yield (
                    fspath(root),
                    img_name(root, xref, ext),
                    root / f'{prefix}.{n:04d}',
                    options.jbig2_threshold,
                )

    if options.jbig2_page_group_size > 1:
        jbig2_args = jbig2_group_args
        jbig2_convert = jbig2enc.convert_group
    else:
        jbig2_args = jbig2_single_args
        jbig2_convert = jbig2enc.convert_single

    executor(
        use_threads=True,
        max_workers=options.jobs,
        progress_kwargs=dict(
            total=len(jbig2_groups),
            desc="JBIG2",
            unit='item',
            disable=not options.progress_bar,
        ),
        task=jbig2_convert,
        task_arguments=jbig2_args(root, jbig2_groups),
    )


def convert_to_jbig2(
    pdf: Pdf,
    jbig2_groups: dict[int, list[XrefExt]],
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
    jbig2_globals_dict: Dictionary | None

    _produce_jbig2_images(jbig2_groups, root, options, executor)

    for group, xref_exts in jbig2_groups.items():
        prefix = f'group{group:08d}'
        jbig2_symfile = root / (prefix + '.sym')
        if jbig2_symfile.exists():
            jbig2_globals_data = jbig2_symfile.read_bytes()
            jbig2_globals = Stream(pdf, jbig2_globals_data)
            jbig2_globals_dict = Dictionary(JBIG2Globals=jbig2_globals)
        elif options.jbig2_page_group_size == 1:
            jbig2_globals_dict = None
        else:
            raise FileNotFoundError(jbig2_symfile)

        for n, xref_ext in enumerate(xref_exts):
            xref, _ = xref_ext
            jbig2_im_file = root / (prefix + f'.{n:04d}')
            jbig2_im_data = jbig2_im_file.read_bytes()
            im_obj = pdf.get_object(xref, 0)
            im_obj.write(
                jbig2_im_data, filter=Name.JBIG2Decode, decode_parms=jbig2_globals_dict
            )


def _optimize_jpeg(
    xref: Xref, in_jpg: Path, opt_jpg: Path, jpeg_quality: int
) -> tuple[Xref, Path | None]:
    with Image.open(in_jpg) as im:
        im.save(opt_jpg, optimize=True, quality=jpeg_quality)

    if opt_jpg.stat().st_size > in_jpg.stat().st_size:
        log.debug(f"xref {xref}, jpeg, made larger - skip")
        opt_jpg.unlink()
        return xref, None
    return xref, opt_jpg


def transcode_jpegs(
    pdf: Pdf, jpegs: Sequence[Xref], root: Path, options, executor: Executor
) -> None:
    """Optimize JPEGs according to optimization settings."""

    def jpeg_args() -> Iterator[tuple[Xref, Path, Path, int]]:
        for xref in jpegs:
            in_jpg = jpg_name(root, xref)
            opt_jpg = in_jpg.with_suffix('.opt.jpg')
            yield xref, in_jpg, opt_jpg, options.jpeg_quality

    def finish_jpeg(result: tuple[Xref, Path | None], pbar: ProgressBar):
        xref, opt_jpg = result
        if opt_jpg:
            compdata = opt_jpg.read_bytes()  # JPEG can inserted into PDF as is
            im_obj = pdf.get_object(xref, 0)
            im_obj.write(compdata, filter=Name.DCTDecode)
        pbar.update()

    executor(
        use_threads=True,  # Processes are significantly slower at this task
        max_workers=options.jobs,
        progress_kwargs=dict(
            desc="Recompressing JPEGs",
            total=len(jpegs),
            unit='image',
            disable=not options.progress_bar,
        ),
        task=_optimize_jpeg,
        task_arguments=jpeg_args(),
        task_finished=finish_jpeg,
    )


def _find_deflatable_jpeg(
    *, pdf: Pdf, root: Path, image: Stream, xref: Xref, options
) -> XrefExt | None:
    result = extract_image_filter(image, xref)
    if result is None:
        return None
    _pim, filtdp = result

    if filtdp[0] == Name.DCTDecode and not filtdp[1] and options.optimize >= 1:
        return XrefExt(xref, '.memory')

    return None


def _deflate_jpeg(
    pdf: Pdf, lock: threading.Lock, xref: Xref, complevel: int
) -> tuple[Xref, bytes]:
    with lock:
        xobj = pdf.get_object(xref, 0)
        try:
            data = xobj.read_raw_bytes()
        except PdfError:
            return xref, b''
    compdata = compress(data, complevel)
    if len(compdata) >= len(data):
        return xref, b''
    return xref, compdata


def deflate_jpegs(pdf: Pdf, root: Path, options, executor: Executor) -> None:
    """Apply FlateDecode to JPEGs.

    This is a lossless compression method that is supported by all PDF viewers,
    and generally results in a smaller file size compared to straight DCTDecode
    images.
    """
    jpegs = []
    for _pageno, xref_ext in extract_images(pdf, root, options, _find_deflatable_jpeg):
        xref = xref_ext.xref
        log.debug(f'xref {xref}: marking this JPEG as deflatable')
        jpegs.append(xref)

    complevel = 9 if options.optimize == 3 else 6

    # Our calls to xobj.write() in finish() need coordination
    lock = threading.Lock()

    def deflate_args() -> Iterator:
        for xref in jpegs:
            yield pdf, lock, xref, complevel

    def finish(result: tuple[Xref, bytes], pbar: ProgressBar):
        xref, compdata = result
        if len(compdata) > 0:
            with lock:
                xobj = pdf.get_object(xref, 0)
                xobj.write(compdata, filter=[Name.FlateDecode, Name.DCTDecode])
        pbar.update()

    executor(
        use_threads=True,  # We're sharing the pdf directly, must use threads
        max_workers=options.jobs,
        progress_kwargs=dict(
            desc="Deflating JPEGs",
            total=len(jpegs),
            unit='image',
            disable=not options.progress_bar,
        ),
        task=_deflate_jpeg,
        task_arguments=deflate_args(),
        task_finished=finish,
    )


def _transcode_png(pdf: Pdf, filename: Path, xref: Xref) -> bool:
    output = filename.with_suffix('.png.pdf')
    with output.open('wb') as f:
        img2pdf.convert(fspath(filename), outputstream=f, **IMG2PDF_KWARGS)

    with Pdf.open(output) as pdf_image:
        foreign_image = next(iter(pdf_image.pages[0].images.values()))
        local_image = pdf.copy_foreign(foreign_image)

        im_obj = pdf.get_object(xref, 0)
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
    pdf: Pdf,
    images: Sequence[Xref],
    image_name_fn: Callable[[Path, Xref], Path],
    root: Path,
    options,
    executor: Executor,
) -> None:
    """Apply lossy transcoding to PNGs."""
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
            progress_kwargs=dict(
                desc="PNGs",
                total=len(images),
                unit='image',
                disable=not options.progress_bar,
            ),
            task=pngquant.quantize,
            task_arguments=pngquant_args(),
        )

    for xref in modified:
        filename = png_name(root, xref)
        _transcode_png(pdf, filename, xref)


DEFAULT_EXECUTOR = SerialExecutor()


def optimize(
    input_file: Path,
    output_file: Path,
    context: PdfContext,
    save_settings: dict[str, Any],
    executor: Executor = DEFAULT_EXECUTOR,
) -> Path:
    """Optimize images in a PDF file."""
    options = context.options
    if options.optimize == 0:
        safe_symlink(input_file, output_file)
        return output_file

    if options.jpeg_quality == 0:
        options.jpeg_quality = DEFAULT_JPEG_QUALITY if options.optimize < 3 else 40
    if options.png_quality == 0:
        options.png_quality = DEFAULT_PNG_QUALITY if options.optimize < 3 else 30
    if options.jbig2_page_group_size == 0:
        options.jbig2_page_group_size = 10 if options.jbig2_lossy else 1

    with Pdf.open(input_file) as pdf:
        root = output_file.parent / 'images'
        root.mkdir(exist_ok=True)

        jpegs, pngs = extract_images_generic(pdf, root, options)
        transcode_jpegs(pdf, jpegs, root, options, executor)
        deflate_jpegs(pdf, root, options, executor)
        # if options.optimize >= 2:
        # Try pngifying the jpegs
        #    transcode_pngs(pdf, jpegs, jpg_name, root, options)
        transcode_pngs(pdf, pngs, png_name, root, options, executor)

        jbig2_groups = extract_images_jbig2(pdf, root, options)
        convert_to_jbig2(pdf, jbig2_groups, root, options, executor)

        target_file = output_file.with_suffix('.opt.pdf')
        pdf.remove_unreferenced_resources()
        pdf.save(target_file, **save_settings)

    input_size = input_file.stat().st_size
    output_size = target_file.stat().st_size
    if output_size == 0:
        raise OutputFileAccessError(
            f"Output file not created after optimizing. We probably ran "
            f"out of disk space in the temporary folder: {tempfile.gettempdir()}."
        )
    savings = 1 - output_size / input_size

    if savings < 0:
        log.info(
            "Image optimization did not improve the file - "
            "optimizations will not be used"
        )
        # We still need to save the file
        with Pdf.open(input_file) as pdf:
            pdf.remove_unreferenced_resources()
            pdf.save(output_file, **save_settings)
    else:
        safe_symlink(target_file, output_file)

    return output_file


def main(infile, outfile, level, jobs=1):
    """Entry point for direct optimization of a file."""
    from shutil import copy  # pylint: disable=import-outside-toplevel
    from tempfile import TemporaryDirectory  # pylint: disable=import-outside-toplevel

    class OptimizeOptions:
        """Emulate ocrmypdf's options."""

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
            self.jbig2_threshold = 0.85
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

    with TemporaryDirectory() as tmpdir:
        context = PdfContext(options, tmpdir, infile, None, None)
        tmpout = Path(tmpdir) / 'out.pdf'
        optimize(
            infile,
            tmpout,
            context,
            dict(
                compress_streams=True,
                preserve_pdfa=True,
                object_stream_mode=ObjectStreamMode.generate,
            ),
        )
        copy(fspath(tmpout), fspath(outfile))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
