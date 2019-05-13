Release notes
=============

OCRmyPDF uses `semantic versioning <http://semver.org/>`_ for its command line interface and its public API.

The ``ocrmypdf`` package may now be imported. The public API may be useful in scripts that launch OCRmyPDF processes or that wish to use some of its features for working with PDFs.

Unfortunately, the public API does **not** expose the ability to actually OCR a PDF. This is due to a limitation in an underlying library (ruffus) that makes OCRmyPDF non-reentrant.

Note that it is licensed under GPLv3, so scripts that ``import ocrmypdf`` and are released publicly should probably also be licensed under GPLv3.

.. Issue regex
   find:    [^`]\#([0-9]{1,3})[^0-9]
   replace: `#$1 <https://github.com/jbarlow83/OCRmyPDF/issues/$1>`_

v8.3.0
------

-   Improved the strategy for updating pages when a new image of the page was produced. We know attempt to preserve more content from the original file, for annotations in particular.

-   For PDFs with more than 100 pages and a sequence where one PDF page was replaced and one or more subsequent ones were skipped, an intermediate file would be corrupted while grafting OCR text, causing processing to fail.

-   Previously, we resized the images produced by Ghostscript by a small number of pixels to ensure the output image size was an exactly what we wanted. Having discovered a way to get Ghostscript to produce the exact image sizes we require, we eliminated the resizing step.

-   Command line completions for ``bash`` are now available, in addition to ``fish``, both in ``misc/completion``. Package maintainers, please install these so users can take advantage.

-   Updated requirements.

-   pikepdf 1.3.0 is now required.

v8.2.4
------

-   Fixed a false positive while checking for a certain type of PDF that only Acrobat can read. We now more accurately detect Acrobat-only PDFs.

-   OCRmyPDF holds fewer open file handles and is more prompt about releasing those it no longer needs.

-   Minor optimization: we no longer traverse the table of contents to ensure all references in it are resolved, as changes to libqpdf have made this unnecessary.

-   pikepdf 1.2.0 is now required.

v8.2.3
------

-   Fixed that ``--mask-barcodes`` would occasionally leave a unwanted temporary file named ``junkpixt`` in the current working folder.

-   Fixed (hopefully) handling of Leptonica errors in an environment where a non-standard ``sys.stderr`` is present.

-   Improved help text for ``--verbose``.

v8.2.2
------

-   Fixed a regression from v8.2.0, an exception that occurred while attempting to report that ``unpaper`` or another optional dependency was unavailable.

-   In some cases, ``ocrmypdf [-c|--clean]`` failed to exit with an error when ``unpaper`` is not installed.

v8.2.1
------

-   This release was canceled.

v8.2.0
------

-   A major improvement to our Docker image is now available thanks to hard work contributed by @mawi12345. The new Docker image, ocrmypdf-alpine, is based on Alpine Linux, and includes most of the functionality of three existed images in a smaller package. This image will replace the main Docker image eventually but for now all are being built. `See documentation for details <https://ocrmypdf.readthedocs.io/en/latest/docker.html>`_.

-   Documentation reorganized especially around the use of Docker images.

-   Fixed a problem with PDF image optimization, where the optimizer would unnecessarily decompress and recompress PNG images, in some cases losing the benefits of the quantization it just had just performed. The optimizer is now capable of embedding PNG images into PDFs without transcoding them.

-   Fixed a minor regression with lossy JBIG2 image optimization. All JBIG2 candidates images were incorrectly placed into a single optimization group for the whole file, instead of grouping pages together. This usually makes a larger JBIG2Globals dictionary and results in inferior compression, so it worked less well than designed. However, quality would not be impacted. Lossless JBIG2 was entirely unaffected.

-   Updated dependencies, including pikepdf to 1.1.0. This fixes `#358 <https://github.com/jbarlow83/OCRmyPDF/issues/358>`_.

-   The install-time version checks for certain external programs have been removed from setup.py. These tests are now performed at run-time.

-   The non-standard option to override install-time checks (``setup.py install --force``) is now deprecated and prints a warning. It will be removed in a future release.

v8.1.0
------

-   Added a feature, ``--unpaper-args``, which allows passing arbitrary arguments to ``unpaper`` when using ``--clean`` or ``--clean-final``. The default, very conservative unpaper settings are suppressed.

-   The argument ``--clean-final`` now implies ``--clean``. It was possible to issue ``--clean-final`` on its before this, but it would have no useful effect.

-   Fixed an exception on traversing corrupt table of contents entries (specifically, those with invalid destination objects)

-   Fixed an issue when using ``--tesseract-timeout`` and image processing features on a file with more than 100 pages. `#347 <https://github.com/jbarlow83/OCRmyPDF/issues/347>`_

-   OCRmyPDF now always calls ``os.nice(5)`` to signal to operating systems that it is a background process.

v8.0.1
------

-   Fixed an exception when parsing PDFs that are missing a required field. `#325 <https://github.com/jbarlow83/OCRmyPDF/issues/325>`_

-   pikepdf 1.0.5 is now required, to address some other PDF parsing issues.

v8.0.0
------

No major features. The intent of this release is to sever support for older versions of certain dependencies.

**Breaking changes**

-   Dropped support for Tesseract 3.x. Tesseract 4.0 or newer is now required.

-   Dropped support for Python 3.5.

-   Some ``ocrmypdf.pdfa`` APIs that were deprecated in v7.x were removed. This functionality has been moved to pikepdf.

**Other changes**

-   Fixed an unhandled exception when attempting to mask barcodes. `#322 <https://github.com/jbarlow83/OCRmyPDF/issues/322>`_

-   It is now possible to use ocrmypdf without pdfminer.six, to support distributions that do not have it or cannot currently use it (e.g. Homebrew). Downstream maintainers should include pdfminer.six if possible.

-   A warning is now issue when PDF/A conversion removes some XMP metadata from the input PDF. (Only a "whitelist" of certain XMP metadata types are allowed in PDF/A.)

-   Fixed several issues that caused PDF/As to be produced with nonconforming XMP metadata (would fail validation with veraPDF).

-   Fixed some instances where invalid DocumentInfo from a PDF cause XMP metadata creation to fail.

-   Fixed a few documentation problems.

-   pikepdf 1.0.2 is now required.

v7.4.0
------

-   ``--force-ocr`` may now be used with the new ``--threshold`` and ``--mask-barcodes`` features

-   pikepdf >= 0.9.1 is now required.

-   Changed metadata handling to pikepdf 0.9.1. As a result, metadata handling of non-ASCII characters in Ghostscript 9.25 or later is fixed.

-   chardet >= 3.0.4 is temporarily listed as required. pdfminer.six depends on it, but the most recent release does not specify this requirement. (`#326 <https://github.com/jbarlow83/OCRmyPDF/issues/326>`_)

-   python-xmp-toolkit and libexempi are no longer required.

-   A new Docker image is now being provided for users who wish to access OCRmyPDF over a simple HTTP interface, instead of the command line.

-   Increase tolerance of PDFs that overflow or underflow the PDF graphics stack. (`#325 <https://github.com/jbarlow83/OCRmyPDF/issues/325>`_)

v7.3.1
------

-   Fixed performance regression from v7.3.0; fast page analysis was not selected when it should be.

-   Fixed a few exceptions related to the new ``--mask-barcodes`` feature and improved argument checking

-   Added missing detection of TrueType fonts that lack a Unicode mapping


v7.3.0
------

-   Added a new feature ``--redo-ocr`` to detect existing OCR in a file, remove it, and redo the OCR. This may be particularly helpful for anyone who wants to take advantage of OCR quality improvements in Tesseract 4.0. Note that OCR added by OCRmyPDF before version 3.0 cannot be detected since it was not properly marked as invisible text in the earliest versions. OCR that constructs a font from visible text, such as Adobe Acrobat's ClearScan.

-   OCRmyPDF's content detection is generally more sophisticated. It learns more about the contents of each PDF and makes better recommendations:

    -   OCRmyPDF can now detect when a PDF contains text that cannot be mapped to Unicode (meaning it is readable to human eyes but copy-pastes as gibberish). In these cases it recommends ``--force-ocr`` to make the text searchable.

    -   PDFs containing vector objects are now rendered at more appropriate resolution for OCR.

    -   We now exit with an error for PDFs that contain Adobe LiveCycle Designer's dynamic XFA forms. Currently the open source community does not have tools to work with these files.

    -   OCRmyPDF now warns when a PDF that contains Adobe AcroForms, since such files probably do not need OCR. It can work with these files.

-   Added three new **experimental** features to improve OCR quality in certain conditions. The name, syntax and behavior of these arguments is subject to change. They may also be incompatible with some other features.

    -   ``--remove-vectors`` which strips out vector graphics. This can improve OCR quality since OCR will not search artwork for readable text; however, it currently removes "text as curves" as well.

    -   ``--mask-barcodes`` to detect and suppress barcodes in files. We have observed that barcodes can interfere with OCR because they are "text-like" but not actually textual.

    -   ``--threshold`` which uses a more sophisticated thresholding algorithm than is currently in use in Tesseract OCR. This works around a `known issue in Tesseract 4.0 <https://github.com/tesseract-ocr/tesseract/issues/1990>`_ with dark text on bright backgrounds.

-   Fixed an issue where an error message was not reported when the installed Ghostscript was very old.

-   The PDF optimizer now saves files with object streams enabled when the optimization level is ``--optimize 1`` or higher (the default). This makes files a little bit smaller, but requires PDF 1.5. PDF 1.5 was first released in 2003 and is broadly supported by PDF viewers, but some rudimentary PDF parsers such as PyPDF2 do not understand object streams. You can use the command line tool ``qpdf --object-streams=disable`` or `pikepdf <https://github.com/pikepdf/pikepdf>`_ library to remove them.

-   New dependency: pdfminer.six 20181108. Note this is a fork of the Python 2-only pdfminer.

-   Deprecation notice: At the end of 2018, we will be ending support for Python 3.5 and Tesseract 3.x. OCRmyPDF v7 will continue to work with older versions.

v7.2.1
------

-   Fix compatibility with an API change in pikepdf 0.3.5.

-   A kludge to support Leptonica versions older than 1.72 in the test suite was dropped. Older versions of Leptonica are likely still compatible. The only impact is that a portion of the test suite will be skipped.


v7.2.0
------

**Lossy JBIG2 behavior change**

A user reported that ocrmypdf was in fact using JBIG2 in **lossy** compression mode. This was not the intended behavior. Users should `review the technical concerns with JBIG2 in lossy mode <https://abbyy.technology/en:kb:tip:jbig2_compression_and_ocr>`_ and decide if this is a concern for their use case.

JBIG2 lossy mode does achieve higher compression ratios than any other monochrome compression technology; for large text documents the savings are considerable. JBIG2 lossless still gives great compression ratios and is a major improvement over the older CCITT G4 standard.

Only users who have reviewed the concerns with JBIG2 in lossy mode should opt-in. As such, lossy mode JBIG2 is only turned on when the new argument ``--jbig2-lossy`` is issued. This is independent of the setting for ``--optimize``.

Users who did not install an optional JBIG2 encoder are unaffected.

(Thanks to user 'bsdice' for reporting this issue.)

**Other issues**

-   When the image optimizer quantizes an image to 1 bit per pixel, it will now attempt to further optimize that image as CCITT or JBIG2, instead of keeping it in the "flate" encoding which is not efficient for 1 bpp images. (`#297 <https://github.com/jbarlow83/OCRmyPDF/issues/297>`_)

-   Images in PDFs that are used as soft masks (i.e. transparency masks or alpha channels) are now excluded from optimization.

-   Fixed handling of Tesseract 4.0-rc1 which now accepts invalid Tesseract configuration files, which broke the test suite.

v7.1.0
------

-   Improve the performance of initial text extraction, which is done to determine if a file contains existing text of some kind or not. On large files, this initial processing is now about 20x times faster. (`#299 <https://github.com/jbarlow83/OCRmyPDF/issues/299>`_)

-   pikepdf 0.3.3 is now required.

-   Fixed issue `#231 <https://github.com/jbarlow83/OCRmyPDF/issues/231>`_, a problem with JPEG2000 images where image metadata was only available inside the JPEG2000 file.

-   Fixed some additional Ghostscript 9.25 compatibility issues.

-   Improved handling of KeyboardInterrupt error messages. (`#301 <https://github.com/jbarlow83/OCRmyPDF/issues/301>`_)

-   README.md is now served in GitHub markdown instead of reStructuredText.

v7.0.6
------

-   Blacklist Ghostscript 9.24, now that 9.25 is available and fixes many regressions in 9.24.


v7.0.5
------

-   Improve capability with Ghostscript 9.24, and enable the JPEG passthrough feature when this version in installed.

-   Ghostscript 9.24 lost the ability to set PDF title, author, subject and keyword metadata to Unicode strings. OCRmyPDF will set ASCII strings and warn when Unicode is suppressed. Other software may be used to update metadata. This is a short term work around.

-   PDFs generated by Kodak Capture Desktop, or generally PDFs that contain indirect references to null objects in their table of contents, would have an invalid table of contents after processing by OCRmyPDF that might interfere with other viewers. This has been fixed.

-   Detect PDFs generated by Adobe LiveCycle, which can only be displayed in Adobe Acrobat and Reader currently. When these are encountered, exit with an error instead of performing OCR on the "Please wait" error message page.

v7.0.4
------

-   Fix exception thrown when trying to optimize a certain type of PNG embedded in a PDF with the ``-O2``

-   Update to pikepdf 0.3.2, to gain support for optimizing some additional image types that were previously excluded from optimization (CMYK and grayscale). Fixes `#285 <https://github.com/jbarlow83/OCRmyPDF/issues/285>`_.

v7.0.3
------

-   Fix issue `#284 <https://github.com/jbarlow83/OCRmyPDF/issues/284>`_, an error when parsing inline images that have are also image masks, by upgrading pikepdf to 0.3.1

v7.0.2
------

-   Fix a regression with ``--rotate-pages`` on pages that already had rotations applied. (`#279 <https://github.com/jbarlow83/OCRmyPDF/issues/279>`_)

-   Improve quality of page rotation in some cases by rasterizing a higher quality preview image. (`#281 <https://github.com/jbarlow83/OCRmyPDF/issues/281>`_)

v7.0.1
------

-   Fix compatibility with img2pdf >= 0.3.0 by rejecting input images that have an alpha channel

-   Add forward compatibility for pikepdf 0.3.0 (unrelated to img2pdf)

-   Various documentation updates for v7.0.0 changes

v7.0.0
------

-   The core algorithm for combining OCR layers with existing PDF pages has been rewritten and improved considerably.  PDFs are no longer split into single page PDFs for processing; instead, images are rendered and the OCR results are grafted onto the input PDF.  The new algorithm uses less temporary disk space and is much more performant especially for large files.

-   New dependency: `pikepdf <https://github.com/pikepdf/pikepdf>`_. pikepdf is a powerful new Python PDF library driving the latest OCRmyPDF features, built on the QPDF C++ library (libqpdf).

-   New feature: PDF optimization with ``-O`` or ``--optimize``.  After OCR, OCRmyPDF will perform image optimizations relevant to OCR PDFs.

    +   If a JBIG2 encoder is available, then monochrome images will be converted, with the potential for huge savings on large black and white images, since JBIG2 is far more efficient than any other monochrome (bi-level) compression. (All known US patents related to JBIG2 have probably expired, but it remains the responsibility of the user to supply a JBIG2 encoder such as `jbig2enc <https://github.com/agl/jbig2enc>`_. OCRmyPDF does not implement JBIG2 encoding.)

    +   If ``pngquant`` is installed, OCRmyPDF will optionally use it to perform lossy quantization and compression of PNG images.

    +   The quality of JPEGs can also be lowered, on the assumption that a lower quality image may be suitable for storage after OCR.

    +   This image optimization component will eventually be offered as an independent command line utility.

    +   Optimization ranges from ``-O0`` through ``-O3``, where ``0`` disables optimization and ``3`` implements all options. ``1``, the default, performs only safe and lossless optimizations. (This is similar to GCC's optimization parameter.) The exact type of optimizations performed will vary over time.

-   Small amounts of text in the margins of a page, such as watermarks, page numbers, or digital stamps, will no longer prevent the rest of a page from being OCRed when ``--skip-text`` is issued. This behavior is based on a heuristic.

-   Removed features

    +   The deprecated ``--pdf-renderer tesseract`` PDF renderer was removed.

    +   ``-g``, the option to generate debug text pages, was removed because it was a maintenance burden and only worked in isolated cases. HOCR pages can still be previewed by running the hocrtransform.py with appropriate settings.

-   Removed dependencies

    +   ``PyPDF2``

    +   ``defusedxml``

    +   ``PyMuPDF``

-   The ``sandwich`` PDF renderer can be used with all supported versions of Tesseract, including that those prior to v3.05 which don't support ``-c textonly``. (Tesseract v4.0.0 is recommended and more efficient.)

-   ``--pdf-renderer auto`` option and the diagnostics used to select a PDF renderer now work better with old versions, but may make different decisions than past versions.

-   If everything succeeds but PDF/A conversion fails, a distinct return code is now returned (``ExitCode.pdfa_conversion_failed (10)``) where this situation previously returned ``ExitCode.invalid_output_pdf (4)``. The latter is now returned only if there is some indication that the output file is invalid.

-   Notes for downstream packagers

    +   There is also a new dependency on ``python-xmp-toolkit`` which in turn depends on ``libexempi3``.

    +   It may be necessary to separately ``pip install pycparser`` to avoid `another Python 3.7 issue <https://github.com/eliben/pycparser/pull/135>`_.

v6.2.5
------

-   Disable a failing test due to Tesseract 4.0rc1 behavior change. Previously, Tesseract would exit with an error message if its configuration was invalid, and OCRmyPDF would intercept this message. Now Tesseract issues a warning, which OCRmyPDF v6.2.5 may relay or ignore. (In v7.x, OCRmyPDF will respond to the warning.)

-   This release branch no longer supports using the optional PyMuPDF installation, since it was removed in v7.x.

-   This release branch no longer supports macOS. macOS users should upgrade to v7.x.

v6.2.4
------

-   Backport Ghostscript 9.25 compatibility fixes, which removes support for setting Unicode metadata
-   Backport blacklisting Ghostscript 9.24
-   Older versions of Ghostscript are still supported

v6.2.3
------

-   Fix compatibility with img2pdf >= 0.3.0 by rejecting input images that have an alpha channel
-   This version will be included in Ubuntu 18.10

v6.2.2
------

-   Backport compatibility fixes for Python 3.7 and ruffus 2.7.0 from v7.0.0
-   Backport fix to ignore masks when deciding what colors are on a page
-   Backport some minor improvements from v7.0.0: better argument validation and warnings about the Tesseract 4.0.0 ``--user-words`` regression

v6.2.1
------

-   Fix recent versions of Tesseract (after 4.0.0-beta1) not being detected as supporting the ``sandwich`` renderer (`#271 <https://github.com/ppjbarlow83/OCRmyPDF/issues/271>`_).

v6.2.0
------

-   **Docker**: The Docker image ``ocrmypdf-tess4`` has been removed. The main Docker images, ``ocrmypdf`` and ``ocrmypdf-polyglot`` now use Ubuntu 18.04 as a base image, and as such Tesseract 4.0.0-beta1 is now the Tesseract version they use. There is no Docker image based on Tesseract 3.05 anymore.

-   Creation of PDF/A-3 is now supported. However, there is no ability to attach files to PDF/A-3.

-   Lists more reasons why the file size might grow.

-   Fix issue `#262 <https://github.com/ppjbarlow83/OCRmyPDF/issues/262>`_, ``--remove-background`` error on PDFs contained colormapped (paletted) images.

-   Fix another XMP metadata validation issue, in cases where the input file's creation date has no timezone and the creation date is not overridden.


v6.1.5
------

-   Fix issue `#253 <https://github.com/jbarlow83/OCRmyPDF/issues/253>`_, a possible division by zero when using the ``hocr`` renderer.

-   Fix incorrectly formatted ``<xmp:ModifyDate>`` field inside XMP metadata for PDF/As.  veraPDF flags this as a PDF/A validation failure. The error is caused the timezone and final digit of the seconds of modified time to be omitted, so at worst the modification time stamp is rounded to the nearest 10 seconds.


v6.1.4
------

-   Fix issue `#248 <https://github.com/jbarlow83/OCRmyPDF/issues/248>`_ ``--clean`` argument may remove OCR from left column of text on certain documents. We now set ``--layout none`` to suppress this.

-   The test cache was updated to reflect the change above.

-   Change test suite to accommodate Ghostscript 9.23's new ability to insert JPEGs into PDFs without transcoding.

-   XMP metadata in PDFs is now examined using ``defusedxml`` for safety.

-   If an external process exits with a signal when asked to report its version, we now print the system error message instead of suppressing it.  This occurred when the required executable was found but was missing a shared library.

-   qpdf 7.0.0 or newer is now required as the test suite can no longer pass without it.

Notes
~~~~~

-   An apparent `regression in Ghostscript 9.23 <https://bugs.ghostscript.com/show_bug.cgi?id=699216>`_ will cause some ocrmypdf output files to become invalid in rare cases; the workaround for the moment is to set ``--force-ocr``.


v6.1.3
------

-   Fix issue `#247 <https://github.com/jbarlow83/OCRmyPDF/issues/247>`_, ``/CreationDate`` metadata not copied from input to output.

-   A warning is now issued when Python 3.5 is used on files with a large page count, as this case is known to regress to single core performance. The cause of this problem is unknown.


v6.1.2
------

-   Upgrade to PyMuPDF v1.12.5 which includes a more complete fix to `#239 <https://github.com/jbarlow83/OCRmyPDF/issues/239>`_.

-   Add ``defusedxml`` dependency.


v6.1.1
------

-   Fix text being reported as found on all pages if PyMuPDF is not installed.


v6.1.0
------

-   PyMuPDF is now an optional but recommended dependency, to alleviate installation difficulties on platforms that have less access to PyMuPDF than the author anticipated.  (For version 6.x only) install OCRmyPDF with ``pip install ocrmypdf[fitz]`` to use it to its full potential.

-   Fix ``FileExistsError`` that could occur if OCR timed out while it was generating the output file. (`#218 <https://github.com/jbarlow83/OCRmyPDF/issues/218>`_)

-   Fix table of contents/bookmarks all being redirected to page 1 when generating a PDF/A (with PyMuPDF).  (Without PyMuPDF the table of contents is removed in PDF/A mode.)

-   Fix "RuntimeError: invalid key in dict" when table of contents/bookmarks titles contained the character ``)``. (`#239 <https://github.com/jbarlow83/OCRmyPDF/issues/239>`_)

-   Added a new argument ``--skip-repair`` to skip the initial PDF repair step if the PDF is already well-formed (because another program repaired it).


v6.0.0
------

-   The software license has been changed to GPLv3. Test resource files and some individual sources may have other licenses.

-   OCRmyPDF now depends on `PyMuPDF <https://pymupdf.readthedocs.io/en/latest/installation/>`_. Including PyMuPDF is the primary reason for the change to GPLv3.

-   Other backward incompatible changes

    + The ``OCRMYPDF_TESSERACT``, ``OCRMYPDF_QPDF``, ``OCRMYPDF_GS`` and ``OCRMYPDF_UNPAPER`` environment variables are no longer used. Change ``PATH`` if you need to override the external programs OCRmyPDF uses.

    + The ``ocrmypdf`` package has been moved to ``src/ocrmypdf`` to avoid issues with accidental import.

    + The function ``ocrmypdf.exec.get_program`` was removed.

    + The deprecated module ``ocrmypdf.pageinfo`` was removed.

    + The ``--pdf-renderer tess4`` alias for ``sandwich`` was removed.

-   Fixed an issue where OCRmyPDF failed to detect existing text on pages, depending on how the text and fonts were encoded within the PDF. (`#233 <https://github.com/jbarlow83/OCRmyPDF/issues/233>`_, `#232 <https://github.com/jbarlow83/OCRmyPDF/issues/232>`_)

-   Fixed an issue that caused dramatic inflation of file sizes when ``--skip-text --output-type pdf`` was used. OCRmyPDF now removes duplicate resources such as fonts, images and other objects that it generates. (`#237 <https://github.com/jbarlow83/OCRmyPDF/issues/237>`_)

-   Improved performance of the initial page splitting step. Originally this step was not believed to be expensive and ran in a process. Large file testing revealed it to be a bottleneck, so it is now parallelized. On a 700 page file with quad core machine, this change saves about 2 minutes. (`#234 <https://github.com/jbarlow83/OCRmyPDF/issues/234>`_)

-   The test suite now includes a cache that can be used to speed up test runs across platforms. This also does not require computing checksums, so it's faster. (`#217 <https://github.com/jbarlow83/OCRmyPDF/issues/217>`_)


v5.7.0
------

-   Fixed an issue that caused poor CPU utilization on machines with more than 4 cores when running Tesseract 4. (Related to issue `#217 <https://github.com/jbarlow83/OCRmyPDF/issues/217>`_.)

-   The 'hocr' renderer has been improved. The 'sandwich' and 'tesseract' renderers are still better for most use cases, but 'hocr' may be useful for people who work with the PDF.js renderer in English/ASCII languages. (`#225 <https://github.com/jbarlow83/OCRmyPDF/issues/225>`_)

    + It now formats text in a matter that is easier for certain PDF viewers to select and extract copy and paste text. This should help macOS Preview and PDF.js in particular.
    + The appearance of selected text and behavior of selecting text is improved.
    + The PDF content stream now uses relative moves, making it more compact and easier for viewers to determine when two words on the same line.
    + It can now deal with text on a skewed baseline.
    + Thanks to @cforcey for the pull request, @jbreiden for many helpful suggestions, @ctbarbour for another round of improvements, and @acaloiaro for an independent review.

v5.6.3
------

-   Suppress two debug messages that were too verbose


v5.6.2
------

-   Development branch accidentally tagged as release. Do not use.


v5.6.1
------

-   Fix issue `#219 <https://github.com/jbarlow83/OCRmyPDF/issues/219>`_: change how the final output file is created to avoid triggering permission errors when the output is a special file such as ``/dev/null``
-   Fix test suite failures due to a qpdf 8.0.0 regression and Python 3.5's handling of symlink
-   The "encrypted PDF" error message was different depending on the type of PDF encryption. Now a single clear message appears for all types of PDF encryption.
-   ocrmypdf is now in Homebrew. Homebrew users are advised to the version of ocrmypdf in the official homebrew-core formulas rather than the private tap.
-   Some linting


v5.6.0
------

-   Fix issue `#216 <https://github.com/jbarlow83/OCRmyPDF/issues/216>`_: preserve "text as curves" PDFs without rasterizing file
-   Related to the above, messages about rasterizing are more consistent
-   For consistency versions minor releases will now get the trailing .0 they always should have had.


v5.5
----

-   Add new argument ``--max-image-mpixels``. Pillow 5.0 now raises an exception when images may be decompression bombs. This argument can be used to override the limit Pillow sets.
-   Fix output page cropped when using the sandwich renderer and OCR is skipped on a rotated and image-processed page
-   A warning is now issued when old versions of Ghostscript are used in cases known to cause issues with non-Latin characters
-   Fix a few parameter validation checks for ``-output-type pdfa-1`` and ``pdfa-2``


v5.4.4
------

-   Fix issue `#181 <https://github.com/jbarlow83/OCRmyPDF/issues/181>`_: fix final merge failure for PDFs with more pages than the system file handle limit (``ulimit -n``)
-   Fix issue `#200 <https://github.com/jbarlow83/OCRmyPDF/issues/200>`_: an uncommon syntax for formatting decimal numbers in a PDF would cause qpdf to issue a warning, which ocrmypdf treated as an error. Now this the warning is relayed.
-   Fix an issue where intermediate PDFs would be created at version 1.3 instead of the version of the original file. It's possible but unlikely this had side effects.
-   A warning is now issued when older versions of qpdf are used since issues like `#200 <https://github.com/jbarlow83/OCRmyPDF/issues/200>`_ cause qpdf to infinite-loop
-   Address issue `#140 <https://github.com/jbarlow83/OCRmyPDF/issues/140>`_: if Tesseract outputs invalid UTF-8, escape it and print its message instead of aborting with a Unicode error
-   Adding previously unlisted setup requirement, pytest-runner
-   Update documentation: fix an error in the example script for Synology with Docker images, improved security guidance, advised ``pip install --user``


v5.4.3
------

-   If a subprocess fails to report its version when queried, exit cleanly with an error instead of throwing an exception
-   Added test to confirm that the system locale is Unicode-aware and fail early if it's not
-   Clarified some copyright information
-   Updated pinned requirements.txt so the homebrew formula captures more recent versions


v5.4.2
------

-   Fixed a regression from v5.4.1 that caused sidecar files to be created as empty files


v5.4.1
------

-   Add workaround for Tesseract v4.00alpha crash when trying to obtain orientation and the latest language packs are installed


v5.4
----

-   Change wording of a deprecation warning to improve clarity
-   Added option to generate PDF/A-1b output if desired (``--output-type pdfa-1``); default remains PDF/A-2b generation
-   Update documentation


v5.3.3
------

-   Fixed missing error message that should occur when trying to force ``--pdf-renderer sandwich`` on old versions of Tesseract
-   Update copyright information in test files
-   Set system ``LANG`` to UTF-8 in Dockerfiles to avoid UTF-8 encoding errors


v5.3.2
------

-   Fixed a broken test case related to language packs


v5.3.1
------

-   Fixed wrong return code given for missing Tesseract language packs
-   Fixed "brew audit" crashing on Travis when trying to auto-brew


v5.3
----

-   Added ``--user-words`` and ``--user-patterns`` arguments which are forwarded to Tesseract OCR as words and regular expressions respective to use to guide OCR. Supplying a list of subject-domain words should assist Tesseract with resolving words. (`#165 <https://github.com/jbarlow83/OCRmyPDF/issues/165>`_)
-   Using a non Latin-1 language with the "hocr" renderer now warns about possible OCR quality and recommends workarounds (`#176 <https://github.com/jbarlow83/OCRmyPDF/issues/176>`_)
-   Output file path added to error message when that location is not writable (`#175 <https://github.com/jbarlow83/OCRmyPDF/issues/175>`_)
-   Otherwise valid PDFs with leading whitespace at the beginning of the file are now accepted


v5.2
----

-   When using Tesseract 3.05.01 or newer, OCRmyPDF will select the "sandwich" PDF renderer by default, unless another PDF renderer is specified with the ``--pdf-renderer`` argument. The previous behavior was to select ``--pdf-renderer=hocr``.
-   The "tesseract" PDF renderer is now deprecated, since it can cause problems with Ghostscript on Tesseract 3.05.00
-   The "tess4" PDF renderer has been renamed to "sandwich". "tess4" is now a deprecated alias for "sandwich".


v5.1
----

-   Files with pages larger than 200" (5080 mm) in either dimension are now supported with ``--output-type=pdf`` with the page size preserved (in the PDF specification this feature is called UserUnit scaling). Due to Ghostscript limitations this is not available in conjunction with PDF/A output.


v5.0.1
------

-   Fixed issue `#169 <https://github.com/jbarlow83/OCRmyPDF/issues/169>`_, exception due to failure to create sidecar text files on some versions of Tesseract 3.04, including the jbarlow83/ocrmypdf Docker image

v5.0
----

-   Backward incompatible changes

     + Support for Python 3.4 dropped. Python 3.5 is now required.
     + Support for Tesseract 3.02 and 3.03 dropped. Tesseract 3.04 or newer is required. Tesseract 4.00 (alpha) is supported.
     + The OCRmyPDF.sh script was removed.

-   Add a new feature, ``--sidecar``, which allows creating "sidecar" text files which contain the OCR results in plain text. These OCR text is more reliable than extracting text from PDFs. Closes `#126 <https://github.com/jbarlow83/OCRmyPDF/issues/126>`_.
-   New feature: ``--pdfa-image-compression``, which allows overriding Ghostscript's lossy-or-lossless image encoding heuristic and making all images JPEG encoded or lossless encoded as desired. Fixes `#163 <https://github.com/jbarlow83/OCRmyPDF/issues/163>`_.
-   Fixed issue `#143 <https://github.com/jbarlow83/OCRmyPDF/issues/143>`_, added ``--quiet`` to suppress "INFO" messages
-   Fixed issue `#164 <https://github.com/jbarlow83/OCRmyPDF/issues/164>`_, a typo
-   Removed the command line parameters ``-n`` and ``--just-print`` since they have not worked for some time (reported as Ubuntu bug `#1687308 <https://bugs.launchpad.net/ubuntu/+source/ocrmypdf/+bug/1687308>`_)

v4.5.6
------

-   Fixed issue `#156 <https://github.com/jbarlow83/OCRmyPDF/issues/156>`_, 'NoneType' object has no attribute 'getObject' on pages with no optional /Contents record.  This should resolve all issues related to pages with no /Contents record.
-   Fixed issue `#158 <https://github.com/jbarlow83/OCRmyPDF/issues/158>`_, ocrmypdf now stops and terminates if Ghostscript fails on an intermediate step, as it is not possible to proceed.
-   Fixed issue `#160 <https://github.com/jbarlow83/OCRmyPDF/issues/160>`_, exception thrown on certain invalid arguments instead of error message

v4.5.5
------

-   Automated update of macOS homebrew tap
-   Fixed issue `#154 <https://github.com/jbarlow83/OCRmyPDF/issues/154>`_, KeyError '/Contents' when searching for text on blank pages that have no /Contents record.  Note: incomplete fix for this issue.

v4.5.4
------

-   Fix ``--skip-big`` raising an exception if a page contains no images (`#152 <https://github.com/jbarlow83/OCRmyPDF/issues/152>`_) (thanks to @TomRaz)
-   Fix an issue where pages with no images might trigger "cannot write mode P as JPEG" (`#151 <https://github.com/jbarlow83/OCRmyPDF/issues/151>`_)

v4.5.3
------

-   Added a workaround for Ghostscript 9.21 and probably earlier versions would fail with the error message "VMerror -25", due to a Ghostscript bug in XMP metadata handling
-   High Unicode characters (U+10000 and up) are no longer accepted for setting metadata on the command line, as Ghostscript may not handle them correctly.
-   Fixed an issue where the ``tess4`` renderer would duplicate content onto output pages if tesseract failed or timed out
-   Fixed ``tess4`` renderer not recognized when lossless reconstruction is possible

v4.5.2
------

-   Fix issue `#147 <https://github.com/jbarlow83/OCRmyPDF/issues/147>`_. ``--pdf-renderer tess4 --clean`` will produce an oversized page containing the original image in the bottom left corner, due to loss DPI information.
-   Make "using Tesseract 4.0" warning less ominous
-   Set up machinery for homebrew OCRmyPDF tap

v4.5.1
------

-   Fix issue `#137 <https://github.com/jbarlow83/OCRmyPDF/issues/137>`_, proportions of images with a non-square pixel aspect ratio would be distorted in output for ``--force-ocr`` and some other combinations of flags

v4.5
----

-   PDFs containing "Form XObjects" are now supported (issue `#134 <https://github.com/jbarlow83/OCRmyPDF/issues/134>`_; PDF reference manual 8.10), and images they contain are taken into account when determining the resolution for rasterizing
-   The Tesseract 4 Docker image no longer includes all languages, because it took so long to build something would tend to fail
-   OCRmyPDF now warns about using ``--pdf-renderer tesseract`` with Tesseract 3.04 or lower due to issues with Ghostscript corrupting the OCR text in these cases

v4.4.2
------

-   The Docker images (ocrmypdf, ocrmypdf-polyglot, ocrmypdf-tess4) are now based on Ubuntu 16.10 instead of Debian stretch

    + This makes supporting the Tesseract 4 image easier
    + This could be a disruptive change for any Docker users who built customized these images with their own changes, and made those changes in a way that depends on Debian and not Ubuntu

-   OCRmyPDF now prevents running the Tesseract 4 renderer with Tesseract 3.04, which was permitted in v4.4 and v4.4.1 but will not work

v4.4.1
------

-   To prevent a `TIFF output error <https://github.com/python-pillow/Pillow/issues/2206>`_ caused by img2pdf >= 0.2.1 and Pillow <= 3.4.2, dependencies have been tightened
-   The Tesseract 4.00 simultaneous process limit was increased from 1 to 2, since it was observed that 1 lowers performance
-   Documentation improvements to describe the ``--tesseract-config`` feature
-   Added test cases and fixed error handling for ``--tesseract-config``
-   Tweaks to setup.py to deal with issues in the v4.4 release

v4.4
----

-   Tesseract 4.00 is now supported on an experimental basis.

    +  A new rendering option ``--pdf-renderer tess4`` exploits Tesseract 4's new text-only output PDF mode. See the documentation on PDF Renderers for details.
    +  The ``--tesseract-oem`` argument allows control over the Tesseract 4 OCR engine mode (tesseract's ``--oem``). Use ``--tesseract-oem 2`` to enforce the new LSTM mode.
    +  Fixed poor performance with Tesseract 4.00 on Linux

-   Fixed an issue that caused corruption of output to stdout in some cases
-   Removed test for Pillow JPEG and PNG support, as the minimum supported version of Pillow now enforces this
-   OCRmyPDF now tests that the intended destination file is writable before proceeding
-   The test suite now requires ``pytest-helpers-namespace`` to run (but not install)
-   Significant code reorganization to make OCRmyPDF re-entrant and improve performance. All changes should be backward compatible for the v4.x series.

    + However, OCRmyPDF's dependency "ruffus" is not re-entrant, so no Python API is available. Scripts should continue to use the command line interface.

v4.3.5
------

-   Update documentation to confirm Python 3.6.0 compatibility. No code changes were needed, so many earlier versions are likely supported.

v4.3.4
------

-   Fixed "decimal.InvalidOperation: quantize result has too many digits" for high DPI images

v4.3.3
------

-   Fixed PDF/A creation with Ghostscript 9.20 properly
-   Fixed an exception on inline stencil masks with a missing optional parameter

v4.3.2
------

-   Fixed a PDF/A creation issue with Ghostscript 9.20 (note: this fix did not actually work)

v4.3.1
------

-   Fixed an issue where pages produced by the "hocr" renderer after a Tesseract timeout would be rotated incorrectly if the input page was rotated with a /Rotate marker
-   Fixed a file handle leak in LeptonicaErrorTrap that would cause a "too many open files" error for files around hundred pages of pages long when ``--deskew`` or ``--remove-background`` or other Leptonica based image processing features were in use, depending on the system value of ``ulimit -n``
-   Ability to specify multiple languages for multilingual documents is now advertised in documentation
-   Reduced the file sizes of some test resources
-   Cleaned up debug output
-   Tesseract caching in test cases is now more cautious about false cache hits and reproducing exact output, not that any problems were observed

v4.3
----

-   New feature ``--remove-background`` to detect and erase the background of color and grayscale images
-   Better documentation
-   Fixed an issue with PDFs that draw images when the raster stack depth is zero
-   ocrmypdf can now redirect its output to stdout for use in a shell pipeline

    +  This does not improve performance since temporary files are still used for buffering
    +  Some output validation is disabled in this mode

v4.2.5
------

-   Fixed an issue (`#100 <https://github.com/jbarlow83/OCRmyPDF/issues/100>`_) with PDFs that omit the optional /BitsPerComponent parameter on images
-   Removed non-free file milk.pdf

v4.2.4
------

-   Fixed an error (`#90 <https://github.com/jbarlow83/OCRmyPDF/issues/90>`_) caused by PDFs that use stencil masks properly
-   Fixed handling of PDFs that try to draw images or stencil masks without properly setting up the graphics state (such images are now ignored for the purposes of calculating DPI)

v4.2.3
------

-   Fixed an issue with PDFs that store page rotation (/Rotate) in an indirect object
-   Integrated a few fixes to simplify downstream packaging (Debian)

    +  The test suite no longer assumes it is installed
    +  If running Linux, skip a test that passes Unicode on the command line

-   Added a test case to check explicit masks and stencil masks
-   Added a test case for indirect objects and linearized PDFs
-   Deprecated the OCRmyPDF.sh shell script

v4.2.2
------

-   Improvements to documentation

v4.2.1
------

-   Fixed an issue where PDF pages that contained stencil masks would report an incorrect DPI and cause Ghostscript to abort
-   Implemented stdin streaming

v4.2
----

-   ocrmypdf will now try to convert single image files to PDFs if they are provided as input (`#15 <https://github.com/jbarlow83/OCRmyPDF/issues/15>`_)

    +  This is a basic convenience feature. It only supports a single image and always makes the image fill the whole page.
    +  For better control over image to PDF conversion, use ``img2pdf`` (one of ocrmypdf's dependencies)

-   New argument ``--output-type {pdf|pdfa}`` allows disabling Ghostscript PDF/A generation

    +  ``pdfa`` is the default, consistent with past behavior
    +  ``pdf`` provides a workaround for users concerned about the increase in file size from Ghostscript forcing JBIG2 images to CCITT and transcoding JPEGs
    +  ``pdf`` preserves as much as it can about the original file, including problems that PDF/A conversion fixes

-   PDFs containing images with "non-square" pixel aspect ratios, such as 200x100 DPI, are now handled and converted properly (fixing a bug that caused to be cropped)
-   ``--force-ocr`` rasterizes pages even if they contain no images

    +  supports users who want to use OCRmyPDF to reconstruct text information in PDFs with damaged Unicode maps (copy and paste text does not match displayed text)
    +  supports reinterpreting PDFs where text was rendered as curves for printing, and text needs to be recovered
    +  fixes issue `#82 <https://github.com/jbarlow83/OCRmyPDF/issues/82>`_

-   Fixes an issue where, with certain settings, monochrome images in PDFs would be converted to 8-bit grayscale, increasing file size (`#79 <https://github.com/jbarlow83/OCRmyPDF/issues/79>`_)
-   Support for Ubuntu 12.04 LTS "precise" has been dropped in favor of (roughly) Ubuntu 14.04 LTS "trusty"

    +  Some Ubuntu "PPAs" (backports) are needed to make it work

-   Support for some older dependencies dropped

    +  Ghostscript 9.15 or later is now required (available in Ubuntu trusty with backports)
    +  Tesseract 3.03 or later is now required (available in Ubuntu trusty)

-   Ghostscript now runs in "safer" mode where possible

v4.1.4
------

-   Bug fix: monochrome images with an ICC profile attached were incorrectly converted to full color images if lossless reconstruction was not possible due to other settings; consequence was increased file size for these images

v4.1.3
------

-   More helpful error message for PDFs with version 4 security handler
-   Update usage instructions for Windows/Docker users
-   Fix order of operations for matrix multiplication (no effect on most users)
-   Add a few leptonica wrapper functions (no effect on most users)

v4.1.2
------

-   Replace IEC sRGB ICC profile with Debian's sRGB (from icc-profiles-free) which is more compatible with the MIT license
-   More helpful error message for an error related to certain types of malformed PDFs

v4.1
----

-   ``--rotate-pages`` now only rotates pages when reasonably confidence in the orientation. This behavior can be adjusted with the new argument ``--rotate-pages-threshold``
-   Fixed problems in error checking if ``unpaper`` is uninstalled or missing at run-time
-   Fixed problems with "RethrownJobError" errors during error handling that suppressed the useful error messages

v4.0.7
------

-   Minor correction to Ghostscript output settings

v4.0.6
------

-   Update install instructions
-   Provide a sRGB profile instead of using Ghostscript's

v4.0.5
------

-   Remove some verbose debug messages from v4.0.4
-   Fixed temporary that wasn't being deleted
-   DPI is now calculated correctly for cropped images, along with other image transformations
-   Inline images are now checked during DPI calculation instead of rejecting the image

v4.0.4
------

Released with verbose debug message turned on. Do not use. Skip to v4.0.5.

v4.0.3
------

New features

-   Page orientations detected are now reported in a summary comment

Fixes

-   Show stack trace if unexpected errors occur
-   Treat "too few characters" error message from Tesseract as a reason to skip that page rather than
    abort the file
-   Docker: fix blank JPEG2000 issue by insisting on Ghostscript versions that have this fixed


v4.0.2
------

Fixes


-   Fixed compatibility with Tesseract 3.04.01 release, particularly its different way of outputting
    orientation information
-   Improved handling of Tesseract errors and crashes
-   Fixed use of chmod on Docker that broke most test cases


v4.0.1
------

Fixes


-   Fixed a KeyError if tesseract fails to find page orientation information


v4.0
----

New features

-   Automatic page rotation (``-r``) is now available. It uses ignores any prior rotation information
    on PDFs and sets rotation based on the dominant orientation of detectable text. This feature is
    fairly reliable but some false positives occur especially if there is not much text to work with. (`#4 <https://github.com/jbarlow83/OCRmyPDF/issues/4>`_)
-   Deskewing is now performed using Leptonica instead of unpaper. Leptonica is faster and more reliable
    at image deskewing than unpaper.


Fixes

-   Fixed an issue where lossless reconstruction could cause some pages to be appear incorrectly
    if the page was rotated by the user in Acrobat after being scanned (specifically if it a /Rotate tag)
-   Fixed an issue where lossless reconstruction could misalign the graphics layer with respect to
    text layer if the page had been cropped such that its origin is not (0, 0) (`#49 <https://github.com/jbarlow83/OCRmyPDF/issues/49>`_)


Changes

-   Logging output is now much easier to read
-   ``--deskew`` is now performed by Leptonica instead of unpaper (`#25 <https://github.com/jbarlow83/OCRmyPDF/issues/25>`_)
-   libffi is now required
-   Some changes were made to the Docker and Travis build environments to support libffi
-   ``--pdf-renderer=tesseract`` now displays a warning if the Tesseract version is less than 3.04.01,
    the planned release that will include fixes to an important OCR text rendering bug in Tesseract 3.04.00.
    You can also manually install ./share/sharp2.ttf on top of pdf.ttf in your Tesseract tessdata folder
    to correct the problem.


v3.2.1
------

Changes

-   Fixed issue `#47 <https://github.com/jbarlow83/OCRmyPDF/issues/47>`_ "convert() got and unexpected keyword argument 'dpi'" by upgrading to img2pdf 0.2
-   Tweaked the Dockerfiles


v3.2
----

New features

-   Lossless reconstruction: when possible, OCRmyPDF will inject text layers without
    otherwise manipulating the content and layout of a PDF page. For example, a PDF containing a mix
    of vector and raster content would see the vector content preserved. Images may still be transcoded
    during PDF/A conversion.  (``--deskew`` and ``--clean-final`` disable this mode, necessarily.)
-   New argument ``--tesseract-pagesegmode`` allows you to pass page segmentation arguments to Tesseract OCR.
    This helps for two column text and other situations that confuse Tesseract.
-   Added a new "polyglot" version of the Docker image, that generates Tesseract with all languages packs installed,
    for the polyglots among us. It is much larger.

Changes

-   JPEG transcoding quality is now 95 instead of the default 75. Bigger file sizes for less degradation.



v3.1.1
------

Changes

-   Fixed bug that caused incorrect page size and DPI calculations on documents with mixed page sizes

v3.1
----

Changes

-   Default output format is now PDF/A-2b instead of PDF/A-1b
-   Python 3.5 and macOS El Capitan are now supported platforms - no changes were
    needed to implement support
-   Improved some error messages related to missing input files
-   Fixed issue `#20 <https://github.com/jbarlow83/OCRmyPDF/issues/20>`_ - uppercase .PDF extension not accepted
-   Fixed an issue where OCRmyPDF failed to text that certain pages contained previously OCR'ed text,
    such as OCR text produced by Tesseract 3.04
-   Inserts /Creator tag into PDFs so that errors can be traced back to this project
-   Added new option ``--pdf-renderer=auto``, to let OCRmyPDF pick the best PDF renderer.
    Currently it always chooses the 'hocrtransform' renderer but that behavior may change.
-   Set up Travis CI automatic integration testing

v3.0
----

New features

-   Easier installation with a Docker container or Python's ``pip`` package manager
-   Eliminated many external dependencies, so it's easier to setup
-   Now installs ``ocrmypdf`` to ``/usr/local/bin`` or equivalent for system-wide
    access and easier typing
-   Improved command line syntax and usage help (``--help``)
-   Tesseract 3.03+ PDF page rendering can be used instead for better positioning
    of recognized text (``--pdf-renderer tesseract``)
-   PDF metadata (title, author, keywords) are now transferred to the
    output PDF
-   PDF metadata can also be set from the command line (``--title``, etc.)
-   Automatic repairs malformed input PDFs if possible
-   Added test cases to confirm everything is working
-   Added option to skip extremely large pages that take too long to OCR and are
    often not OCRable (e.g. large scanned maps or diagrams); other pages are still
    processed (``--skip-big``)
-   Added option to kill Tesseract OCR process if it seems to be taking too long on
    a page, while still processing other pages (``--tesseract-timeout``)
-   Less common colorspaces (CMYK, palette) are now supported by conversion to RGB
-   Multiple images on the same PDF page are now supported

Changes

-   New, robust rewrite in Python 3.4+ with ruffus_ pipelines
-   Now uses Ghostscript 9.14's improved color conversion model to preserve PDF colors
-   OCR text is now rendered in the PDF as invisible text. Previous versions of OCRmyPDF
    incorrectly rendered visible text with an image on top.
-   All "tasks" in the pipeline can be executed in parallel on any
    available CPUs, increasing performance
-   The ``-o DPI`` argument has been phased out, in favor of ``--oversample DPI``, in
    case we need ``-o OUTPUTFILE`` in the future
-   Removed several dependencies, so it's easier to install.  We no
    longer use:

    - GNU parallel_
    - ImageMagick_
    - Python 2.7
    - Poppler
    - MuPDF_ tools
    - shell scripts
    - Java and JHOVE_
    - libxml2

-   Some new external dependencies are required or optional, compared to v2.x:

    - Ghostscript 9.14+
    - qpdf_ 5.0.0+
    - Unpaper_ 6.1 (optional)
    - some automatically managed Python packages

.. _ruffus: http://www.ruffus.org.uk/index.html
.. _parallel: https://www.gnu.org/software/parallel/
.. _ImageMagick: http://www.imagemagick.org/script/index.php
.. _MuPDF: http://mupdf.com/docs/
.. _qpdf: http://qpdf.sourceforge.net/
.. _Unpaper: https://github.com/Flameeyes/unpaper
.. _JHOVE: http://jhove.sourceforge.net/

Release candidates^

-   rc9:

    - fix issue `#118 <https://github.com/jbarlow83/OCRmyPDF/issues/118>`_: report error if ghostscript iccprofiles are missing
    - fixed another issue related to `#111 <https://github.com/jbarlow83/OCRmyPDF/issues/111>`_: PDF rasterized to palette file
    - add support image files with a palette
    - don't try to validate PDF file after an exception occurs

-   rc8:

    - fix issue `#111 <https://github.com/jbarlow83/OCRmyPDF/issues/111>`_: exception thrown if PDF is missing DocumentInfo dictionary

-   rc7:

    - fix error when installing direct from pip, "no such file 'requirements.txt'"

-   rc6:

    - dropped libxml2 (Python lxml) since Python 3's internal XML parser is sufficient
    - set up Docker container
    - fix Unicode errors if recognized text contains Unicode characters and system locale is not UTF-8

-   rc5:

    - dropped Java and JHOVE in favour of qpdf
    - improved command line error output
    - additional tests and bug fixes
    - tested on Ubuntu 14.04 LTS

-   rc4:

    - dropped MuPDF in favour of qpdf
    - fixed some installer issues and errors in installation instructions
    - improve performance: run Ghostscript with multithreaded rendering
    - improve performance: use multiple cores by default
    - bug fix: checking for wrong exception on process timeout

-   rc3: skipping version number intentionally to avoid confusion with Tesseract
-   rc2: first release for public testing to test-PyPI, Github
-   rc1: testing release process

Compatibility notes
-------------------

-   ``./OCRmyPDF.sh`` script is still available for now
-   Stacking the verbosity option like ``-vvv`` is no longer supported

-   The configuration file ``config.sh`` has been removed.  Instead, you can
    feed a file to the arguments for common settings:

::

    ocrmypdf input.pdf output.pdf @settings.txt

where ``settings.txt`` contains *one argument per line*, for example:

::

    -l
    deu
    --author
    A. Merkel
    --pdf-renderer
    tesseract


Fixes


-   Handling of filenames containing spaces: fixed

Notes and known issues

-   Some dependencies may work with lower versions than tested, so try
    overriding dependencies if they are "in the way" to see if they work.

-   ``--pdf-renderer tesseract`` will output files with an incorrect page size in Tesseract 3.03,
    due to a bug in Tesseract.

-   PDF files containing "inline images" are not supported and won't be for the 3.0 release. Scanned
    images almost never contain inline images.


v2.2-stable (2014-09-29)
------------------------

OCRmyPDF versions 1 and 2 were implemented as shell scripts. OCRmyPDF 3.0+ is a fork that gradually replaced all shell scripts with Python while maintaining the existing command line arguments. No one is maintaining old versions.

For details on older versions, see the `final version of its release notes <https://github.com/fritz-hh/OCRmyPDF/blob/7fd3dbdf42ca53a619412ce8add7532c5e81a9d1/RELEASE_NOTES.md>`_.
