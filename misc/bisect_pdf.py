#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MIT

"""Helper script for bisecting PDFs to find a page with an issue."""

import sys

import pikepdf

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <input.pdf>")
    sys.exit(1)

with pikepdf.open(sys.argv[1]) as pdf:
    num_pages = len(pdf.pages)
    low = 0
    high = num_pages - 1
    while low <= high:
        mid = (low + high) // 2
        with pikepdf.new() as new_pdf:
            new_pdf.pages.extend(pdf.pages[low : mid + 1])
            new_pdf.save(f"bisect-issue-{low + 1}-{mid + 1}.pdf")
        print(f"Is bisect-issue-{low + 1}-{mid + 1}.pdf good or bad?", end=" ")
        while True:
            response = input().lower()
            if response == "good":
                low = mid + 1
                break
            elif response == "bad":
                high = mid - 1
                break
            else:
                print("Please respond with 'good' or 'bad'.")
    print(f"The issue is on page {low + 1} of the original PDF.")
    with pikepdf.new() as new_pdf:
        new_pdf.pages.extend(pdf.pages[low])
        new_pdf.save(f"bisect-issue-bad-{low + 1}.pdf")
    with pikepdf.new() as new_pdf:
        new_pdf.pages.extend(pdf.pages[:low])
        new_pdf.pages.extend(pdf.pages[low + 1 :])
        new_pdf.save(f"bisect-issue-good-{low + 1}.pdf")
