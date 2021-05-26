# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from abc import ABC, abstractmethod, abstractstaticmethod
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from logging import Handler
from pathlib import Path
from typing import TYPE_CHECKING, AbstractSet, List, Optional

import pluggy

from ocrmypdf._concurrent import Executor
from ocrmypdf.helpers import Resolution

if TYPE_CHECKING:
    from PIL import Image

    # pylint: disable=ungrouped-imports
    from ocrmypdf._jobcontext import PageContext
    from ocrmypdf.pdfinfo import PdfInfo

    # pylint: enable=ungrouped-imports

hookspec = pluggy.HookspecMarker('ocrmypdf')

# pylint: disable=unused-argument


@hookspec(firstresult=True)
def get_logging_console() -> Handler:
    """Returns a custom logging handler.

    Generally this is necessary when both logging output and a progress bar are both
    outputting to ``sys.stderr``.

    Note:
        This is a :ref:`firstresult hook<firstresult>`.
    """


@hookspec
def add_options(parser: ArgumentParser) -> None:
    """Allows the plugin to add its own command line and API arguments.

    OCRmyPDF converts command line arguments to API arguments, so adding
    arguments here will cause new arguments to be processed for API calls
    to ``ocrmypdf.ocr``, or when invoked on the command line.

    Note:
        This hook will be called from the main process, and may modify global state
        before child worker processes are forked.
    """


@hookspec
def check_options(options: Namespace) -> None:
    """Called to ask the plugin to check all of the options.

    The plugin may check if options that it added are valid.

    Warnings or other messages may be passed to the user by creating a logger
    object using ``log = logging.getLogger(__name__)`` and logging to this.

    The plugin may also modify the *options*. All objects that are in options
    must be picklable so they can be marshalled to child worker processes.

    Raises:
        ocrmypdf.exceptions.ExitCodeException: If options are not acceptable
            and the application should terminate gracefully with an informative
            message and error code.
    Note:
        This hook will be called from the main process, and may modify global state
        before child worker processes are forked.
    """


@hookspec(firstresult=True)
def get_executor(progressbar_class) -> Executor:
    """Called to obtain an object that manages parallel execution.

    This may be used to replace OCRmyPDF's default parallel execution system
    with a third party alternative. For example, you could make OCRmyPDF run in a
    distributed environment.

    OCRmyPDF's executors are analogous to the standard Python executors in
    ``conconcurrent.futures``, but they do not work the same way. Executors may
    be reused for different, unrelated batch operations, since all of the context
    for a given job are passed to :meth:`Executor.__call__`.

    Should be of type :class:`Executor` or otherwise conforming to the protocol
    of that call.

    Arguments:
        progressbar_class: A progress bar class, which will be created when

    Note:
        This hook will be called from the main process, and may modify global state
        before child worker processes are forked.
    Note:
        This is a :ref:`firstresult hook<firstresult>`.
    """


@hookspec(firstresult=True)
def get_progressbar_class():
    """Called to obtain a class that can be used to monitor progress.

    A progress bar is assumed, but this could be used for any type of monitoring.

    The class should follow a tqdm-like protocol. Calling the class should return
    a new progress bar object, which is activated with ``__enter__`` and terminated
    ``__exit__``. An update method is called whenever the progress bar is updated.
    Progress bar objects will not be reused; a new one will be created for each
    group of tasks.

    The progress bar is held in the main process/thread and not updated by child
    process/threads. When a child notifies the parent of completed work, the
    parent updates the progress bar.

    The arguments are the same as `tqdm <https://github.com/tqdm/tqdm>`_ accepts.

    Progress bars should never write to ``sys.stdout``, or they will corrupt the
    output if OCRmyPDF writes a PDF to standard output.

    The type of events that OCRmyPDF reports to a progress bar may change in
    minor releases.

    Here is how OCRmyPDF will use the progress bar:

    Example:
        pbar_class = pm.hook.get_progressbar_class()
        with pbar_class(**tqdm_kwargs) as pbar:
            ...
            pbar.update(1)
    """


@hookspec
def validate(pdfinfo: 'PdfInfo', options: Namespace) -> None:
    """Called to give a plugin an opportunity to review *options* and *pdfinfo*.

    *options* contains the "work order" to process a particular file. *pdfinfo*
    contains information about the input file obtained after loading and
    parsing. The plugin may modify the *options*. For example, you could decide
    that a certain type of file should be treated with ``options.force_ocr = True``
    based on information in its *pdfinfo*.

    Raises:
        ocrmypdf.exceptions.ExitCodeException: If options or pdfinfo are not acceptable
            and the application should terminate gracefully with an informative
            message and error code.
    Note:
        This hook will be called from the main process, and may modify global state
        before child worker processes are forked.
    """


