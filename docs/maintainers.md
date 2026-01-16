% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

# Maintainer notes

This is for those who package OCRmyPDF for downstream use. (Thank you
for your hard work.)

## Known ports/packagers

OCRmyPDF has been ported to many platforms already. If you are
interesting in porting to a new platform, check with
[Repology](https://repology.org/projects/?search=ocrmypdf) to see the
status of that platform.

### Make sure you can package pikepdf

pikepdf, created by the same author, is a mixed Python and C++14 package
with much stiffer build requirements. If you want to use OCRmyPDF on
some novel platform or distribution, first make sure you can package
pikepdf.

### Core dependencies

:::{versionchanged} 17.0.0
Ghostscript is no longer strictly required. OCRmyPDF now supports alternative
codepaths for both PDF rasterization and PDF/A conversion.
:::

OCRmyPDF has the following runtime dependencies:

**For PDF rasterization** (converting PDF pages to images for OCR):

- `pypdfium2` (Python package) - OR -
- `ghostscript` (system binary)
- Recommendation: Install both for best compatibility

**For PDF/A conversion**:

- `verapdf` (system binary) with pikepdf's speculative conversion - OR -
- `ghostscript` (system binary)
- Recommendation: Install both for best compatibility

**For OCR**:
- `tesseract-ocr` (system binary) - Required for MVP

**For text rendering** (expressing OCR results in PDF):
- `fpdf2` (Python package) - Required for text layer rendering
- `uharfbuzz` (Python package) - Required for text layer rendering
- `font-noto` (system package) - Recommended for text layer rendering

**Other dependencies**:
- `unpaper` (system binary) - Optional, enables `--clean` and `--clean-final`
- `pngquant` (system binary) - Optional, enables `--optimize 2` and `--optimize 3`
- `jbig2enc` (system binary) - Optional, improves compression of monochrome images

While Ghostscript remains a capable and feature-rich tool with a long history,
recent releases have introduced some compatibility challenges that OCRmyPDF v17
addresses through alternative codepaths. For the best user experience, packagers
should install both Ghostscript and the alternative tools (pypdfium2, verapdf)
when available.

On Windows, OCRmyPDF will also check the registry for Tesseract and Ghostscript
locations.

Tesseract OCR relies on SIMD for performance and only has proper support
for this on ARM and x86\_64. Performance may be poor on other processor
architectures.

### Versioning scheme

OCRmyPDF uses hatch-vcs for versioning, which derives the version from
Git as a single source of truth. This may be unsuitable for some
distributions, e.g. to indicate that your distribution modifies OCRmyPDF
in some way.

You can patch the `__version__` variable in `src/ocrmypdf/_version.py`
if necessary, or set the environment variable
`SETUPTOOLS_SCM_PRETEND_VERSION` to the required version, if you need to
override versioning for some reason.

### jbig2enc

OCRmyPDF will use jbig2enc, a JBIG2 encoder, if one can be found. Some
distributions have shied away from packaging JBIG2 because it contains
patented algorithms, but all patents have expired since 2017. If
possible, consider packaging it too to improve OCRmyPDF's compression.

:::{note}
Lossy JBIG2 encoding has been removed in v17.0.0 due to well-documented
risks of character substitution errors. Previously we provided this feature
on a "caveat emptor" basis but in the interest of focusing and eliminating
risks, we decided to remove this option. Now, only lossless JBIG2 compression
is supported.
:::

### Dependency matrix for packagers

:::{versionadded} 17.0.0
:::

The following table summarizes the dependency options introduced in v17.0.0:

| Feature | Option 1 | Option 2 | Notes |
|---------|----------|----------|-------|
| PDF rasterization | pypdfium2 (Python) | ghostscript (binary) | pypdfium2 preferred when available |
| PDF/A conversion | verapdf + pikepdf | ghostscript | verapdf validates speculative conversion |
| Text rendering | fpdf2 (Python) | - | Required, replaces legacy hOCR renderer |
| OCR | tesseract-ocr | `--ocr-engine none` | Can be skipped entirely |

**Minimum viable installation:**

- tesseract-ocr + (pypdfium2 OR ghostscript) + fpdf2

**Recommended installation:**

- tesseract-ocr + pypdfium2 + ghostscript + verapdf + fpdf2 + unpaper + pngquant + jbig2enc

:::{warning}
If Ghostscript is not installed and verapdf is not available, PDF/A output
cannot be produced. The output will be a standard PDF instead. This is a
breaking change for rare configurations that previously relied on PDF/A
output without Ghostscript alternatives.
:::

**Sample debian/control dependency specification**

```
Depends:
 fonts-noto,
 fpdf2 (>= 2.8),
 ghostscript (>= 9.55),  # Not strictly required, but best user experience
 icc-profiles-free,
 img2pdf,
 python3-coloredlogs,
 python3-deprecation,
 python3-pdfminer (>= 20181108+dfsg-3),
 python3-pikepdf (>= 8.14.0),
 python3-pil,
 python3-pluggy,
 python3-reportlab,
 python3-rich,
 python3-uharfbuzz,  # Not currently in Debian
 tesseract-ocr (>= 5.0.0),
 zlib1g,
 ${misc:Depends},
 ${python3:Depends},
Recommends:
 cyclopts,   # Not currently in Debian
 jbig2
 paddleocr,  # Not currently in Debian
 pngquant,
 pypdfium2,  # Not currently in Debian
 unpaper,
 verapdf,    # Not currently in Debian
Suggests:
 ocrmypdf-doc,
 python-watchdog,
```

### Command line completions

Please ensure that command line completions are installed, as described
in the installation documentation.

### 32-bit Linux support

If you maintain a Linux distribution that supports 32-bit x86 or ARM,
OCRmyPDF should continue to work as long as all of its dependencies
continue to be available in 32-bit form. Please note we do not test on
32-bit platforms.

### HEIF/HEIC

OCRmyPDF defaults to installing the pi-heif PyPI package, which supports
converting HEIF (High Efficiency Image File Format) images to PDF from
the command line. If your distribution does not have this library
available, you can exclude it and OCRmyPDF will gracefully degrade
automatically, losing only support for this feature.
