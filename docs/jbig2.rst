.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _jbig2:

============================
Installing the JBIG2 encoder
============================

Most Linux distributions do not include a JBIG2 encoder since JBIG2
encoding was patented for a long time. All known JBIG2 US patents have
expired as of 2017, but it is possible that unknown patents exist.

JBIG2 encoding is recommended for OCRmyPDF and is used to losslessly
create smaller PDFs. If JBIG2 encoding is not available, lower quality
CCITT encoding will be used for monochrome images.

JBIG2 decoding is not patented and is performed automatically by most
PDF viewers. It is widely supported and has been part of the PDF
specification since 2001.

JBIG encoding is automatically provided by these OCRmyPDF packages:
- Docker image (both Ubuntu and Alpine)
- Snap package
- ArchLinux AUR package
- Alpine Linux package
- Homebrew on macOS

For all other platforms, you would need to build the JBIG2 encoder from source:

.. code-block:: bash

   git clone https://github.com/agl/jbig2enc
   cd jbig2enc
   ./autogen.sh
   ./configure && make
   [sudo] make install

.. _jbig2-lossy:

Dependencies include libtoolize and libleptonica, which on Ubuntu systems
are packaged as libtool and libleptonica-dev. On Fedora (35) they are packaged
as libtool and leptonica-devel. For this to work, please make sure to install
``autotools``, ``automake``, ``libtool`` and ``leptonica`` first if not already
installed.

.. code-block:: bash

    [sudo] apt install autotools-dev automake libtool libleptonica-dev
..


Lossy mode JBIG2
================

OCRmyPDF provides lossy mode JBIG2 as an advanced and potentially dangerous
feature. Users should
`review the technical concerns with JBIG2 in lossy
mode <https://en.wikipedia.org/wiki/JBIG2#Disadvantages>`__
and decide if this feature is acceptable for their use case. In general,
this mode should not be used for archival purposes, should not be used when
the original document is not available or will be destroyed, and should
not be used when numbers present in the document are important, because
there is a risk of 6/8 and 8/6 substitution errors.

JBIG2 lossy mode does achieve higher compression ratios than any other
monochrome (bitonal) compression technology; for large text documents
the savings are considerable. JBIG2 lossless still gives great
compression ratios and is a major improvement over the older CCITT G4
standard.

To turn on JBIG2 lossy mode, add the argument ``--jbig2-lossy``.
``--optimize {1,2,3}`` are necessary for the argument to take effect
also required. Also, a JBIG2 encoder must be installed as described in
the previous section.

You can adjust the threshold for JBIG2 compression with the
``--jbig2-threshold``. The default is 0.85, meaning that if two symbols
are 85% similar, they will be compressed together.

*Due to an oversight, ocrmypdf v7.0 and v7.1 used lossy mode by
default.*
