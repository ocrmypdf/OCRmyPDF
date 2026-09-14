# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tolerance for PDFs that store the wrong type at a structural key.

Every scan in OCRmyPDF walks paths like ``/Resources /XObject`` or
``/Root /AcroForm /SigFlags`` through files it did not write. A malformed
producer may put an array, a name, or nothing at all at any step, and none of
those may abort the run: the answer is "no XObjects", not a traceback. These
tests pin that down for each traversal, since the well-formed fixtures in the
rest of the suite exercise none of it.
"""

from __future__ import annotations

from decimal import Decimal

import pikepdf
import pytest
from pikepdf import Array, Dictionary, Name, NamePath, Stream

from ocrmypdf import helpers
from ocrmypdf._annots import remove_broken_goto_annotations
from ocrmypdf._graft import discard_text_search_index
from ocrmypdf.builtin_plugins.ghostscript import _collect_dctdecode_images
from ocrmypdf.optimize import extract_image_filter
from ocrmypdf.pdfa import find_nonembedded_cid_fonts
from ocrmypdf.pdfinfo import PdfInfo

#: Values a malformed PDF may store where a dictionary or number belongs.
WRONG_TYPES = [
    pytest.param(Array([1, 2]), id='array'),
    pytest.param(Name.Nope, id='name'),
    pytest.param(pikepdf.String('nope'), id='string'),
    pytest.param(42, id='integer'),
]

#: The subset that is not a number either, for keys that hold a number.
NON_NUMERIC_TYPES = WRONG_TYPES[:3]


def _empty_name_tree(pdf) -> None:
    """Give *pdf* a valid but empty /Names /Dests tree.

    pikepdf's NameTree requires the dictionary it wraps to be owned by the Pdf,
    so both levels have to be indirect objects.
    """
    pdf.Root[Name.Names] = pdf.make_indirect(
        Dictionary(Dests=pdf.make_indirect(Dictionary(Names=Array([]))))
    )


@pytest.fixture
def blank_pdf():
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(200, 200))
    return pdf


class TestAccessors:
    """The scalar accessors reach pikepdf's safe accessors via explicit mode."""

    @pytest.mark.parametrize(
        'value, expected',
        [
            (7, 7),
            (pikepdf.Object.parse(b'7'), 7),
            (Decimal('3.9'), 3),  # a Real under an integer key truncates
            (True, 1),
            (pikepdf.String('7'), 99),  # a number written as a string is not one
            (Name.Seven, 99),
            (Array([7]), 99),
            (None, 99),  # key absent
        ],
    )
    def test_get_int(self, value, expected):
        d = Dictionary()
        if value is not None:
            d[Name.K] = value
        assert helpers.pikepdf_get_int(d, Name.K, 99) == expected

    @pytest.mark.parametrize(
        'value, expected',
        [
            (True, True),
            (False, False),
            (1, True),  # malformed producers store flags as 0/1
            (0, False),
            (pikepdf.Object.parse(b'true'), True),
            (pikepdf.String('true'), False),
            (Array([1]), False),
            (None, False),
        ],
    )
    def test_get_bool(self, value, expected):
        d = Dictionary()
        if value is not None:
            d[Name.K] = value
        assert helpers.pikepdf_get_bool(d, Name.K, False) is expected

    @pytest.mark.parametrize(
        'value, expected',
        [
            (Decimal('1.5'), Decimal('1.5')),
            (3, Decimal(3)),
            (Name.Nope, Decimal(9)),
            (None, Decimal(9)),
        ],
    )
    def test_get_decimal(self, value, expected):
        d = Dictionary()
        if value is not None:
            d[Name.K] = value
        assert helpers.pikepdf_get_decimal(d, Name.K, Decimal(9)) == expected

    def test_get_decimal_keeps_written_digits(self):
        """A Real must not round-trip through binary float."""
        d = Dictionary()
        d[Name.K] = Decimal('0.1')
        assert helpers.pikepdf_get_decimal(d, Name.K) == Decimal('0.1')

    def test_accessors_take_a_namepath(self):
        d = Dictionary(A=Dictionary(B=5))
        assert helpers.pikepdf_get_int(d, NamePath.A.B, 0) == 5
        assert helpers.pikepdf_get_int(d, NamePath.A.Missing, 0) == 0
        assert helpers.pikepdf_get_int(d, NamePath.Missing.B, 0) == 0

    def test_conversion_mode_is_restored(self):
        """The helper must not leave the thread in explicit mode.

        Explicit mode silently changes isinstance(x, int) and raises on bool()
        and ordering comparisons, so leaking it out of a lookup would break
        unrelated code running on the same thread.
        """
        before = pikepdf.get_object_conversion_mode()
        helpers.pikepdf_get_int(Dictionary(K=1), Name.K)
        assert pikepdf.get_object_conversion_mode() == before

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_get_dict_tolerates_wrong_type(self, wrong):
        d = Dictionary()
        d[Name.K] = wrong
        assert len(helpers.pikepdf_get_dict(d, Name.K)) == 0

    def test_get_dict_on_missing_key(self):
        assert len(helpers.pikepdf_get_dict(Dictionary(), Name.K)) == 0

    def test_get_dict_returns_the_dictionary(self):
        d = Dictionary(K=Dictionary(A=1))
        assert helpers.pikepdf_get_dict(d, Name.K)[Name.A] == 1

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_get_dict_tolerates_wrong_type_mid_path(self, wrong):
        d = Dictionary()
        d[Name.Resources] = wrong
        assert len(helpers.pikepdf_get_dict(d, helpers.RESOURCES_XOBJECT)) == 0


