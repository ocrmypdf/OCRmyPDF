# © 2020 James R. Barlow: github.com/jbarlow83
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

from abc import ABC, abstractmethod, abstractstaticmethod
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from pathlib import Path
from typing import TYPE_CHECKING, AbstractSet, List, Optional

import pluggy
from PIL import Image

from ocrmypdf.helpers import Resolution

if TYPE_CHECKING:
    from ocrmypdf._jobcontext import PageContext
    from ocrmypdf.pdfinfo import PdfInfo

hookspec = pluggy.HookspecMarker('ocrmypdf')

# pylint: disable=unused-argument


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
    page_dpi: Optional[Resolution] = None,
    rotation: Optional[int] = None,
    filter_vector: bool = False,
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
        output_file
    Note:
        This hook will be called from child processes. Modifying global state
        will not affect the main process or other child processes.
    """


@hookspec(firstresult=True)
def filter_ocr_image(page: 'PageContext', image: Image) -> Image:
    """Called to filter the image before it is sent to OCR.

    This is the image that OCR sees, not what the user sees when they view the
    PDF.

    Note:
        This hook will be called from child processes. Modifying global state
        will not affect the main process or other child processes.
    """


@hookspec(firstresult=True)
def filter_page_image(page: 'PageContext', image_filename: Path) -> Path:
    """Called to filter the whole page before it is inserted into the PDF.

    A whole page image is only produced when preprocessing command line arguments
    are issued or when ``--force-ocr`` is issued. If no whole page is image is
    produced for a given page, this function will not be called. This is not
    the image that will be shown to OCR.

    ocrmypdf will create the PDF page based on the image format used. If you
    convert the image to a JPEG, the output page will be created as a JPEG, etc.
    Note that the ocrmypdf image optimization stage may ultimately chose a
    different format.

    Note:
        This hook will be called from child processes. Modifying global state
        will not affect the main process or other child processes.
    """


OrientationConfidence = namedtuple('OrientationConfidence', ('angle', 'confidence'))


class OcrEngine(ABC):
    @abstractstaticmethod
    def version() -> str:
        """Returns the version of the OCR engine."""

    @abstractstaticmethod
    def creator_tag(options: Namespace) -> str:
        """Returns the creator tag to identify this software's role in creating the PDF."""

    @abstractmethod
    def __str__(self):
        """Returns name of OCR engine and version."""

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
    """


@hookspec(firstresult=True)
def generate_pdfa(
    pdf_pages: List[Path],
    pdfmark: Path,
    output_file: Path,
    compression: str,
    pdf_version: str,
    pdfa_part: str,
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

    Returns:
        output_file: If successful, the hook should return ``output_file``.
    """
