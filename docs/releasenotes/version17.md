% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

# v17

## v17.12.0

**Changes**

- OCRmyPDF now requires pikepdf 10.2 or later, up from pikepdf 10. This is the
  first release that provides `pikepdf.NamePath`, the `Object.as_int()` family
  of type-safe accessors, and a thread-local `explicit_conversion()`. OCRmyPDF
  uses all three to read optional values out of PDFs it did not write.

**Fixes**

- Words containing `fi`, `ff`, `fl` and similar pairs extracted with the
  letters missing (`con dentiality`, `e ects`) from `--output-type pdfa` files
  when the PDF/A conversion ran through Ghostscript 10.05.0 through 10.06.x.
  Those Ghostscript releases drop ToUnicode entries that expand to more than
  one character (Ghostscript bug 709030, fixed in 10.07.0), and the fpdf2
  renderer's HarfBuzz shaping had been forming optional Latin ligatures whose
  entries do exactly that. Invisible text in scripts that do not need shaping
  is now encoded one glyph per character, so no such entries exist to lose.
  Complex scripts still get shaped, and OCRmyPDF now warns when an affected
  Ghostscript is in use, since their conjunct mappings can still be dropped.
  Thanks @kmn5 ({issue}`1744`).
- A malformed PDF that stores something other than a dictionary at a
  structural key -- `/Resources`, `/Resources /XObject`, `/Root /AcroForm`,
  `/Root /MarkInfo`, `/Root /Names`, `/Root /PieceInfo`, an annotation's `/A`,
  or an image's `/SMask` -- is now tolerated everywhere rather than in the
  handful of places that had been hardened individually. Such a file is read as
  though the key were absent, which is what the well-guarded paths already did.
- An image XObject with no `/Subtype` no longer raises out of the optimizer.
- `PdfInfo` no longer aborts on a `/MarkInfo << /Marked 1 >>`, where a producer
  wrote a flag as an integer instead of a Boolean. Thanks @linhongyu510
  ({issue}`1742`).
- A page `/UserUnit` written as a PDF Real is now read exactly rather than via
  binary floating point, so the digits the file wrote are the digits used.

## v17.11.0

**Enhancements**

- New `--max-ocr-image-mpixels` downsamples the image sent to OCR when a page
  exceeds the given size, which bounds the largest consumer of memory. The
  visible page is never downsampled, so output appearance is unaffected in every
  mode; what it trades is OCR accuracy on very high resolution scans. A 34
  megapixel page that peaks at 492 MB peaks at 325 MB under
  `--max-ocr-image-mpixels 8`, and recognizes the same text. See the "Memory"
  section of the performance documentation for how to size a memory limit.