class TestMalformedResources:
    """/Resources or /Resources /XObject holding something that is not a dict."""

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_pdfinfo_scans_page(self, blank_pdf, outdir, wrong):
        blank_pdf.pages[0].obj[Name.Resources] = wrong
        target = outdir / 'bad_resources.pdf'
        blank_pdf.save(target)
        assert PdfInfo(target).pages[0].images == []

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_pdfinfo_scans_nested_xobject(self, blank_pdf, outdir, wrong):
        blank_pdf.pages[0].obj[Name.Resources] = Dictionary(XObject=wrong)
        target = outdir / 'bad_xobject.pdf'
        blank_pdf.save(target)
        assert PdfInfo(target).pages[0].images == []

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_ghostscript_jpeg_scan(self, blank_pdf, wrong):
        blank_pdf.pages[0].obj[Name.Resources] = Dictionary(XObject=wrong)
        assert _collect_dctdecode_images(blank_pdf) == {}

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_ghostscript_jpeg_scan_through_form(self, blank_pdf, wrong):
        form = blank_pdf.make_stream(b'', Subtype=Name.Form, Resources=wrong)
        blank_pdf.pages[0].obj[Name.Resources] = Dictionary(
            XObject=Dictionary(Fm0=form)
        )
        assert _collect_dctdecode_images(blank_pdf) == {}

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_pdfa_font_scan(self, blank_pdf, wrong):
        blank_pdf.pages[0].obj[Name.Resources] = Dictionary(Font=wrong)
        assert find_nonembedded_cid_fonts(blank_pdf) == set()

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_pdfa_font_scan_through_form(self, blank_pdf, wrong):
        form = blank_pdf.make_stream(b'', Subtype=Name.Form, Resources=wrong)
        blank_pdf.pages[0].obj[Name.Resources] = Dictionary(
            XObject=Dictionary(Fm0=form)
        )
        assert find_nonembedded_cid_fonts(blank_pdf) == set()

    def test_pdfa_font_descriptor_is_not_a_dict(self, blank_pdf):
        descendant = Dictionary(FontDescriptor=Array([1, 2]))
        font = Dictionary(
            Subtype=Name.Type0,
            BaseFont=Name.Broken,
            DescendantFonts=Array([descendant]),
        )
        blank_pdf.pages[0].obj[Name.Resources] = Dictionary(Font=Dictionary(F0=font))
        # No embedded FontFile is reachable, so the font blocks PDF/A.
        assert find_nonembedded_cid_fonts(blank_pdf) == {'Broken'}


