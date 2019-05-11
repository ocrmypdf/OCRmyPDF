# © 2018 James R. Barlow: github.com/jbarlow83
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

from contextlib import suppress
from itertools import groupby
from pathlib import Path
import os

import pikepdf

from .exec import tesseract
from .helpers import flatten_groups, page_number


MAX_REPLACE_PAGES = int(os.environ.get('_OCRMYPDF_MAX_REPLACE_PAGES', 100))


def _update_page_resources(*, page, font, font_key, procset):
    """Update this page's fonts with a reference to the Glyphless font"""

    if '/Resources' not in page:
        page['/Resources'] = pikepdf.Dictionary({})
    resources = page['/Resources']
    try:
        fonts = resources['/Font']
    except KeyError:
        fonts = pikepdf.Dictionary({})
    if font_key is not None and font_key not in fonts:
        fonts[font_key] = font
    resources['/Font'] = fonts

    # Reassign /ProcSet to one that just lists everything - ProcSet is
    # obsolete and doesn't matter but recommended for old viewer support
    resources['/ProcSet'] = procset


def strip_invisible_text(pdf, page, log):
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


def _weave_layers_graft(
    *, pdf_base, page_num, text, font, font_key, procset, rotation, strip_old_text, log
):
    """Insert the text layer from text page 0 on to pdf_base at page_num"""

    log.debug("Grafting")
    if Path(text).stat().st_size == 0:
        return

    # This is a pointer indicating a specific page in the base file
    pdf_text = pikepdf.open(text)
    pdf_text_contents = pdf_text.pages[0].Contents.read_bytes()

    if not tesseract.has_textonly_pdf():
        # If we don't have textonly_pdf, edit the stream to delete the
        # instruction to draw the image Tesseract generated, which we do not
        # use.
        stream = bytearray(pdf_text_contents)
        pattern = b'/Im1 Do'
        idx = stream.find(pattern)
        stream[idx : (idx + len(pattern))] = b' ' * len(pattern)
        pdf_text_contents = bytes(stream)

    base_page = pdf_base.pages.p(page_num)

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
    # -rotation because the input is a clockwise angle and this formula
    # uses CCW
    rotation = -rotation % 360
    rotate = pikepdf.PdfMatrix().rotated(rotation)

    # Because of rounding of DPI, we might get a text layer that is not
    # identically sized to the target page. Scale to adjust. Normally this
    # is within 0.998.
    if rotation in (90, 270):
        wt, ht = ht, wt
    scale_x = wp / wt
    scale_y = hp / ht

    log.debug('%r', (scale_x, scale_y))
    scale = pikepdf.PdfMatrix().scaled(scale_x, scale_y)

    # Translate the text so it is centered at (0, 0), rotate it there, adjust
    # for a size different between initial and text PDF, then untranslate
    ctm = translate @ rotate @ scale @ untranslate

    pdf_text_contents = b'q %s cm\n' % ctm.encode() + pdf_text_contents + b'\nQ\n'

    new_text_layer = pikepdf.Stream(pdf_base, pdf_text_contents)

    if strip_old_text:
        strip_invisible_text(pdf_base, base_page, log)

    base_page.page_contents_add(new_text_layer, prepend=True)

    _update_page_resources(
        page=base_page, font=font, font_key=font_key, procset=procset
    )
    pdf_text.close()


def _find_font(text, pdf_base):
    """Copy a font from the filename text into pdf_base"""

    font, font_key = None, None
    possible_font_names = ('/f-0-0', '/F1')
    try:
        with pikepdf.open(text) as pdf_text:
            try:
                pdf_text_fonts = pdf_text.pages[0].Resources.get('/Font', {})
            except (AttributeError, IndexError, KeyError):
                return None, None
            for f in possible_font_names:
                pdf_text_font = pdf_text_fonts.get(f, None)
                if pdf_text_font is not None:
                    font_key = f
                    break
            if pdf_text_font:
                font = pdf_base.copy_foreign(pdf_text_font)
            return font, font_key
    except (FileNotFoundError, pikepdf.PdfError):
        # PdfError occurs if a 0-length file is written e.g. due to OCR timeout
        return None, None


