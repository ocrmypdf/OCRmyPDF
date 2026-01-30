#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Extract information about the content of a PDF."""

from __future__ import annotations

import logging
import statistics
from collections.abc import Callable, Container, Iterable, Iterator
from contextlib import nullcontext
from decimal import Decimal
from os import PathLike
from pathlib import Path
from typing import NamedTuple

from pdfminer.layout import LTPage, LTTextBox
from pikepdf import Name, Page, Pdf

from ocrmypdf._concurrent import Executor, SerialExecutor
from ocrmypdf.exceptions import EncryptedPdfError
from ocrmypdf.helpers import Resolution
from ocrmypdf.pdfinfo._contentstream import TextboxInfo, TextMarker, VectorMarker
from ocrmypdf.pdfinfo._image import ImageInfo, _process_content_streams
from ocrmypdf.pdfinfo._types import FloatRect
from ocrmypdf.pdfinfo._worker import _pdf_pageinfo_concurrent
from ocrmypdf.pdfinfo.layout import (
    LTStateAwareChar,
    PdfMinerState,
    get_text_boxes,
)

logger = logging.getLogger()


def _page_has_text(text_blocks: Iterable[FloatRect], page_width, page_height) -> bool:
    """Smarter text detection that ignores text in margins."""
    pw, ph = float(page_width), float(page_height)  # pylint: disable=invalid-name

    margin_ratio = 0.125
    interior_bbox = (
        margin_ratio * pw,  # left
        (1 - margin_ratio) * ph,  # top
        (1 - margin_ratio) * pw,  # right
        margin_ratio * ph,  # bottom  (first quadrant: bottom < top)
    )

    def rects_intersect(a: FloatRect, b: FloatRect) -> bool:
        """Check if two 4-tuple rects intersect.

        Where (a,b) are 4-tuple rects (left-0, top-1, right-2, bottom-3)
        https://stackoverflow.com/questions/306316/determine-if-two-rectangles-overlap-each-other
        Formula assumes all boxes are in first quadrant.
        """
        return a[0] < b[2] and a[2] > b[0] and a[1] > b[3] and a[3] < b[1]

    has_text = False
    for bbox in text_blocks:
        if rects_intersect(bbox, interior_bbox):
            has_text = True
            break
    return has_text


def simplify_textboxes(
    miner_page: LTPage, textbox_getter: Callable[[LTPage], Iterator[LTTextBox]]
) -> Iterator[TextboxInfo]:
    """Extract only limited content from text boxes.

    We do this to save memory and ensure that our objects are pickleable.
    """
    for box in textbox_getter(miner_page):
        first_line = box._objs[0]  # pylint: disable=protected-access
        first_char = first_line._objs[0]  # pylint: disable=protected-access
        if not isinstance(first_char, LTStateAwareChar):
            continue
        visible = first_char.rendermode != 3
        corrupt = first_char.get_text() == '\ufffd'
        yield TextboxInfo(box.bbox, visible, corrupt)


class PageResolutionProfile(NamedTuple):
    """Information about the resolutions of a page."""

    weighted_dpi: float
    """The weighted average DPI of the page, weighted by the area of each image."""

    max_dpi: float
    """The maximum DPI of an image on the page."""

    average_to_max_dpi_ratio: float
    """The average DPI of the page divided by the maximum DPI of the page.

    This indicates the intensity of the resolution variation on the page.

    If the average is 1.0 or close to 1.0, has all of its content at a uniform
    resolution. If the average is much lower than 1.0, some content is at a
    higher resolution than the rest of the page.
    """

    area_ratio: float
    """The maximum-DPI area of the page divided by the total drawn area.

    This indicates the prevalence of high-resolution content on the page.
    """


