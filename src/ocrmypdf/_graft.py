# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""For grafting text-only PDF pages onto freeform PDF pages."""

from __future__ import annotations

import logging
from contextlib import suppress
from enum import Enum
from pathlib import Path

from pikepdf import (
    Dictionary,
    Matrix,
    Name,
    Operator,
    Page,
    Pdf,
    PdfError,
    Stream,
    parse_content_stream,
    unparse_content_stream,
)

from ocrmypdf._jobcontext import PdfContext


class RenderMode(Enum):
    ON_TOP = 0
    UNDERNEATH = 1


log = logging.getLogger(__name__)
MAX_REPLACE_PAGES = 100


def _ensure_dictionary(obj: Dictionary | Stream, name: Name):
    if name not in obj:
        obj[name] = Dictionary({})
    return obj[name]


def _update_resources(
    *,
    obj: Dictionary | Stream,
    font: Dictionary | None,
    font_key: Name | None,
):
    """Update this obj's fonts with a reference to the Glyphless font.

    obj can be a page or Form XObject.
    """
    resources = _ensure_dictionary(obj, Name.Resources)
    fonts = _ensure_dictionary(resources, Name.Font)
    if font_key is not None and font_key not in fonts:
        fonts[font_key] = font


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
            try:
                render_mode = render_mode_stack.pop()
            except IndexError:
                # Stack underflow: content stream is malformed
                # but try to carry on
                pass

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
        self.font: Dictionary | None = None
        self.font_key: Name | None = None

        self.pdfinfo = context.pdfinfo
        self.output_file = context.get_path('graft_layers.pdf')

        self.emplacements = 1
        self.interim_count = 0
        self.render_mode = RenderMode.UNDERNEATH

    def graft_page(
        self,
        *,
        pageno: int,
        image: Path | None,
        textpdf: Path | None,
        autorotate_correction: int,
    ):
        if textpdf and not self.font:
            self.font, self.font_key = self._find_font(textpdf)

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

        # Calculate if the text is misaligned compared to the content
        if emplaced_page:
            content_rotation = autorotate_correction
        text_rotation = autorotate_correction
        text_misaligned = (text_rotation - content_rotation) % 360
        log.debug(
            f"Text rotation: (text, autorotate, content) -> text misalignment = "
            f"({text_rotation}, {autorotate_correction}, {content_rotation}) -> "
            f"{text_misaligned}"
        )

        if textpdf and self.font:
            if self.font_key is None:
                raise ValueError("Font key is not set")
            # Graft the text layer onto this page, whether new or old, possibly
            # rotating the text layer by the amount is misaligned.
            strip_old = self.context.options.redo_ocr
            self._graft_text_layer(
                page_num=pageno + 1,
                textpdf=textpdf,
                font=self.font,
                font_key=self.font_key,
                text_rotation=text_misaligned,
                strip_old_text=strip_old,
            )

        # Correct the overall page rotation if needed, now that the text and content
        # are aligned
        page_rotation = (content_rotation - autorotate_correction) % 360
        self.pdf_base.pages[pageno].Rotate = page_rotation
        log.debug(
            f"Page rotation: (content, auto) -> page = "
            f"({content_rotation}, {autorotate_correction}) -> {page_rotation}"
        )
        if self.emplacements % MAX_REPLACE_PAGES == 0:
            self.save_and_reload()

    def save_and_reload(self) -> None:
        """Save and reload the Pdf.

        This will keep a lid on our memory usage for very large files. Attach
        the font to page 1 even if page 1 doesn't use it, so we have a way to get it
        back.
        """
        page0 = self.pdf_base.pages[0]
        _update_resources(obj=page0.obj, font=self.font, font_key=self.font_key)

        # We cannot read and write the same file, that will corrupt it
        # but we don't to keep more copies than we need to. Delete intermediates.
        # {interim_count} is the opened file we were updating
        # {interim_count - 1} can be deleted
        # {interim_count + 1} is the new file will produce and open
        old_file = self.output_file.with_suffix(f'.working{self.interim_count - 1}.pdf')
        if not self.context.options.keep_temporary_files:
            with suppress(FileNotFoundError):
                old_file.unlink()

        next_file = self.output_file.with_suffix(
            f'.working{self.interim_count + 1}.pdf'
        )
        self.pdf_base.save(
            next_file, deterministic_id=self.context.options.deterministic_output
        )
        self.pdf_base.close()

        self.pdf_base = Pdf.open(next_file)
        self.font, self.font_key = None, None  # Ensure we reacquire this information
        self.interim_count += 1

    def finalize(self):
        self.pdf_base.save(
            self.output_file, deterministic_id=self.context.options.deterministic_output
        )
        self.pdf_base.close()
        return self.output_file

    def _find_font(self, text: Path) -> tuple[Dictionary | None, Name | None]:
        """Copy a font from the filename text into pdf_base."""
        font, font_key = None, None
        possible_font_names = ('/f-0-0', '/F1')
        try:
            with Pdf.open(text) as pdf_text:
                try:
                    pdf_text_fonts = pdf_text.pages[0].Resources.get(
                        Name.Font, Dictionary()
                    )
                except (AttributeError, IndexError, KeyError):
                    return None, None
                if not isinstance(pdf_text_fonts, Dictionary):
                    log.warning("Page fonts are not stored in a dictionary")
                    return None, None
                pdf_text_font = None
                for f in possible_font_names:
                    pdf_text_font = pdf_text_fonts.get(f, None)
                    if pdf_text_font is not None:
                        font_key = Name(f)
                        break
                if pdf_text_font:
                    font = self.pdf_base.copy_foreign(pdf_text_font)
                if not isinstance(font, Dictionary):
                    log.warning("Font is not a dictionary")
                    font, font_key = None, None
                return font, font_key
        except (FileNotFoundError, PdfError):
            # PdfError occurs if a 0-length file is written e.g. due to OCR timeout
            return None, None

    def _graft_text_layer(
        self,
        *,
        page_num: int,
        textpdf: Path,
        font: Dictionary,
        font_key: Name,
        text_rotation: int,
        strip_old_text: bool,
    ):
        """Insert the text layer from text page 0 on to pdf_base at page_num."""
        # pylint: disable=invalid-name

        log.debug("Grafting")
        if Path(textpdf).stat().st_size == 0:
            return

        # This is a pointer indicating a specific page in the base file
        with Pdf.open(textpdf) as pdf_text:
            pdf_text_contents = pdf_text.pages[0].Contents.read_bytes()

            base_page = self.pdf_base.pages.p(page_num)

            # The text page always will be oriented up by this stage but the original
            # content may have a rotation applied. Wrap the text stream with a rotation
            # so it will be oriented the same way as the rest of the page content.
            # (Previous versions OCRmyPDF rotated the content layer to match the text.)
            mediabox = pdf_text.pages[0].mediabox
            wt, ht = mediabox[2] - mediabox[0], mediabox[3] - mediabox[1]

            mediabox = base_page.mediabox
            wp, hp = mediabox[2] - mediabox[0], mediabox[3] - mediabox[1]

            translate = Matrix().translated(-wt / 2, -ht / 2)
            untranslate = Matrix().translated(wp / 2, hp / 2)
            corner = Matrix().translated(mediabox[0], mediabox[1])
            # -rotation because the input is a clockwise angle and this formula
            # uses CCW
            text_rotation = -text_rotation % 360
            rotate = Matrix().rotated(text_rotation)

            # Because of rounding of DPI, we might get a text layer that is not
            # identically sized to the target page. Scale to adjust. Normally this
            # is within 0.998.
            if text_rotation in (90, 270):
                wt, ht = ht, wt
            scale_x = wp / wt
            scale_y = hp / ht

            # log.debug('%r', scale_x, scale_y)
            scale = Matrix().scaled(scale_x, scale_y)

            # Translate the text so it is centered at (0, 0), rotate it there, adjust
            # for a size different between initial and text PDF, then untranslate, and
            # finally move the lower left corner to match the mediabox.
            ctm = translate @ rotate @ scale @ untranslate @ corner
            log.debug("Grafting with ctm %r", ctm)

            base_resources = _ensure_dictionary(base_page.obj, Name.Resources)
            base_xobjs = _ensure_dictionary(base_resources, Name.XObject)
            if self.context.options.deterministic_output:
                # Use a stable name per page for deterministic output
                text_xobj_name = Name(f"/OCR-{page_num:06d}")
            else:
                text_xobj_name = Name.random(prefix="OCR-")
            xobj = self.pdf_base.make_stream(pdf_text_contents)
            base_xobjs[text_xobj_name] = xobj
            xobj.Type = Name.XObject
            xobj.Subtype = Name.Form
            xobj.FormType = 1
            xobj.BBox = mediabox
            _update_resources(obj=xobj, font=font, font_key=font_key)

            pdf_draw_xobj = (
                (b'q %s cm\n' % ctm.encode()) + (b'%s Do\n' % text_xobj_name) + b'\nQ\n'
            )
            new_text_layer = Stream(self.pdf_base, pdf_draw_xobj)

            if strip_old_text:
                strip_invisible_text(self.pdf_base, base_page)
            base_page.contents_coalesce()
            if self.render_mode == RenderMode.ON_TOP:
                # Add q/Q to ensure content we append is drawn correctly
                # Strictly speaking this needs to trace the whole q/Q stack in case
                # stack is not balanced.
                original = base_page.Contents.read_bytes()
                base_page.Contents.write(b'q\n' + original + b'\nQ\n')
            base_page.contents_add(
                new_text_layer, prepend=self.render_mode == RenderMode.UNDERNEATH
            )
            base_page.contents_coalesce()

            _update_resources(obj=base_page.obj, font=font, font_key=font_key)
