# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-FileCopyrightText: 2026 Danny Ward
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from unittest.mock import patch

import pikepdf
import pytest

import ocrmypdf

from .conftest import RENDERERS


def test_no_glyphless_graft(resources, outdir):
    with (
        pikepdf.open(resources / 'francais.pdf') as pdf,
        pikepdf.open(resources / 'aspect.pdf') as pdf_aspect,
        pikepdf.open(resources / 'cmyk.pdf') as pdf_cmyk,
    ):
        pdf.pages.extend(pdf_aspect.pages)
        pdf.pages.extend(pdf_cmyk.pages)
        pdf.save(outdir / 'test.pdf')

    with patch('ocrmypdf._graft.MAX_REPLACE_PAGES', 2):
        ocrmypdf.ocr(
            outdir / 'test.pdf',
            outdir / 'out.pdf',
            deskew=True,
            tesseract_timeout=0,
            force_ocr=True,
        )
    # This test needs asserts


def test_links(resources, outpdf):
    ocrmypdf.ocr(
        resources / 'link.pdf', outpdf, redo_ocr=True, oversample=200, output_type='pdf'
    )
    with pikepdf.open(outpdf) as pdf:
        p1 = pdf.pages[0]
        p2 = pdf.pages[1]
        assert p1.Annots[0].A.D[0].objgen == p2.objgen
        assert p2.Annots[0].A.D[0].objgen == p1.objgen


def test_redo_ocr_with_offset_mediabox(resources, outdir):
    """Test that --redo-ocr handles non-zero mediabox origins correctly.

    Regression test for issue #1630 where PDFs with mediabox origins like
    [0, 100, width, height+100] (common in cropped/JSTOR-style PDFs)
    would have OCR text shifted vertically because the text layer CTM
    did not account for the page origin offset.
    """
    # Create a PDF with a non-zero mediabox origin
    input_pdf = outdir / 'offset_mediabox_input.pdf'
    y_offset = 100

    with pikepdf.open(resources / 'graph_ocred.pdf') as pdf:
        page = pdf.pages[0]
        original_mb = list(page.MediaBox)

        # Shift mediabox Y origin to simulate cropped/JSTOR-style PDFs
        page.MediaBox = [
            original_mb[0],
            original_mb[1] + y_offset,
            original_mb[2],
            original_mb[3] + y_offset,
        ]

        pdf.save(input_pdf)

    # Run --redo-ocr (this is where the bug occurred)
    output_pdf = outdir / 'offset_redo_ocr.pdf'
    ocrmypdf.ocr(input_pdf, output_pdf, redo_ocr=True)

    # Verify the output
    with pikepdf.open(output_pdf) as pdf:
        page = pdf.pages[0]
        mediabox = list(page.MediaBox)

        # MediaBox origin should be preserved
        assert float(mediabox[1]) == y_offset, (
            f"MediaBox Y origin should be preserved at {y_offset}, got {mediabox[1]}"
        )

        # The content stream should include a CTM with the Y origin translation.
        # Without the fix, the CTM was omitted for rotation==0, causing a shift.
        content = page.Contents.read_bytes()
        assert b'cm' in content, (
            "Content stream should include a CTM to translate by the page origin"
        )


def _text_layer_extents(page: pikepdf.Page) -> list[pikepdf.Rectangle]:
    """Return the page-space extent of each grafted OCR form XObject's /BBox."""
    extents = []
    ctm = pikepdf.Matrix()
    for operands, operator in pikepdf.parse_content_stream(page):
        if operator == pikepdf.Operator('q'):
            ctm = pikepdf.Matrix()
        elif operator == pikepdf.Operator('cm'):
            ctm = pikepdf.Matrix(*operands)
        elif operator == pikepdf.Operator('Do') and str(operands[0]).startswith(
            '/OCR-'
        ):
            xobj = page.Resources.XObject[operands[0]]
            extents.append(ctm.transform(pikepdf.Rectangle(xobj.BBox)))
    return extents


def _assert_text_layer_covers_page(page: pikepdf.Page):
    extents = _text_layer_extents(page)
    assert extents, "Expected a grafted text layer"
    mediabox = pikepdf.Rectangle(page.mediabox)
    for extent in extents:
        # The form /BBox clips its content, so mapped onto the page it must
        # cover the whole page or OCR text will be lost
        assert extent.llx <= mediabox.llx + 1
        assert extent.lly <= mediabox.lly + 1
        assert extent.urx >= mediabox.urx - 1
        assert extent.ury >= mediabox.ury - 1


