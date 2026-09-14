# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF PDF annotation cleanup."""

from __future__ import annotations

import logging

from pikepdf import Dictionary, Name, NamePath, NameTree, Pdf

log = logging.getLogger(__name__)

#: The document's named-destination tree.
NAMES_DESTS = NamePath.Names.Dests

#: The named destination an annotation's GoTo action points at.
ACTION_DESTINATION = NamePath.A.D


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

    # Check if there are any named destinations. A NamePath lookup returns None
    # if any step is missing or is not a dictionary, so one guard covers a file
    # with no /Names, no /Dests, or garbage at either.
    dests = pdf.Root.get(NAMES_DESTS)
    if not isinstance(dests, Dictionary):
        return modified
    nametree = NameTree(dests)

    # Create a set of all named destinations
    names = set(k for k in nametree.keys())

    for n, page in enumerate(pdf.pages):
        for annot in page.obj.get(Name.Annots, []):
            if not isinstance(annot, Dictionary):
                continue
            destination = annot.get(ACTION_DESTINATION)
            if destination is None:
                continue
            # We found an annotation that points to a named destination
            named_destination = str(destination)
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
