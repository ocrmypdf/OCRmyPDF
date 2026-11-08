# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pytest
from pikepdf import Array, Dictionary, Name, NameTree, Pdf, String

from ocrmypdf._annots import remove_broken_goto_annotations


def test_remove_broken_goto_annotations(resources):
    with Pdf.open(resources / 'link.pdf') as pdf:
        assert not remove_broken_goto_annotations(pdf), "File should not be modified"

        # Construct Dests nametree
        nt = NameTree.new(pdf)
        names = pdf.Root[Name.Names] = pdf.make_indirect(Dictionary())
        names[Name.Dests] = nt.obj
        # Create a broken named destination
        nt['Invalid'] = pdf.make_indirect(Dictionary())
        # Create a valid named destination
        nt['Valid'] = Array([pdf.pages[0].obj, Name.XYZ, 0, 0, 0])

        pdf.pages[0].Annots[0].A.D = 'Missing'
        pdf.pages[1].Annots[0].A.D = 'Valid'

        assert remove_broken_goto_annotations(pdf), "File should be modified"

        assert Name.D not in pdf.pages[0].Annots[0].A
        assert Name.D in pdf.pages[1].Annots[0].A


@pytest.fixture
def trivial(resources):
    """A one page PDF we can decorate with (broken) annotations."""
    with Pdf.open(resources / 'trivial.pdf') as pdf:
        yield pdf


def add_named_destinations(pdf: Pdf) -> None:
    """Give the PDF a valid, but empty, name tree of destinations."""
    nt = NameTree.new(pdf)
    names = pdf.Root[Name.Names] = pdf.make_indirect(Dictionary())
    names[Name.Dests] = nt.obj


def link_annot(pdf: Pdf, **kwargs) -> Dictionary:
    return pdf.make_indirect(
        Dictionary(Type=Name.Annot, Subtype=Name.Link, Rect=[0, 0, 10, 10], **kwargs)
    )


def test_no_names_in_root(trivial):
    """A PDF with no name tree at all has no named destinations to break."""
    assert Name.Names not in trivial.Root
    assert remove_broken_goto_annotations(trivial) is False


def test_names_without_dests(trivial):
    """A name tree that contains no destinations (only, say, EmbeddedFiles)."""
    trivial.Root[Name.Names] = trivial.make_indirect(
        Dictionary(EmbeddedFiles=trivial.make_indirect(Dictionary(Names=Array())))
    )
    assert remove_broken_goto_annotations(trivial) is False


@pytest.mark.parametrize(
    'dests',
    [Array([]), String('not a dictionary'), 42],
    ids=['array', 'string', 'integer'],
)
def test_dests_is_not_a_dictionary(trivial, dests):
    """Malformed /Dests must be ignored rather than crash the name tree reader."""
    trivial.Root[Name.Names] = trivial.make_indirect(Dictionary(Dests=dests))
    trivial.pages[0].Annots = Array(
        [link_annot(trivial, A=Dictionary(S=Name.GoTo, D=String('Missing')))]
    )
    assert remove_broken_goto_annotations(trivial) is False
    assert Name.D in trivial.pages[0].Annots[0].A, "annotation must be untouched"


def test_page_without_annots(trivial):
    add_named_destinations(trivial)
    assert Name.Annots not in trivial.pages[0]
    assert remove_broken_goto_annotations(trivial) is False


def test_annot_is_not_a_dictionary(trivial):
    """/Annots may contain junk; skip anything that is not an annotation."""
    add_named_destinations(trivial)
    trivial.pages[0].Annots = Array([42, String('junk'), Array([])])
    assert remove_broken_goto_annotations(trivial) is False
    assert len(trivial.pages[0].Annots) == 3


@pytest.mark.parametrize(
    'annots',
    [42, Name.Junk, Dictionary(A=Dictionary(D=String('Missing')))],
    ids=['integer', 'name', 'dictionary'],
)
def test_annots_is_not_an_array(trivial, annots):
    """A malformed /Annots that is not an array holds no annotations."""
    add_named_destinations(trivial)
    trivial.pages[0].Annots = annots
    assert remove_broken_goto_annotations(trivial) is False


def test_annot_without_action_or_destination(trivial):
    add_named_destinations(trivial)
    trivial.pages[0].Annots = Array(
        [
            link_annot(trivial),  # no /A at all
            link_annot(trivial, A=Dictionary(S=Name.URI, URI=String('https://x/'))),
        ]
    )
    assert remove_broken_goto_annotations(trivial) is False
    assert Name.A not in trivial.pages[0].Annots[0]
    assert Name.URI in trivial.pages[0].Annots[1].A


def test_broken_destination_is_disabled(trivial, caplog):
    """The one case that does modify the file: /D naming a missing destination."""
    add_named_destinations(trivial)
    annot = link_annot(trivial, A=Dictionary(S=Name.GoTo, D=String('Missing')))
    trivial.pages[0].Annots = Array([annot])

    assert remove_broken_goto_annotations(trivial) is True
    assert Name.D not in trivial.pages[0].Annots[0].A
    assert Name.A in trivial.pages[0].Annots[0], "only /D is removed"
    assert 'non-existent named destination' in caplog.text
    assert 'page 1' in caplog.text
