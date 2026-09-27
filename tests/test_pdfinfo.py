# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pickle
import warnings
from io import BytesIO
from math import isclose

import img2pdf
import pikepdf
import pytest
from PIL import Image
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

from ocrmypdf import pdfinfo
from ocrmypdf.exceptions import InputFileError
from ocrmypdf.helpers import IMG2PDF_KWARGS, Resolution
from ocrmypdf.pdfinfo import Colorspace, Encoding, Ink
from ocrmypdf.pdfinfo._contentstream import _ink_from_components, _interpret_contents
from ocrmypdf.pdfinfo.layout import PDFPage

warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="reportlab.lib.rl_safe_eval"
)

# pylint: disable=protected-access


@pytest.fixture
def single_page_text(outdir):
    filename = outdir / 'text.pdf'
    pdf = Canvas(str(filename), pagesize=(8 * inch, 6 * inch))
    text = pdf.beginText()
    text.setFont('Helvetica', 12)
    text.setTextOrigin(1 * inch, 3 * inch)
    text.textLine(
        "Methink'st thou art a general offence and every man should beat thee."
    )
    pdf.drawText(text)
    pdf.showPage()
    pdf.save()
    return filename


def test_single_page_text(single_page_text):
    info = pdfinfo.PdfInfo(single_page_text)

    assert len(info) == 1
    page = info[0]

    assert page.has_text
    assert len(page.images) == 0


@pytest.fixture(scope='session')
def eight_by_eight():
    im = Image.new('1', (8, 8), 0)
    for n in range(8):
        im.putpixel((n, n), 1)
    return im


@pytest.fixture
def eight_by_eight_regular_image(eight_by_eight, outpdf):
    im = eight_by_eight
    bio = BytesIO()
    im.save(bio, format='PNG')
    bio.seek(0)

    imgsize = ((img2pdf.ImgSize.dpi, 8), (img2pdf.ImgSize.dpi, 8))
    layout_fun = img2pdf.get_layout_fun(None, imgsize, None, None, None)

    with outpdf.open('wb') as f:
        img2pdf.convert(
            bio,
            producer="img2pdf",
            layout_fun=layout_fun,
            outputstream=f,
            **IMG2PDF_KWARGS,
        )
    return outpdf


def test_single_page_image(eight_by_eight_regular_image):
    info = pdfinfo.PdfInfo(eight_by_eight_regular_image)

    assert len(info) == 1
    page = info[0]

    assert not page.has_text
    assert len(page.images) == 1

    pdfimage = page.images[0]
    assert pdfimage.width == 8
    assert pdfimage.color == Colorspace.gray

    # DPI in a 1"x1" is the image width
    assert isclose(pdfimage.dpi.x, 8)
    assert isclose(pdfimage.dpi.y, 8)


@pytest.fixture
def eight_by_eight_inline_image(eight_by_eight, outpdf):
    pdf = Canvas(str(outpdf), pagesize=(8 * 72, 6 * 72))
    # Draw image in a 72x72 pt or 1"x1" area
    pdf.drawInlineImage(eight_by_eight, 0, 0, width=72, height=72)
    pdf.showPage()
    pdf.save()
    return outpdf


def test_single_page_inline_image(eight_by_eight_inline_image):
    info = pdfinfo.PdfInfo(eight_by_eight_inline_image)
    print(info)
    pdfimage = info[0].images[0]
    assert isclose(pdfimage.dpi.x, 8)
    assert pdfimage.color == Colorspace.gray
    assert pdfimage.width == 8


def test_jpeg(jpeg_scan):
    filename = jpeg_scan

    pdf = pdfinfo.PdfInfo(filename)

    pdfimage = pdf[0].images[0]
    assert pdfimage.enc == Encoding.jpeg
    assert isclose(pdfimage.dpi.x, 150)