@pytest.mark.parametrize('renderer', RENDERERS)
@pytest.mark.parametrize('y_offset', [400, 1000])
def test_text_layer_bbox_with_offset_mediabox(resources, outdir, renderer, y_offset):
    input_pdf = outdir / 'offset_mediabox_input.pdf'
    with pikepdf.open(resources / 'linn.pdf') as pdf:
        page = pdf.pages[0]
        llx, lly, urx, ury = (float(v) for v in page.MediaBox)
        page.MediaBox = [llx, lly + y_offset, urx, ury + y_offset]
        page.contents_add(
            pikepdf.Stream(pdf, b'1 0 0 1 0 %d cm' % y_offset), prepend=True
        )
        pdf.save(input_pdf)

    output_pdf = outdir / 'out.pdf'
    ocrmypdf.ocr(input_pdf, output_pdf, pdf_renderer=renderer, output_type='pdf')

    with pikepdf.open(output_pdf) as pdf:
        _assert_text_layer_covers_page(pdf.pages[0])


@pytest.mark.parametrize('renderer', RENDERERS)
def test_text_layer_bbox_with_rotated_text(resources, outdir, renderer):
    output_pdf = outdir / 'out.pdf'
    ocrmypdf.ocr(
        resources / 'cardinal.pdf',
        output_pdf,
        rotate_pages=True,
        rotate_pages_threshold=0,
        pdf_renderer=renderer,
        output_type='pdf',
    )

    with pikepdf.open(output_pdf) as pdf:
        for page in pdf.pages:
            _assert_text_layer_covers_page(page)


def test_strip_invisble_text():
    pdf = pikepdf.Pdf.new()
    print(pikepdf.parse_content_stream(pikepdf.Stream(pdf, b'3 Tr')))
    page = pdf.add_blank_page()
    visible_text = [
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('BT')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.Name('/F0'), 12), pikepdf.Operator('Tf')
        ),
        pikepdf.ContentStreamInstruction((288, 720), pikepdf.Operator('Td')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.String('visible'),), pikepdf.Operator('Tj')
        ),
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('ET')),
    ]
    invisible_text = [
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('BT')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.Name('/F0'), 12), pikepdf.Operator('Tf')
        ),
        pikepdf.ContentStreamInstruction((288, 720), pikepdf.Operator('Td')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.String('invisible'),), pikepdf.Operator('Tj')
        ),
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('ET')),
    ]
    invisible_text_setting_tr = [
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('BT')),
        pikepdf.ContentStreamInstruction([3], pikepdf.Operator('Tr')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.Name('/F0'), 12), pikepdf.Operator('Tf')
        ),
        pikepdf.ContentStreamInstruction((288, 720), pikepdf.Operator('Td')),
        pikepdf.ContentStreamInstruction(
            (pikepdf.String('invisible'),), pikepdf.Operator('Tj')
        ),
        pikepdf.ContentStreamInstruction((), pikepdf.Operator('ET')),
    ]
    stream = [
        pikepdf.ContentStreamInstruction([], pikepdf.Operator('q')),
        pikepdf.ContentStreamInstruction([3], pikepdf.Operator('Tr')),
        *invisible_text,
        pikepdf.ContentStreamInstruction([], pikepdf.Operator('Q')),
        *visible_text,
        *invisible_text_setting_tr,
        *invisible_text,
    ]
    content_stream = pikepdf.unparse_content_stream(stream)
    page.Contents = pikepdf.Stream(pdf, content_stream)

    def count(string, page):
        return len(
            [
                True
                for operands, operator in pikepdf.parse_content_stream(page)
                if operator == pikepdf.Operator('Tj')
                and operands[0] == pikepdf.String(string)
            ]
        )

    nr_visible_pre = count('visible', page)
    ocrmypdf._graft.strip_invisible_text(pdf, page)
    nr_visible_post = count('visible', page)
    assert nr_visible_pre == nr_visible_post, (
        'Number of visible text elements did not change'
    )
    assert count('invisible', page) == 0, 'No invisible elems left'


def test_strip_visible_text_when_render_mode_changes_within_text_object():
    """Keep visible text when a hidden run ends the same BT/ET block (#1769)."""
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    page.Contents = pikepdf.Stream(
        pdf,
        b'BT\n/F0 12 Tf\n72 720 Td\n(visible) Tj\n3 Tr\n(invisible) Tj\nET\n',
    )

    def strings():
        return [
            bytes(operands[0])
            for operands, operator in pikepdf.parse_content_stream(page)
            if operator == pikepdf.Operator('Tj')
        ]

    assert strings() == [b'visible', b'invisible']

    ocrmypdf._graft.strip_invisible_text(pdf, page)

    assert strings() == [b'visible']


