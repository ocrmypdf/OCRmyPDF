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

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

import pluggy
from PIL import Image

hookspec = pluggy.HookspecMarker('ocrmypdf')

# pylint: disable=unused-argument


@hookspec
def add_options(parser: ArgumentParser) -> None:
    """Allows the plugin to add its own command line arguments.

    Even if you do not intend to use plugins in a command line context, you
    should use this function to create your options.
    """


@hookspec
def prepare(options: Namespace) -> None:
    """Called to notify a plugin that a file will be processed.

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
