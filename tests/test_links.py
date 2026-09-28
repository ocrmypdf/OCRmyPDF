# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests that hyperlinks (Link annotations) survive OCR."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import img2pdf
import pikepdf
import pypdfium2 as pdfium
import pytest
from pikepdf import Array, Dictionary, Name, Pdf, String
from PIL import Image, ImageDraw

import ocrmypdf
from ocrmypdf._options import ProcessingMode
from ocrmypdf.cli import get_options_and_plugins

from .conftest import check_ocrmypdf

URI = 'https://ocrmypdf.readthedocs.io/'

# Page image: 300x200 px at 100 dpi, so the page is 216x144 pt
IMAGE_SIZE = (300, 200)
IMAGE_DPI = 100
# A black square on the page image, in pixels (left, top, right, bottom)
SQUARE_PX = (30, 30, 90, 70)


def _page_image() -> bytes:
    im = Image.new('L', IMAGE_SIZE, 255)
    ImageDraw.Draw(im).rectangle(SQUARE_PX, fill=0)
    bio = BytesIO()
    im.save(bio, format='PNG', dpi=(IMAGE_DPI, IMAGE_DPI))
    return bio.getvalue()


def _square_rect_pt() -> list[float]:
    """The black square in PDF user space of an unrotated page at the origin."""
    scale = 72 / IMAGE_DPI
    left, top, right, bottom = SQUARE_PX
    height = IMAGE_SIZE[1]
    return [
        left * scale,
        (height - bottom) * scale,
        right * scale,
        (height - top) * scale,
    ]


def _link(pdf: Pdf, rect, **kwargs) -> Dictionary:
    """A Link annotation without /F, as many PDF producers write them."""
    return pdf.make_indirect(
        Dictionary(
            Type=Name.Annot,
            Subtype=Name.Link,
            Rect=Array(rect),
            Border=Array([0, 0, 0]),
            **kwargs,
        )
    )


def _make_linked_pdf(path: Path, *, origin=(0, 0), rotate=0) -> Path:
    """Two image-only pages; page 1 links to page 2 three ways and to a URI."""
    image = _page_image()
    pdf = Pdf.open(BytesIO(img2pdf.convert([image, image])))
    ox, oy = origin
    if origin != (0, 0) or rotate:
        for page in pdf.pages:
            mediabox = [float(v) for v in page.MediaBox]
            page.MediaBox = Array(
                [ox, oy, mediabox[2] + ox, mediabox[3] + oy],
            )
            # Shift the content to follow the MediaBox
            page.contents_add(
                pdf.make_stream(f'1 0 0 1 {ox} {oy} cm'.encode()), prepend=True
            )
            if rotate:
                page.Rotate = rotate
    page2 = pdf.pages[1].obj
    square = _square_rect_pt()
    square = [square[0] + ox, square[1] + oy, square[2] + ox, square[3] + oy]
    pdf.pages[0].Annots = pdf.make_indirect(
        Array(
            [
                _link(pdf, square, Dest=Array([page2, Name.Fit])),
                _link(
                    pdf,
                    [ox + 100, oy + 10, ox + 140, oy + 30],
                    A=Dictionary(
                        S=Name.GoTo, D=Array([page2, Name.XYZ, ox, oy + 144, 0])
                    ),
                ),
                _link(
                    pdf,
                    [ox + 150, oy + 10, ox + 200, oy + 30],
                    A=Dictionary(S=Name.URI, URI=String(URI)),
                ),
                pdf.make_indirect(
                    Dictionary(
                        Type=Name.Annot,
                        Subtype=Name.Text,
                        Rect=Array([ox + 10, oy + 100, ox + 30, oy + 120]),
                        Contents=String('a note'),
                        F=4,
                    )
                ),
            ]
        )
    )
    pdf.save(path)
    return path


@pytest.fixture
def linked_pdf(tmp_path) -> Path:
    return _make_linked_pdf(tmp_path / 'linked.pdf')


def _links(page: pikepdf.Page) -> list[Dictionary]:
    return [
        annot
        for annot in page.obj.get(Name.Annots, Array())
        if annot.get(Name.Subtype) == Name.Link
    ]