@hookspec(firstresult=True)
def rasterize_pdf_page(
    input_file: Path,
    output_file: Path,
    raster_device: str,
    raster_dpi: Resolution,
    pageno: int,
    page_dpi: Optional[Resolution],
    rotation: Optional[int],
    filter_vector: bool,
) -> Path:
    """Rasterize one page of a PDF at resolution raster_dpi in canvas units.

    The image is sized to match the integer pixels dimensions implied by
    raster_dpi even if those numbers are noninteger. The image's DPI will
    be overridden with the values in page_dpi.

    Args:
        input_file: The PDF to rasterize.
        output_file: The desired name of the rasterized image.
        raster_device: Type of image to produce at output_file
        raster_dpi: Resolution at which to rasterize page
        pageno: Page number to rasterize (beginning at page 1)
        page_dpi: Resolution, overriding output image DPI
        rotation: Cardinal angle, clockwise, to rotate page
        filter_vector: If True, remove vector graphics objects
    Returns:
        Path: output_file if successful
    Note:
        This hook will be called from child processes. Modifying global state
        will not affect the main process or other child processes.
    Note:
        This is a :ref:`firstresult hook<firstresult>`.
    """


@hookspec(firstresult=True)
def filter_ocr_image(page: 'PageContext', image: 'Image') -> 'Image':
    """Called to filter the image before it is sent to OCR.

    This is the image that OCR sees, not what the user sees when they view the
    PDF. If ``redo_ocr`` is enabled, portions of the image will be masked so
    they are not shown to OCR. The main use of this hook is expected to be hiding
    content from OCR.

    The input image may be color, grayscale, or monochrome, and the
    output image may differ. The pixel width and height of the
    output image must be identical to the input image, or misalignment between
    the OCR text layer and visual position of the text will occur. Likewise,
    the output must be a faithful representation of the input, or alignment
    errors may occurs.

    Tesseract OCR only deals with monochrome images, and internally converts
    non-monochrome images to OCR.

    Note:
        This hook will be called from child processes. Modifying global state
        will not affect the main process or other child processes.
    Note:
        This is a :ref:`firstresult hook<firstresult>`.
    """


@hookspec(firstresult=True)
def filter_page_image(page: 'PageContext', image_filename: Path) -> Path:
    """Called to filter the whole page before it is inserted into the PDF.

    A whole page image is only produced when preprocessing command line arguments
    are issued or when ``--force-ocr`` is issued. If no whole page is image is
    produced for a given page, this function will not be called. This is not
    the image that will be shown to OCR.

    If the function does not want to modify the image, it should return
    ``image_filename``. The hook may overwrite ``image_filename`` with a new file.

    The output image should preserve the same physical unit dimensions, that is
    (width * dpi_x, height * dpi_y). That is, if the image is resized, the DPI
    must be adjusted by the reciprocal. If this is not preserved, the PDF page
    will be resized and the OCR layer misaligned. OCRmyPDF does not nothing
    to enforce these constraints; it is up to the plugin to do sensible things.

    OCRmyPDF will create the PDF page based on the image format used (unless the
    hook is overriden). If you convert the image to a JPEG, the output page will
    be created as a JPEG, etc. If you change the colorspace, that change will be
    kept. Note that the OCRmyPDF image optimization stage, if enabled, may
    ultimately chose a different format.

    If the return value is a file that does not exist, ``FileNotFoundError``
    will occur. The return value should be a path to a file in the same folder
    as ``image_filename``.

    Implementation detail: If the value returned is falsy, OCRmyPDF will ignore
    the return value and assume the input file was unmodified. This is deprecated.
    To leave the image unmodified, ``image_filename`` should be returned.

    Note:
        This hook will be called from child processes. Modifying global state
        will not affect the main process or other child processes.
    Note:
        This is a :ref:`firstresult hook<firstresult>`.
    """


@hookspec(firstresult=True)
def filter_pdf_page(
    page: 'PageContext', image_filename: Path, output_pdf: Path
) -> Path:
    """Called to convert a filtered whole page image into a PDF.

    A whole page image is only produced when preprocessing command line arguments
    are issued or when ``--force-ocr`` is issued. If no whole page is image is
    produced for a given page, this function will not be called. This is not
    the image that will be shown to OCR. The whole page image is filtered in
    the hook above, ``filter_page_image``, then this function is called for
    PDF conversion.

    This function will only be called when OCRmyPDF runs in a mode such as
    "force OCR" mode where rasterizing of all content is performed.

    Clever things could be done at this stage such as segmenting the page image into
    color regions or vector equivalents.

    The provider of the hook implementation is responsible for ensuring that the
    OCR text layer is aligned with the PDF produced here, or text misalignment
    will result.

    Currently this function must produce a single page PDF or the pipeline will
    fail.  If the intent is to remove the PDF, then create a single page empty
    PDF.

    Args:
        page: Context for this page.
        image_filename: Filename of the input image used to create output_pdf,
            for "reference" if recreating the output_pdf entirely.
        output_pdf: The previous created output_pdf.

    Returns:
        output_pdf

    Note:
        This hook will be called from child processes. Modifying global state
        will not affect the main process or other child processes.
    Note:
        This is a :ref:`firstresult hook<firstresult>`.
    """