@pytest.fixture
def flate_jpeg_pdf(outpdf):
    """Create a PDF with a FlateDecode+DCTDecode (flate+jpeg) encoded image.

    This simulates what OCRmyPDF's optimizer does when it deflates JPEGs.
    """
    from zlib import compress

    # Create an RGB image and save as JPEG
    im = Image.new('RGB', (64, 64), color=(128, 64, 192))
    bio = BytesIO()
    im.save(bio, format='JPEG')
    jpeg_data = bio.getvalue()

    # Compress the JPEG data with flate
    flate_jpeg_data = compress(jpeg_data)

    # Create a PDF with the flate+jpeg image
    with pikepdf.Pdf.new() as pdf:
        pdf.add_blank_page(page_size=(72, 72))
        image_dict = pikepdf.Stream(
            pdf,
            flate_jpeg_data,
            BitsPerComponent=8,
            ColorSpace=pikepdf.Name.DeviceRGB,
            Filter=[pikepdf.Name.FlateDecode, pikepdf.Name.DCTDecode],
            Height=64,
            Subtype=pikepdf.Name.Image,
            Type=pikepdf.Name.XObject,
            Width=64,
        )
        objname = pdf.pages[0].add_resource(
            image_dict, pikepdf.Name.XObject, pikepdf.Name.Im0
        )
        pdf.pages[0].Contents = pikepdf.Stream(
            pdf, b"q 72 0 0 72 0 0 cm %s Do Q" % bytes(objname)
        )
        pdf.save(outpdf)
    return outpdf


def test_flate_jpeg(flate_jpeg_pdf):
    """Test that pdfinfo correctly identifies FlateDecode+DCTDecode as flate_jpeg."""
    pdf = pdfinfo.PdfInfo(flate_jpeg_pdf)

    pdfimage = pdf[0].images[0]
    assert pdfimage.enc == Encoding.flate_jpeg


def test_form_xobject(resources):
    filename = resources / 'formxobject.pdf'

    pdf = pdfinfo.PdfInfo(filename)
    pdfimage = pdf[0].images[0]
    assert pdfimage.width == 50


def test_no_contents(resources):
    filename = resources / 'no_contents.pdf'

    pdf = pdfinfo.PdfInfo(filename)
    assert len(pdf[0].images) == 0
    assert not pdf[0].has_text


def test_oversized_page(resources):
    pdf = pdfinfo.PdfInfo(resources / 'poster.pdf')
    image = pdf[0].images[0]
    assert image.width * image.dpi.x > 200, "this is supposed to be oversized"


def test_pickle(resources):
    # For multiprocessing we must be able to pickle our information - if
    # this fails then we are probably storing some unpickleabe pikepdf or
    # other external data around
    filename = resources / 'graph_ocred.pdf'
    pdf = pdfinfo.PdfInfo(filename)
    pickle.dumps(pdf)


def test_vector(resources):
    filename = resources / 'vector.pdf'
    pdf = pdfinfo.PdfInfo(filename)
    assert pdf[0].has_vector
    assert not pdf[0].has_text


def test_ocr_detection(resources):
    filename = resources / 'graph_ocred.pdf'
    pdf = pdfinfo.PdfInfo(filename)
    assert not pdf[0].has_vector
    assert pdf[0].has_text


@pytest.mark.parametrize(
    'testfile', ('truetype_font_nomapping.pdf', 'type3_font_nomapping.pdf')
)
def test_corrupt_font_detection(resources, testfile):
    filename = resources / testfile
    pdf = pdfinfo.PdfInfo(filename, detailed_analysis=True)
    assert pdf[0].has_corrupt_text


def test_stack_abuse():
    p = pikepdf.Pdf.new()

    stream = pikepdf.Stream(p, b'q ' * 35)
    with pytest.warns(UserWarning, match="overflowed"):
        _interpret_contents(stream)

    stream = pikepdf.Stream(p, b'q Q Q Q Q')
    with pytest.warns(UserWarning, match="underflowed"):
        _interpret_contents(stream)

    stream = pikepdf.Stream(p, b'q ' * 135)
    with pytest.warns(UserWarning), pytest.raises(RuntimeError):
        _interpret_contents(stream)


def test_pages_issue700(monkeypatch, resources):
    def get_no_pages(*args, **kwargs):
        return iter([])

    monkeypatch.setattr(PDFPage, 'get_pages', get_no_pages)

    with pytest.raises(InputFileError, match="pdfminer"):
        pi = pdfinfo.PdfInfo(
            resources / 'cardinal.pdf',
            detailed_analysis=True,
            progbar=False,
            max_workers=1,
        )
        pi._miner_state.get_page_analysis(0)


