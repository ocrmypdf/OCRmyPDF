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

OCRmyPDF uses setuptools-scm-git-archive to ensure that tarballs downloaded from
GitHub contain version information. Unfortunately, these tarballs are not always
deterministic. See this
`issue <https://github.com/ocrmypdf/OCRmyPDF/issues/841#issuecomment-936562696>`_.

jbig2enc
--------

OCRmyPDF will use jbig2enc, a JBIG2 encoder, if one can be found. Some distributions
have shied away from packaging JBIG2 because it contains patented algorithms, but
all patents have expired since 2017. If possible, consider packaging it too to
improve OCRmyPDF's compression.

Command line completions
------------------------

Please ensure that command line completions are installed.