def weave_layers(infiles, output_file, log, context):
    """Apply text layer and/or image layer changes to baseline file

    This is where the magic happens. infiles will be the main PDF to modify,
    and optional .text.pdf and .image-layer.pdf files, organized however ruffus
    organizes them.

    From .text.pdf, we copy the content stream (which contains the Tesseract
    OCR results), and rotate it into place. The first time we do this, we also
    copy the GlyphlessFont, and then reference that font again.

    For .image-layer.pdf, we check if this is a "pointer" to the original file,
    or a new file. If a new file, we replace the page and remember that we
    replaced this page.

    Every 100 open files, we save intermediate results, to avoid any resource
    limits, since pikepdf/qpdf need to keep a lot of open file handles in the
    background. When objects are copied from one file to another qpdf, qpdf
    doesn't actually copy the data until asked to write, so all the resources
    it may need to remain available.

    For completeness, we set up a /ProcSet on every page, although it's
    unlikely any PDF viewer cares about this anymore.

    """

    def input_sorter(key):
        try:
            return page_number(key)
        except ValueError:
            return -1

    flat_inputs = sorted(flatten_groups(infiles), key=input_sorter)
    groups = groupby(flat_inputs, key=input_sorter)

    # Extract first item
    _, basegroup = next(groups)
    base = list(basegroup)[0]
    path_base = Path(base).resolve()
    pdf_base = pikepdf.open(path_base)
    font, font_key, procset = None, None, None
    pdfinfo = context.get_pdfinfo()

    procset = pdf_base.make_indirect(
        pikepdf.Object.parse(b'[ /PDF /Text /ImageB /ImageC /ImageI ]')
    )

    emplacements = 1
    interim_count = 0

    # Iterate rest
    for page_num, layers in groups:
        layers = list(layers)
        log.debug(page_num)
        log.debug(layers)

        text = next((ii for ii in layers if ii.endswith('.text.pdf')), None)
        image = next((ii for ii in layers if ii.endswith('.image-layer.pdf')), None)

        if text and not font:
            font, font_key = _find_font(text, pdf_base)

        emplaced_page = False
        content_rotation = pdfinfo[page_num - 1].rotation

        path_image = Path(image).resolve() if image else None
        if path_image is not None and path_image != path_base:
            # We are updating the old page with a rasterized PDF of the new
            # page (without changing objgen, to preserve references)
            log.debug("Emplacement update")
            with pikepdf.open(image) as pdf_image:
                emplacements += 1
                foreign_image_page = pdf_image.pages[0]
                pdf_base.pages.append(foreign_image_page)
                local_image_page = pdf_base.pages[-1]
                pdf_base.pages[page_num - 1].emplace(local_image_page)
                del pdf_base.pages[-1]
            emplaced_page = True

        autorotate_correction = context.get_rotation(page_num - 1)
        if emplaced_page:
            content_rotation = autorotate_correction
        text_rotation = autorotate_correction
        text_misaligned = (text_rotation - content_rotation) % 360
        log.debug(
            '%r',
            [text_rotation, autorotate_correction, text_misaligned, content_rotation],
        )

        if text and font:
            # Graft the text layer onto this page, whether new or old
            strip_old = context.get_options().redo_ocr
            _weave_layers_graft(
                pdf_base=pdf_base,
                page_num=page_num,
                text=text,
                font=font,
                font_key=font_key,
                rotation=text_misaligned,
                procset=procset,
                strip_old_text=strip_old,
                log=log,
            )

        # Correct the rotation if applicable
        pdf_base.pages[page_num - 1].Rotate = (
            content_rotation - autorotate_correction
        ) % 360

        if emplacements % MAX_REPLACE_PAGES == 0:
            # Periodically save and reload the Pdf object. This will keep a
            # lid on our memory usage for very large files. Attach the font to
            # page 1 even if page 1 doesn't use it, so we have a way to get it
            # back.
            # TODO refactor this to outside the loop
            page0 = pdf_base.pages[0]
            _update_page_resources(
                page=page0, font=font, font_key=font_key, procset=procset
            )

            # We cannot read and write the same file, that will corrupt it
            # but we don't to keep more copies than we need to. Delete intermediates.
            # {interim_count} is the opened file we were updateing
            # {interim_count - 1} can be deleted
            # {interim_count + 1} is the new file will produce and open
            old_file = output_file + f'_working{interim_count - 1}.pdf'
            if not context.get_options().keep_temporary_files:
                with suppress(FileNotFoundError):
                    os.unlink(old_file)

            next_file = output_file + f'_working{interim_count + 1}.pdf'
            pdf_base.save(next_file)
            pdf_base.close()

            pdf_base = pikepdf.open(next_file)
            procset = pdf_base.pages[0].Resources.ProcSet
            font, font_key = None, None  # Ensure we reacquire this information
            interim_count += 1

    pdf_base.save(output_file)
    pdf_base.close()
