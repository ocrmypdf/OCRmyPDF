# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-FileCopyrightText: 2026 Som Samantray
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pikepdf
import pymupdf
import pytest

import ocrmypdf
from ocrmypdf._graft import OcrGrafter, RenderMode
from ocrmypdf._options import ProcessingMode


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


@pytest.mark.parametrize('renderer', ['fpdf2', 'sandwich'])
def test_offset_mediabox_does_not_clip_grafted_text(renderer, tmp_path):
    """Grafted text uses its own coordinates even when the page origin is offset."""
    base = pikepdf.Pdf.new()
    page = base.add_blank_page(page_size=(612, 792))
    page.MediaBox = [0, 400, 612, 1192]

    text_pdf = pikepdf.Pdf.new()
    text_page = text_pdf.add_blank_page(page_size=(612, 792))
    font = text_pdf.make_indirect(
        pikepdf.Dictionary(
            Type=pikepdf.Name.Font,
            Subtype=pikepdf.Name.Type1,
            BaseFont=pikepdf.Name.Helvetica,
        )
    )
    text_page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
    text_page.Contents = text_pdf.make_stream(
        b'BT /F1 12 Tf 72 700 Td (Top line) Tj 0 -600 Td (Bottom line) Tj ET'
    )
    text_path = tmp_path / 'text.pdf'
    text_pdf.save(text_path)

    grafter = OcrGrafter.__new__(OcrGrafter)
    grafter.pdf_base = base
    grafter.context = SimpleNamespace(
        options=SimpleNamespace(mode=ProcessingMode.default)
    )
    grafter.render_mode = RenderMode.UNDERNEATH

    if renderer == 'fpdf2':
        grafter._graft_fpdf2_text_layer(0, text_page, 0)
    else:
        grafter._graft_sandwich_text_layer(pageno=0, textpdf=text_path, text_rotation=0)

    output_path = tmp_path / f'{renderer}.pdf'
    base.save(output_path)

    with pymupdf.open(output_path) as document:
        assert document[0].get_text() == 'Top line\nBottom line\n'
        words = {word[4]: word[1] for word in document[0].get_text('words')}
        assert words['Top'] == pytest.approx(79.1)
        assert words['Bottom'] == pytest.approx(679.1)

    with pikepdf.open(output_path) as output:
        xobj = next(
            xobj
            for xobj in output.pages[0].Resources.XObject.values()
            if xobj.Subtype == pikepdf.Name.Form
        )
        assert [float(value) for value in xobj.BBox] == [0, 0, 612, 792]


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