OrientationConfidence = namedtuple('OrientationConfidence', ('angle', 'confidence'))
"""Expresses an OCR engine's confidence in page rotation.

Attributes:
    angle (int): The clockwise angle (0, 90, 180, 270) that the page should be
        rotated. 0 means no rotation.
    confidence (float): How confident the OCR engine is that this the correct
        rotation. 0 is not confident, 15 is very confident. Arbitrary units.
"""


class OcrEngine(ABC):
    """A class representing an OCR engine with capabilities similar to Tesseract OCR.

    This could be used to create a plugin for another OCR engine instead of
    Tesseract OCR.
    """

    @abstractstaticmethod
    def version() -> str:
        """Returns the version of the OCR engine."""

    @abstractstaticmethod
    def creator_tag(options: Namespace) -> str:
        """Returns the creator tag to identify this software's role in creating the PDF.

        This tag will be inserted in the XMP metadata and DocumentInfo dictionary
        as appropriate. Ideally you should include the name of the OCR engine and its
        version. The text should not contain line breaks. This is to help developers
        like yourself identify the software that produced this file.

        OCRmyPDF will always prepend its name to this value.
        """

    @abstractmethod
    def __str__(self):
        """Returns name of OCR engine and version.

        This is used when OCRmyPDF wants to mention the name of the OCR engine
        to the user, usually in an error message.
        """

    @abstractstaticmethod
    def languages(options: Namespace) -> AbstractSet[str]:
        """Returns the set of all languages that are supported by the engine.

        Languages are typically given in 3-letter ISO 3166-1 codes, but actually
        can be any value understood by the OCR engine."""

    @abstractstaticmethod
    def get_orientation(input_file: Path, options: Namespace) -> OrientationConfidence:
        """Returns the orientation of the image."""

    @abstractstaticmethod
    def generate_hocr(
        input_file: Path, output_hocr: Path, output_text: Path, options: Namespace
    ) -> None:
        """Called to produce a hOCR file and sidecar text file."""

    @abstractstaticmethod
    def generate_pdf(
        input_file: Path, output_pdf: Path, output_text: Path, options: Namespace
    ) -> None:
        """Called to produce a text only PDF.

        Args:
            input_file: A page image on which to perform OCR.
            output_pdf: The expected name of the output PDF, which must be
                a single page PDF with no visible content of any kind, sized
                to the dimensions implied by the input_file's width, height
                and DPI. The image will be grafted onto the input PDF page.
        """


@hookspec(firstresult=True)
def get_ocr_engine() -> OcrEngine:
    """Returns an OcrEngine to use for processing this file.

    The OcrEngine may be instantiated multiple times, by both the main process
    and child process. As such, it must be obtain store any state in ``options``
    or some common location.

    Note:
        This is a :ref:`firstresult hook<firstresult>`.
    """


@hookspec(firstresult=True)
def generate_pdfa(
    pdf_pages: List[Path],
    pdfmark: Path,
    output_file: Path,
    compression: str,
    pdf_version: str,
    pdfa_part: str,
    progressbar_class,
) -> Path:
    """Generate a PDF/A.

    This API strongly assumes a PDF/A generator with Ghostscript's semantics.

    OCRmyPDF will modify the metadata and possibly linearize the PDF/A after it
    is generated.

    Arguments:
        pdf_pages: A list of one or more filenames, will be merged into output_file.
        pdfmark: A PostScript file intended for Ghostscript with details on
            how to perform the PDF/A conversion.
        output_file: The name of the desired output file.
        compression: One of ``'jpeg'``, ``'lossless'``, ``''``. For ``'jpeg'``,
            the PDF/A generator should convert all images to JPEG encoding where
            possible. For lossless, all images should be converted to FlateEncode
            (lossless PNG). If an empty string, the PDF generator should make its
            own decisions about how to encode images.
        pdf_version: The minimum PDF version that the output file should be.
            At its own discretion, the PDF/A generator may raise the version,
            but should not lower it.
        pdfa_part: The desired PDF/A compliance level, such as ``'2B'``.
        progressbar_class: The class of a progress bar with a tqdm-like API. An
            instance of this class will be initialized when PDF/A conversion
            begins, using
            ``instance = progressbar_class(total: int, desc: str, unit:str)``,
            defining the number of work units, a user-visible description,
            and the name of the work units ("page"). Then ``instance.update()``
            will be called when a work unit is completed. If ``None``, no
            progress information is reported.

    Returns:
        Path: If successful, the hook should return ``output_file``.

    Note:
        This is a :ref:`firstresult hook<firstresult>`.

    See also:
        https://github.com/tqdm/tqdm
    """