def _destination(link: Dictionary) -> Array:
    """The explicit destination of a link, whether in /Dest or a GoTo action.

    Ghostscript rewrites a GoTo action to an explicit destination as /Dest.
    """
    if Name.Dest in link:
        return link.Dest
    assert Name.GoTo == link.A.S
    return link.A.D


def _check_links_intact(outpdf: Path) -> None:
    with Pdf.open(outpdf) as pdf:
        links = _links(pdf.pages[0])
        assert len(links) == 3
        page2 = pdf.pages[1].obj
        dest_link, goto_link, uri_link = links
        assert _destination(dest_link)[0].objgen == page2.objgen
        assert _destination(dest_link)[1] == Name.Fit
        assert _destination(goto_link)[0].objgen == page2.objgen
        assert _destination(goto_link)[1] == Name.XYZ
        assert str(uri_link.A.URI) == URI


def test_ghostscript_pdfa_keeps_links(linked_pdf, outpdf):
    """Ghostscript drops annotations without the Print flag from PDF/A."""
    check_ocrmypdf(
        linked_pdf,
        outpdf,
        '--skip-text',
        '--ocr-engine',
        'none',
        '--output-type',
        'pdfa',
        '--pdfa-backend',
        'ghostscript',
    )
    _check_links_intact(outpdf)
    with Pdf.open(outpdf) as pdf:
        for annot in pdf.pages[0].Annots:
            assert int(annot.F) & 4, "PDF/A requires the Print flag"


def _add_hidden_annotation(path: Path, *, unsupported_by_validator: bool) -> None:
    """Add a hidden Text annotation to page 1, which PDF/A does not permit."""
    with Pdf.open(path, allow_overwriting_input=True) as pdf:
        pdf.pages[0].Annots.append(
            pdf.make_indirect(
                Dictionary(
                    Type=Name.Annot,
                    Subtype=Name.Text,
                    Rect=Array([40, 100, 60, 120]),
                    Contents=String('a hidden note'),
                    F=2,
                )
            )
        )
        if unsupported_by_validator:
            # pikepdf's validator does not check optional content, so
            # speculative conversion is rejected and Ghostscript is used
            ocg = pdf.make_indirect(Dictionary(Type=Name.OCG, Name=String('Layer')))
            pdf.Root.OCProperties = Dictionary(
                OCGs=Array([ocg]), D=Dictionary(ON=Array([ocg]))
            )
        pdf.save(path)


def _hidden_annotation_warnings(caplog) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.levelno == logging.WARNING and 'hidden or not viewable' in r.getMessage()
    ]


@pytest.mark.parametrize(
    'pdfa_backend, unsupported_by_validator',
    [('ghostscript', False), ('auto', True)],
    ids=['ghostscript', 'auto-rejected'],
)
def test_ghostscript_pdfa_removes_hidden_annotations(
    linked_pdf, outpdf, caplog, pdfa_backend, unsupported_by_validator
):
    """Hidden annotations are removed once, and reported once, on every path."""
    _add_hidden_annotation(
        linked_pdf, unsupported_by_validator=unsupported_by_validator
    )
    with caplog.at_level(logging.INFO, logger='ocrmypdf'):
        check_ocrmypdf(
            linked_pdf,
            outpdf,
            '--skip-text',
            '--ocr-engine',
            'none',
            '--output-type',
            'pdfa',
            '--pdfa-backend',
            pdfa_backend,
        )
    _check_links_intact(outpdf)
    with Pdf.open(outpdf) as pdf:
        contents = [str(annot.get(Name.Contents, '')) for annot in pdf.pages[0].Annots]
        assert 'a hidden note' not in contents
        assert 'a note' in contents
    if unsupported_by_validator:
        assert 'conversion was not used' in caplog.text
    warnings = _hidden_annotation_warnings(caplog)
    assert len(warnings) == 1, caplog.text
    assert '1 annotation (1 Text) on page 1' in warnings[0]


