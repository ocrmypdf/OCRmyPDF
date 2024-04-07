# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""OCRmyPDF automatically installs these filters as plugins."""

from __future__ import annotations

from ocrmypdf import hookimpl


@hookimpl
def filter_pdf_page(page, image_filename, output_pdf):  # pylint: disable=unused-argument
    return output_pdf