def test_strip_invisible_text_before_later_visible_run_preserves_position():
    """Do not remove hidden text if doing so could shift visible text."""
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    page.Contents = pikepdf.Stream(
        pdf,
        b'BT\n/F0 12 Tf\n72 720 Td\n3 Tr\n(hidden) Tj\n0 Tr\n(visible) Tj\nET\n',
    )

    ocrmypdf._graft.strip_invisible_text(pdf, page)

    assert [
        bytes(operands[0])
        for operands, operator in pikepdf.parse_content_stream(page)
        if operator == pikepdf.Operator('Tj')
    ] == [b'hidden', b'visible']


def _stripped(content: bytes, conversion_mode: str = 'implicit') -> bytes:
    """Strip a one-page PDF with the given content stream and return it."""
    from io import BytesIO

    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page().Contents = pikepdf.Stream(pdf, content)
    buffer = BytesIO()
    pdf.save(buffer)
    with pikepdf.Pdf.open(buffer, conversion_mode=conversion_mode) as pdf:
        page = pdf.pages[0]
        ocrmypdf._graft.strip_invisible_text(pdf, page)
        return pikepdf.unparse_content_stream(pikepdf.parse_content_stream(page))


def test_strip_hidden_text_before_a_new_line():
    """Hidden text is removed when a new line starts before the visible text.

    Td positions from the text line matrix, which showing text does not move,
    so the visible text stays where it was.
    """
    assert _stripped(
        b'BT /F1 12 Tf 3 Tr 72 700 Td (hidden) Tj 0 Tr 0 -14 Td (visible) Tj ET'
    ) == (b'BT\n/F1 12 Tf\n3 Tr\n72 700 Td\n0 Tr\n0 -14 Td\n(visible) Tj\nET')


def test_strip_hidden_quote_before_visible_text():
    """A hidden ' still moves to the next line when its string is removed."""
    assert _stripped(
        b"BT /F1 12 Tf 14 TL 72 700 Td 3 Tr (hidden) ' 0 Tr 0 -14 Td (visible) Tj ET"
    ) == (
        b'BT\n/F1 12 Tf\n14 TL\n72 700 Td\n3 Tr\nT*\n0 Tr\n0 -14 Td\n(visible) Tj\nET'
    )


def test_strip_trailing_hidden_quotes():
    """The quote operators keep their line moves and spacing, not their text."""
    assert _stripped(
        b"BT /F1 12 Tf 14 TL 72 700 Td (vis) Tj 3 Tr (h1) ' 1 2 (h2) \" ET"
    ) == (b'BT\n/F1 12 Tf\n14 TL\n72 700 Td\n(vis) Tj\n3 Tr\nT*\n1 Tw\n2 Tc\nT*\nET')


def test_strip_keeps_visible_text_before_a_trailing_tr():
    """Visible text survives a text object that ends in invisible mode."""
    content = b'BT /F1 12 Tf 72 700 Td (visible) Tj 3 Tr ET'
    assert _stripped(content) == (b'BT\n/F1 12 Tf\n72 700 Td\n(visible) Tj\n3 Tr\nET')


def test_strip_hidden_text_object_keeps_text_state():
    """Text state set in a removed text object still applies to later text.

    Text state is part of the graphics state, so the font selected in the
    hidden text object is the one the visible text object uses.
    """
    assert _stripped(
        b'BT /F1 12 Tf 3 Tr 72 700 Td (hidden) Tj ET BT 0 Tr 72 680 Td (visible) Tj ET'
    ) == (b'/F1 12 Tf\n3 Tr\nBT\n0 Tr\n72 680 Td\n(visible) Tj\nET')


@pytest.mark.parametrize('conversion_mode', ['implicit', 'explicit'])
def test_strip_hidden_text_object_keeps_leading_from_td(conversion_mode):
    """TD sets the leading as well as moving to a new line."""
    assert _stripped(
        b'BT 3 Tr 0 -14.5 TD (hidden) Tj ET BT 0 Tr T* (visible) Tj ET',
        conversion_mode,
    ) == (b'3 Tr\n14.5 TL\nBT\n0 Tr\nT*\n(visible) Tj\nET')