@pytest.fixture
def image_scale0(resources, outpdf):
    with pikepdf.open(resources / 'cmyk.pdf') as cmyk:
        xobj = cmyk.pages[0].as_form_xobject()

        p = pikepdf.Pdf.new()
        p.add_blank_page(page_size=(72, 72))
        objname = p.pages[0].add_resource(
            p.copy_foreign(xobj), pikepdf.Name.XObject, pikepdf.Name.Im0
        )
        print(objname)
        p.pages[0].Contents = pikepdf.Stream(
            p, b"q 0 0 0 0 0 0 cm %s Do Q" % bytes(objname)
        )
        p.save(outpdf)
    return outpdf


def test_image_scale0(image_scale0):
    pi = pdfinfo.PdfInfo(
        image_scale0, detailed_analysis=True, progbar=False, max_workers=1
    )
    assert not pi.pages[0]._images[0].dpi.is_finite
    assert pi.pages[0].dpi == Resolution(0, 0)


def test_ink_enum_is_picklable():
    # ImageInfo crosses the worker-process boundary, so Ink must pickle.
    for member in (Ink.mono, Ink.gray, Ink.color):
        assert pickle.loads(pickle.dumps(member)) is member


def test_pngmonod_device_exists():
    from ocrmypdf.pluginspec import GhostscriptRasterDevice

    assert GhostscriptRasterDevice.PNGMONOD == 'pngmonod'
    # PNGMONO retained for compatibility / explicit use
    assert GhostscriptRasterDevice.PNGMONO == 'pngmono'


def _ink_of_first_xobject(body: bytes):
    from ocrmypdf.pdfinfo._contentstream import _interpret_contents

    p = pikepdf.Pdf.new()
    stream = pikepdf.Stream(p, body)
    info = _interpret_contents(stream)
    return info.xobject_settings[0].fill_ink


@pytest.mark.parametrize(
    "body, expected",
    [
        (b"/Im0 Do", 'mono'),  # default fill is black
        (b"0.263 0.263 0.263 rg /Im0 Do", 'gray'),
        (b"0.5 g /Im0 Do", 'gray'),
        (b"0 g /Im0 Do", 'mono'),
        (b"0.8 0.2 0.2 rg /Im0 Do", 'color'),
        (b"0 0 0 0.5 k /Im0 Do", 'gray'),
        (b"0.5 0.1 0 0 k /Im0 Do", 'color'),
    ],
)
def test_fill_ink_tracked_per_draw(body, expected):
    assert _ink_of_first_xobject(body) is Ink[expected]


def test_fill_ink_non_device_colorspace_is_color():
    # cs to a non-device colorspace then scn -> conservative color
    assert _ink_of_first_xobject(b"/CS0 cs 0.4 scn /Im0 Do") is Ink.color


def test_fill_ink_pattern_scn_is_color():
    assert _ink_of_first_xobject(b"/Pattern cs /P0 scn /Im0 Do") is Ink.color


def test_fill_ink_respects_graphics_stack():
    # Set red, save, set gray, restore -> red again at the Do
    assert _ink_of_first_xobject(b"0.8 0.1 0.1 rg q 0.5 g Q /Im0 Do") is Ink.color


@pytest.mark.parametrize(
    "body",
    [
        b"g /Im0 Do",  # g with no operand
        b"/Foo g /Im0 Do",  # g with a non-numeric operand
        b"cs /Im0 Do",  # cs with no operand
        b"0.5 /Foo k /Im0 Do",  # k with a non-numeric operand
        b"/DeviceRGB cs /Foo 0.5 scn /Im0 Do",  # scn with mixed bad operands
    ],
)
def test_fill_ink_tolerates_malformed_color_operands(body):
    # Malformed color operators must not crash the interpreter; they leave the
    # fill state at its prior value (default mono) or fall back conservatively.
    assert _ink_of_first_xobject(body) in (Ink.mono, Ink.color)


@pytest.mark.parametrize(
    "space, comps, expected",
    [
        ('gray', [0.0], 'mono'),
        ('gray', [0.263], 'gray'),
        ('gray', [1.0], 'gray'),  # white -> gray (harmless)
        ('rgb', [0.0, 0.0, 0.0], 'mono'),
        ('rgb', [0.263, 0.263, 0.263], 'gray'),
        ('rgb', [0.8, 0.2, 0.2], 'color'),
        ('rgb', [1.0, 1.0, 1.0], 'gray'),
        ('cmyk', [0.0, 0.0, 0.0, 0.0], 'mono'),  # white
        ('cmyk', [0.0, 0.0, 0.0, 0.5], 'gray'),
        ('cmyk', [0.5, 0.1, 0.0, 0.0], 'color'),
        ('unknown', [0.5], 'color'),  # conservative fallback
    ],
)
def test_ink_from_components(space, comps, expected):
    assert _ink_from_components(space, comps) is Ink[expected]


