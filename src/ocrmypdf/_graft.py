# © 2018 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Optional

import pikepdf
from pikepdf.objects import Dictionary, Name

log = logging.getLogger(__name__)
MAX_REPLACE_PAGES = 100


def _ensure_dictionary(obj, name):
    if name not in obj:
        obj[name] = Dictionary({})
    return obj[name]


def _update_resources(*, obj, font, font_key, procset):
    """Update this obj's fonts with a reference to the Glyphless font.

    obj can be a page or Form XObject.
    """

    resources = _ensure_dictionary(obj, Name.Resources)
    fonts = _ensure_dictionary(resources, Name.Font)
    if font_key is not None and font_key not in fonts:
        fonts[font_key] = font

    # Reassign /ProcSet to one that just lists everything - ProcSet is
    # obsolete and doesn't matter but recommended for old viewer support
    if procset:
        resources['/ProcSet'] = procset


def strip_invisible_text(pdf, page):
    stream = []
    in_text_obj = False
    render_mode = 0
    text_objects = []

    page.page_contents_coalesce()
    for operands, operator in pikepdf.parse_content_stream(page, ''):
        if not in_text_obj:
            if operator == pikepdf.Operator('BT'):
                in_text_obj = True
                render_mode = 0
                text_objects.append((operands, operator))
            else:
                stream.append((operands, operator))
        else:
            if operator == pikepdf.Operator('Tr'):
                render_mode = operands[0]
            text_objects.append((operands, operator))
            if operator == pikepdf.Operator('ET'):
                in_text_obj = False
                if render_mode != 3:
                    stream.extend(text_objects)
                text_objects.clear()

    def convert(op):
        try:
            return op.unparse()
        except AttributeError:
            return str(op).encode('ascii')

    lines = []

    for operands, operator in stream:
        if operator == pikepdf.Operator('INLINE IMAGE'):
            iim = operands[0]
            line = iim.unparse()
        else:
            line = b' '.join(convert(op) for op in operands) + b' ' + operator.unparse()
        lines.append(line)

    content_stream = b'\n'.join(lines)
    page.Contents = pikepdf.Stream(pdf, content_stream)


