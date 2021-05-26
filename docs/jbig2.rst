.. _jbig2:

============================
Installing the JBIG2 encoder
============================

Most Linux distributions do not include a JBIG2 encoder since JBIG2
encoding was patented for a long time. All known JBIG2 US patents have
expired as of 2017, but it is possible that unknown patents exist.

JBIG2 encoding is recommended for OCRmyPDF and is used to losslessly
create smaller PDFs. If JBIG2 encoding not available, lower quality
encodings will be used.

JBIG2 decoding is not patented and is performed automatically by most
PDF viewers. It is widely supported has been part of the PDF
specification since 2001.

On macOS, Homebrew packages jbig2enc and OCRmyPDF includes it by
default. The Docker image for OCRmyPDF also builds its own JBIG2 encoder
from source.

For all other Linux, you must build a JBIG2 encoder from source:

.. code-block:: bash

   git clone https://github.com/agl/jbig2enc
   cd jbig2enc
   ./autogen.sh
   ./configure && make
   [sudo] make install

.. _jbig2-lossy:

Lossy mode JBIG2
================

OCRmyPDF provides lossy mode JBIG2 as an advanced feature. Users should
`review the technical concerns with JBIG2 in lossy
mode <https://abbyy.technology/en:kb:tip:jbig2_compression_and_ocr>`__
and decide if this feature is acceptable for their use case.

JBIG2 lossy mode does achieve higher compression ratios than any other
monochrome (bitonal) compression technology; for large text documents
the savings are considerable. JBIG2 lossless still gives great
compression ratios and is a major improvement over the older CCITT G4
standard. As explained above, there is some risk of substitution errors.

To turn on JBIG2 lossy mode, add the argument ``--jbig2-lossy``.
``--optimize {1,2,3}`` are necessary for the argument to take effect
also required. Also, a JBIG2 encoder must be installed as described in
the previous section.

*Due to an oversight, ocrmypdf v7.0 and v7.1 used lossy mode by
default.*