def _make_image_mask_pdf(path, content_fill: bytes):
    """Build a 1-page PDF with one 8x8 image mask painted with content_fill.

    content_fill is the color operator sequence emitted before drawing the
    mask, e.g. b"0.263 0.263 0.263 rg".
    """
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(72, 72))
    # 8x8 1-bpc mask, each row padded to a byte (1 byte per row).
    mask_bytes = bytes([0x7E] * 8)
    mask = pikepdf.Stream(pdf, mask_bytes)
    mask.Type = pikepdf.Name.XObject
    mask.Subtype = pikepdf.Name.Image
    mask.Width = 8
    mask.Height = 8
    mask.ImageMask = True
    mask.BitsPerComponent = 1
    name = pdf.pages[0].add_resource(mask, pikepdf.Name.XObject)
    pdf.pages[0].Contents = pikepdf.Stream(
        pdf, b"q 72 0 0 72 0 0 cm %s %s Do Q" % (content_fill, bytes(name))
    )
    pdf.save(path)
    return path


@pytest.fixture
def mask_gray_pdf(outdir):
    return _make_image_mask_pdf(outdir / 'mask_gray.pdf', b"0.263 0.263 0.263 rg")


@pytest.fixture
def mask_rgb_pdf(outdir):
    return _make_image_mask_pdf(outdir / 'mask_rgb.pdf', b"0.8 0.2 0.2 rg")


@pytest.fixture
def mask_black_pdf(outdir):
    return _make_image_mask_pdf(outdir / 'mask_black.pdf', b"0 g")


def test_imageinfo_ink_gray(mask_gray_pdf):
    image = pdfinfo.PdfInfo(mask_gray_pdf)[0].images[0]
    assert image.type_ == 'stencil'
    assert image.ink is Ink.gray


def test_imageinfo_ink_color(mask_rgb_pdf):
    image = pdfinfo.PdfInfo(mask_rgb_pdf)[0].images[0]
    assert image.ink is Ink.color


def test_imageinfo_ink_black(mask_black_pdf):
    image = pdfinfo.PdfInfo(mask_black_pdf)[0].images[0]
    assert image.ink is Ink.mono


def test_imageinfo_ink_none_for_regular_image(eight_by_eight_regular_image):
    image = pdfinfo.PdfInfo(eight_by_eight_regular_image)[0].images[0]
    assert image.ink is None


def test_fill_ink_cs_resets_color_to_black():
    # `cs` resets the fill color to the colorspace's initial value (black),
    # so a stale color set before `cs` must not leak to the drawn mask.
    assert _ink_of_first_xobject(b"0.8 0.2 0.2 rg /DeviceGray cs /Im0 Do") is Ink.mono


def test_nondict_xobject_tolerated(outdir):
    # A malformed PDF may store a non-dictionary object (here an Array) at
    # /Resources /XObject. Scanning for images must tolerate this rather than
    # crash on .items(); OCRmyPDF's domain is messy machine-generated PDFs.
    # Same robustness class as the pdfa.py find_nonembedded_cid_fonts fix.
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page(page_size=(612, 792))
    page.Resources = pikepdf.Dictionary(
        Font=pikepdf.Array([]), XObject=pikepdf.Array([])
    )
    out = outdir / 'malformed_xobj.pdf'
    pdf.save(out)

    info = pdfinfo.PdfInfo(out)
    assert len(info) == 1
    assert len(info[0].images) == 0