def test_strip_hidden_text_objects_leave_one_text_state():
    """A layer of hidden words leaves one set of text state, not one per word."""
    words = b''.join(
        b'BT /F1 %d Tf 3 Tr 100 Tz 1 0 0 1 %d 700 Tm (w) Tj ET ' % (10 + i, 72 + i)
        for i in range(50)
    )
    assert _stripped(words) == b'/F1 59 Tf\n3 Tr\n100 Tz'


def test_strip_keeps_unterminated_text_object():
    """A text object with no ET is kept as it is."""
    assert _stripped(b'0 0 m 9 9 l S BT /F1 12 Tf (open) Tj') == (
        b'0 0 m\n9 9 l\nS\nBT\n/F1 12 Tf\n(open) Tj'
    )


def test_strip_invisible_text_in_form_xobject():
    """Invisible text inside a Form XObject is stripped too.

    Regression test for #1730. OCRmyPDF grafts its own OCR text layer as a
    Form XObject and appends ``/OCR-xxxx Do`` to the page (see
    ``OcrGrafter._graft_fpdf2_text_layer``), so on OCRmyPDF's own output the
    invisible text is not in the page content stream at all and ``--mode
    strip`` used to be a no-op.
    """
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    font = pdf.make_indirect(
        pikepdf.Dictionary(
            Type=pikepdf.Name.Font,
            Subtype=pikepdf.Name.Type1,
            BaseFont=pikepdf.Name.Helvetica,
        )
    )

    def text(string, render_mode):
        return b'BT\n%d Tr\n/F0 12 Tf\n72 720 Td\n(%s) Tj\nET\n' % (
            render_mode,
            string,
        )

    # The grafted text layer: invisible OCR text plus a visible run that must
    # survive, exactly as they would sit inside an /OCR-... Form XObject.
    xobj = pdf.make_stream(text(b'invisible', 3) + text(b'visible-in-form', 0))
    xobj.Type = pikepdf.Name.XObject
    xobj.Subtype = pikepdf.Name.Form
    xobj.FormType = 1
    xobj.BBox = pikepdf.Array([0, 0, 612, 792])
    xobj.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F0=font))
    page.obj[pikepdf.Name.Resources] = pikepdf.Dictionary(
        Font=pikepdf.Dictionary(F0=font),
        XObject=pikepdf.Dictionary({'/OCR-abc': xobj}),
    )
    page.Contents = pikepdf.Stream(pdf, text(b'visible', 0) + b'q\n/OCR-abc Do\nQ\n')

    def strings(obj):
        return [
            bytes(operands[0])
            for operands, operator in pikepdf.parse_content_stream(obj, '')
            if operator == pikepdf.Operator('Tj')
        ]

    assert strings(page) == [b'visible']
    assert strings(xobj) == [b'invisible', b'visible-in-form']

    ocrmypdf._graft.strip_invisible_text(pdf, page)

    assert strings(page) == [b'visible'], 'page text must be untouched'
    assert strings(xobj) == [b'visible-in-form'], (
        'invisible text in the Form XObject must be removed, visible text kept'
    )
    assert b'Do' in page.Contents.read_bytes(), (
        'a form that still paints must keep its Do'
    )
    assert '/OCR-abc' in page.obj.Resources.XObject, (
        'a form that still paints must keep its resource entry'
    )


def test_strip_invisible_text_with_inherited_resources():
    """/Resources inherited from an ancestor /Pages node are still searched.

    A page need not carry its own /Resources; it may inherit them from a
    /Pages node (ISO 32000-2, 7.7.3.4). pikepdf's ``Page.resources`` does not
    resolve inheritance, so the strip code walks /Parent itself.
    """
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    del page.obj[pikepdf.Name.Resources]
    font = pdf.make_indirect(
        pikepdf.Dictionary(
            Type=pikepdf.Name.Font,
            Subtype=pikepdf.Name.Type1,
            BaseFont=pikepdf.Name.Helvetica,
        )
    )
    xobj = pdf.make_stream(
        b'BT\n3 Tr\n/F0 12 Tf\n72 720 Td\n(invisible) Tj\nET\n'
        b'BT\n0 Tr\n/F0 12 Tf\n72 700 Td\n(visible-in-form) Tj\nET\n'
    )
    xobj.Type = pikepdf.Name.XObject
    xobj.Subtype = pikepdf.Name.Form
    xobj.FormType = 1
    xobj.BBox = pikepdf.Array([0, 0, 612, 792])
    xobj.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F0=font))
    pdf.Root.Pages[pikepdf.Name.Resources] = pikepdf.Dictionary(
        Font=pikepdf.Dictionary(F0=font),
        XObject=pikepdf.Dictionary({'/OCR-abc': xobj}),
    )
    page.Contents = pikepdf.Stream(pdf, b'q\n/OCR-abc Do\nQ\n')

    assert pikepdf.Name.Resources not in page.obj

    ocrmypdf._graft.strip_invisible_text(pdf, page)

    strings = [
        bytes(operands[0])
        for operands, operator in pikepdf.parse_content_stream(xobj, '')
        if operator == pikepdf.Operator('Tj')
    ]
    assert strings == [b'visible-in-form'], (
        'invisible text must be stripped from a form reached via inherited /Resources'
    )