class PageInfo:
    """Information about type of contents on each page in a PDF."""

    _has_text: bool | None
    _has_vector: bool | None
    _images: list[ImageInfo] = []

    def __init__(
        self,
        pdf: Pdf,
        pageno: int,
        infile: PathLike,
        check_pages: Container[int],
        detailed_analysis: bool = False,
        miner_state: PdfMinerState | None = None,
    ):
        """Initialize a PageInfo object."""
        self._pageno = pageno
        self._infile = infile
        self._detailed_analysis = detailed_analysis
        self._gather_pageinfo(
            pdf, pageno, infile, check_pages, detailed_analysis, miner_state
        )

    def _gather_pageinfo(
        self,
        pdf: Pdf,
        pageno: int,
        infile: PathLike,
        check_pages: Container[int],
        detailed_analysis: bool,
        miner_state: PdfMinerState | None,
    ):
        page: Page = pdf.pages[pageno]
        mediabox = [Decimal(d) for d in page.mediabox.as_list()]
        width_pt = mediabox[2] - mediabox[0]
        height_pt = mediabox[3] - mediabox[1]

        self._artbox = [float(d) for d in page.artbox.as_list()]
        self._bleedbox = [float(d) for d in page.bleedbox.as_list()]
        self._cropbox = [float(d) for d in page.cropbox.as_list()]
        self._mediabox = [float(d) for d in page.mediabox.as_list()]
        self._trimbox = [float(d) for d in page.trimbox.as_list()]

        check_this_page = pageno in check_pages

        if check_this_page and detailed_analysis:
            page_analysis = miner_state.get_page_analysis(pageno)
            if page_analysis is not None:
                self._textboxes = list(
                    simplify_textboxes(page_analysis, get_text_boxes)
                )
            else:
                self._textboxes = []
            bboxes = (box.bbox for box in self._textboxes)

            self._has_text = _page_has_text(bboxes, width_pt, height_pt)
        else:
            self._textboxes = []
            self._has_text = None  # i.e. "no information"

        userunit = page.get(Name.UserUnit, Decimal(1.0))
        if not isinstance(userunit, Decimal):
            userunit = Decimal(userunit)
        self._userunit = userunit
        self._width_inches = width_pt * userunit / Decimal(72.0)
        self._height_inches = height_pt * userunit / Decimal(72.0)
        self._rotate = int(getattr(page.obj, 'Rotate', 0))

        userunit_shorthand = (userunit, 0, 0, userunit, 0, 0)

        if check_this_page:
            self._has_vector = False
            self._has_text = False
            self._images = []
            for info in _process_content_streams(
                pdf=pdf, container=page, shorthand=userunit_shorthand
            ):
                if isinstance(info, VectorMarker):
                    self._has_vector = True
                elif isinstance(info, TextMarker):
                    self._has_text = True
                elif isinstance(info, ImageInfo):
                    self._images.append(info)
                else:
                    raise NotImplementedError()
        else:
            self._has_vector = None  # i.e. "no information"
            self._has_text = None
            self._images = []

        self._dpi = None
        if self._images:
            dpi = Resolution(0.0, 0.0).take_max(
                image.dpi for image in self._images if image.renderable
            )
            self._dpi = dpi
            self._width_pixels = int(round(dpi.x * float(self._width_inches)))
            self._height_pixels = int(round(dpi.y * float(self._height_inches)))

    @property
    def pageno(self) -> int:
        """Return page number (0-based)."""
        return self._pageno

    @property
    def has_text(self) -> bool:
        """Return True if page has text, False if not or unknown."""
        return bool(self._has_text)

    @property
    def has_corrupt_text(self) -> bool:
        """Return True if page has corrupt text, False if not or unknown."""
        if not self._detailed_analysis:
            raise NotImplementedError('Did not do detailed analysis')
        return any(tbox.is_corrupt for tbox in self._textboxes)

    @property
    def has_vector(self) -> bool:
        """Return True if page has vector graphics, False if not or unknown.

        Vector graphics are sometimes used to draw fonts, so it may not be
        obvious on visual inspection whether a page has text or not.
        """
        return bool(self._has_vector)

    @property
    def width_inches(self) -> Decimal:
        """Return width of page in inches."""
        return self._width_inches

    @property
    def height_inches(self) -> Decimal:
        """Return height of page in inches."""
        return self._height_inches

    @property
    def width_pixels(self) -> int:
        """Return width of page in pixels."""
        return int(round(float(self.width_inches) * self.dpi.x))

    @property
    def height_pixels(self) -> int:
        """Return height of page in pixels."""
        return int(round(float(self.height_inches) * self.dpi.y))

    @property
    def rotation(self) -> int:
        """Return rotation of page in degrees.

        Will only be a multiple of 90.
        """
        return self._rotate

    @rotation.setter
    def rotation(self, value):
        if value in (0, 90, 180, 270, 360, -90, -180, -270):
            self._rotate = value
        else:
            raise ValueError("rotation must be a cardinal angle")

    @property
    def cropbox(self) -> FloatRect:
        """Return cropbox of page in PDF coordinates."""
        return self._cropbox

    @property
    def mediabox(self) -> FloatRect:
        """Return mediabox of page in PDF coordinates."""
        return self._mediabox

    @property
    def trimbox(self) -> FloatRect:
        """Return trimbox of page in PDF coordinates."""
        return self._trimbox

    @property
    def artbox(self) -> FloatRect:
        """Return artbox of page in PDF coordinates."""
        return self._artbox

    @property
    def bleedbox(self) -> FloatRect:
        """Return bleedbox of page in PDF coordinates."""
        return self._bleedbox

    @property
    def images(self) -> list[ImageInfo]:
        """Return images."""
        return self._images

    def get_textareas(self, visible: bool | None = None, corrupt: bool | None = None):
        """Return textareas bounding boxes in PDF coordinates on the page."""

        def predicate(
            obj: TextboxInfo, want_visible: bool | None, want_corrupt: bool | None
        ) -> bool:
            result = True
            if want_visible is not None and obj.is_visible != want_visible:
                result = False
            if want_corrupt is not None and obj.is_corrupt != want_corrupt:
                result = False
            return result

        if not self._textboxes:
            if visible is not None and corrupt is not None:
                raise NotImplementedError('Incomplete information on textboxes')
            return self._textboxes

        return (obj.bbox for obj in self._textboxes if predicate(obj, visible, corrupt))

    @property
    def dpi(self) -> Resolution:
        """Return DPI needed to render all images on the page."""
        if self._dpi is None:
            return Resolution(0.0, 0.0)
        return self._dpi

    @property
    def userunit(self) -> Decimal:
        """Return user unit of page."""
        return self._userunit

    @property
    def min_version(self) -> str:
        """Return minimum PDF version needed to render this page."""
        if self.userunit is not None:
            return '1.6'
        else:
            return '1.5'

    def page_dpi_profile(self) -> PageResolutionProfile | None:
        """Return information about the DPIs of the page.

        This is useful to detect pages with a small proportion of high-resolution
        content that is forcing us to use a high DPI for the whole page. The ratio
        is weighted by the area of each image. If images overlap, the overlapped
        area counts.

        Vector graphics and text are ignored.

        Returns None if there is no meaningful DPI for the page.
        """
        image_dpis = []
        image_areas = []
        for image in self._images:
            if not image.renderable:
                continue
            image_dpis.append(image.dpi.to_scalar())
            image_areas.append(image.printed_area)

        total_drawn_area = sum(image_areas)
        if total_drawn_area == 0:
            return None

        weights = [area / total_drawn_area for area in image_areas]
        # Calculate harmonic mean of DPIs weighted by area
        weighted_dpi = statistics.harmonic_mean(image_dpis, weights)
        max_dpi = max(image_dpis)
        dpi_average_max_ratio = weighted_dpi / max_dpi

        arg_max_dpi = image_dpis.index(max_dpi)
        max_area_ratio = image_areas[arg_max_dpi] / total_drawn_area
        return PageResolutionProfile(
            weighted_dpi,
            max_dpi,
            dpi_average_max_ratio,
            max_area_ratio,
        )

    def __repr__(self):
        """Return string representation."""
        return (
            f'<PageInfo '
            f'pageno={self.pageno} {self.width_inches}"x{self.height_inches}" '
            f'rotation={self.rotation} dpi={self.dpi} has_text={self.has_text}>'
        )