- `watcher.py` (the `watcher` extra) gained a configurable output layout and
  conflict policy. These are watcher-only changes; they do not affect the
  `ocrmypdf` library API.
    - New `OCR_OUTPUT_STRUCTURE` setting (`--output-structure`): `FLAT`
      (default, all outputs directly in the destination directory),
      `YEAR_MONTH` (`{destination}/{year}/{month}/{filename}`, same layout as
      the old `OCR_OUTPUT_DIRECTORY_YEAR_MONTH=1`), or `HIERARCHY`, which
      mirrors the input directory tree under the destination, e.g.
      `input/a/b/c.pdf` → `output/a/b/c.pdf`.
    - New `OCR_ON_CONFLICT` setting (`--on-conflict`) controls what happens
      when the intended destination file already exists: `SUFFIX` (default)
      writes `name (1).pdf`, `name (2).pdf`, ... in the OS style; `SKIP` logs
      and leaves the file unprocessed; `OVERWRITE` is the old behavior.
      **Behavior change: the default is now `SUFFIX`, so existing output
      files are no longer silently overwritten.**
    - Both settings now apply equally to `OCR_OUTPUT_DIRECTORY` and to the
      archive directory used by `OCR_ON_SUCCESS_ARCHIVE`; previously the
      archive directory was always flat and silently overwrote on a name
      collision.
    - Output and archive filenames and directory components are sanitized
      for filesystems more restrictive than the input side (e.g. an SMB
      share): characters illegal on Windows/SMB (`<>:"/\|?*` and control
      characters) are replaced with `_`, trailing dots/spaces are stripped,
      and reserved DOS device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`-`9`,
      `LPT1`-`9`) are prefixed with `_`.
    - `OCR_OUTPUT_DIRECTORY_YEAR_MONTH` is now deprecated in favor of
      `OCR_OUTPUT_STRUCTURE=YEAR_MONTH`. It is still honored and logs a
      deprecation warning; if both are set, `OCR_OUTPUT_STRUCTURE` wins.
    - See the "Watched folders with watcher.py" section of the batch
      processing documentation for the full description, including a note
      for SMB users about client-side directory/file-info caching delays.

**Performance**

- The image sent to OCR is no longer decoded and re-encoded when nothing needs
  to change it. On a page with no pre-existing text to mask and no filtering
  plugin -- the ordinary case for a scanned document -- the rasterized page
  already *is* the OCR image, so it is linked rather than rewritten. Producing
  it was costing 3.3 seconds and a full-size buffer on a 34 megapixel page, out
  of about 15 seconds for the whole file. Building the mask is now deferred
  until a text area actually needs blanking, since that step is what forced the
  decode. The minimum Pillow version is raised to 12, because deciding whether
  anything decoded the image reads an attribute whose shape settled in Pillow 11
  (`pi-heif` already required Pillow 11.1, so the effective floor barely moves).
- Reduced peak memory on files with large images by about a third at default
  settings. On a 34 megapixel page the process tree peaked at 752 MB and now
  peaks at 492 MB. Two changes account for it: rasterizing a page no longer
  allocates a third full-page buffer to correct PDFium's rounding of the
  rendered size by a pixel or two, and freed heap memory is now returned to the
  operating system before the OCR engine runs, instead of counting against our
  resident set for as long as the engine is working. Rasterization is also
  faster, since correcting the size no longer resamples the whole page.
- Several OCR jobs may now run concurrently in a single Python process. The API
  previously held a lock for the whole duration of `ocrmypdf.ocr()`, so a second
  call in another thread had to wait for the first to finish. Plugin state is
  now guarded by a readers-writer lock: installing a plugin set takes it
  exclusively, and a job holds it shared for its run. An in-flight job therefore
  cannot have the plugin infrastructure it depends on replaced underneath it,
  while jobs that are past installation proceed concurrently.
- A plugin set is now installed once per interpreter and reused, rather than
  being reinstalled on every call. Previously each `ocrmypdf.ocr()` call
  re-executed plugin modules given as file paths and rebound them in
  `sys.modules`. Plugins must not rely on being re-executed for each job, and
  must not store per-job state on the plugin manager, which concurrent jobs
  requesting the same plugin set now share.
- Jobs requesting different plugin sets serialize against each other, since
  installing the second set must wait for the first set's jobs to finish. Use
  the same plugin set across concurrent jobs, or separate processes.
- Image optimization is substantially faster on documents with large images.
  An image stored as `/FlateDecode` with a PNG predictor already holds exactly
  what a PNG `IDAT` chunk holds, so it is now repackaged as a PNG directly
  instead of being decoded to a bitmap and re-encoded. On a 6-page document
  containing one 9000x9000 image, the optimization step went from 3.4s to 0.6s,
  and to 0.04s together with the JPEG change below; total runtime went from
  10.0s to 7.0s. Output is unchanged: the compressed
  data is reused verbatim. Images that are not in a directly repackageable form
  still take the previous path.
- During image optimization, we decoded all JPEGs, even if the code
  path was an optimization setting with the decoded JPEG would be never be
  re-encoded (below `--optimize 2`). We now decode only on code paths that
  use the decoded JPEG. Output is unchanged.
- An uncompressed image (one with no `/Filter`) no longer produces a spurious
  "could not be processed by the optimizer" warning. Such an image raised
  `IndexError` internally, which the optimizer's best-effort handler caught and
  reported as a warning; it is now recognized and skipped quietly.
- Removed an unreachable branch in the image optimizer that claimed to handle
  1 bit per component images in an ICC-based colorspace. An earlier check sends
  every 1 bpc image to the JBIG2 pass, which handles ICC-based images by
  neutralizing the profile before extracting, so the branch could never run.
- Removed the process-wide lock that serialized worker pools across all
  `Executor` instances. `Executor.pool_lock` is retained but no longer acquired,
  and is deprecated; it will be removed in a future major release. The invariant
  it protected - that only one progress bar renders on the shared console - is
  now enforced by the progress bar, which disables itself if another bar already
  owns the console.
- Note that N concurrent jobs each configured with `jobs=M` may now spawn up to
  N*M workers, where previously they were serialized to M. Size `jobs`
  accordingly.
- Known limitation of concurrent in-process jobs: they must use the same
  `max_image_mpixels`. Pillow's decompression-bomb limit is interpreter-global
  and the last job to set it wins. Use separate processes to run jobs with
  differing configurations.

**Fixes**

- Fixed a latent use-after-free in the pypdfium2 rasterizer. `to_pil()` lets
  Pillow alias PDFium's bitmap buffer for some formats -- grayscale renders
  among them, which is every mono and grayscale page -- and the buffer was freed
  immediately afterwards, leaving Pillow reading memory PDFium had released.
- Windows: OCRmyPDF no longer prints `[WinError 2] The system cannot find the
  file specified` warnings while it searches for Ghostscript and Tesseract
  ([#1671](https://github.com/ocrmypdf/OCRmyPDF/discussions/1671)). These
  messages came from probing registry keys that simply don't exist when the
  programs were installed by a package manager such as Scoop, or not installed
  at all. Since the search then continues elsewhere and usually succeeds, these
  failures are normal, and are now logged at debug level, naming the location
  that was searched. If a program genuinely cannot be found, OCRmyPDF still
  reports that as an error.
- Windows: fixed a crash when the `PROGRAMFILES` environment variable pointed to
  a folder that does not exist.
- `--mode strip` failed to remove OCR text layers that OCRmyPDF itself
  produced ({issue}`1730`). OCRmyPDF grafts its text layer as a Form XObject
  and stripping only examined the page content stream, so the invisible text
  was never found. The same flaw made `--mode redo` stack a second text layer
  on top of the old one instead of replacing it. Stripping now descends into
  Form XObjects. Thanks @Anai-Guo ({issue}`1732`).
- Stripping now also resolves page `/Resources` inherited from an ancestor
  `/Pages` node, rather than only looking at the page's own resources.
- A text layer that becomes empty after stripping is now removed from the page
  instead of being left behind as a vestigial Form XObject husk.
- Setting `clean_final` on an existing options object in the Python API no
  longer leaves `clean` unset. `--clean-final` implies `--clean`, but the rule
  lived in a field validator that only ran while the options object was being
  constructed, so assigning to the attribute afterwards silently skipped it.
- Validation errors for out-of-range or misspelled options now name the option
  they are about, and their wording comes from Pydantic rather than being
  hand-written, so it has changed slightly. For example, `--jobs 999` now
  reports `--jobs: Input should be less than or equal to 256`. The set of
  accepted values is unchanged.

## v17.10.0

- The `watcher.py` watched-folder helper (the `watcher` extra) has been
  modernized and security-hardened:
    - It now uses `watchfiles` instead of `watchdog`. Installing
      `ocrmypdf[watcher]` now pulls in `watchfiles`; native OS filesystem
      notifications are used by default, with `OCR_USE_POLLING=1` to force
      polling.
    - It enforces a "Harvard architecture" separation between data and code:
      at startup it refuses to run (exit code 9) if the input, output or
      archive directory overlaps any Python interpreter path (`sys.path`,
      the virtual environment, site-packages, or `$PATH`), if
      `OCR_JSON_SETTINGS` points at a file inside a data directory or one that
      is group/world-writable, or if it specifies a plugin located inside a
      data directory. It also refuses to run when the output or archive
      directory is the input directory or a subdirectory of it, which would
      otherwise cause OCRmyPDF output to be reprocessed in an endless loop.
    - At runtime it no longer follows symlinks or processes non-regular files
      (fifos, devices, etc.) in the watched directory, and refuses to write
      output onto a destination occupied by a non-regular file.
    - A password-protected PDF dropped into the watched folder no longer stops
      the watcher ({issue}`1715`). `pikepdf.PasswordError` does not derive from
      `pikepdf.PdfError`, so it escaped the handler that waits for a file to be
      fully written and tore down the watch loop, leaving files that arrived
      afterwards unprocessed. Encrypted files are now logged and skipped
      immediately — no amount of retrying will supply the password. More
      generally, no per-file error can stop the watcher now: failures are
      logged and watching continues. Thanks @christophdb for the report and a
      fix ({issue}`1716`).

  See the "Watcher security model" section of the batch processing
  documentation for details. Existing
  deployments where the data directories are kept separate from the application
  are unaffected; deployments that co-located data with the interpreter or its
  environment will need to relocate one or the other.
- Ghostscript 10.7.0 and later are no longer treated as affected by the JPEG
  passthrough truncation bug, which Ghostscript fixed in 10.07.0
  ({issue}`1726`). The version check had no upper bound, so users on a fixed
  Ghostscript still saw the "JPEG encoding errors" warning and, worse, silently
  had every JPEG lossily re-encoded at `--optimize 1` (the default) to work
  around a bug their Ghostscript did not have. Thanks @zuentec-droid for the
  detailed measurements and upstream analysis.
- The same JPEG re-encoding workaround no longer applies when Ghostscript did
  not produce the file at all. It was previously triggered by the mere presence
  of an affected Ghostscript, so `--output-type pdf` and files converted by the
  speculative PDF/A path — neither of which runs Ghostscript — paid the quality
  loss for nothing.

## v17.9.0

- OCRmyPDF now uses any Noto font installed on the system, not just the two
  dozen script families it knows by name ({issue}`1722`). Previously a document
  in, say, Cherokee or Vai was rendered with the glyphless fallback font even
  though the matching font was installed — a common situation on macOS, which
  ships around a hundred script-specific Noto faces. When the named fonts
  cannot cover a word, OCRmyPDF now searches the installed fonts for one that
  can.
- The "no installed font has glyphs" warning now names the characters it could
  not render, with their codepoints and Unicode names, so it is clear which
  font to install. Text that mixes scripts no single font covers is now
  reported as such, instead of advising the user to install fonts they may
  already have.
- Fixed the macOS font installation instructions, which recommended a Homebrew
  package (`font-noto`) that does not exist ({issue}`1722`). Homebrew has no
  single Noto package; each family is a separate cask. The Fedora package name
  was also corrected to `google-noto-fonts-all`.
- Font providers may now implement the optional `GlyphSearchingFontProvider`
  protocol to participate in coverage-based font search.
- Fixed `--jpeg-quality`/`--jpg-quality` having no effect on the CLI: the
  value was silently dropped before reaching the optimizer, which then
  always used its own built-in default JPEG quality regardless of what was
  requested ({issue}`1723`). The same bug affected the Python API's
  `jpg_quality` parameter. `ocrmypdf.ocr()` now accepts `jpeg_quality`
  (matching the CLI flag name) as the canonical parameter; `jpg_quality`
  still works but is deprecated.
- Hardened PDF parsing against malformed (non-dictionary) `/Resources`,
  `/XObject`, and `/FontDescriptor` entries, which previously crashed
  `ocrmypdf.ocr()` with `AttributeError`/`TypeError`/`ValueError` on
  otherwise-processable files, both during PDF/A font scanning and general
  image scanning ({issue}`1713`). Thanks @mvanhorn for the initial fix.
- Release process improvements: fixed a CI bug where every push to main
  after a release was tagged would incorrectly revert the just-published
  GitHub release back to draft status.

## v17.8.1

- Improved the `--tesseract-pagesegmode` help text to point to
  `tesseract --help-extra`, since Tesseract 5.5.2 moved the page segmentation
  mode documentation there from `tesseract --help`. Thanks @sokai.
- Internal refactoring: completed a project-wide mypy type-checking pass
  (`--check-untyped-defs` is now enabled, and the mypy pre-commit hook is now
  blocking rather than advisory), fixing several latent edge-case bugs
  surfaced along the way.
- Release process improvements: migrated from pre-commit to prek for local
  git hooks, and added a dedicated lint job to CI.
- Improved typing strictness for `Path`.

## v17.8.0

- `--output-type auto` (the default) again produces PDF/A whenever it can,
  matching OCRmyPDF 16's "PDF/A by default" behavior. It first tries the fast
  Ghostscript-free conversion (validated by veraPDF when available) and now
  falls back to Ghostscript when that cannot produce PDF/A, only emitting a
  regular PDF when even Ghostscript cannot safely convert (for example, an
  input with non-embedded CID/CJK fonts, per {issue}`1561`). A consequence is
  that the default path may once again invoke Ghostscript, which is slower and
  may transcode images; use `--output-type pdf` to skip PDF/A conversion
  entirely.
- Fixed detection of veraPDF 1.30.0 and newer: recent builds print JVM
  warnings before their version string, which caused OCRmyPDF to report
  veraPDF as unavailable and skip the fast PDF/A path.
- OCRmyPDF no longer silently corrupts a non-embedded CID (CJK) text layer when
  producing PDF/A ({issue}`1561`). PDF/A requires all fonts to be embedded, so
  Ghostscript substitutes and re-embeds non-embedded CID fonts — such as the OCR
  text layer Adobe Acrobat adds to scanned CJK documents — which mangles the
  text and destroys searchability. OCRmyPDF now detects non-embedded CID fonts
  before conversion: with `--output-type auto` (the default) it produces a
  regular PDF and preserves the existing text layer, and with an explicit
  `--output-type pdfa*` it stops with an error rather than emit corrupted
  output. Use `--output-type pdf` to keep the text layer, or `--force-ocr` to
  rebuild it with embedded fonts.
- Writing the output PDF to standard output (`ocrmypdf input.pdf -`) is now
  protected against corruption at the operating system level. Previously
  OCRmyPDF relied on no in-process code — third-party libraries, plugins, or
  stray `print()` calls — ever writing to stdout; a single accidental write
  would silently corrupt the PDF. The command line program now saves the real
  stdout at startup, before plugins are loaded or any worker process/thread is
  started, and redirects file descriptor 1 to stderr, so that only OCRmyPDF's
  final PDF output can reach stdout. A consequence is that a plugin which
  intentionally prints to stdout will have that output redirected to stderr.
- Added the public API function {func}`ocrmypdf.configure_stdout_protection`,
  which installs this same protection. Like {func}`ocrmypdf.configure_logging`,
  it is optional and intended for callers that want command-line-like behavior;
  applications that manage their own standard output should not call it.
- Fixed an uncaught `UnicodeDecodeError` when processing a PDF whose
  `/DocumentInfo` dictionary contains a `/Name` key encoded in Latin-1 (or
  another non-UTF-8 encoding), such as `/Saks#e5r`. `repair_docinfo_nuls` now
  treats such a block as malformed, logs a message, and continues instead of
  crashing the pipeline ({issue}`1540`). Current pikepdf releases tolerate these
  keys by surrogate-escaping them, but older versions raised while iterating the
  dictionary.

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