@pytest.mark.parametrize(
    'resources',
    [
        pikepdf.Array([]),  # non-dict /Resources
        pikepdf.Name.Foo,  # non-dict /Resources (name)
        pikepdf.Dictionary(XObject=pikepdf.Array([])),  # non-dict /XObject
        pikepdf.Dictionary(XObject=pikepdf.Name.Foo),  # non-dict /XObject (name)
    ],
)
def test_image_scanners_tolerate_nondict_resources(resources):
    # Exercise the image scanners directly on an in-memory container whose
    # /Resources or /Resources /XObject is not a dictionary. (pikepdf
    # normalizes a non-dict /Resources assigned to a page on save, so these
    # cases must be built in memory to reach the scanner unmodified.)
    from ocrmypdf.pdfinfo._contentstream import ContentsInfo
    from ocrmypdf.pdfinfo._image import _find_form_xobject_images, _image_xobjects

    container = pikepdf.Dictionary(Type=pikepdf.Name.Page, Resources=resources)
    empty = ContentsInfo(
        xobject_settings=[],
        inline_images=[],
        found_vector=False,
        found_text=False,
        name_index={},
    )
    pdf = pikepdf.Pdf.new()

    assert list(_image_xobjects(container)) == []
    assert list(_find_form_xobject_images(pdf, container, empty)) == []


def test_imageinfo_ink_inherited_in_form_xobject(outdir):
    # A mask drawn inside a Form XObject inherits the fill color set before the
    # Do that paints the form; the gray classification must reach the mask.
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(72, 72))

    mask = pikepdf.Stream(pdf, bytes([0x7E] * 8))
    mask.Type = pikepdf.Name.XObject
    mask.Subtype = pikepdf.Name.Image
    mask.Width = 8
    mask.Height = 8
    mask.ImageMask = True
    mask.BitsPerComponent = 1

    # Form draws the mask with no color of its own, inheriting the caller's.
    form = pikepdf.Stream(pdf, b"q 72 0 0 72 0 0 cm /Im0 Do Q")
    form.Type = pikepdf.Name.XObject
    form.Subtype = pikepdf.Name.Form
    form.BBox = [0, 0, 72, 72]
    form.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im0=mask))

    fname = pdf.pages[0].add_resource(form, pikepdf.Name.XObject)
    pdf.pages[0].Contents = pikepdf.Stream(
        pdf, b"0.263 0.263 0.263 rg %s Do" % bytes(fname)
    )
    out = outdir / 'form_mask.pdf'
    pdf.save(out)

    image = pdfinfo.PdfInfo(out)[0].images[0]
    assert image.type_ == 'stencil'
    assert image.ink is Ink.gray


def test_malformed_number_token_issue1054():
    """A malformed number in a content stream must not abort the scan.

    Some PDF producers emit broken real numbers such as ``0.000-50131235``.
    qpdf parses such a token as an operator, which steals the operands of the
    operator that follows, leaving e.g. ``cm`` with the wrong operand count.
    Viewers tolerate this, so we warn and ignore the operator rather than
    declaring the whole file unreadable.
    """
    p = pikepdf.Pdf.new()

    stream = pikepdf.Stream(
        p, b'q 381 0 0 381 0 0 cm q 1.0 0 0 1.0 0 0.000-50131235 cm /Im0 Do Q Q'
    )
    with pytest.warns(UserWarning, match="malformed"):
        info = _interpret_contents(stream)
    # The outer cm survives; the inner malformed one is ignored
    assert len(info.xobject_settings) == 1
    assert info.xobject_settings[0].shorthand == (381, 0, 0, 381, 0, 0)


@pytest.mark.parametrize('conversion_mode', ['explicit', 'implicit'])
def test_cm_with_non_numeric_operand(conversion_mode):
    """A ``cm`` with six operands, one of them not a number, is ignored."""
    p = pikepdf.Pdf.new(conversion_mode=conversion_mode)

    stream = pikepdf.Stream(p, b'q 381 0 0 381 0 0 cm q 1 0 0 /Oops 0 0 cm /Im0 Do Q Q')
    with pytest.warns(UserWarning, match="malformed"):
        info = _interpret_contents(stream)
    assert len(info.xobject_settings) == 1
    assert info.xobject_settings[0].shorthand == (381, 0, 0, 381, 0, 0)


def test_do_without_operand():
    """A ``Do`` whose name operand was stolen must not raise."""
    p = pikepdf.Pdf.new()

    stream = pikepdf.Stream(p, b'q 1 0 0 1 0 0 cm 0.0-1 Do Q')
    with pytest.warns(UserWarning, match="malformed"):
        info = _interpret_contents(stream)
    assert info.xobject_settings == []


