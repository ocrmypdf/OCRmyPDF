.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

================
Maintainer notes
================

This is for those who package OCRmyPDF for downstream use.  (Thank you
for your hard work.)

Known ports/packagers
=====================

OCRmyPDF has been ported to many platforms already. If you are interesting in
porting to a new platform, check with
`Repology <https://repology.org/projects/?search=ocrmypdf>`__ to see the status
of that platform.

Make sure you can package pikepdf
---------------------------------

pikepdf, created by the same author, is a mixed Python and C++14 package with
much stiffer build requirements. If you want to use OCRmyPDF on some novel platform
or distribution, first make sure you can package pikepdf.

Non-Python dependencies
-----------------------

Note that we have non-Python dependencies. In particular, OCRmyPDF requires
Ghostscript and Tesseract OCR to be installed and needs to be able to locate their
binaries on the system PATH. On Windows, OCRmyPDF will also check the registry
for their locations.

Tesseract OCR relies on SIMD for performance and only has proper support for this
on ARM and x86_64. Performance may be poor on other processor architectures.

Versioning scheme
-----------------

OCRmyPDF uses setuptools-scm for versioning, which derives the version from
Git as a single source of truth. This may be unsuitable for some distributions, e.g.
to indicate that your distribution modifies OCRmyPDF in some way.

You can patch the ``__version__`` variable in ``src/ocrmypdf/_version.py`` if
necessary.

jbig2enc
--------

OCRmyPDF will use jbig2enc, a JBIG2 encoder, if one can be found. Some distributions
have shied away from packaging JBIG2 because it contains patented algorithms, but
all patents have expired since 2017. If possible, consider packaging it too to
improve OCRmyPDF's compression.

Command line completions
------------------------

Please ensure that command line completions are installed, as described in the
installation documentation.

32-bit Linux support
--------------------

If you maintain a Linux distribution that supports 32-bit x86 or ARM, OCRmyPDF
should continue to work as long as all of its dependencies continue to be
available in 32-bit form. Please note we do not test on 32-bit platforms.

HEIF/HEIC
---------

OCRmyPDF defaults to installing the pi-heif PyPI package, which supports converting
HEIF (High Efficiency Image File Format) images to PDF from the command line.
If your distribution does not have this library available, you can exclude it and
OCRmyPDF will gracefully degrade automatically, losing only support for this
feature.