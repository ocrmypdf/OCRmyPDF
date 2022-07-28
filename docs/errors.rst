.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

=====================
Common error messages
=====================

Page already has text
=====================

.. code-block::

   ERROR -    1: page already has text! – aborting (use --force-ocr to force OCR)

You ran ocrmypdf on a file that already contains printable text or a
hidden OCR text layer (it can't quite tell the difference). You probably
don't want to do this, because the file is already searchable.

As the error message suggests, your options are:

-  ``ocrmypdf --force-ocr`` to :ref:`rasterize <raster-vector>` all
   vector content and run OCR on the images. This is useful if a
   previous OCR program failed, or if the document contains a text
   watermark.
-  ``ocrmypdf --skip-text`` to skip OCR and other processing on any
   pages that contain text. Text pages will be copied into the output
   PDF without modification.
-  ``ocrmypdf --redo-ocr`` to scan the file for any existing OCR
   (non-printing text), remove it, and do OCR again. This is one way
   to take advantage of improvements in OCR accuracy. Printable vector
   text is excluded from OCR, so this can be used on files that contain
   a mix of digital and scanned files.


Input file 'filename' is not a valid PDF
========================================

OCRmyPDF checks files with pikepdf, a library that in turn uses libqpdf to fixes
errors in PDFs, before it tries to work on them. In most cases this happens
because the PDF is corrupt and truncated (incomplete file copying) and not much
can be done.

You can try rewriting the file with Ghostscript:

.. code-block:: bash

    gs -o output.pdf -dSAFER -sDEVICE=pdfwrite input.pdf

``pdftk`` can also rewrite PDFs:

.. code-block:: bash

    pdftk input.pdf cat output output.pdf

Sometimes Acrobat can repair PDFs with its `Preflight
tool <https://helpx.adobe.com/acrobat/using/correcting-problem-areas-preflight-tool.html>`__.