def _text_stream(body: bytes, basefont=None, conversion_mode='implicit'):
    """Build a content stream whose /F1 font has the given BaseFont.

    Returns the owning Pdf too, which must be kept alive while the stream is used.
    """
    p = pikepdf.Pdf.new(conversion_mode=conversion_mode)
    stream = pikepdf.Stream(p, body)
    if basefont is not None:
        if isinstance(basefont, str):
            basefont = pikepdf.Name(basefont)
        font = pikepdf.Dictionary(
            Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type0, BaseFont=basefont
        )
        stream.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
    return p, stream


@pytest.mark.parametrize('conversion_mode', ['explicit', 'implicit'])
@pytest.mark.parametrize(
    'body, visible',
    [
        (b'BT /F1 12 Tf (Hi) Tj ET', True),
        (b'BT 0 Tr /F1 12 Tf (Hi) Tj ET', True),
        (b'BT 3 Tr /F1 12 Tf (Hi) Tj ET', False),
        (b'BT 7 Tr /F1 12 Tf (Hi) Tj ET', False),
        (b'BT 3 Tr /F1 12 Tf [(Hi)] TJ (x) \' 1 2 (y) " ET', False),
        # Text render mode persists across BT/ET
        (b'3 Tr BT /F1 12 Tf (Hi) Tj ET BT (Hi) Tj ET', False),
        # ...but is restored by Q
        (b'q 3 Tr BT /F1 12 Tf (Hi) Tj ET Q BT /F1 12 Tf (Hi) Tj ET', True),
        (b'q 3 Tr Q BT /F1 12 Tf (Hi) Tj ET', True),
        # Visible text after invisible text in the same block
        (b'BT 3 Tr /F1 12 Tf (Hi) Tj 0 Tr (Hi) Tj ET', True),
    ],
)
def test_text_render_mode_visibility(body, visible, conversion_mode):
    _pdf, stream = _text_stream(body, '/Helvetica', conversion_mode=conversion_mode)
    info = _interpret_contents(stream)
    assert info.found_text
    assert info.found_visible_text is visible


@pytest.mark.parametrize(
    'basefont, visible',
    [
        ('/GlyphLessFont', False),
        ('/PGGPHE+GlyphLessFont', False),
        ('/glyphlessfont', False),
        ('/Occulta', False),
        ('/MPDFAA+Occulta-Regular', False),
        ('/Helvetica', True),
        ('/MPDFAA+NotoSans', True),
        ('/pggphe+GlyphLessFont', True),  # not a subset prefix
        ('/GlyphLessFontX', True),
    ],
)
def test_glyphless_font_visibility(basefont, visible):
    _pdf, stream = _text_stream(b'BT /F1 12 Tf (Hi) Tj ET', basefont)
    info = _interpret_contents(stream)
    assert info.found_text
    assert info.found_visible_text is visible


def test_glyphless_font_then_real_font():
    _pdf, stream = _text_stream(
        b'BT /F1 12 Tf (Hi) Tj /F2 12 Tf (Hi) Tj ET', '/GlyphLessFont'
    )
    stream.Resources.Font.F2 = pikepdf.Dictionary(
        Type=pikepdf.Name.Font,
        Subtype=pikepdf.Name.Type1,
        BaseFont=pikepdf.Name.Helvetica,
    )
    assert _interpret_contents(stream).found_visible_text


def test_glyphless_font_restored_by_q():
    _pdf, stream = _text_stream(
        b'BT /F2 12 Tf ET q BT /F1 12 Tf (Hi) Tj ET Q BT (Hi) Tj ET', '/GlyphLessFont'
    )
    stream.Resources.Font.F2 = pikepdf.Dictionary(
        Type=pikepdf.Name.Font,
        Subtype=pikepdf.Name.Type1,
        BaseFont=pikepdf.Name.Helvetica,
    )
    assert _interpret_contents(stream).found_visible_text


def test_glyphless_font_inherited_from_page_tree():
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page()
    del page.obj.Resources
    font = pikepdf.Dictionary(
        Type=pikepdf.Name.Font,
        Subtype=pikepdf.Name.Type0,
        BaseFont=pikepdf.Name('/GlyphLessFont'),
    )
    pdf.Root.Pages.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
    page.Contents = pikepdf.Stream(pdf, b'BT /F1 12 Tf (Hi) Tj ET')
    info = _interpret_contents(page.obj)
    assert info.found_text
    assert not info.found_visible_text


