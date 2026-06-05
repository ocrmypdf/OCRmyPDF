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


def test_jpeg(resources):
    filename = resources / 'c02-22.pdf'

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
