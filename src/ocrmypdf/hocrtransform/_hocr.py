# SPDX-FileCopyrightText: 2010 Jonathan Brinley
# SPDX-FileCopyrightText: 2013-2014 Julien Pfefferkorn
# SPDX-FileCopyrightText: 2023-2025 James R. Barlow
# SPDX-FileCopyrightText: 2025 Odin Dahlstr\u00f6m
# SPDX-License-Identifier: MIT

"""hOCR transform implementation.

This module provides backward-compatible HocrTransform class that wraps the
new separated HocrParser and PdfTextRenderer components.
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

from pikepdf import Name

from ocrmypdf.hocrtransform._font import EncodableFont as Font
from ocrmypdf.hocrtransform._font import GlyphlessFont
from ocrmypdf.hocrtransform.hocr_parser import HocrParseError, HocrParser
from ocrmypdf.hocrtransform.pdf_renderer import (
    DebugRenderOptions,
    PdfTextRenderer,
)

log = logging.getLogger(__name__)


class HocrTransformError(Exception):
    """Error while applying hOCR transform."""


class HocrTransform:
    """A class for converting documents from the hOCR format.

    For details of the hOCR format, see:
    http://kba.github.io/hocr-spec/1.2/.

    This class provides backward compatibility with existing code. Internally,
    it uses the new HocrParser and PdfTextRenderer components.
    """

    def __init__(
        self,
        *,
        hocr_filename: str | Path,
        dpi: float,
        debug: bool = False,
        fontname: Name = Name("/f-0-0"),
        font: Font = GlyphlessFont(),
        debug_render_options: DebugRenderOptions | None = None,
    ):
        """Initialize the HocrTransform object.

        Args:
            hocr_filename: Path to the hOCR file
            dpi: Resolution of the source image in dots per inch
            debug: Deprecated; use debug_render_options instead
            fontname: PDF font name to use
            font: Font implementation for encoding and metrics
            debug_render_options: Options for debug visualization
        """
        if debug:
            warnings.warn(
                "Use debug_render_options instead of debug parameter",
                DeprecationWarning,
                stacklevel=2,
            )
            self.render_options = DebugRenderOptions(
                render_baseline=debug,
                render_triangle=debug,
                render_line_bbox=False,
                render_word_bbox=debug,
                render_paragraph_bbox=False,
                render_space_bbox=False,
            )
        else:
            self.render_options = debug_render_options or DebugRenderOptions()

        self.dpi = dpi
        self._fontname = fontname
        self._font = font
        self._hocr_filename = Path(hocr_filename)

        # Parse the hOCR file
        try:
            parser = HocrParser(hocr_filename)
            self._page = parser.parse()
        except HocrParseError as e:
            raise HocrTransformError(str(e)) from e

        if self._page.bbox is None:
            raise HocrTransformError("hocr file is missing page dimensions")

        # Calculate page size in PDF points
        INCH = 72.0
        self.width = self._page.bbox.width / (self.dpi / INCH)
        self.height = self._page.bbox.height / (self.dpi / INCH)

    def to_pdf(
        self,
        *,
        out_filename: Path,
        image_filename: Path | None = None,
        invisible_text: bool = True,
    ) -> None:
        """Creates a PDF file with an image superimposed on top of the text.

        Text is positioned according to the bounding box of the lines in
        the hOCR file.
        The image need not be identical to the image used to create the hOCR
        file.
        It can have a lower resolution, different color mode, etc.

        Args:
            out_filename: Path of PDF to write.
            image_filename: Image to use for this file. If omitted, the OCR text
                is shown.
            invisible_text: If True, text is rendered invisible so that is
                selectable but never drawn. If False, text is visible and may
                be seen if the image is skipped or deleted in Acrobat.
        """
        renderer = PdfTextRenderer(
            page=self._page,
            dpi=self.dpi,
            fontname=self._fontname,
            font=self._font,
            debug_render_options=self.render_options,
        )

        renderer.render(
            out_filename=out_filename,
            image_filename=image_filename,
            invisible_text=invisible_text,
        )

    @property
    def page(self):
        """Get the parsed OcrElement page.

        Returns:
            The root OcrElement representing the parsed page
        """
        return self._page
