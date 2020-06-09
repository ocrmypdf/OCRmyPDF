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
from typing import AbstractSet, List, Optional

import pluggy
from PIL import Image

from ocrmypdf.helpers import Resolution

hookspec = pluggy.HookspecMarker('ocrmypdf')

# pylint: disable=unused-argument


@hookspec
def add_options(parser: ArgumentParser) -> None:
    """Allows the plugin to add its own command line arguments.

    Even if you do not intend to use plugins in a command line context, you
    should use this function to create your options.
    """


@hookspec
def check_options(options: Namespace) -> None:
    """Called to ask the plugin to check all of its options.

	The plugin may modify the *options*. All objects that are in options must
	be picklable so they can be marshalled to child worker processes.
	"""


@hookspec
def validate(pdfinfo: 'PdfInfo', options: Namespace) -> None:
    """Called to give a plugin an opportunity to review *options* and *pdfinfo*.

    *options* contains the "work order" to process a particular file. *pdfinfo*
    contains information about the input file obtained after loading and
    parsing. The plugin may modify the *options*. For example, you could decide
    that a certain type of file should be treated with ``options.force_ocr = True``
    based on information in its *pdfinfo*.

    The plugin may raise :class:`ocrmypdf.exceptions.InputFileError` or any
    :class:`ocrmypdf.exceptions.ExitCodeException` to request
    normal termination. ocrmypdf will hold the plugin responsible for raising
    exceptions of any other type.

    The return value is ignored. To abort processing, raise an ``ExitCodeException``.
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
        raster_device: type of image to produce at output_file
        raster_dpi: resolution at which to rasterize page
        pageno: page number to rasterize (beginning at page 1)
        page_dpi: resolution, overriding output image DPI
        rotation: cardinal angle, clockwise, to rotate page
        filter_vector: if True, remove vector graphics objects
    Returns:
        output_file
    """


@hookspec(firstresult=True)
def filter_ocr_image(page: 'PageContext', image: Image) -> Image:
    """Called to filter the image before it is sent to OCR.

    This is the image that OCR sees, not what the user sees when they view the
    PDF.
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
        """Returns set of languages that are supported."""

    @abstractstaticmethod
    def get_orientation(input_file: Path, options: Namespace) -> OrientationConfidence:
        """Returns the orientation of the image."""

    @abstractstaticmethod
    def generate_hocr(
        input_file: Path, output_hocr: Path, output_text: Path, options: Namespace
    ) -> None:
        """Called to produce a hOCR file."""

    @abstractstaticmethod
    def generate_pdf(
        input_file: Path, output_pdf: Path, output_text: Path, options: Namespace
    ) -> None:
        """Called to produce a text only PDF (no image, invisible text)."""


@hookspec(firstresult=True)
def get_ocr_engine() -> OcrEngine:
    pass


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

    The pdf_pages, a list of files, will be merged into output_file. One or more
    PDF files may be merged. The pdfmark file is a PostScript.ps file that
    provides Ghostscript with details on how to perform the PDF/A
    conversion. By default with we pick PDF/A-2b, but this works for 1 or 3.

    compression can be 'jpeg', 'lossless', or an empty string. In 'jpeg',
    Ghostscript is instructed to convert color and grayscale images to DCT
    (JPEG encoding). In 'lossless' Ghostscript is told to convert images to
    Flate (lossless/PNG). If the parameter is omitted Ghostscript is left to
    make its own decisions about how to encode images; it appears to use a
    heuristic to decide how to encode images. As of Ghostscript 9.25, we
    support passthrough JPEG which allows Ghostscript to avoid transcoding
    images entirely. (The feature was added in 9.23 but broken, and the 9.24
    release of Ghostscript had regressions, so we don't support it until 9.25.)

    Returns:
        output_file
    """
