% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

# v17

## v17.7.1

- Fixed a severe, Windows-specific performance regression in the "Scanning
  contents" phase, most visible with `--redo-ocr` ({issue}`1662`). Since
  v16.4.3, OCRmyPDF forced pdfminer's read buffer to 256 MiB to work around a
  pdfminer bug that mishandled tokens split across the buffer boundary
  ({issue}`1361`). On Windows, CPython's `BufferedReader.read()` eagerly
  allocates a buffer of the requested size on every read, so the oversized
  buffer made each of pdfminer's thousands of reads cost tens of milliseconds
  (this allocation is lazy, and effectively free, on Linux). The underlying
  pdfminer bug was fixed upstream in pdfminer.six 20250327
  ([#1030](https://github.com/pdfminer/pdfminer.six/pull/1030)), with a
  follow-up for tokens split across streams in 20260107
  ([#1158](https://github.com/pdfminer/pdfminer.six/pull/1158)), so the
  workaround has been removed and the minimum pdfminer.six version raised to
  20260107.
- The font discovery used to build the OCR text layer now finds variable fonts
  such as `NotoSansArabic[wdth,wght].ttf`, the form shipped by Homebrew casks
  and current Google Fonts releases. Previously only static `-Regular.ttf`/`.otf`
  files were matched, so users who had installed the correct Noto font still got
  the glyphless fallback and a "No font found" warning ({issue}`1652`).
- Font discovery is now language-aware for CJK: each Chinese, Japanese, and
  Korean language maps to its own per-language Noto family (NotoSansSC, TC, HK,
  JP, KR), with the pan-CJK super font kept as a shared fallback, since the
  per-language fonts are region subsets that may lack glyphs from other scripts.
- The warning shown when no installed font has glyphs for some text was reworded
  to explain the consequence — the text is still added as a searchable, copyable
  layer but appears blank when highlighted in a viewer — and to name the specific
  font family to install.

## v17.7.0

- The Docker images now run as a non-root user (`app`, uid/gid 1000) by default
  rather than as root, as a defense-in-depth measure. If you bind-mount a
  directory for input and output, you may now need to add a `--user` argument so
  the container can write to it; the correct value differs for rootless Docker,
  Podman, and rootful Docker, and is described in the Docker documentation.
  Piping the input and output through stdin/stdout still works with no
  permission setup.
- The Docker images now default their working directory to `/data`, so files in
  a directory mounted there can be given as relative paths without an explicit
  `--workdir`.
- The Ubuntu Docker image now installs Tesseract 5 from the Ubuntu archive
  instead of the third-party `alex-p/tesseract-ocr5` PPA, and the base images
  were updated to Ubuntu 26.04 and Alpine 3.24.
- Fixed a missing space in the error message shown when OCRmyPDF cannot access
  its working directory inside a Docker container.
- Updated packaged dependencies, including the optional web service stack
  (starlette, tornado, python-multipart) and cryptography.

## v17.6.0

- When the optimizer encounters an image it cannot process (for example, an
  exotic colorspace that cannot be transcoded), it now logs a concise warning
  that the image was left unchanged rather than printing an alarming
  traceback. The output file was already valid in these cases; only the
  reporting was misleading. The full traceback is still available at debug
  verbosity (`-v 1`) ({issue}`846`).
- `--pdfa-image-compression=auto` (the default) now selects lossless image
  compression at `-O0` so Ghostscript no longer transcodes lossless images to
  JPEG during PDF/A generation. At `-O1` and above, `auto` continues to defer
  to Ghostscript's heuristic, which may recompress images lossily. `-O1` (the
  default level) is kept as a historical exception because coercing it to
  lossless can substantially bloat output; users who want guaranteed lossless
  image handling should pass `--pdfa-image-compression=lossless` or use `-O0`
  ({issue}`1124`).
- `--pdfa-image-compression=lossless` now passes existing JPEG images through
  unchanged rather than re-encoding them with a lossless codec. Re-encoding an
  already-lossy JPEG losslessly cannot recover quality and only inflates the
  file, so JPEGs are preserved while non-JPEG images are encoded losslessly.
- OCRmyPDF now validates and repairs malformed page-boundary boxes
  (``/MediaBox``, ``/CropBox``, ``/TrimBox``, ``/ArtBox``, ``/BleedBox``) in its
  input, following the PDF 2.0 specification. Coordinates written in invalid
  exponential notation are reinterpreted ({issue}`1398`); rectangles whose
  corners are given in reversed order are normalized, which previously crashed
  with ``NegativeDimensionError`` ({issue}`1526`); and a crop/trim/art/bleed box
  that falls outside the MediaBox is clamped to their intersection, or discarded
  when that intersection is empty, which previously produced an output with a
  zero-height effective page that some viewers refused to open ({issue}`1400`).
  When a box is discarded, clamped, or reinterpreted, OCRmyPDF logs a warning
  recommending visual inspection of the output. Thanks @ajdlinux for the initial
  fix in PR #1691.
- OCRmyPDF now discards an embedded Adobe full-text search index
  (``/Root/PieceInfo/SearchIndex``) from its output. This proprietary index,
  produced by Acrobat's "Embed Index" feature, is read only by Adobe Acrobat;
  other viewers ignore it and search the text on the fly. Because any change to
  a PDF invalidates the index, retaining it after OCRmyPDF rewrites the document
  would leave a stale index that returns incorrect search results in Acrobat.
  Modern viewers rebuild a search index on demand, so there is no loss of
  search capability.
- OCRmyPDF now discards embedded per-page thumbnail images (the optional
  ``/Thumb`` image XObject on a page) from its output. OCRmyPDF alters page
  appearance (deskew, clean, rasterize, re-render) and plugins may edit pages
  arbitrarily, so a retained thumbnail would be stale and no longer match its
  page. Embedded thumbnails are a navigation aid that modern viewers generate
  on demand, so there is no loss of functionality.
- Fixed a regression in OCR quality for PDFs that paint a 1-bit image mask
  (stencil) with a gray or colored fill color. Previously such pages were
  rasterized as 1-bit black-and-white before OCR, so Ghostscript dithered
  mid-tone text into an unreadable stipple and Tesseract failed to recognize
  it. The rasterizer now inspects the fill color used to paint a mask and
  promotes the page to grayscale or full color as needed, so the distinction
  is preserved for the OCR engine. This applies to both the Ghostscript and
  pypdfium rasterizers. {issue}`1688`
- The default 1-bit raster device for Ghostscript is now ``pngmonod``
  (error-diffusion) instead of ``pngmono`` (ordered dithering). It produces
  better input for OCR on faint or anti-aliased scans at negligible cost and
  no change to output file size, since the rasterized image is an
  intermediate that is discarded after OCR.
- When rasterizing pages with Ghostscript, OCRmyPDF now enables text and
  graphics anti-aliasing (``-dTextAlphaBits=4 -dGraphicsAlphaBits=4``) for the
  grayscale and color raster devices. Ghostscript 10.x renders aliased glyphs
  that OCR frequently misreads as extra word breaks or substituted characters;
  anti-aliasing materially improves OCR accuracy on the Ghostscript
  rasterization path, especially for small fonts at moderate resolution. The
  1-bit monochrome devices are unaffected, since they perform their own
  anti-aliased downscaling and older Ghostscript versions reject alpha-bit
  options on them. Note that the default rasterizer (``--rasterizer auto``)
  prefers pypdfium2, which already anti-aliases; this change benefits users who
  select ``--rasterizer ghostscript`` or do not have pypdfium2 installed.
  OCRmyPDF now also logs which rasterizer rendered each page at debug verbosity
  (``-v 1``), and the ``--rasterizer`` help text explains the OCR-quality
  trade-off, to make such reports easier to diagnose. {issue}`1439`
- When Tesseract reports a page with many diacritics, OCRmyPDF still logs its
  interpreted "lots of diacritics - possibly poor OCR" hint, but now also emits
  Tesseract's raw message at debug verbosity (``-v 1``) so the original wording
  is available for diagnosis. {issue}`1566`
- Added ``--mode strip``, which removes the invisible OCR text layer from a PDF
  in place. Unlike ``--ocr-engine none --force-ocr``, it does not rasterize the
  page, so images and visible content are preserved unchanged and the output is
  smaller rather than larger. Only text drawn as invisible (PDF text render mode
  3) is removed; some OCR engines -- and OCRmyPDF v2.2 and earlier -- express
  text as visible glyphs covered by an opaque image, and that text cannot be
  removed this way. {issue}`1435`

## v17.5.0

- Added support for the ``end`` alias in ``--pages``, denoting the last page
  of the document. For example, ``--pages 3-end`` OCRs from page 3 through
  the final page. {issue}`1615`
- Added ``--ghostscript-jpeg-quality`` and ``--ghostscript-jpeg-maxdpi``
  advanced options for tuning Ghostscript's PDF/A output. The optimizer's
  ``--jpeg-quality`` remains the recommended file-size control.
- Fixed pypdfium2 rasterizer clipping content when the CropBox was smaller
  than the MediaBox (e.g. JSTOR or cropped PDFs). {issue}`1685`
- Fixed Form XObject cycle detection in the optimizer's image xref scan.
  Self-referential or DAG-shaped Form graphs (notably from PowerPoint
  exports) previously produced floods of recursion warnings and could hang
  for minutes. {issue}`1321`
- Tesseract config errors are now surfaced as ``TesseractConfigError`` with
  actionable guidance, instead of crashing later with a confusing
  ``FileNotFoundError`` on the missing hOCR output. {issue}`1687`
- Refreshed the Chinese README translation. Thanks @cislunarspace.
- Internal refactoring of the ``_exec`` and ``subprocess`` modules to
  separate probing from execution.
- CI dependency updates.

## v17.4.2

- Fixed Python API unconditionally overriding ``PIL.Image.MAX_IMAGE_PIXELS``
  when the caller did not explicitly set ``max_image_mpixels``. Host
  applications (e.g. Paperless-NGX) that configure the PIL limit before
  invoking ``ocrmypdf.ocr()`` now have their setting respected. The CLI
  default of 250 megapixels is unchanged. {issue}`1665`
- Updated uv.lock to avoid pinning a vulnerable version of Pillow. {issue}`1666`

## v17.4.1

- Fixed RTL text extraction order in the fpdf2 renderer. Arabic lam-alef
  ligatures and other multi-character CMap entries were garbled by the bidi
  algorithm during text extraction. {issue}`1655`
- Fixed ``work_folder`` not being set in ``PdfContext`` options when using
  the Python API. Thanks @bluebox-steven. {issue}`1613`
- Updated Ghostscript JPEG corruption warning to include the detected version
  number, confirming the bug persists in Ghostscript 10.7.0.
- Internal refactoring.
- CI dependency updates.

## v17.4.0

- Added ``--no-overwrite`` / ``-n`` option to prevent overwriting output files.
  If the destination file already exists, OCRmyPDF exits with code 5
  (``OutputFileAccessError``). {issue}`1642`
- Fixed text layer stretching in the fpdf2 renderer for widely-spaced words.
  The horizontal scaling (Tz) was incorrectly stretched to fill inter-word gaps
  instead of relying on Td positioning, causing text selection to highlight far
  beyond the actual word boundaries. {issue}`1635`
- Fixed ``optimize=2`` or ``optimize=3`` crash when using the Python API without
  explicitly setting ``jpg_quality`` or ``png_quality``. {issue}`1641`
- Fixed ``verapdf`` availability check crashing with ``NotADirectoryError`` on
  some platforms. {issue}`1638`

## v17.3.0

- Fixed Python API ignoring the ``language`` parameter, always defaulting to
  ``eng``. The API now correctly maps ``language`` to OcrOptions ``languages``
  and splits ``+``-separated codes (e.g. ``eng+deu``) to match CLI behavior.
  {issue}`1640`
- Fixed Python API producing empty OCR output because ``tesseract_timeout``
  defaulted to 0, causing Tesseract to time out immediately. The default is
  now ``None``, falling back to the plugin's 180-second timeout. {issue}`1636`
- Fixed OCR text layer displacement on PDFs with non-zero MediaBox origins
  (e.g. JSTOR or cropped PDFs). The coordinate transformation matrix is now
  always computed, not skipped when rotation is zero. {issue}`1630`
- Restored image overlay support (``--image``) for the hocrtransform tool,
  enabling sandwich PDF output with the fpdf2 renderer. {issue}`1634`
- Docker: updated Alpine base image to 3.23.
- Documentation restructured into per-major-version release notes files.
- Release process improvements.

## v17.2.0

- Fixed incorrect word spacing in poppler-based PDF viewers and tools (Evince,
  pdftotext, and others) where words on the same line appeared separated by
  double newlines. This works around a poppler bug where Tz (horizontal scaling)
  is not carried across BT/ET boundaries. {issue}`1632`
- Fixed OCR text layer being visible instead of invisible due to incorrect fpdf2
  text rendering mode attribute. This caused OCR text to appear when images were
  removed from the PDF. {issue}`1631`
- Fixed OCR text layer misalignment with non-zero mediabox origins, which
  affected cropped PDFs and JSTOR PDFs generated by iText. The ``--redo-ocr``
  mode would shift text vertically on these files. {issue}`1630`
- Fixed Ghostscript rasterization failure with very low DPI values (below 10).
  OCRmyPDF now renders at a minimum of 10 DPI and resizes the output to match
  the originally requested dimensions. {issue}`1612`

## v17.1.0

- Added `--tagged-pdf-mode` to allow skipping the TaggedPDF error message, if desired.
- Fixed an issue where deflated JPEGs (FlateDecode + DCTDecode) were counted as
  lossless images for the purpose of determining whether to compress to JPEG,
  causing file size inflation with some workflows (`--mode force` in particular).

## v17.0.1

- Fixed output file size inflation when using pypdfium as rasterizer and force-ocr
  mode.

## v17.0.0

**Breaking changes**

- **Plugin interface migration**: Plugin hooks now receive `OcrOptions` objects instead of
  `argparse.Namespace` objects. Most plugins will continue working due to duck-typing
  compatibility, but plugin developers should update their type hints from `Namespace`
  to `OcrOptions`.
- Built-in plugins no longer modify options in-place, improving immutability and
  code clarity.
- **Lossy JBIG2 removed**: The `--jbig2-lossy` and `--jbig2-page-group-size` options have been
  removed due to well-documented risks of character substitution errors. These options are now
  deprecated and will emit warnings if used. Only lossless JBIG2 compression is supported.
- **PDF/A output behavior change**: If neither Ghostscript nor verapdf is installed,
  `--output-type auto` (the new default) will produce a standard PDF instead of PDF/A. This is
  a change from previous versions where Ghostscript was required and PDF/A was always produced.
  This configuration is rare but users should be aware of the change.

**New features**

- **pypdfium2 rasterizer**: Added optional pypdfium2-based PDF rasterization plugin as an
  alternative to Ghostscript for page rendering. Use `--rasterizer pypdfium` to enable
  (requires `pip install pypdfium2`). The default `--rasterizer auto` prefers pypdfium when
  available and falls back to Ghostscript.
- **Pluggable OCR engines**: New `--ocr-engine` option allows selecting OCR engines:
  - `auto` (default): Uses Tesseract
  - `tesseract`: Explicit Tesseract selection
  - `none`: Skip OCR entirely for PDF processing-only workflows

  This prepares the foundation for future third-party OCR engine plugins.
- **Smart PDF/A conversion**: New `--output-type auto` (now the default) produces best-effort
  PDF/A output without requiring Ghostscript when the verapdf validator is available. Falls back
  to traditional Ghostscript conversion when needed.
- **verapdf integration**: Added optional verapdf validation for fast PDF/A conversion. When
  available, OCRmyPDF attempts speculative PDF/A conversion using pikepdf, validates with verapdf,
  and skips Ghostscript if validation passes.
- **Optional Ghostscript**: As a consequence of the changes above, Ghostscript is no longer a required dependency. It is optional.
- **fpdf2 text renderer**: Replaced legacy hOCR text renderer with new fpdf2-based implementation,
  providing better multilingual support and more accurate text positioning.
- **Improved Occulta glyphless font**: The new Occulta font provides better handling of
  zero-width markers and double-width CJK characters for accurate text layer positioning.
- **Expanded multilingual font support**: Added FontProvider infrastructure with language-aware
  font selection for Devanagari (Hindi, Sanskrit, Marathi, Nepali), CJK (Chinese, Japanese,
  Korean), Arabic script, and many other scripts. System font discovery reduces package size.
- **Simplified mode selection**: New `--mode` (`-m`) argument consolidates processing options:
  - `default`: Error if text is found (standard behavior)
  - `force`: Rasterize all content and run OCR (replaces `--force-ocr`)
  - `skip`: Skip pages with existing text (replaces `--skip-text`)
  - `redo`: Re-OCR pages, stripping old text layer (replaces `--redo-ocr`)

  Legacy flags remain as silent aliases for backward compatibility.

**API improvements**

- Centralized validation logic in the `OcrOptions` Pydantic model
- Removed scattered option mutation throughout the codebase
- Better type safety for plugin development
- Simplified plugin option handling
- New `OcrElement`, `OcrClass`, and `BoundingBox` exports for OCR engine plugin developers
- Extended `OcrEngine` ABC with `generate_ocr()` method for direct OCR tree output, eliding the need to translate a modern engine's output to hOCR or directly write to PDF.

**Bug fixes**

- Fixed double-compression of already-deflated JPEGs.
- Fixed tesseract_cache plugin to properly handle cache misses.
- Fixed handling of PDF page boxes (ArtBox, BleedBox) which were not being processed correctly.
- Added thread safety lock to pypdfium plugin for concurrent operations.
- Improved pdfminer.six compatibility with explicit word spacing.

**Documentation**

- Updated cookbook to replace deprecated `--tesseract-timeout 0` with `--ocr-engine none`.
- Added comprehensive plugin documentation for new OCR engine framework.

**Dependency changes**

- Requires: one of `pypdfium2` or `ghostscript` for PDF rasterization (PDF to image)
  - Preferred: both
- Requires: one of `verapdf` or `ghostscript` for PDF/A generation
  - Preferred: both
- Recommended: `pypdfium2` for PDF rasterization (new dependency)
- Recommended: `ghostscript` (used to be Required)
- Recommended: Noto fonts for improved OCR text positioning
- Optional: `verapdf` for fast PDF/A validation (new dependency)
- Requires: `fpdf2` for text layer rendering (new dependency)
- Recommended: replace `typer` with `cyclopts` in misc scripts (new dependency)
- See docs/maintainers.md for details.

**Migration guide for plugin developers**

- Update imports: `from ocrmypdf._options import OcrOptions`
- Update type hints: `def check_options(options: OcrOptions)` instead of `options: Namespace`
- Attribute access remains unchanged: `options.languages`, `options.output_type`, etc.
- Remove any in-place option modifications - compute values at point of use instead
- Most existing plugins will continue working without changes due to duck-typing