def test_strip_removes_vestigial_ocr_form():
    """A form left painting nothing after stripping is unlinked from the page.

    OCRmyPDF's own text layer is an /OCR-... Form XObject that contains only
    invisible text plus graphics-state residue. Once the text is stripped the
    form draws nothing, so the ``Do`` and the /XObject entry must go too rather
    than leaving an empty husk behind.
    """
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    font = pdf.make_indirect(
        pikepdf.Dictionary(
            Type=pikepdf.Name.Font,
            Subtype=pikepdf.Name.Type1,
            BaseFont=pikepdf.Name.Helvetica,
        )
    )
    xobj = pdf.make_stream(
        b'2 J\n0.57 w\nq\n0.99 0 0 0.99 0 0 cm\n'
        b'BT\n3 Tr\n/F0 12 Tf\n72 720 Td\n(invisible) Tj\nET\n'
        b'Q\n'
    )
    xobj.Type = pikepdf.Name.XObject
    xobj.Subtype = pikepdf.Name.Form
    xobj.FormType = 1
    xobj.BBox = pikepdf.Array([0, 0, 612, 792])
    xobj.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F0=font))
    page.obj[pikepdf.Name.Resources] = pikepdf.Dictionary(
        Font=pikepdf.Dictionary(F0=font),
        XObject=pikepdf.Dictionary({'/OCR-abc': xobj}),
    )
    page.Contents = pikepdf.Stream(
        pdf,
        b'BT\n0 Tr\n/F0 12 Tf\n72 720 Td\n(visible) Tj\nET\nq\n/OCR-abc Do\nQ\n',
    )

    ocrmypdf._graft.strip_invisible_text(pdf, page)

    content = page.Contents.read_bytes()
    assert b'Do' not in content, 'the vestigial form must no longer be drawn'
    assert b'visible' in content, 'page text must be untouched'
    assert '/OCR-abc' not in page.obj.Resources.XObject, (
        'the vestigial form must be unlinked from the page resources'
    )


def test_strip_keeps_image_xobject():
    """An image XObject is not a text container and must be left alone."""
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    image = pdf.make_stream(b'\xff\x00\x00\xff')
    image.Type = pikepdf.Name.XObject
    image.Subtype = pikepdf.Name.Image
    image.Width = 2
    image.Height = 2
    image.ColorSpace = pikepdf.Name.DeviceGray
    image.BitsPerComponent = 8
    page.obj[pikepdf.Name.Resources] = pikepdf.Dictionary(
        XObject=pikepdf.Dictionary(Im0=image)
    )
    page.Contents = pikepdf.Stream(
        pdf, b'q\n612 0 0 792 0 0 cm\n/Im0 Do\nQ\nBT\n3 Tr\n(invisible) Tj\nET\n'
    )

    ocrmypdf._graft.strip_invisible_text(pdf, page)

    content = page.Contents.read_bytes()
    assert b'/Im0 Do' in content, 'image XObjects must still be drawn'
    assert b'invisible' not in content
    assert '/Im0' in page.obj.Resources.XObject


def test_strip_invisible_text_with_self_referential_form():
    """A Form XObject that draws itself must not recurse forever (#1730)."""
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    xobj = pdf.make_stream(b'BT\n3 Tr\n/F0 12 Tf\n(invisible) Tj\nET\n/Self Do\n')
    xobj.Type = pikepdf.Name.XObject
    xobj.Subtype = pikepdf.Name.Form
    xobj.FormType = 1
    xobj.BBox = pikepdf.Array([0, 0, 612, 792])
    xobj.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary({'/Self': xobj}))
    page.obj[pikepdf.Name.Resources] = pikepdf.Dictionary(
        XObject=pikepdf.Dictionary({'/Self': xobj})
    )
    page.Contents = pikepdf.Stream(pdf, b'/Self Do\n')

    ocrmypdf._graft.strip_invisible_text(pdf, page)

    assert b'invisible' not in xobj.read_bytes()
