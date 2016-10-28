Common error messages
=====================

Page already has text
---------------------

.. code::

	ERROR -    1: page already has text! – aborting (use --force-ocr to force OCR)

You ran ocrmypdf on a file that already contains printable text or a hidden OCR text layer (it can't quite tell the difference). You probably don't want to do this, because the file is already searchable.

As the error message suggests, your options are:

- ``ocrmypdf --force-ocr`` to :ref:`rasterize <raster-vector>` all vector content and run OCR on the images. This is useful if a previous OCR program failed, or if the document contains a text watermark.

- ``ocrmypdf --skip-text`` to skip OCR and other processing on any pages that contain text. Text pages will be copied into the output PDF without modification.


Input file 'filename' is not a valid PDF
----------------------------------------

OCRmyPDF passes files through qpdf, a program that fixes errors in PDFs, before it tries to work on them. In most cases this happens because the PDF is corrupt and
truncated (incomplete file copying) and not much can be done.

You can try rewriting the file with Ghostscript or pdftk:

- ``gs -o output.pdf -dSAFER -sDEVICE=pdfwrite input.pdf``

- ``pdftk input.pdf cat output output.pdf``

Sometimes Acrobat can repair PDFs with its `Preflight tool <https://helpx.adobe.com/acrobat/using/correcting-problem-areas-preflight-tool.html>`_.

