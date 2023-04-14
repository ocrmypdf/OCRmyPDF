#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""For extracting information about PDFs prior to OCR."""

from __future__ import annotations

from ocrmypdf.pdfinfo.info import Colorspace, Encoding, PageInfo, PdfInfo

__all__ = ["Colorspace", "Encoding", "PageInfo", "PdfInfo"]
