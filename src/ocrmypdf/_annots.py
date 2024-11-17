# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF PDF annotation cleanup."""

from __future__ import annotations

import logging

from pikepdf import Dictionary, Name, NameTree, Pdf

log = logging.getLogger(__name__)


def remove_broken_goto_annotations(pdf: Pdf) -> bool:
    """Remove broken goto annotations from a PDF.

    If a PDF contains a GoTo Action that points to a named destination that does not
    exist, Ghostscript PDF/A conversion will fail. In any event, a named destination
    that is not defined is not useful.

    Args:
        pdf: Opened PDF file.

    Returns:
        bool: True if the file was modified, False if not.
    """
    modified = False

    # Check if there are any named destinations
    if Name.Names not in pdf.Root:
        return modified
    if Name.Dests not in pdf.Root[Name.Names]:
        return modified

    dests = pdf.Root[Name.Names][Name.Dests]
    if not isinstance(dests, Dictionary):
        return modified
    nametree = NameTree(dests)

    # Create a set of all named destinations
    names = set(k for k in nametree.keys())

    for n, page in enumerate(pdf.pages):
        if Name.Annots not in page:
            continue
        for annot in page[Name.Annots]:
            if not isinstance(annot, Dictionary):
                continue
            if Name.A not in annot or Name.D not in annot[Name.A]:
                continue
            # We found an annotation that points to a named destination
            named_destination = str(annot[Name.A][Name.D])
            if named_destination not in names:
                # If there is no corresponding named destination, remove the
                # annotation. Having no destination set is still valid and just
                # makes the link non-functional.
                log.warning(
                    f"Disabling a hyperlink annotation on page {n + 1} to a "
                    "non-existent named destination "
                    f"{named_destination}."
                )
                del annot[Name.A][Name.D]
                modified = True

    return modified