DEFAULT_EXECUTOR = SerialExecutor()


class PdfInfo:
    """Extract summary information about a PDF without retaining the PDF itself.

    Crucially this lets us get the information in a pure Python format so that
    it can be pickled and passed to a worker process.
    """

    _has_acroform: bool = False
    _has_signature: bool = False
    _needs_rendering: bool = False

    def __init__(
        self,
        infile: Path,
        *,
        detailed_analysis: bool = False,
        progbar: bool = False,
        max_workers: int | None = None,
        use_threads: bool = True,
        check_pages=None,
        executor: Executor = DEFAULT_EXECUTOR,
    ):
        """Initialize."""
        self._infile = infile
        if check_pages is None:
            check_pages = range(0, 1_000_000_000)

        with Pdf.open(infile) as pdf:
            if pdf.is_encrypted:
                raise EncryptedPdfError()  # Triggered by encryption with empty passwd
            pscript5_mode = str(pdf.docinfo.get(Name.Creator, "")).startswith(
                'PScript5'
            )
            self._miner_state = (
                PdfMinerState(infile, pscript5_mode)
                if detailed_analysis
                else nullcontext()
            )
            with self._miner_state as miner_state:
                self._pages = _pdf_pageinfo_concurrent(
                    pdf,
                    executor,
                    max_workers,
                    use_threads,
                    infile,
                    progbar,
                    check_pages=check_pages,
                    detailed_analysis=detailed_analysis,
                    miner_state=miner_state,
                )
            self._needs_rendering = pdf.Root.get(Name.NeedsRendering, False)
            if Name.AcroForm in pdf.Root:
                if (
                    len(pdf.Root.AcroForm.get(Name.Fields, [])) > 0
                    or Name.XFA in pdf.Root.AcroForm
                ):
                    self._has_acroform = True
                self._has_signature = bool(pdf.Root.AcroForm.get(Name.SigFlags, 0) & 1)
            self._is_tagged = bool(
                pdf.Root.get(Name.MarkInfo, {}).get(Name.Marked, False)
            )

    @property
    def pages(self) -> list[PageInfo | None]:
        """Return list of PageInfo objects, one per page in the PDF."""
        return self._pages

    @property
    def min_version(self) -> str:
        """Return minimum PDF version needed to render this PDF."""
        # The minimum PDF is the maximum version that any particular page needs
        return max(page.min_version for page in self.pages if page)

    @property
    def has_userunit(self) -> bool:
        """Return True if any page has a user unit."""
        return any(page.userunit != 1.0 for page in self.pages if page)

    @property
    def has_acroform(self) -> bool:
        """Return True if the document catalog has an AcroForm."""
        return self._has_acroform

    @property
    def has_signature(self) -> bool:
        """Return True if the document annotations has a digital signature."""
        return self._has_signature

    @property
    def is_tagged(self) -> bool:
        """Return True if the document catalog indicates this is a Tagged PDF."""
        return self._is_tagged

    @property
    def filename(self) -> str | Path:
        """Return filename of PDF."""
        if not isinstance(self._infile, str | Path):
            raise NotImplementedError("can't get filename from stream")
        return self._infile

    @property
    def needs_rendering(self) -> bool:
        """Return True if PDF contains XFA forms.

        XFA forms are not supported by most standard PDF renderers, so we
        need to detect and suppress them.
        """
        return self._needs_rendering

    def __getitem__(self, item) -> PageInfo:
        """Return PageInfo object for page number `item`."""
        return self._pages[item]

    def __len__(self):
        """Return number of pages in PDF."""
        return len(self._pages)

    def __repr__(self):
        """Return string representation."""
        return f"<PdfInfo('...'), page count={len(self)}>"


def main():  # pragma: no cover
    """Run as a script."""
    import argparse  # pylint: disable=import-outside-toplevel
    from pprint import pprint  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    args = parser.parse_args()
    pdfinfo = PdfInfo(args.infile)

    pprint(pdfinfo)
    for page in pdfinfo.pages:
        pprint(page)
        for im in page.images:
            pprint(im)


if __name__ == '__main__':
    main()