class TestMalformedCatalog:
    """Catalog entries PdfInfo reads before any OCR work begins."""

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_acroform_is_not_a_dict(self, blank_pdf, outdir, wrong):
        blank_pdf.Root[Name.AcroForm] = wrong
        target = outdir / 'bad_acroform.pdf'
        blank_pdf.save(target)
        info = PdfInfo(target)
        assert info.has_acroform is False
        assert info.has_signature is False

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_markinfo_is_not_a_dict(self, blank_pdf, outdir, wrong):
        blank_pdf.Root[Name.MarkInfo] = wrong
        target = outdir / 'bad_markinfo.pdf'
        blank_pdf.save(target)
        assert PdfInfo(target).is_tagged is False

    def test_marked_written_as_an_integer(self, blank_pdf, outdir):
        """A /Marked stored as 1 rather than true still reads as tagged."""
        blank_pdf.Root[Name.MarkInfo] = blank_pdf.make_indirect(Dictionary(Marked=1))
        target = outdir / 'marked_int.pdf'
        blank_pdf.save(target)
        assert PdfInfo(target).is_tagged is True

    @pytest.mark.parametrize('wrong', NON_NUMERIC_TYPES)
    def test_userunit_is_not_a_number(self, blank_pdf, outdir, wrong):
        blank_pdf.pages[0].obj[Name.UserUnit] = wrong
        target = outdir / 'bad_userunit.pdf'
        blank_pdf.save(target)
        assert PdfInfo(target).pages[0].userunit == Decimal(1)

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_pieceinfo_is_not_a_dict(self, blank_pdf, wrong):
        blank_pdf.Root[Name.PieceInfo] = wrong
        assert discard_text_search_index(blank_pdf) is False

    def test_pieceinfo_search_index_is_discarded(self, blank_pdf):
        blank_pdf.Root[Name.PieceInfo] = blank_pdf.make_indirect(
            Dictionary(SearchIndex=Dictionary(Private=1))
        )
        assert discard_text_search_index(blank_pdf) is True
        assert Name.PieceInfo not in blank_pdf.Root


class TestMalformedAnnotations:
    """The named-destination cleanup walks /Names /Dests and /Annots /A /D."""

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_names_is_not_a_dict(self, blank_pdf, wrong):
        blank_pdf.Root[Name.Names] = wrong
        assert remove_broken_goto_annotations(blank_pdf) is False

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_dests_is_not_a_dict(self, blank_pdf, wrong):
        blank_pdf.Root[Name.Names] = blank_pdf.make_indirect(Dictionary(Dests=wrong))
        assert remove_broken_goto_annotations(blank_pdf) is False

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_annotation_action_is_not_a_dict(self, blank_pdf, wrong):
        _empty_name_tree(blank_pdf)
        annot = Dictionary(A=wrong)
        blank_pdf.pages[0].obj[Name.Annots] = Array([annot])
        assert remove_broken_goto_annotations(blank_pdf) is False

    def test_broken_destination_is_disabled(self, blank_pdf):
        _empty_name_tree(blank_pdf)
        annot = blank_pdf.make_indirect(
            Dictionary(A=Dictionary(D=pikepdf.String('nowhere')))
        )
        blank_pdf.pages[0].obj[Name.Annots] = Array([annot])
        assert remove_broken_goto_annotations(blank_pdf) is True
        assert Name.D not in annot[Name.A]


class TestMalformedImageStream:
    """Image dictionaries the optimizer inspects before transcoding."""

    def test_image_without_subtype(self, blank_pdf):
        image = Stream(blank_pdf, b'x' * 1000, Width=100, Height=100)
        assert extract_image_filter(image, 1) is None

    @pytest.mark.parametrize('wrong', NON_NUMERIC_TYPES)
    def test_image_dimensions_not_integers(self, blank_pdf, wrong):
        image = Stream(
            blank_pdf,
            b'x' * 1000,
            Subtype=Name.Image,
            Width=wrong,
            Height=wrong,
        )
        assert extract_image_filter(image, 1) is None

    @pytest.mark.parametrize('wrong', WRONG_TYPES)
    def test_smask_is_not_a_dict(self, blank_pdf, wrong):
        """A /SMask that is not a dictionary has no /Matte to worry about."""
        image = Stream(
            blank_pdf,
            b'x' * 1000,
            Subtype=Name.Image,
            Width=100,
            Height=100,
            SMask=wrong,
        )
        # Reaches the /SMask /Matte check without raising; an uncompressed
        # image is then skipped for want of a filter.
        assert extract_image_filter(image, 1) is None
