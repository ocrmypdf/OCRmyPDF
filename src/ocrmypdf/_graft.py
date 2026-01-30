# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""For grafting text-only PDF pages onto freeform PDF pages."""

from __future__ import annotations

import logging
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocrmypdf.hocrtransform import OcrElement

from pikepdf import (
    Dictionary,
    Name,
    Operator,
    Page,
    Pdf,
    Stream,
    parse_content_stream,
    unparse_content_stream,
)

from ocrmypdf._jobcontext import PdfContext
from ocrmypdf._options import ProcessingMode
from ocrmypdf._pipeline import VECTOR_PAGE_DPI


class RenderMode(Enum):
    """Controls where the OCR text layer is placed relative to page content.

    ON_TOP: Text layer renders above page content (reserved for future use).
    UNDERNEATH: Text layer renders below page content (current default behavior).
    """

    ON_TOP = 0
    UNDERNEATH = 1


@dataclass
class Fpdf2PageInfo:
    """Information needed to render and graft an fpdf2 page."""

    pageno: int
    hocr_path: Path
    dpi: float
    autorotate_correction: int
    emplaced_page: bool


@dataclass
class Fpdf2ParsedPage:
    """Parsed page data ready for fpdf2 rendering."""

    pageno: int
    ocr_tree: OcrElement
    dpi: float
    autorotate_correction: int
    emplaced_page: bool


# Alias for backward compatibility with plan documentation
Fpdf2DirectPage = Fpdf2ParsedPage


def _compute_text_misalignment(
    content_rotation: int, autorotate_correction: int, emplaced_page: bool
) -> int:
    """Compute rotation needed to align text layer with page content.

    Args:
        content_rotation: Original page /Rotate value (degrees).
        autorotate_correction: Rotation applied during rasterization (degrees).
        emplaced_page: Whether the page content was replaced with rasterized image.

    Returns:
        Rotation in degrees to apply to text layer to align with content.
    """
    if emplaced_page:
        # New image is upright after autorotation was applied
        content_rotation = autorotate_correction
    text_rotation = autorotate_correction
    return (text_rotation - content_rotation) % 360


def _compute_page_rotation(
    content_rotation: int, autorotate_correction: int, emplaced_page: bool
) -> int:
    """Compute final page /Rotate value after grafting.

    Args:
        content_rotation: Original page /Rotate value (degrees).
        autorotate_correction: Rotation applied during rasterization (degrees).
        emplaced_page: Whether the page content was replaced with rasterized image.

    Returns:
        Final /Rotate value for the page.
    """
    if emplaced_page:
        content_rotation = autorotate_correction
    return (content_rotation - autorotate_correction) % 360


def _build_text_layer_ctm(
    text_width: float,
    text_height: float,
    page_width: float,
    page_height: float,
    page_origin_x: float,
    page_origin_y: float,
    text_rotation: int,
):
    """Build transformation matrix to align text layer with page content.

    Args:
        text_width: Width of text layer mediabox.
        text_height: Height of text layer mediabox.
        page_width: Width of target page mediabox.
        page_height: Height of target page mediabox.
        page_origin_x: X origin of target page mediabox.
        page_origin_y: Y origin of target page mediabox.
        text_rotation: Rotation in degrees (clockwise) to apply to text layer.

    Returns:
        pikepdf.Matrix transformation matrix, or None if no rotation needed.
    """
    if text_rotation == 0:
        return None

    from pikepdf import Matrix

    wt, ht = text_width, text_height

    # Center text, rotate, scale to fit page, then position at page origin
    translate = Matrix().translated(-wt / 2, -ht / 2)
    untranslate = Matrix().translated(page_width / 2, page_height / 2)
    corner = Matrix().translated(page_origin_x, page_origin_y)

    # Negate rotation because input is clockwise angle
    rotate = Matrix().rotated(-text_rotation % 360)

    # Swap dimensions if 90 or 270 degree rotation
    if text_rotation in (90, 270):
        wt, ht = ht, wt

    # Scale to fit page dimensions
    scale_x = page_width / wt if wt else 1.0
    scale_y = page_height / ht if ht else 1.0
    scale = Matrix().scaled(scale_x, scale_y)

    return translate @ rotate @ scale @ untranslate @ corner


