.. SPDX-FileCopyrightText: 2023 James R. Barlow
.. SPDX-License-Identifier: CC-BY-SA-4.0

============
Design notes
============

Why doesn't OCRmyPDF use PyTesseract?
=====================================

PyTesseract is a Python wrapper around the Tesseract OCR engine. When OCRmyPDF was
first written, PyTesseract used ABI bindings to call the Tesseract library. This
was not a good fit for OCRmyPDF because ABI bindings can be fragile.

PyTesseract has since evolved calling the Tesseract executable, abandoning the ABI
approach and using the CLI instead, just like OCRmyPDF does. If it were written from
scratch today, OCRmyPDF might use PyTesseract.

PyTesseract has more features don't particularly need PDF output, but less features
than OCRmyPDF's API for creating PDFs.

What is ``executor()``?
=======================

OCRmyPDF uses a custom concurrent executor which can support either threads or
processes with the same interface. This is useful because OCRmyPDF can use
either threads or processes to parallelize work, whichever is more appropriate
for the task at hand.

The interface is currently private and subject to change. In particular, if
experiments with asyncio and anyio are successful, the interface will change.

