================
PDF optimization
================

OCRmyPDF includes an image-oriented PDF optimizer. By default, the optimizer
runs with safe settings with the goal of improving compression at no loss of
quality. At higher optimization levels, lossy optimizations may be applied and
tuned. Optimization occurs after OCR, and only if OCR succeeded.  It does not
perform other possible optimizations such as deduplicating resources,
consolidating fonts, simplifying vector drawings, or anything of that nature.

Optimization ranges from ``-O0`` through ``-O3``, where ``0`` disables
optimization and ``3`` implements all options. ``1``, the default, performs only
safe and lossless optimizations. (This is similar to GCC's optimization
parameter.) The exact type of optimizations performed will vary over time.

PDF optimization requires third-party, optional tools for certain optimizations.
If these are not installed or cannot be found by OCRmyPDF, optimization will not
be as good.

Optimizations that always occurs
================================

OCRmyPDF will automatically replace obsolete or inferior compression schemes
such as RLE or LZW with superior schemes such as Deflate and converting
monochrome images to CCITT G4. Since this is harmless it always occurs and there
is no way to disable it. Other non-image compressed objects are compressed as
well.

Fast web view
=============

OCRmyPDF automatically optimizes PDFs for "fast web view" in Adobe Acrobat's
parlance, or equivalently, linearizes PDFs so that the resources they reference
are presented in the order a viewer needs them for sequential display. This
reduces the latency of viewing a PDF both online and from local storage. This
actually slightly increases the file size.

To disable this optimization and all others, use ``ocrmypdf --optimize 0 ...``
or the shorthand ``-O0``.

Lossless optimizations
======================

At optimization level ``-O1`` (the default), OCRmyPDF will also attempt lossless
image optimization.

If a JBIG2 encoder is available, then monochrome images will be converted to
JBIG2, with the potential for huge savings on large black and white images,
since JBIG2 is far more efficient than any other monochrome (bi-level)
compression. (All known US patents related to JBIG2 have probably expired, but
it remains the responsibility of the user to supply a JBIG2 encoder such as
`jbig2enc <https://github.com/agl/jbig2enc>`__. OCRmyPDF does not implement
JBIG2 encoding on its own.)

OCRmyPDF currently does not attempt to recompress losslessly compressed objects
more aggressively.

Lossy optimizations
===================

At optimization level ``-O2`` and ``-O3``, OCRmyPDF will some attempt lossy
image optimization.

If ``pngquant`` is installed, OCRmyPDF will use it to perform quantize paletted
images to reduce their size.

The quality of JPEGs may be lowered, on the assumption that a lower quality
image may be suitable for storage after OCR.

It is not possible to optimize all image types. Uncommon image types may be
skipped by the optimizer.

OCRmyPDF provides :ref:`lossy mode JBIG2 <jbig2-lossy>` as an advanced feature
that additional requires the argument ``--jbig2-lossy``.