log = logging.getLogger(__name__)
MAX_REPLACE_PAGES = 100


def _ensure_dictionary(obj: Dictionary | Stream, name: Name):
    if name not in obj:
        obj[name] = Dictionary({})
    return obj[name]


def strip_invisible_text(pdf: Pdf, page: Page):
    stream = []
    in_text_obj = False
    render_mode = 0
    render_mode_stack = []
    text_objects = []

    for operands, operator in parse_content_stream(page, ''):
        if operator == Operator('Tr'):
            render_mode = operands[0]

        if operator == Operator('q'):
            render_mode_stack.append(render_mode)

        if operator == Operator('Q'):
            # IndexError is raised if stack is empty; try to carry on
            with suppress(IndexError):
                render_mode = render_mode_stack.pop()

        if not in_text_obj:
            if operator == Operator('BT'):
                in_text_obj = True
                text_objects.append((operands, operator))
            else:
                stream.append((operands, operator))
        else:
            text_objects.append((operands, operator))
            if operator == Operator('ET'):
                in_text_obj = False
                if render_mode != 3:
                    stream.extend(text_objects)
                text_objects.clear()

    content_stream = unparse_content_stream(stream)
    page.Contents = Stream(pdf, content_stream)


class OcrGrafter:
    """Manages grafting text-only PDFs onto regular PDFs."""

    def __init__(self, context: PdfContext):
        self.context = context
        self.path_base = context.origin

        self.pdf_base = Pdf.open(self.path_base)

        self.pdfinfo = context.pdfinfo
        self.output_file = context.get_path('graft_layers.pdf')

        self.emplacements = 1
        self.render_mode = RenderMode.UNDERNEATH

        # Check renderer type
        pdf_renderer = context.options.pdf_renderer
        self.use_sandwich_renderer = pdf_renderer == 'sandwich'

        # For fpdf2: accumulate pages before rendering
        self.fpdf2_hocr_pages: list[Fpdf2PageInfo] = []
        self.fpdf2_parsed_pages: list[Fpdf2ParsedPage] = []

    def graft_page(
        self,
        *,
        pageno: int,
        image: Path | None,
        ocr_output: Path | None,
        ocr_tree: OcrElement | None,
        autorotate_correction: int,
    ):
        """Graft OCR output onto a page of the base PDF.

        Args:
            pageno: Zero-based page number.
            image: Path to the visible page image PDF, or None if not replacing.
            ocr_output: Path to OCR output file. For fpdf2 renderer this is an
                hOCR file; for sandwich renderer this is a text-only PDF.
            ocr_tree: OCR tree for fpdf2 renderer.
            autorotate_correction: Orientation correction in degrees (0, 90, 180, 270).
        """
        if ocr_output and ocr_tree:
            raise ValueError(
                'Cannot specify both ocr_output and ocr_tree for fpdf2 renderer'
            )
        # Handle image emplacement first
        emplaced_page = False
        content_rotation = self.pdfinfo[pageno].rotation
        path_image = Path(image).resolve() if image else None
        if path_image is not None and path_image != self.path_base:
            # We are updating the old page with a rasterized PDF of the new
            # page (without changing objgen, to preserve references)
            log.debug("Emplacement update")
            with Pdf.open(path_image) as pdf_image:
                self.emplacements += 1
                foreign_image_page = pdf_image.pages[0]
                self.pdf_base.pages.append(foreign_image_page)
                local_image_page = self.pdf_base.pages[-1]
                self.pdf_base.pages[pageno].emplace(
                    local_image_page, retain=(Name.Parent,)
                )
                del self.pdf_base.pages[-1]
            emplaced_page = True

        if self.use_sandwich_renderer:
            # Sandwich renderer: graft pre-rendered PDF immediately
            if ocr_output:
                text_misaligned = _compute_text_misalignment(
                    content_rotation, autorotate_correction, emplaced_page
                )
                self._graft_sandwich_text_layer(
                    pageno=pageno,
                    textpdf=ocr_output,
                    text_rotation=text_misaligned,
                )
                page_rotation = _compute_page_rotation(
                    content_rotation, autorotate_correction, emplaced_page
                )
                self.pdf_base.pages[pageno].Rotate = page_rotation
        else:
            # fpdf2 renderer: accumulate page info for batch rendering.
            # The hOCR coordinates are in the corrected (upright) coordinate system.
            # We store autorotate_correction and emplaced_page to set the final
            # page /Rotate tag after grafting.
            if ocr_tree:
                self.fpdf2_parsed_pages.append(
                    Fpdf2ParsedPage(
                        ocr_tree=ocr_tree,
                        pageno=pageno,
                        autorotate_correction=autorotate_correction,
                        emplaced_page=emplaced_page,
                        dpi=self.pdfinfo[pageno].dpi.to_scalar(),
                    )
                )
            if ocr_output:
                self.fpdf2_hocr_pages.append(
                    Fpdf2PageInfo(
                        hocr_path=ocr_output,
                        pageno=pageno,
                        autorotate_correction=autorotate_correction,
                        emplaced_page=emplaced_page,
                        dpi=self.pdfinfo[pageno].dpi.to_scalar(),
                    )
                )

    def finalize(self):
        # Can have hocr OR parsed pages OR neither (no OCR), but not both
        assert not (
            self.fpdf2_hocr_pages and self.fpdf2_parsed_pages
        ), "Can't have both hocr and ocrtree pages"

        if self.fpdf2_hocr_pages:
            # Render all pages with fpdf2, then graft
            parsed_pages = self._parse_hocr_pages()
            self.fpdf2_parsed_pages = parsed_pages

        if self.fpdf2_parsed_pages:
            self._render_and_graft_fpdf2_pages()

        self.pdf_base.save(self.output_file)
        self.pdf_base.close()
        return self.output_file

    def _parse_hocr_pages(self):
        """Render all pages to multi-page PDF with shared fonts, then graft."""
        from ocrmypdf.hocrtransform.hocr_parser import HocrParser

        log.info(
            "Parsing %d pages with HocrParser",
            len(self.fpdf2_hocr_pages),
        )

        # Parse all hOCR files and collect OcrElements
        pages_data: list[Fpdf2ParsedPage] = []
        for page_info in self.fpdf2_hocr_pages:
            if page_info.hocr_path.stat().st_size == 0:
                continue  # Skip empty pages

            # Parse hOCR to OcrElement
            parser = HocrParser(page_info.hocr_path)
            ocr_tree = parser.parse()

            # Use DPI from hOCR (scan_res) which reflects actual rasterization DPI.
            # Fall back to pdfinfo DPI or VECTOR_PAGE_DPI for vector-only pages.
            effective_dpi = ocr_tree.dpi or page_info.dpi or float(VECTOR_PAGE_DPI)
            pages_data.append(
                Fpdf2ParsedPage(
                    pageno=page_info.pageno,
                    ocr_tree=ocr_tree,
                    dpi=effective_dpi,
                    autorotate_correction=page_info.autorotate_correction,
                    emplaced_page=page_info.emplaced_page,
                )
            )

        return pages_data

    def _render_and_graft_fpdf2_pages(self):
        font_dir = Path(__file__).parent / "data"

        # Render all pages to single PDF
        multi_page_pdf_path = self.context.get_path('fpdf2_multipage.pdf')

        from ocrmypdf.font import MultiFontManager
        from ocrmypdf.fpdf_renderer import Fpdf2MultiPageRenderer

        multi_font_manager = MultiFontManager(font_dir)
        # Build renderer input as (pageno, ocr_tree, dpi) tuples
        renderer_pages_data = [
            (parsed.pageno, parsed.ocr_tree, parsed.dpi)
            for parsed in self.fpdf2_parsed_pages
        ]
        renderer = Fpdf2MultiPageRenderer(
            pages_data=renderer_pages_data,
            multi_font_manager=multi_font_manager,
            invisible_text=True,
        )

        renderer.render(multi_page_pdf_path)

        # Now graft each page from the multi-page PDF
        with Pdf.open(multi_page_pdf_path) as pdf_text:
            for idx, parsed in enumerate(self.fpdf2_parsed_pages):
                # Copy page from multi-page PDF
                text_page = pdf_text.pages[idx]

                content_rotation = self.pdfinfo[parsed.pageno].rotation
                text_misaligned = _compute_text_misalignment(
                    content_rotation,
                    parsed.autorotate_correction,
                    parsed.emplaced_page,
                )
                self._graft_fpdf2_text_layer(parsed.pageno, text_page, text_misaligned)

                page_rotation = _compute_page_rotation(
                    content_rotation,
                    parsed.autorotate_correction,
                    parsed.emplaced_page,
                )
                self.pdf_base.pages[parsed.pageno].Rotate = page_rotation

        # Clean up multi-page PDF if not keeping temp files
        if not self.context.options.keep_temporary_files:
            with suppress(FileNotFoundError):
                multi_page_pdf_path.unlink()

    def _graft_fpdf2_text_layer(self, pageno: int, text_page: Page, text_rotation: int):
        """Graft a single text page onto the base PDF.

        Similar to existing _graft_text_layer but works with
        already-rendered pikepdf Page instead of file path.

        Args:
            pageno: Zero-based page number.
            text_page: The text-only PDF page to graft.
            text_rotation: Rotation to apply to align text with content (degrees).
        """
        from pikepdf import Array

        base_page = self.pdf_base.pages[pageno]

        # Extract content stream from text_page
        text_contents = text_page.Contents.read_bytes()

        # Get the mediabox from the text page
        mediabox = Array([float(x) for x in text_page.mediabox])  # type: ignore[misc]
        wt = float(mediabox[2]) - float(mediabox[0])
        ht = float(mediabox[3]) - float(mediabox[1])

        # Get base page mediabox
        base_mediabox = base_page.mediabox
        wp = float(base_mediabox[2]) - float(base_mediabox[0])
        hp = float(base_mediabox[3]) - float(base_mediabox[1])

        # Create Form XObject from text page content
        base_resources = _ensure_dictionary(base_page.obj, Name.Resources)
        base_xobjs = _ensure_dictionary(base_resources, Name.XObject)
        text_xobj_name = Name.random(prefix="OCR-")
        xobj = self.pdf_base.make_stream(text_contents)
        base_xobjs[text_xobj_name] = xobj
        xobj.Type = Name.XObject
        xobj.Subtype = Name.Form
        xobj.FormType = 1
        xobj.BBox = mediabox

        # Copy resources from text page's Resources to xobj
        # We need to handle this carefully since text_page is from a foreign PDF
        if hasattr(text_page, 'Resources') and text_page.Resources:
            # Create empty Resources dictionary for xobj
            xobj_resources = _ensure_dictionary(xobj, Name.Resources)

            # Copy fonts if they exist
            if Name.Font in text_page.Resources:
                xobj_fonts = _ensure_dictionary(xobj_resources, Name.Font)
                text_fonts = text_page.Resources[Name.Font]
                # Copy each font from the foreign PDF
                for font_name, font_obj in text_fonts.items():
                    xobj_fonts[font_name] = self.pdf_base.copy_foreign(font_obj)

            # Copy ExtGState (graphics state) if it exists - needed for transparency
            if Name.ExtGState in text_page.Resources:
                xobj_extstates = _ensure_dictionary(xobj_resources, Name.ExtGState)
                text_extstates = text_page.Resources[Name.ExtGState]
                # Copy each graphics state from the foreign PDF
                for gs_name, gs_obj in text_extstates.items():
                    xobj_extstates[gs_name] = self.pdf_base.copy_foreign(gs_obj)

        # Build transformation matrix for rotation and scaling
        ctm = _build_text_layer_ctm(
            wt,
            ht,
            wp,
            hp,
            float(base_mediabox[0]),
            float(base_mediabox[1]),
            text_rotation,
        )
        if ctm is not None:
            pdf_draw_xobj = (
                (b'q %s cm\n' % ctm.encode()) + (b'%s Do\n' % text_xobj_name) + b'Q\n'
            )
        else:
            pdf_draw_xobj = b'q\n' + (b'%s Do\n' % text_xobj_name) + b'\nQ\n'

        new_text_layer = Stream(self.pdf_base, pdf_draw_xobj)

        # Strip old invisible text if redo mode is enabled
        if self.context.options.mode == ProcessingMode.redo:
            strip_invisible_text(self.pdf_base, base_page)

        # Add text layer to base page
        base_page.contents_coalesce()
        base_page.contents_add(
            new_text_layer, prepend=self.render_mode == RenderMode.UNDERNEATH
        )
        base_page.contents_coalesce()

    def _graft_sandwich_text_layer(
        self,
        *,
        pageno: int,
        textpdf: Path,
        text_rotation: int,
    ):
        """Graft a pre-rendered text-only PDF onto the base PDF.

        This is used by the sandwich renderer which generates PDFs directly
        from Tesseract rather than going through hOCR.
        """
        from pikepdf import PdfError

        log.debug("Grafting sandwich text layer")
        if Path(textpdf).stat().st_size == 0:
            return

        try:
            with Pdf.open(textpdf) as pdf_text:
                pdf_text_contents = pdf_text.pages[0].Contents.read_bytes()

                base_page = self.pdf_base.pages[pageno]

                # Get font from the text PDF
                pdf_text_fonts = pdf_text.pages[0].Resources.get(
                    Name.Font, Dictionary()
                )
                font = None
                font_key = None
                for f in ('/f-0-0', '/F1'):
                    pdf_text_font = pdf_text_fonts.get(f, None)
                    if pdf_text_font is not None:
                        font_key = Name(f)
                        font = self.pdf_base.copy_foreign(pdf_text_font)
                        break

                # Get mediabox dimensions for rotation calculations
                mediabox = pdf_text.pages[0].mediabox
                wt = float(mediabox[2]) - float(mediabox[0])
                ht = float(mediabox[3]) - float(mediabox[1])

                base_mediabox = base_page.mediabox
                wp = float(base_mediabox[2]) - float(base_mediabox[0])
                hp = float(base_mediabox[3]) - float(base_mediabox[1])

                # Build transformation matrix for rotation and scaling
                ctm = _build_text_layer_ctm(
                    wt,
                    ht,
                    wp,
                    hp,
                    float(base_mediabox[0]),
                    float(base_mediabox[1]),
                    text_rotation,
                )
                log.debug("Grafting with ctm %r", ctm)

                # Create Form XObject
                base_resources = _ensure_dictionary(base_page.obj, Name.Resources)
                base_xobjs = _ensure_dictionary(base_resources, Name.XObject)
                text_xobj_name = Name.random(prefix="OCR-")
                xobj = self.pdf_base.make_stream(pdf_text_contents)
                base_xobjs[text_xobj_name] = xobj
                xobj.Type = Name.XObject
                xobj.Subtype = Name.Form
                xobj.FormType = 1
                xobj.BBox = base_mediabox

                # Add font to xobj resources
                if font_key is not None and font is not None:
                    xobj_resources = _ensure_dictionary(xobj, Name.Resources)
                    xobj_fonts = _ensure_dictionary(xobj_resources, Name.Font)
                    if font_key not in xobj_fonts:
                        xobj_fonts[font_key] = font

                if ctm is not None:
                    pdf_draw_xobj = (
                        (b'q %s cm\n' % ctm.encode())
                        + (b'%s Do\n' % text_xobj_name)
                        + b'\nQ\n'
                    )
                else:
                    pdf_draw_xobj = b'q\n' + (b'%s Do\n' % text_xobj_name) + b'\nQ\n'
                new_text_layer = Stream(self.pdf_base, pdf_draw_xobj)

                if self.context.options.mode == ProcessingMode.redo:
                    strip_invisible_text(self.pdf_base, base_page)
                base_page.contents_coalesce()
                base_page.contents_add(
                    new_text_layer, prepend=self.render_mode == RenderMode.UNDERNEATH
                )
                base_page.contents_coalesce()

                # Add font to page resources
                if font_key is not None and font is not None:
                    page_resources = _ensure_dictionary(base_page.obj, Name.Resources)
                    page_fonts = _ensure_dictionary(page_resources, Name.Font)
                    if font_key not in page_fonts:
                        page_fonts[font_key] = font
        except (FileNotFoundError, PdfError):
            # PdfError occurs if a 0-length file is written e.g. due to OCR timeout
            pass