def test_non_utf8_font_name_does_not_crash():
    gbk_name = pikepdf.Object.parse(b'/#b7#bd#d5#fd#b4#f3#ba#da_GBK+ZEFSzV-12')
    _pdf, stream = _text_stream(b'BT /F1 12 Tf (Hi) Tj ET', gbk_name)
    info = _interpret_contents(stream)
    assert info.found_visible_text


@pytest.mark.parametrize(
    'resources',
    [
        None,
        pikepdf.Array([]),
        pikepdf.Dictionary(Font=pikepdf.Array([])),
        pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=pikepdf.Array([]))),
        pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=pikepdf.Dictionary())),
        pikepdf.Dictionary(
            Font=pikepdf.Dictionary(F1=pikepdf.Dictionary(BaseFont=pikepdf.Array([])))
        ),
    ],
)
def test_malformed_font_resources_count_as_visible(resources):
    _pdf, stream = _text_stream(b'BT /F1 12 Tf (Hi) Tj ET')
    if resources is not None:
        stream.Resources = resources
    info = _interpret_contents(stream)
    assert info.found_text
    assert info.found_visible_text


@pytest.mark.parametrize(
    'body',
    [
        b'BT /Tr Tr (Hi) Tj ET',
        b'BT Tr (Hi) Tj ET',
        b'BT Tf (Hi) Tj ET',
        b'BT 3.5 Tr (Hi) Tj ET',
    ],
)
def test_malformed_text_state_operators(body):
    # Malformed operands leave the text state unchanged rather than raising
    _pdf, stream = _text_stream(body, '/Helvetica')
    info = _interpret_contents(stream)
    assert info.found_text
    assert info.found_visible_text


def _invisible_ocr_layer_pdf(path, *, in_form: bool, tr_in_form: bool = True):
    """A 150 dpi scan with an invisible (3 Tr) text layer, like prior OCR."""
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page(page_size=(72, 72))
    im = Image.new('L', (150, 150), 128)
    image = pikepdf.Stream(pdf, im.tobytes())
    image.Type = pikepdf.Name.XObject
    image.Subtype = pikepdf.Name.Image
    image.Width, image.Height = 150, 150
    image.ColorSpace = pikepdf.Name.DeviceGray
    image.BitsPerComponent = 8
    font = pikepdf.Dictionary(
        Type=pikepdf.Name.Font,
        Subtype=pikepdf.Name.Type1,
        BaseFont=pikepdf.Name.Helvetica,
    )
    page.Resources = pikepdf.Dictionary(
        XObject=pikepdf.Dictionary(Im0=image), Font=pikepdf.Dictionary(F1=font)
    )
    text = b'BT %s/F1 12 Tf 10 10 Td (Hello) Tj ET' % (b'3 Tr ' if tr_in_form else b'')
    if in_form:
        form = pikepdf.Stream(pdf, text)
        form.Type = pikepdf.Name.XObject
        form.Subtype = pikepdf.Name.Form
        form.BBox = [0, 0, 72, 72]
        form.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
        page.Resources.XObject.Fx0 = form
        prefix = b'' if tr_in_form else b'3 Tr '
        text = prefix + b'q /Fx0 Do Q'
    page.Contents = pikepdf.Stream(pdf, b'q 72 0 0 72 0 0 cm /Im0 Do Q ' + text)
    pdf.save(path)
    return path


@pytest.mark.parametrize(
    'in_form, tr_in_form', [(False, True), (True, True), (True, False)]
)
def test_pageinfo_invisible_text(outdir, in_form, tr_in_form):
    path = _invisible_ocr_layer_pdf(
        outdir / 'invisible.pdf', in_form=in_form, tr_in_form=tr_in_form
    )
    page = pdfinfo.PdfInfo(path)[0]
    assert page.has_text
    assert not page.has_visible_text
    assert page.dpi == Resolution(150, 150)
    # PageInfo crosses the worker-process boundary
    assert not pickle.loads(pickle.dumps(page)).has_visible_text


def test_pageinfo_visible_text(single_page_text):
    page = pdfinfo.PdfInfo(single_page_text)[0]
    assert page.has_text
    assert page.has_visible_text
