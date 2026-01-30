% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

{#jbig2}

# Installing the JBIG2 encoder

Most Linux distributions do not include a JBIG2 encoder since JBIG2
encoding was patented for a long time. All known JBIG2 US patents have
expired as of 2017, but it is possible that unknown patents exist.

JBIG2 encoding is recommended for OCRmyPDF and is used to losslessly
create smaller PDFs. If JBIG2 encoding is not available, lower quality
CCITT encoding will be used for monochrome images.

JBIG2 decoding is not patented and is performed automatically by most
PDF viewers. It is widely supported and has been part of the PDF
specification since 2001.

JBIG encoding is automatically provided by these OCRmyPDF packages: -
Docker image (both Ubuntu and Alpine) - Snap package - ArchLinux AUR
package - Alpine Linux package - Homebrew on macOS

For all other platforms, you would need to build the JBIG2 encoder from
source:

:::{code} bash
git clone https://github.com/agl/jbig2enc
cd jbig2enc
./autogen.sh
./configure && make
[sudo] make install
:::

Dependencies include libtoolize and libleptonica, which on Ubuntu
systems are packaged as libtool and libleptonica-dev. On Fedora (35)
they are packaged as libtool and leptonica-devel. For this to work,
please make sure to install `autotools`, `automake`, `libtool`, `pkg-config`
and `leptonica` first if not already installed. Other dependencies might
be required depending on your system.

:::{code} bash
[sudo] apt install autotools-dev automake libtool libleptonica-dev pkg-config
:::

## JBIG2 Compression

OCRmyPDF uses JBIG2 lossless compression for bitonal (black and white)
images. This provides excellent compression ratios compared to the older
CCITT G4 standard, while preserving the exact pixel content of the
original image.

You can adjust the threshold for JBIG2 compression with
`--jbig2-threshold`. The default is 0.85.

:::{note}
Previous versions of OCRmyPDF supported a lossy JBIG2 mode
(`--jbig2-lossy`). This feature has been removed due to the well-known
risk of character substitution errors (e.g., 6/8 confusion). See
[JBIG2 disadvantages](https://en.wikipedia.org/wiki/JBIG2#Disadvantages)
for more information on why lossy JBIG2 is problematic. The `--jbig2-lossy`
and `--jbig2-page-group-size` arguments are now ignored with a warning.
:::