class OcrGrafter:
    def __init__(self, context):
        self.context = context
        self.path_base = context.origin

        self.pdf_base = pikepdf.open(self.path_base)
        self.font, self.font_key = None, None

        self.pdfinfo = context.pdfinfo
        self.output_file = context.get_path('graft_layers.pdf')

        self.procset = self.pdf_base.make_indirect(
            pikepdf.Object.parse(b'[ /PDF /Text /ImageB /ImageC /ImageI ]')
        )

        self.emplacements = 1
        self.interim_count = 0

    def graft_page(
        self,
        *,
        pageno: int,
        image: Optional[Path],
        textpdf: Optional[Path],
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
            with pikepdf.open(image) as pdf_image:
                self.emplacements += 1
                foreign_image_page = pdf_image.pages[0]
                self.pdf_base.pages.append(foreign_image_page)
                local_image_page = self.pdf_base.pages[-1]
                self.pdf_base.pages[pageno].emplace(local_image_page)
                del self.pdf_base.pages[-1]
            emplaced_page = True

        # Calculate if the text is misaligned compared to the content
        if emplaced_page:
            content_rotation = autorotate_correction
        text_rotation = autorotate_correction
        text_misaligned = (text_rotation - content_rotation) % 360
        log.debug(
            f"Text rotation: (text, autorotate, content) -> text misalignment = "
            f"({text_rotation}, {autorotate_correction}, {content_rotation}) -> {text_misaligned}"
        )

        if textpdf and self.font:
            # Graft the text layer onto this page, whether new or old, possibly
            # rotating the text layer by the amount is misaligned.
            strip_old = self.context.options.redo_ocr
            self._graft_text_layer(
                page_num=pageno + 1,
                textpdf=textpdf,
                font=self.font,
                font_key=self.font_key,
                text_rotation=text_misaligned,
                procset=self.procset,
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

    def save_and_reload(self):
        """Save and reload the Pdf.

        This will keep a lid on our memory usage for very large files. Attach
        the font to page 1 even if page 1 doesn't use it, so we have a way to get it
        back.
        """

        page0 = self.pdf_base.pages[0]
        _update_resources(
            obj=page0, font=self.font, font_key=self.font_key, procset=self.procset
        )

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
        self.pdf_base.save(next_file)
        self.pdf_base.close()

        self.pdf_base = pikepdf.open(next_file)
        self.procset = self.pdf_base.pages[0].Resources.ProcSet
        self.font, self.font_key = None, None  # Ensure we reacquire this information
        self.interim_count += 1

    def finalize(self):
        self.pdf_base.save(self.output_file)
        self.pdf_base.close()
        return self.output_file

    def _find_font(self, text):
        """Copy a font from the filename text into pdf_base"""

        font, font_key = None, None
        possible_font_names = ('/f-0-0', '/F1')
        try:
            with pikepdf.open(text) as pdf_text:
                try:
                    pdf_text_fonts = pdf_text.pages[0].Resources.get('/Font', {})
                except (AttributeError, IndexError, KeyError):
                    return None, None
                pdf_text_font = None
                for f in possible_font_names:
                    pdf_text_font = pdf_text_fonts.get(f, None)
                    if pdf_text_font is not None:
                        font_key = f
                        break
                if pdf_text_font:
                    font = self.pdf_base.copy_foreign(pdf_text_font)
                return font, font_key
        except (FileNotFoundError, pikepdf.PdfError):
            # PdfError occurs if a 0-length file is written e.g. due to OCR timeout
            return None, None

    def _graft_text_layer(
        self,
        *,
        page_num: int,
        textpdf: Path,
        font: pikepdf.Object,
        font_key: pikepdf.Object,
        procset: pikepdf.Object,
        text_rotation: int,
        strip_old_text: bool,
    ):
        """Insert the text layer from text page 0 on to pdf_base at page_num"""

        log.debug("Grafting")
        if Path(textpdf).stat().st_size == 0:
            return

        # This is a pointer indicating a specific page in the base file
        with pikepdf.open(textpdf) as pdf_text:
            pdf_text_contents = pdf_text.pages[0].Contents.read_bytes()

            base_page = self.pdf_base.pages.p(page_num)

            # The text page always will be oriented up by this stage but the original
            # content may have a rotation applied. Wrap the text stream with a rotation
            # so it will be oriented the same way as the rest of the page content.
            # (Previous versions OCRmyPDF rotated the content layer to match the text.)
            mediabox = [float(pdf_text.pages[0].MediaBox[v]) for v in range(4)]
            wt, ht = mediabox[2] - mediabox[0], mediabox[3] - mediabox[1]

            mediabox = [float(base_page.MediaBox[v]) for v in range(4)]
            wp, hp = mediabox[2] - mediabox[0], mediabox[3] - mediabox[1]

            translate = pikepdf.PdfMatrix().translated(-wt / 2, -ht / 2)
            untranslate = pikepdf.PdfMatrix().translated(wp / 2, hp / 2)
            corner = pikepdf.PdfMatrix().translated(mediabox[0], mediabox[1])
            # -rotation because the input is a clockwise angle and this formula
            # uses CCW
            text_rotation = -text_rotation % 360
            rotate = pikepdf.PdfMatrix().rotated(text_rotation)

            # Because of rounding of DPI, we might get a text layer that is not
            # identically sized to the target page. Scale to adjust. Normally this
            # is within 0.998.
            if text_rotation in (90, 270):
                wt, ht = ht, wt
            scale_x = wp / wt
            scale_y = hp / ht

            # log.debug('%r', scale_x, scale_y)
            scale = pikepdf.PdfMatrix().scaled(scale_x, scale_y)

            # Translate the text so it is centered at (0, 0), rotate it there, adjust
            # for a size different between initial and text PDF, then untranslate, and
            # finally move the lower left corner to match the mediabox
            ctm = translate @ rotate @ scale @ untranslate @ corner

            base_resources = _ensure_dictionary(base_page, Name.Resources)
            base_xobjs = _ensure_dictionary(base_resources, Name.XObject)
            text_xobj_name = Name('/' + str(uuid.uuid4()))
            xobj = self.pdf_base.make_stream(pdf_text_contents)
            base_xobjs[text_xobj_name] = xobj
            xobj.Type = Name.XObject
            xobj.Subtype = Name.Form
            xobj.FormType = 1
            xobj.BBox = mediabox
            _update_resources(
                obj=xobj, font=font, font_key=font_key, procset=[Name.PDF]
            )

            pdf_draw_xobj = (
                (b'q %s cm\n' % ctm.encode()) + (b'%s Do\n' % text_xobj_name) + b'\nQ\n'
            )
            new_text_layer = pikepdf.Stream(self.pdf_base, pdf_draw_xobj)

            if strip_old_text:
                strip_invisible_text(self.pdf_base, base_page)

            base_page.page_contents_add(new_text_layer, prepend=True)

            _update_resources(
                obj=base_page, font=font, font_key=font_key, procset=procset
            )
