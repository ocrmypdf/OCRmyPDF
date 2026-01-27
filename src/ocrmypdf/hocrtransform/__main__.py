# SPDX-FileCopyrightText: 2023-2025 James R. Barlow
# SPDX-License-Identifier: MIT

"""Simple CLI for testing HOCR to PDF conversion using fpdf2 renderer."""
from __future__ import annotations

import argparse
from pathlib import Path

from ocrmypdf.font import MultiFontManager
from ocrmypdf.fpdf_renderer import DebugRenderOptions, Fpdf2PdfRenderer
from ocrmypdf.hocrtransform.hocr_parser import HocrParser

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert hocr file to PDF')
    parser.add_argument(
        '-b',
        '--boundingboxes',
        action="store_true",
        default=False,
        help='Show bounding boxes borders (debug mode)',
    )
    parser.add_argument(
        '-r',
        '--resolution',
        type=int,
        default=300,
        help='Resolution of the image that was OCRed',
    )
    parser.add_argument(
        '-i',
        '--image',
        default=None,
        help='Path to the image to be placed above the text (not yet supported)',
    )
    parser.add_argument('hocrfile', help='Path to the hocr file to be parsed')
    parser.add_argument('outputfile', help='Path to the PDF file to be generated')
    args = parser.parse_args()

    # Parse hOCR file
    hocr_parser = HocrParser(args.hocrfile)
    ocr_page = hocr_parser.parse()

    # Use DPI from hOCR if available, otherwise use command-line resolution
    dpi = ocr_page.dpi or args.resolution

    # Setup debug render options if requested
    debug_options = None
    if args.boundingboxes:
        debug_options = DebugRenderOptions(
            render_line_bbox=True,
            render_word_bbox=True,
            render_baseline=True,
        )

    # Create multi-font manager with default font directory
    font_dir = Path(__file__).parent.parent / "data"
    multi_font_manager = MultiFontManager(font_dir)

    # Render to PDF using fpdf2
    renderer = Fpdf2PdfRenderer(
        page=ocr_page,
        dpi=dpi,
        multi_font_manager=multi_font_manager,
        invisible_text=not args.boundingboxes,  # Visible text in debug mode
        debug_render_options=debug_options,
    )
    renderer.render(Path(args.outputfile))

    if args.image:
        print(
            f"Warning: Image overlay (--image {args.image}) is not yet supported "
            "with the fpdf2 renderer."
        )
