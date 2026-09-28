# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""OCRmyPDF PDF annotation cleanup."""

from __future__ import annotations

import logging
from collections.abc import Callable

from pikepdf import Array, Dictionary, Name, NamePath, NameTree, Page, Pdf

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


def link_annotations(page: Page) -> list[Dictionary]:
    """Return the Link annotations (hyperlinks) of a page."""
    annots = page.obj.get(Name.Annots)
    if not isinstance(annots, Array):
        return []
    return [
        annot
        for annot in annots
        if isinstance(annot, Dictionary) and annot.get(Name.Subtype) == Name.Link
    ]


def _page_point_mapper(
    mediabox: tuple[float, float, float, float],
    rotation: int,
    new_size: tuple[float, float],
) -> Callable[[float, float], tuple[float, float]]:
    """Map points on a page to the page that shows it rotated and rasterized.

    The rasterized page has its MediaBox at the origin and shows the old page
    as it was displayed, turned clockwise by *rotation* degrees, scaled to
    *new_size*.
    """
    x0, y0, x1, y1 = mediabox
    width, height = x1 - x0, y1 - y0
    rotation %= 360
    rotated_size = (height, width) if rotation in (90, 270) else (width, height)
    sx = new_size[0] / rotated_size[0] if rotated_size[0] else 1.0
    sy = new_size[1] / rotated_size[1] if rotated_size[1] else 1.0

    def map_point(x: float, y: float) -> tuple[float, float]:
        x, y = x - x0, y - y0
        if rotation == 90:
            x, y = y, width - x
        elif rotation == 180:
            x, y = width - x, height - y
        elif rotation == 270:
            x, y = height - y, x
        return x * sx, y * sy

    return map_point


def transfer_link_annotations(
    links: list[Dictionary],
    page: Page,
    *,
    old_mediabox: tuple[float, float, float, float],
    rotation: int,
) -> None:
    """Put Link annotations on a page that replaced their page with an image.

    The rasterized page has its own coordinate system, so the /Rect and
    /QuadPoints of each link are mapped onto it. The raster already shows
    whatever the link looked like, so the link's own border and appearance
    stream are removed to keep them from being drawn a second time, perhaps
    misaligned; what remains is a clickable area. The annotations keep their
    object numbers, so their /Dest and /A entries, and anything that refers to
    them, are unaffected.

    Args:
        links: Link annotations of the old page.
        page: The page that replaced it, whose MediaBox is at the origin.
        old_mediabox: MediaBox of the old page.
        rotation: Clockwise rotation in degrees from the old page's default
            user space to the new page.
    """
    new_mediabox = [float(v) for v in page.mediabox]
    map_point = _page_point_mapper(
        old_mediabox,
        rotation,
        (new_mediabox[2] - new_mediabox[0], new_mediabox[3] - new_mediabox[1]),
    )
    kept = []
    for link in links:
        rect = link.get(Name.Rect)
        if not isinstance(rect, Array) or len(rect) != 4:
            continue
        try:
            coords = [float(v) for v in rect]
        except (TypeError, ValueError):
            continue
        xa, ya = map_point(coords[0], coords[1])
        xb, yb = map_point(coords[2], coords[3])
        link[Name.Rect] = Array([min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb)])
        quadpoints = link.get(Name.QuadPoints)
        if isinstance(quadpoints, Array):
            try:
                qp = [float(v) for v in quadpoints]
            except (TypeError, ValueError):
                del link[Name.QuadPoints]
            else:
                mapped: list[float] = []
                for i in range(0, len(qp) - 1, 2):
                    mapped.extend(map_point(qp[i], qp[i + 1]))
                link[Name.QuadPoints] = Array(mapped)
        for key in (Name.AP, Name.AS, Name.BS):
            if key in link:
                del link[key]
        link[Name.Border] = Array([0, 0, 0])
        kept.append(link)
    if kept:
        page.obj[Name.Annots] = Array(kept)