@pytest.mark.parametrize('mode_args', [('--force-ocr',), ('--mode', 'force')])
def test_force_ocr_keeps_links(linked_pdf, outpdf, mode_args):
    check_ocrmypdf(
        linked_pdf,
        outpdf,
        *mode_args,
        '--ocr-engine',
        'none',
        '--output-type',
        'pdf',
    )
    _check_links_intact(outpdf)
    with Pdf.open(outpdf) as pdf:
        subtypes = [annot.Subtype for annot in pdf.pages[0].Annots]
        assert Name.Text not in subtypes, "other annotations are rasterized"


def test_force_ocr_no_links_drops_links(linked_pdf, outpdf):
    check_ocrmypdf(
        linked_pdf,
        outpdf,
        '--mode',
        'force-ocr-no-links',
        '--ocr-engine',
        'none',
        '--output-type',
        'pdf',
    )
    with Pdf.open(outpdf) as pdf:
        assert Name.Annots not in pdf.pages[0].obj
        assert len(pdf.pages) == 2


def _pixel_under_rect_center(pdf_path: Path, rect, origin=(0, 0)) -> int:
    """Render unrotated page 1 and return the gray level at the center of rect."""
    doc = pdfium.PdfDocument(str(pdf_path))
    try:
        page = doc[0]
        _width, height = page.get_size()
        scale = 2
        bitmap = page.render(scale=scale, grayscale=True)
        im = bitmap.to_pil().convert('L')
        cx = (float(rect[0]) + float(rect[2])) / 2 - origin[0]
        cy = (float(rect[1]) + float(rect[3])) / 2 - origin[1]
        return im.getpixel((int(cx * scale), int((height - cy) * scale)))
    finally:
        doc.close()


@pytest.mark.parametrize('rotate', [0, 90, 180, 270])
def test_force_ocr_link_follows_content(tmp_path, outpdf, rotate):
    """A kept link must still cover the content it covered before rasterizing."""
    infile = _make_linked_pdf(tmp_path / 'in.pdf', origin=(50, 70), rotate=rotate)
    with Pdf.open(infile) as pdf:
        before = _links(pdf.pages[0])[0].Rect
    if rotate == 0:
        # Checks the fixture; the pixel lookup assumes an unrotated page
        assert _pixel_under_rect_center(infile, before, origin=(50, 70)) < 64

    check_ocrmypdf(
        infile, outpdf, '--force-ocr', '--ocr-engine', 'none', '--output-type', 'pdf'
    )
    with Pdf.open(outpdf) as pdf:
        page = pdf.pages[0]
        after = _links(page)[0].Rect
        mediabox = [float(v) for v in page.MediaBox]
        assert mediabox[0] == 0 and mediabox[1] == 0
    assert _pixel_under_rect_center(outpdf, after) < 64


def test_force_ocr_no_links_mode_options(tmp_path):
    options, _ = get_options_and_plugins(
        ['--mode', 'force-ocr-no-links', 'in.pdf', 'out.pdf']
    )
    assert options.mode == ProcessingMode.force_ocr_no_links
    assert options.force_ocr
    assert options.is_force_mode
    assert not options.lossless_reconstruction


def test_force_mode_options():
    options, _ = get_options_and_plugins(['-f', 'in.pdf', 'out.pdf'])
    assert options.mode == ProcessingMode.force
    assert options.force_ocr
    assert options.is_force_mode


def test_api_force_ocr_no_links(linked_pdf, outpdf):
    ocrmypdf.ocr(
        linked_pdf,
        outpdf,
        mode='force-ocr-no-links',
        ocr_engine='none',
        output_type='pdf',
    )
    with Pdf.open(outpdf) as pdf:
        assert Name.Annots not in pdf.pages[0].obj


def test_discard_structure_tree_clears_annotation_struct_parent(resources):
    from ocrmypdf._graft import discard_structure_tree

    with Pdf.open(resources / 'link.pdf') as pdf:
        pdf.Root.StructTreeRoot = pdf.make_indirect(
            Dictionary(Type=Name.StructTreeRoot)
        )
        annot = pdf.pages[0].Annots[0]
        annot.StructParent = 1
        assert discard_structure_tree(pdf)
        assert Name.StructParent not in annot
