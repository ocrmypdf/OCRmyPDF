.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

=============
Release notes
=============

OCRmyPDF uses `semantic versioning <http://semver.org/>`__ for its
command line interface and its public API.

OCRmyPDF's output messages are not considered part of the stable interface -
that is, output messages may be improved at any release level, so parsing them
may be unreliable. Use the API to depend on precise behavior.

The public API may be useful in scripts that launch OCRmyPDF processes or that
wish to use some of its features for working with PDFs.

The most recent release of OCRmyPDF is |OCRmyPDF PyPI|. Any newer versions
referred to in these notes may exist the main branch but have not been
tagged yet.

OCRmyPDF typically supports the three most recent Python versions.

.. note::

   Attention maintainers: these release notes may be updated with information
   about a forthcoming release that has not been tagged yet. A release is only
   official when it's tagged and posted to PyPI.

.. |OCRmyPDF PyPI| image:: https://img.shields.io/pypi/v/ocrmypdf.svg

v16.3.0
=======

-  Fixed progress bar not displaying for Ghostscript PDF/A conversion. :issue:`1313`
-  Added progress bar for linearization. :issue:`1313`
-  If `--rotate-pages-threshold` issued without `--rotate-pages` we now exit with
   an error since the user likely intended to use `--rotate-pages`. :issue:`1309`
-  If Tesseract hOCR gives an invalid line box, print an error message instead of
   exiting with an error. :issue:`1312`

v16.2.0
=======

-  Fixed issue 'NoneType' object has no attribute 'get' when optimizing certain PDFs.
   :issue:`1293,1271`
-  Switched formatting from black to ruff.
-  Added support for sending sidecar output to io.BytesIO.
-  Added support for converting HEIF/HEIC images (the native image of iPhones and
   some other devices) to PDFs, when the appropriate pi-hief library is installed.
   This library is marked as a dependency, but maintainers may opt out if needed.
-  We now default to downsampling large images that would exceed Tesseract's internal
   limits, but only if it cause processing to fail. Previously, this behavior only
   occurred if specifically requested on command line. It can still be configured
   and disabled. See the --tesseract command line options.
-  Added Macports install instructions. Thanks @akierig.
-  Improved logging output when an unexpected error occurs while trying to obtain
   the version of a third party program.

v16.1.2
=======

-  Fixed test suite failure when using Ghostscript 10.3.
-  Other minor corrections.

v16.1.1
=======

-  Fixed PyPy 3.10 support.

v16.1.0
=======

-  Improved hOCR renderer is now default for left to right languages.
-  Improved handling of rotated pages. Previously, OCR text might be missing for
   pages that were rotated with a /Rotate tag on the page entry.
-  Improved handling of cropped pages. Previously, in some cases a page with a
   crop box would not have its OCR applied correctly and misalignment between
   OCR text and visible text coudl occur.
-  Documentation improvements, especially installation instructions for less
   common platforms.

v16.0.4
=======

-  Fixed some issues for left-to-right text with the new hOCR renderer. It is still
   not default yet but will be made so soon. Right-to-left text is still in progress.
-  Added an error to prevent use of several versions of Ghostscript that seem
   corrupt existing text in input PDFs. Newly generated OCR is not affected.
   For best results, use Ghostscript 10.02.1 or newer, which contains the fix
   for the issue.

v16.0.3
=======

-  Changed minimum required Ghostscript to 9.54, to support users of RHEL 9 and its
   derivatives, since that is the latest version available there.
-  Removed warning message about CVE-2023-43115, on the assumption that most
   distributions have backported the patch by now.

v16.0.2
=======

-  Temporarily changed PDF text renderer back to sandwich by default to address
   regressions in macOS Preview.

v16.0.1
=======

-  Fixed text rendering issue with new hOCR text renderer - extraneous byte order
   marks.
-  Tightened dependencies.

v16.0.0
=======

-  Added OCR text renderer, combined the best ideas of Tesseract's PDF
   generator and the older hOCR transformer renderer. The result is a hopefully
   permanent fix for wordssmushedtogetherwithoutspaces issues in extracted text,
   better registration/position of text on skewed baselines :issue:`1009`,
   fixes to character output when the German Fraktur script is used :issue:`1191`,
   proper rendering of right to left languages (Arabic, Hebrew, Persian) :issue:`1157`.
   Asian languages may still have excessive word breaks compared to expectations.
   The new renderer is the default; the old sandwich renderer is still available
   using ``--pdf-renderer sandwich``; the old hOCR renderer is no more.
-  The ``ocrmypdf.hocrtransform`` API has changed substantially.
-  Support for Python 3.9 has been dropped. Python 3.10+ is now required.
-  pikepdf >= 8.8.0 is now required.


v15.4.4
=======

-  Fixed documentation for installing Ghostscript on Windows. :issue:`1198`
-  Added warning message about security issue in older versions of Ghostscript.

v15.4.3
=======

-  Fixed deprecation warning in pikepdf older than 8.7.1; pikepdf >= 8.7.1 is
   now required.

v15.4.2
=======

-  We now raise an exception on a certain class of PDFs that likely need an
   explicit color conversion strategy selected to display correctly
   for PDF/A conversion.
-  Fixed an error that occurred while trying to write a log message after the
   debug log handler was removed.

v15.4.1
=======

-  Fixed misc/watcher.py regressions: accept ``--ocr-json-settings`` as either
   filename or JSON string, as previously; and argument count mismatch.
   :issue:`1183,1185`
-  We no longer attempt to set /ProcSet in the PDF output, since this is an
   obsolete PDF feature.
-  Documentation improvements.

v15.4.0
=======

-  Added new experimental APIs to support offline editing of the final text.
   Specifically, one can now generate hOCR files with OCRmyPDF, edit them with
   some other tool, and then finalize the PDF. They are experimental and
   subject to change, including details of how the working folder is used.
   There is no command line interface.
-  Code reorganization: executors, progress bars, initialization and setup.
-  Fixed test coverage in cases where the coverage tool did not properly trace
   into threads or subprocesses. This code was still being tested but appeared
   as not covered.
-  In the test suite, reduced use of subprocesses and other techniques that
   interfere with coverage measurement.
-  Improved error check for when we appear to be running inside a snap container
   and files are not available.
-  Plugin specification now properly defines progress bars as a protocol rather
   than defining them as "tqdm-like".
-  We now default to using "forkserver" process creation on POSIX platforms
   rather than fork, since this is method is more robust and avoids some
   issues when threads are present.
-  Fixed an instance where the user's request to ``--no-use-threads`` was ignored.
-  If a PDF does not have language metadata on its top level object, we add
   the OCR language.
-  Replace some cryptic test error messages with more helpful ones.
-  Debug messages for how OCRmyPDF picks the colorspace for a page are now
   more descriptive.

v15.3.1
=======

-  Fixed an issue with logging settings for misc/watcher.py introduced in the
   previous release. :issue:`1180`
-  We now attempt to preserve the input's extended attributes when creating
   the output file.
-  For some reason, the macOS build now needs OpenSSL explicitly installed.
-  Updated documentation on Docker performance concerns.

v15.3.0
=======

-  Update misc/watcher.py to improve command line interface using Typer, and
   support ``.env`` specification of environment variables. Improved error
   messages. Thanks to @mflagg2814 for the PR that prompted this improvement.
-  Improved error message when a file cannot be read because we are running in
   a snap container.

v15.2.0
=======

-  Added a Docker image based on Alpine Linux. This image is smaller than the
   Ubuntu-based image and may be useful in some situations. Currently hosted at
   jbarlow83/ocrmypdf-alpine. Currently not available in ARM flavor.
-  The Ubuntu Docker is now aliased to jbarlow83/ocrmypdf-ubuntu.
-  Updated Docker documentation.

v15.1.0
=======

-  We now require Pillow 10.0.1, due a serious security vulnerability in all earlier
   versions of that dependency. The vulnerability concerns WebP images and could
   be triggered in OCRmyPDF when creating a PDF from a malicious WebP image.
-  Added some keyword arguments to ``ocrmypdf.ocr`` that were previously accepted
   but undocumented.
-  Documentation updates and typing improvements.

v15.0.2
=======

-  Added Python 3.12 to test matrix.
-  Updated documentation for notes on Python 3.12, 32-bit support and some new
   features in v15.

v15.0.1
=======

-  Wheels Python tag changed to py39.
-  Marked as a expected fail a test that fails on recent Ghostscript versions.
-  Clarified documentation and release notes around the extent of 32-bit support.
-  Updated installation documentation to changes in v15.

v15.0.0
=======

-  Dropped support for Python 3.8.
-  Dropped support some older dependencies, specifically ``coloredlogs`` and
   ``tqdm`` in favor of rich - see ``pyproject.toml`` for details.
   Generally speaking, Ubuntu 22.04 is our new baseline system.
-  Tightened version requirements for some dependencies.
-  Dropped support for 32-bit Linux wheels. We strongly recommend a 64-bit operating
   system, and 64-bit versions of Python, Tesseract and Ghostscript to use OCRmyPDF.
   Many of our dependencies are dropping 32-bit builds (e.g. Pillow), and we are
   following suit. (Maintainers may still build 32-bit versions from source.)
-  Changed to trusted release for PyPI publishing.
-  pikepdf memory mapping is enabled again for improved performance, now that an
   issue with feature in pikepdf is fixed.
-  ``ocrmypdf.helpers.calculate_downsample`` previously had two variants, one
   that took a ``PIL.Image`` and one that took a ``tuple[int, int]``. The latter
   was removed.
-  The snap version of ocrmypdf is now based on Ubuntu core22.
-  We now account for situations where a small portion of an image on a page is drawn
   at high DPI (resolution). Previously, the entire page would be rasterized at the
   highest resolution of any feature, which caused performance problems. Now,
   the page is rasterized
   at a resolution based on the average DPI of the page, weighted by the area that
   each feature occupies. Typically, small areas of high resolution in PDFs are
   errors or quirks from the repeated use of assets and high resolution is not
   beneficial. :issue:`1010,1104,1004,1079,1010`
-  Ghostscript color conversion strategy is now configurable using
   ``--color-conversion-strategy``. :issue:`1143`
-  JBIG2 threshold for optimization is now configurable using
   ``--jbig2-threshold``. :issue:`1133`

v14.4.0
=======

-  Digitally signed PDFs are now detected. If the PDF is signed, OCRmyPDF will
   refuse to modify it. Previously, only encrypted PDFs were detected, not
   those that were signed but not encrypted. :issue:`1040`
-  In addition, ``--invalidate-digital-signatures`` can be used to override the
   above behavior and modify the PDF anyway. :issue:`1040`
-  tqdm progress bars replaced with "rich" progress bars. The rich library is
   a new dependency. Certain APIs that used tqdm are now deprecated and will
   be removed in the next major release.
-  Improved integration with GitHub Releases. Thanks to @stumpylog.

v14.3.0
=======

-  Renamed master branch to main.
-  Improve PDF rasterization accuracy by using the ``-dPDFSTOPONERROR`` option
   to Ghostscript. Use ``--continue-on-soft-render-error`` if you want to render
   the PDF anyway. The plugin specification was adjusted to support this feature;
   plugin authors may want to adapt PDF rasterizing and rendering
   plugins. :issue:`1083`
-  The calculated deskew angle is now recorded in the logged output. :issue:`1101`
-  Metadata can now be unset by setting a metadata type such as ``--title`` to an
   empty string. :issue:`1117,1059`
-  Fixed random order of languages due to use of a set. This may have caused output
   to vary when multiple languages were set for OCR. :issue:`1113`
-  Clarified the optimization ratio reported in the log output.
-  Documentation improvements.

v14.2.1
=======

-  Fixed :issue:`977`, where images inside Form XObjects were always excluded
   from image optimization.

v14.2.0
=======

-  Added ``--tesseract-downsample-above`` to downsample larger images even when
   they do not exceed Tesseract's internal limits. This can be used to speed
   up OCR, possibly sacrificing accuracy.
-  Fixed resampling AttributeError on older Pillow. :issue:`1096`
-  Removed an error about using Ghostscript on PDFs with that have the /UserUnit
   feature in use. Previously, Ghostscript would fail to process these PDFs,
   but in all supported versions it is now supported, so the error is no longer
   needed.
-  Improved documentation around installing other language packs for Tesseract.

v14.1.0
=======

-  Added ``--tesseract-non-ocr-timeout``. This allows using Tesseract's deskew
   and other non-OCR features while disabling OCR using ``--tesseract-timeout 0``.
-  Added ``--tesseract-downsample-large-images``. This downsamples larges images
   that exceed the maximum image size Tesseract can handle. Large images may still
   take a long time to process, but this allows them to be processed if that
   is desired.
-  Fixed :issue:`1082`, an issue with snap packaged building.
-  Change linter to ruff, fix lint errors, update documentation.

v14.0.4
=======

-  Fixed :issue:`1066, 1075`, an exception when processing certain malformed PDFs.

v14.0.3
=======

-  Fixed :issue:`1068`, avoid deleting /dev/null when running as root.
-  Other documentation fixes.

v14.0.2
=======

-  Fixed :issue:`1052`, an exception on attempting to process certain nonconforming PDFs.
-  Explicitly documented that Windows 32-bit is no longer supported.
-  Fixed source installation instructions.
-  Other documentation fixes.

v14.0.1
=======

-  Fixed some version checks done with smart version comparison.
-  Added missing jbig2dec to Docker image.

v14.0.0
=======

-  Dropped support for Python 3.7.
-  Dropped support generally speaking, all dependencies older than what Ubuntu 20.04
   provides.
-  Ghostscript 9.50 or newer is now required. Shims to support old versions were
   removed.
-  Tesseract 4.1.1 or newer is now required. Shims to support old versions were
   removed.
-  Docker image now uses Tesseract 5.
-  Dropped setup.cfg configuration for pyproject.toml.
-  Removed deprecation exception PdfMergeFailedError.
-  A few more public domain test files were removed or replaced. We are aiming for
   100% compliance with SPDX and generally towards simplifying copyright.

v13.7.0
=======

-  Fixed an exception when attempting to run and Tesseract is not installed.
-  Changed to SPDX license tracking and information files.

v13.6.2
=======

-  Added a shim to prevent an "error during error handling" for Python 3.7 and 3.8.
-  Modernized some type annotations.
-  Improved annotations on our _windows module to help IDEs and mypy figure out what
   we're doing.

v13.6.1
=======

-  Require setuptools-scm 7.0.5 to avoid possible issues with source distributions in
   earlier versions of setuptools-scm.
-  Suppress a spurious warning, improve tests, improve typing and other miscellany.

v13.6.0
=======

-  Added a new ``initialize`` plugin hook, making it possible to suppress built-in
   plugins more easily, among other possibilities.
-  Fixed an issue where unpaper would exit with a "wrong stream" error, probably
   related to images with an odd integer width. :issue:`887, 665`

v13.5.0
=======

-  Added a new ``optimize_pdf`` plugin hook, making it possible to create plugins that
   replace or enhance OCRmyPDF's PDF optimizer.
-  Removed all max version restrictions. Our new policy is to blacklist known-bad releases
   and only block known-bad versions of dependencies.
-  The naming schema for object that holds all OCR text that OCRmyPDF inserts has
   changed. This has always been an implementation detail (and remains so), but possibly,
   someone was relying on it and would appreciate the heads-up.
-  Cleanup.

v13.4.7
=======

-  Fixed PermissionError when cleaning up temporary files in rare cases. :issue:`974`
-  Fixed PermissionError when calling ``os.nice`` on platforms that lack it. :issue:`973`
-  Suppressed some warnings from libxmp during tests.

v13.4.6
=======

-  Convert error on corrupt ICC profiles into a warning. Thanks to @oscherler.

v13.4.5
=======

-  Remove upper bound on pdfminer.six version.
-  Documentation.

v13.4.4
=======

-  Updated pdfminer.six version.
-  Docker image changed to Ubuntu 22.04 now that it is released and provides the
   dependencies we need. This seems more consistent than our recent change to
   Debian.

v13.4.3
=======

-  Fix error on pytest.skip() with older versions of pytest.
-  Documentation updates.

v13.4.2
=======

-  Worked around a
   `major regression in Ghostscript 9.56.0 <https://bugs.ghostscript.com/show_bug.cgi?id=705187>`__
   where **all OCR text is stripped out of the PDF**. It simply removes all text,
   even generated by software other than OCRmyPDF. Fortunately, we can ask
   Ghostscript 9.56.0 to use its old behavior that worked correctly for our purposes.
   Users must avoid the combination (Ghostscript 9.56.0, ocrmypdf <13.4.2) since
   older versions of OCRmyPDF have no way of detecting that this particular
   version of Ghostscript removes all OCR text.
-  Marked pdfminer 20220319 as supported.
-  Fixed some deprecation warnings from recent versions of Pillow and pytest.
-  Test suite now covers Python 3.10 (Python 3.10 worked fine before, but was not
   being tested).
-  Docker image now uses debian:bookworm-slim as the base image to fix the Docker
   image build.

v13.4.1
=======

-  Temporarily make threads rather than processes the default executor worker, due
   to a persistent deadlock issue when processes are used. Add a new command line
   argument ``--no-use-threads`` to disable this.

v13.4.0
=======

-  Fixed test failures when using pikepdf 5.0.0.
-  Various improvements to the optimizer. In particular, we now recognize PDF images
   that are encoded with both deflate (PNG) and DCT (JPEG), and also produce PDF
   with images compressed with deflate and DCT, since this often yields file size
   improvements compared to plain DCT.

v13.3.0
=======

-  Made a harmless but "scary" exception after failing to optimize an image less scary.
-  Added a warning if a page image is too large for unpaper to clean. The image is
   passed through without cleaning. This is due to a hard-coded limitation in a
   C library used by unpaper so it cannot be rectified easily.
-  We now use better default settings when calling img2pdf.
-  We no longer try to optimize images that we failed to save in certain situations.
-  We now account for some differences in text output from Tesseract 5 compared to
   Tesseract 4.
-  Better handling of Ghostscript producing empty images when attempting to rasterize
   page images.

v13.2.0
=======

-  Removed all runtime uses of distutils since it is deprecated in standard library. We
   previous used ``distutils.version`` to examine version numbers of dependencies
   at run time, and now use ``packaging.version`` for this. This is a new
   dependency.
-  Fixed an error message advising the user that Ghostscript was not installed being
   suppressed when this condition actually happens.
-  Fixed an issue with incorrect page number and totals being displayed in the progress
   bar. This was purely a display/presentation issue. :issue:`876`.

v13.1.1
=======

-  Fixed issue with attempting to deskew a blank page on Tesseract 5. :issue:`868`.

v13.1.0
=======

-  Changed to using Python concurrent.futures-based parallel execution instead of
   pools, since futures have now exceed pools in features.
-  If a child worker is terminated (perhaps by the operating system or the user
   killing it in a task manager), the parallel task will fail an error message.
   Previously, the main ocrmypdf process would "hang" indefinitely, waiting for the
   child to report.
-  Added new argument ``--tesseract-thresholding`` to provide control over Tesseract 5's
   threshold parameter.
-  Documentation updates and changes. Better documentation for ``--output-type none``,
   added a few releases ago. Removed some obsolete documentation.
-  Improved bash completions - thanks to @FPille.

v13.0.0
=======

**Breaking changes**

-  The deprecated module ``ocrmypdf.leptonica`` has been removed.
-  We no longer depend on Leptonica (``liblept``) or CFFI (``libffi``,
   ``python3-cffi``). (Note that Tesseract still requires Leptonica; OCRmyPDF no longer
   directly uses this library.)
-  The argument ``--remove-background`` is temporarily disabled while we search for an
   alternative to the Leptonica implementation of this feature.
-  The ``--threshold`` argument has been removed, since this also depended on Leptonica.
   Tesseract 5.x has implemented improvements to thresholding, so this feature will be
   redundant anyway.
-  ``--deskew`` was previous calculated by a Leptonica algorithm. We now use a feature
   of Tesseract to find the appropriate the angle to deskew a page. The deskew angle
   according to Tesseract may differ from Leptonica's algorithm. At least in theory,
   Tesseract's deskew angle is informed by a more complex analysis than Leptonica,
   so this should improve results in general. We also use Pillow to perform the
   deskewing, which may affect the appearance of the image compared to Leptonica.
-  Support for Python 3.6 was dropped, since this release is approaching end of life.
-  We now require pikepdf 4.0 or newer. This, in turn, means that OCRmyPDF requires
   a system compatible with the manylinux2014 specification. This change was "forced"
   by Pillow not releasing manylinux2010 wheels anymore.
-  We no longer provide requirements.txt-style files. Use ``pip install ocrmypdf[...]``
   instead.
-  Bumped required versions of several libraries.

**Fixes**

-  Fixed an issue where OCRmyPDF failed to find Ghostscript on Windows even when
   installed, and would exit with an error.
-  By removing Leptonica, we fixed all issues related to Leptonica on Apple
   Silicon or Leptonica failing to import on Windows.

v12.7.2
=======

-  Fixed "invalid version number" error for Tesseract packaging with nonstandard
   version "5.0.0-rc1.20211030".
-  Fixed use of deprecated ``importlib.resources.read_binary``.
-  Replace some uses of string paths with ``pathlib.Path``.
-  Fixed a leaked file handle when using ``--output-type none``.
-  Removed shims to support versions of pikepdf that are no longer supported.

v12.7.1
=======

-  Declare support for pdfminer.six v20211012.

v12.7.0
=======

-  Fixed test suite failure when using pikepdf 3.2.0 that was compiled with pybind11
   2.8.0. :issue:`843`
-  Improve advice to user about using ``--max-image-mpixels`` if OCR fails for this
   reason.
-  Minor documentation fixes. (Thanks to @mara004.)
-  Don't require importlib-metadata and importlib-resources backports on versions of
   Python where the standard library implementation is sufficient.
   (Thanks to Marco Genasci.)

v12.6.0
=======

-  Implemented ``--output-type=none`` to skip producing PDFs for applications that
   only want sidecar files (:issue:`787`).
-  Fixed ambiguities in descriptions of behavior of ``--jbig2-lossy``.
-  Various improvements to documentation.

v12.5.0
=======

-  Fixed build failure for the combination of PyPy 3.6 and pikepdf 3.0. This
   combination can work in a source build but does not work with wheels.
-  Accepted bot that wanted to upgrade our deprecated requirements.txt.
-  Documentation updates.
-  Replace pkg_resources and install dependency on setuptools with
   importlib-metadata and importlib-resources.
-  Fixed regression in hocrtransform causing text to be omitted when this
   renderer was used.
-  Fixed some typing errors.

v12.4.0
=======

-  When grafting text layers, use pikepdf's ``unparse_content_stream`` if available.
-  Confirmed support for pluggy 1.0. (Thanks @QuLogic.)
-  Fixed some typing issues, improved pre-commit settings, and fixed issues
   flagged by linters.
-  PyPy 7.3.3 (=Python 3.6) is now supported. Note that PyPy does not necessarily
   run faster, because the vast majority of OCRmyPDF's execution time is spent
   running OCR or generally executing native code. However, PyPy may bring speed
   improvements in some areas.

v12.3.3
=======

-  watcher.py: fixed interpretation of boolean env vars (:issue:`821`).
-  Adjust CI scripts to test Tesseract 5 betas.
-  Document our support for the Tesseract 5 betas.

v12.3.2
=======

-  Indicate support for flask 2.x, watcher 2.x (:issue:`815, 816`).

v12.3.1
=======

-  Fixed issue with selection of text when using the hOCR renderer (:issue:`813`).
-  Fixed build errors with the Docker image by upgrading to a newer Ubuntu.
   Also set the timezone of this image to UTC.

v12.3.0
=======

-  Fixed a regression introduced in Pillow 8.3.0. Pillow no longer rounds DPI
   for image resolutions. We now account for this (:issue:`802`).
-  We no longer use some API calls that are deprecated in the latest versions of
   pikepdf.
-  Improved error message when a language is requested that doesn't look like a
   typical ISO 639-2 code.
-  Fixed some tests that attempted to symlink on Windows, breaking tests on a
   Windows desktop but not usually on CI.
-  Documentation fixes (thanks to @mara004)

v12.2.0
=======

-  Fixed invalid Tesseract version number on Windows (:issue:`795`).
-  Documentation tweaks. Documentation build now depends on sphinx-issues package.

v12.1.0
=======

-  For security reasons we now require Pillow >= 8.2.x. (Older versions will continue
   to work if upgrading is not an option.)
-  The build system was reorganized to rely on ``setup.cfg`` instead of ``setup.py``.
   All changes should work with previously supported versions of setuptools.
-  The files in ``requirements/*`` are now considered deprecated but will be retained for v12.
   Instead use ``pip install ocrmypdf[test]`` instead of ``requirements/test.txt``, etc.
   These files will be removed in v13.

v12.0.3
=======

-  Expand the list of languages supported by the hocr PDF renderer.
   Several languages were previously considered not supported, particularly those
   non-European languages that use the Latin alphabet.
-  Fixed a case where the exception stack trace was suppressed in verbose mode.
-  Improved documentation around commercial OCR.

v12.0.2
=======

-  Fixed exception thrown when using ``--remove-background`` on files containing small
   images (:issue:`769`).
-  Improve documentation for description of adding language packs to the Docker image
   and corrected name of French language pack.

v12.0.1
=======

-  Fixed "invalid version number" for untagged tesseract versions (:issue:`770`).

v12.0.0
=======

**Breaking changes**

-  Due to recent security issues in pikepdf, Pillow and reportlab, we now require
   newer versions of these libraries and some of their dependencies. (If necessary,
   package maintainers may override these versions at their discretion; lower
   versions will often work.)
-  We now use the "LeaveColorUnchanged" color conversion strategy when directing
   Ghostscript to create a PDF/A. Generally this is faster than performing a
   color conversion, which is not always necessary.
-  OCR text is now packaged in a Form XObject. This makes it easier to isolate
   OCR from other document content. However, some poorly implemented PDF text
   extraction algorithms may fail to detect the text.
-  Many API functions have stricter parameter checking or expect keyword arguments
   were they previously did not.
-  Some deprecated functions in ``ocrmypdf.optimize`` were removed.
-  The ``ocrmypdf.leptonica`` module is now deprecated, due to difficulties with
   the current strategy of ABI binding on newer platforms like Apple Silicon.
   It will be removed and replaced, either by repackaging Leptonica as an
   independent library using or using a different image processing library.
-  Continuous integration moved to GitHub Actions.
-  We no longer depend on ``pytest_helpers_namespace`` for testing.

**New features**

-  New plugin hook: ``get_progressbar_class``, for progress reporting,
   allowing developers to replace the standard console progress bar with some
   other mechanism, such as updating a GUI progress bar.
-  New plugin hook: ``get_executor``, for replacing the concurrency model.
   This is primarily to support execution on AWS Lambda, which does not support
   standard Python ``multiprocessing`` due to its lack of shared memory.
-  New plugin hook: ``get_logging_console``, for replacing the standard
   way OCRmyPDF outputs its messages.
-  New plugin hook: ``filter_pdf_page``, for modifying individual PDF
   pages produced by OCRmyPDF.
-  OCRmyPDF now runs on nonstandard execution environments that do not have
   interprocess semaphores, such as AWS Lambda and Android Termux. If the environment
   does not have semaphores, OCRmyPDF will automatically select an alternate
   process executor that does not use semaphores.
-  Continuous integration moved to GitHub Actions.
-  We now generate an ARM64-compatible Docker image alongside the x64 image.
   Thanks to @andkrause for doing most of the work in a pull request several months
   ago, which we were finally able to integrate now. Also thanks to @0x326 for
   review comments.

**Fixes**

-  Fixed a possible deadlock on attempting to flush ``sys.stderr`` when older
   versions of Leptonica are in use.
-  Some worker processes inherited resources from their parents such as log
   handlers that may have also lead to deadlocks. These resources are now released.
-  Improvements to test coverage.
-  Removed vestiges of support for Tesseract versions older than 4.0.0-beta1 (
   which ships with Ubuntu 18.04).
-  OCRmyPDF can now parse all of Tesseract version numbers, since several
   schemes have been in use.
-  Fixed an issue with parsing PDFs that contain images drawn at a scale of 0. (:issue:`761`)
-  Removed a frequently repeated message about disabling mmap.

v11.7.3
=======

-  Exclude CCITT Group 3 images from being optimized. Some libraries
   OCRmyPDF uses do not seem to handle this obscure compression format properly.
   You may get errors or possible corrupted output images without this fix.

v11.7.2
=======

-  Updated pinned versions in main.txt, primarily to upgrade Pillow to 8.1.2, due
   to recently disclosed security vulnerabilities in that software.
-  The ``--sidecar`` parameter now causes an exception if set to the same file as
   the input or output PDF.

v11.7.1
=======

-  Some exceptions while attempting image optimization were only logged at the debug
   level, causing them to be suppressed. These errors are now logged appropriately.
-  Improved the error message related to ``--unpaper-args``.
-  Updated documentation to mention the new conda distribution.

v11.7.0
=======

-  We now support using ``--sidecar`` in conjunction with ``--pages``; these arguments
   used to be mutually exclusive. (:issue:`735`)
-  Fixed a possible issue with PDF/A-1b generation. Acrobat complained that our PDFs use
   object streams. More robust PDF/A validators like veraPDF don't consider this a
   problem, but we'll honor Acrobat's objection from here on. This may increase file
   size of PDF/A-1b files. PDF/A-2b files will not be affected.

v11.6.2
=======

-  Fixed a regression where the wrong page orientation would be produced when using
   arguments such as ``--deskew --rotate-pages`` (:issue:`730`).

v11.6.1
=======

-  Fixed an issue with attempting optimize unusually narrow-width images by excluding
   these images from optimization (:issue:`732`).
-  Remove an obsolete compatibility shim for a version of pikepdf that is no longer
   supported.

v11.6.0
=======

-  OCRmyPDF will now automatically register plugins from the same virtual environment
   with an appropriate setuptools entrypoint.
-  Refactor the plugin manager to remove unnecessary complications and make plugin
   registration more automatic.
-  ``PageContext`` and ``PdfContext`` are now formally part of the API, as they
   should have been, since they were part of ``ocrmypdf.pluginspec``.

v11.5.0
=======

-  Fixed an issue where the output page size might differ by a fractional amount
   due to rounding, when ``--force-ocr`` was used and the page contained objects
   with multiple resolutions.
-  When determining the resolution at which to rasterize a page, we now consider
   printed text on the page as requiring a higher resolution. This fixes issues
   with certain pages being rendered with unacceptably low resolution text, but
   may increase output file sizes in some workflows where low resolution text
   is acceptable.
-  Added a workaround to fix an exception that occurs when trying to
   ``import ocrmypdf.leptonica`` on Apple ARM silicon (or potentially, other
   platforms that do not permit write+executable memory).

v11.4.5
=======

-  Fixed an issue where files may not be closed when the API is used.
-  Improved ``setup.cfg`` with better settings for test coverage.

v11.4.4
=======

-  Fixed ``AttributeError: 'NoneType' object has no attribute 'userunit'`` (:issue:`700`),
   related to OCRmyPDF not properly forwarded an error message from pdfminer.six.
-  Adjusted typing of some arguments.
-  ``ocrmypdf.ocr`` now takes a ``threading.Lock`` for reasons outlined in the
   documentation.

v11.4.3
=======

-  Removed a redundant debug message.
-  Test suite now asserts that most patched functions are called when they should be.
-  Test suite now skips a test that fails on two particular versions of piekpdf.

v11.4.2
=======

-  Fixed support for Cygwin, hopefully.
-  watcher.py: Fixed an issue with the OCR_LOGLEVEL not being interpreted.

v11.4.1
=======

-  Fixed an issue where invalid pages ranges passed using the ``pages`` argument,
   such as "1-0" would cause unhandled exceptions.
-  Accepted a user-contributed to the Synology demo script in misc/synology.py.
-  Clarified documentation about change of temporary file location ``ocrmypdf.io``.
-  Fixed Python wheel tag which was incorrectly set to py35 even though we long
   since dropped support for Python 3.5.

v11.4.0
=======

-  When looking for Tesseract and Ghostscript, we now check the Windows Registry to
   see if their installers registered the location of their executables. This should
   help Windows users who have installed these programs to non-standard
   locations.
-  We now report on the progress of PDF/A conversion, since this operation is
   sometimes slow.
-  Improved command line completions.
-  The prefix of the temporary folder OCRmyPDF creates has been changed from
   ``com.github.ocrmypdf`` to ``ocrmypdf.io``. Scripts that chose to depend on this
   prefix may need to be adjusted. (This has always been an implementation detail so is
   not considered part of the semantic versioning "contract".)
-  Fixed :issue:`692`, where a particular file with malformed fonts would flood an
   internal message cue by generating so many debug messages.
-  Fixed an exception on processing hOCR files with no page record. Tesseract
   is not known to generate such files.

v11.3.4
=======

-  Fixed an error message 'called readLinearizationData for file that is not
   linearized' that may occur when pikepdf 2.1.0 is used. (Upgrading to pikepdf
   2.1.1 also fixes the issue.)
-  File watcher now automatically includes ``.PDF`` in addition to ``.pdf`` to
   better support case sensitive file systems.
-  Some documentation and comment improvements.

v11.3.3
=======

-  If unpaper outputs non-UTF-8 data, quietly fix this rather than choke on the
   conversion. (Possibly addresses :issue:`671`.)

v11.3.2
=======

-  Explicitly require pikepdf 2.0.0 or newer when running on Python 3.9. (There are
   concerns about the stability of pybind11 2.5.x with Python 3.9, which is used in
   pikepdf 1.x.)
-  Fixed another issue related to page rotation.
-  Fixed an issue where image marked as image masks were not properly considered
   as optimization candidates.
-  On some systems, unpaper seems to be unable to process the PNGs we offer it
   as input. We now convert the input to PNM format, which unpaper always accepts.
   Fixes :issue:`665` and :issue:`667`.
-  DPI sent to unpaper is now rounded to a more reasonable number of decimal digits.
-  Debug and error messages from unpaper were being suppressed.
-  Some documentation tweaks.

v11.3.1
=======

-  Declare support for new versions: pdfminer.six 20201018 and pikepdf 2.x
-  Fixed warning related to ``--pdfa-image-compression`` that appears at the wrong
   time.

v11.3.0
=======

-  The "OCR" step is describing as "Image processing" in the output messages when
   OCR is disabled, to better explain the application's behavior.
-  Debug logs are now only created when run as a command line, and not when OCR
   is performed for an API call. It is the calling application's responsibility
   to set up logging.
-  For PDFs with a low number of pages, we gathered information about the input PDF
   in a thread rather than process (when there are more pages). When run as a
   thread, we did not close the file handle to the working PDF, leaking one file
   handle per call of ``ocrmypdf.ocr``.
-  Fixed an issue where debug messages send by child worker processes did not match
   the log settings of parent process, causing messages to be dropped. This affected
   macOS and Windows only where the parent process is not forked.
-  Fixed the hookspec of rasterize_pdf_page to remove default parameters that
   were not handled in an expected way by pluggy.
-  Fixed another issue with automatic page rotation (:issue:`658`) due to the issue above.

v11.2.1
=======

-  Fixed an issue where optimization of a 1-bit image with a color palette or
   associated ICC that was optimized to JBIG2 could have its colors inverted.

v11.2.0
=======

-  Fixed an issue with optimizing PNG-type images that had soft masks or image masks.
   This is a regression introduced in (or about) v11.1.0.
-  Improved type checking of the ``plugins`` parameter for the ``ocrmypdf.ocr``
   API call.

v11.1.2
=======

-  Fixed hOCR renderer writing the text in roughly reverse order. This should not
   affect reasonably smart PDF readers that properly locate the position of all
   text, but may confuse those that rely on the order of objects in the content
   stream. (:issue:`642`)

v11.1.1
=======

-  We now avoid using named temporary files when using pngquant allowing containerized
   pngquant installs to be used.
-  Clarified an error message.
-  Highest number of 1's in a release ever!

v11.1.0
=======

-  Fixed page rotation issues: :issue:`634,589`.
-  Fixed some cases where optimization created an invalid image such as a
   1-bit "RGB" image: :issue:`629,620`.
-  Page numbers are now displayed in debug logs when pages are being grafted.
-  ocrmypdf.optimize.rewrite_png and ocrmypdf.optimize.rewrite_png_as_g4 were
   marked deprecated. Strictly speaking these should have been internal APIs,
   but they were never hidden.
-  As a precaution, pikepdf mmap-based file access has been disabled due to a
   rare race condition that causes a crash when certain objects are deallocated.
   The problem is likely in pikepdf's dependency pybind11.
-  Extended the example plugin to demonstrate conversion to mono.

v11.0.2
=======

-  Fixed :issue:`612`, TypeError exception. Fixed by eliminating unnecessary repair of
   input PDF metadata in memory.

v11.0.1
=======

-  Blacklist pdfminer.six 20200720, which has a regression fixed in 20200726.
-  Approve img2pdf 0.4 as it passes tests.
-  Clarify that the GPL-3 portion of pdfa.py was removed with the changes in v11.0.0;
   the debian/copyright file did not properly annotate this change.

v11.0.0
=======

-  Project license changed to Mozilla Public License 2.0. Some miscellaneous
   code is now under MIT license and non-code content/media remains under
   CC-BY-SA 4.0. License changed with approval of all people who were found
   to have contributed to GPLv3 licensed sections of the project. (:issue:`600`)
-  Because the license changed, this is being treated as a major version number
   change; however, there are no known breaking changes in functional behavior
   or API compared to v10.x.

v10.3.3
=======

-  Fixed a "KeyError: 'dpi'" error message when using ``--threshold`` on an image.
   (:issue:`607`)

v10.3.2
=======

-  Fixed a case where we reported "no reason" for a file size increase, when we
   could determine the reason.
-  Enabled support for pdfminer.six 20200726.

v10.3.1
=======

-  Fixed a number of test suite failures with pdfminer.six older than version 20200402.
-  Enabled support for pdfminer.six 20200720.

v10.3.0
=======

-  Fixed an issue where we would consider images that were already JBIG2-encoded
   for optimization, potentially producing a less optimized image than the original.
   We do not believe this issue would ever cause an image to loss fidelity.
-  Where available, pikepdf memory mapping is now used. This improves performance.
-  When Leptonica 1.79+ is installed, use its new error handling API to avoid
   a "messy" redirection of stderr which was necessary to capture its error
   messages.
-  For older versions of Leptonica, added a new thread level lock. This fixes a
   possible race condition in handling error conditions in Leptonica (although
   there is no evidence it ever caused issues in practice).
-  Documentation improvements and more type hinting.

v10.2.1
=======

-  Disabled calculation of text box order with pdfminer. We never needed this result
   and it is expensive to calculate on files with complex pre-existing text.
-  Fixed plugin manager to accept ``Path(plugin)`` as a path to a plugin.
-  Fixed some typing errors.
-  Documentation improvements.

v10.2.0
=======

-  Update Docker image to use Ubuntu 20.04.
-  Fixed issue PDF/A acquires title "Untitled" after conversion. (:issue:`582`)
-  Fixed a problem where, when using ``--pdf-renderer hocr``, some text would
   be missing from the output when using a more recent version of Tesseract.
   Tesseract began adding more detailed markup about the semantics of text
   that our HOCR transform did not recognize, so it ignored them. This option is
   not the default. If necessary ``--redo-ocr`` also redoing OCR to fix such issues.
-  Fixed an error in Python 3.9 beta, due to removal of deprecated
   ``Element.getchildren()``. (:issue:`584`)
-  Implemented support using the API with ``BytesIO`` and other file stream objects.
   (:issue:`545`)

v10.1.1
=======

-  Fixed ``OMP_THREAD_LIMIT`` set to invalid value error messages on some input
   files. (The error was harmless, apart from less than optimal performance in
   some cases.)

v10.1.0
=======

-  Previously, we ``--clean-final`` would cause an unpaper-cleaned page image to
   be produced twice, which was necessary in some cases but not in general. We
   now take this optimization opportunity and reuse the image if possible.
-  We now provide PNG files as input to unpaper, since it accepts them, instead
   of generating PPM files which can be very large. This can improve performance
   and temporary disk usage.
-  Documentation updated for plugins.

v10.0.1
=======

-  Fixed regression when ``-l lang1+lang2`` is used from command line.

v10.0.0
=======

**Breaking changes**

-  Support for pdfminer.six version 20181108 has been dropped, along with a
   monkeypatch that made this version work.
-  Output messages are now displayed in color (when supported by the terminal)
   and prefixes describing the severity of the message are removed. As such
   programs that parse OCRmyPDF's log message will need to be revised. (Please
   consider using OCRmyPDF as a library instead.)
-  The minimum version for certain dependencies has increased.
-  Many API changes; see developer changes.
-  The Python libraries pluggy and coloredlogs are now required.

**New features and improvements**

-  PDF page scanning is now parallelized across CPUs, speeding up this phase
   dramatically for files with a high page counts.
-  PDF page scanning is optimized, addressing some performance regressions.
-  PDF page scanning is no longer run on pages that are not selected when the
   ``--pages`` argument is used.
-  PDF page scanning is now independent of Ghostscript, ending our past reliance
   on this occasionally unstable feature in Ghostscript.
-  A plugin architecture has been added, currently allowing one to more easily
   use a different OCR engine or PDF renderer from Tesseract and Ghostscript,
   respectively. A plugin can also override some decisions, such changing
   the OCR settings after initial scanning.
-  Colored log messages.

**Developer changes**

-  The test spoofing mechanism, used to test correct handling of failures in
   Tesseract and Ghostscript, has been removed in favor of using plugins for
   testing. The spoofing mechanism was fairly complex and required many special
   hacks for Windows.
-  Code describing the resolution in DPI of images was refactored into a
   ``ocrmypdf.helpers.Resolution`` class.
-  The module ``ocrmypdf._exec`` is now private to OCRmyPDF.
-  The ``ocrmypdf.hocrtransform`` module has been updated to follow PEP8 naming
   conventions.
-  Ghostscript is no longer used for finding the location of text in PDFs, and
   APIs related to this feature have been removed.
-  Lots of internal reorganization to support plugins.

v9.8.2
======

-  Fixed an issue where OCRmyPDF would ignore text inside Form XObject when
   making certain decisions about whether a document already had text.
-  Fixed file size increase warning to take overhead of small files into account.
-  Added instructions for installing on Cygwin.

v9.8.1
======

-  Fixed an issue where unexpected files in the ``%PROGRAMFILES%\gs`` directory
   (Windows) caused an exception.
-  Mark pdfminer.six 20200517 as supported.
-  If jbig2enc is missing and optimization is requested, a warning is issued
   instead of an error, which was the intended behavior.
-  Documentation updates.

v9.8.0
======

-  Fixed issue where only the first PNG (FlateDecode) image in a file would be
   considered for optimization. File sizes should be improved from here on.
-  Fixed a startup crash when the chosen language was Japanese (:issue:`543`).
-  Added options to configure polling and log level to watcher.py.

v9.7.2
======

-  Fixed an issue with ``ocrmypdf.ocr(...language=)`` not accepting a list of
   languages as documented.
-  Updated setup.py to confirm that pdfminer.six version 20200402 is supported.

v9.7.1
======

-  Fixed version check failing when used with qpdf 10.0.0.
-  Added some missing type annotations.
-  Updated documentation to warn about need for "ifmain" guard and Windows.

v9.7.0
======

-  Fixed an error in watcher.py if ``OCR_JSON_SETTINGS`` was not defined.
-  Ghostscript 9.51 is now blacklisted, due to numerous problems with this version.
-  Added a workaround for a problem with "txtwrite" in Ghostscript 9.52.
-  Fixed an issue where the incorrect number of threads used was shown when
   ``OMP_THREAD_LIMIT`` was manipulated.
-  Removed a possible performance bottlenecks for files that use hundreds to
   thousands of images on the same page.
-  Documentation improvements.
-  Optimization will now be applied to some monochrome images that have a color
   profile defined instead of only black and white.
-  ICC profiles are consulted when determining the simplified colorspace of an
   image.

v9.6.1
======

-  Documentation improvements - thanks to many users for their contributions!

      - Fixed installation instructions for ArchLinux (@pigmonkey)
      - Updated installation instructions for FreeBSD and other OSes (@knobix)
      - Added instructions for using Docker Compose with watchdog (@ianalexander,
        @deisi)
      - Other miscellany (@mb720, @toy, @caiofacchinato)
      - Some scripts provided in the documentation have been migrated out so that
        they can be copied out as whole files, and to ensure syntax checking
        is maintained.

-  Fixed an error that caused bash completions to fail on macOS. (:issue:`502,504`;
   @AlexanderWillner)
-  Fixed a rare case where OCRmyPDF threw an exception while processing a PDF
   with the wrong object type in its ``/Trailer /Info``. The error is now logged
   and incorrect object is ignored. (:issue:`497`)
-  Removed potentially non-free file ``enron1.pdf`` and simplified the test that
   used it.
-  Removed potentially non-free file ``misc/media/logo.afdesign``.

v9.6.0
======

-  Fixed a regression with transferring metadata from the input PDF to the output
   PDF in certain situations.
-  pdfminer.six is now supported up to version 2020-01-24.
-  Messages are explaining page rotation decisions are now shown at the standard
   verbosity level again when ``--rotate-pages``. In some previous version they
   were set to debug level messages that only appeared with the parameter ``-v1``.
-  Improvements to ``misc/watcher.py``. Thanks to @ianalexander and @svenihoney.
-  Documentation improvements.

v9.5.0
======

-  Added API functions to measure OCR quality.
-  Modest improvements to handling PDFs with difficult/non compliant metadata.

v9.4.0
======

-  Updated recommended dependency versions.
-  Improvements to test coverage and changes to facilitate better measurement of
   test coverage, such as when tests run in subprocesses.
-  Improvements to error messages when Leptonica is not installed correctly.
-  Fixed use of pytest "session scope" that may have caused some intermittent
   CI failures.
-  When the argument ``--keep-temporary-files`` or verbosity is set to ``-v1``,
   a debug log file is generated in the working temporary folder.

v9.3.0
======

-  Improved native Windows support: we now check in the obvious places in
   the "Program Files" folders installations of Tesseract and Ghostscript,
   rather than relying on the user to edit ``PATH`` to specify their location.
   The ``PATH`` environment variable can still be used to differentiate when
   multiple installations are present or the programs are installed to non-
   standard locations.
-  Fixed an exception on parsing Ghostscript error messages.
-  Added an improved example demonstrating how to set up a watched folder
   for automated OCR processing (thanks to @ianalexander for the contribution).

v9.2.0
======

-  Native Windows is now supported.
-  Continuous integration moved to Azure Pipelines.
-  Improved test coverage and speed of tests.
-  Fixed an issue where a page that was originally a JPEG would be saved as a
   PNG, increasing file size. This occurred only when a preprocessing option
   was selected along with ``--output-type=pdf`` and all images on the original
   page were JPEGs. Regression since v7.0.0.
-  OCRmyPDF no longer depends on the QPDF executable ``qpdf`` or ``libqpdf``.
   It uses pikepdf (which in turn depends on ``libqpdf``). Package maintainers
   should adjust dependencies so that OCRmyPDF no longer calls for libqpdf on
   its own. For users of Python binary wheels, this change means a separate
   installation of QPDF is no longer necessary. This change is mainly to
   simplify installation on Windows.
-  Fixed a rare case where log messages from Tesseract would be discarded.
-  Fixed incorrect function signature for pixFindPageForeground, causing
   exceptions on certain platforms/Leptonica versions.

v9.1.1
======

-  Expand the range of pdfminer.six versions that are supported.
-  Fixed Docker build when using pikepdf 1.7.0.
-  Fixed documentation to recommend using pip from get-pip.py.

v9.1.0
======

-  Improved diagnostics when file size increases at output. Now warns if JBIG2
   or pngquant were not available.
-  pikepdf 1.7.0 is now required, to pick up changes that remove the need for
   a source install on Linux systems running Python 3.8.

v9.0.5
======

-  The Alpine Docker image (jbarlow83/ocrmypdf-alpine) has been dropped due to
   the difficulties of supporting Alpine Linux.
-  The primary Docker image (jbarlow83/ocrmypdf) has been improved to take on
   the extra features that used to be exclusive to the Alpine image.
-  No changes to application code.
-  pdfminer.six version 20191020 is now supported.

v9.0.4
======

-  Fixed compatibility with Python 3.8 (but requires source install for the moment).
-  Fixed Tesseract settings for ``--user-words`` and ``--user-patterns``.
-  Changed to pikepdf 1.6.5 (for Python 3.8).
-  Changed to Pillow 6.2.0 (to mitigate a security vulnerability in earlier Pillow).
-  A debug message now mentions when English is automatically selected if the locale
   is not English.

v9.0.3
======

-  Embed an encoded version of the sRGB ICC profile in the intermediate
   Postscript file (used for PDF/A conversion). Previously we included the
   filename, which required Postscript to run with file access enabled. For
   security, Ghostscript 9.28 enables ``-dSAFER`` and as such, no longer
   permits access to any file by default. This fix is necessary for
   compatibility with Ghostscript 9.28.
-  Exclude a test that sometimes times out and fails in continuous integration
   from the standard test suite.

v9.0.2
======

-  The image optimizer now skips optimizing flate (PNG) encoded images in some
   situations where the optimization effort was likely wasted.
-  The image optimizer now ignores images that specify arbitrary decode arrays,
   since these are rare.
-  Fixed an issue that caused inversion of black and white in monochrome images.
   We are not certain but the problem seems to be linked to Leptonica 1.76.0 and
   older.
-  Fixed some cases where the test suite failed if
   English or German Tesseract language packs were not installed.
-  Fixed a runtime error if the Tesseract English language is not installed.
-  Improved explicit closing of Pillow images after use.
-  Actually fixed of Alpine Docker image build.
-  Changed to pikepdf 1.6.3.

v9.0.1
======

-  Fixed test suite failing when either of optional dependencies unpaper and
   pngquant were missing.
-  Attempted fix of Alpine Docker image build.
-  Documented that FreeBSD ports are now available.
-  Changed to pikepdf 1.6.1.

v9.0.0
======

**Breaking changes**

-  The ``--mask-barcodes`` experimental feature has been dropped due to poor
   reliability and occasional crashes, both due to the underlying library that
   implements this feature (Leptonica).
-  The ``-v`` (verbosity level) parameter now accepts only ``0``, ``1``, and
   ``2``.
-  Dropped support for Tesseract 4.00.00-alpha releases. Tesseract 4.0 beta and
   later remain supported.
-  Dropped the ``ocrmypdf-polyglot`` and ``ocrmypdf-webservice`` images.

**New features**

-  Added a high level API for applications that want to integrate OCRmyPDF.
   Special thanks to Martin Wind (@mawi1988) whose made significant contributions
   to this effort.
-  Added progress bars for long-running steps. ■■■■■■■□□
-  We now create linearized ("fast web view") PDFs by default. The new parameter
   ``--fast-web-view`` provides control over when this feature is applied.
-  Added a new ``--pages`` feature to limit OCR to only a specific page range.
   The list may contain commas or single pages, such as ``1, 3, 5-11``.
-  When the number of pages is small compared to the number of allowed jobs, we
   run Tesseract in multithreaded (OpenMP) mode when available. This should
   improve performance on files with low page counts.
-  Removed dependency on ``ruffus``, and with that, the non-reentrancy
   restrictions that previous made an API impossible.
-  Output and logging messages overhauled so that ocrmypdf may be integrated
   into applications that use the logging module.
-  pikepdf 1.6.0 is required.
-  Added a logo. 😊

**Bug fixes**

-  Pages with vector artwork are treated as full color. Previously, vectors
   were ignored when considering the colorspace needed to cover a page, which
   could cause loss of color under certain settings.
-  Test suite now spawns processes less frequently, allowing more accurate
   measurement of code coverage.
-  Improved test coverage.
-  Fixed a rare division by zero (if optimization produced an invalid file).
-  Updated Docker images to use newer versions.
-  Fixed images encoded as JBIG2 with a colorspace other than ``/DeviceGray``
   were not interpreted correctly.
-  Fixed a OCR text-image registration (i.e. alignment) problem when the page
   when MediaBox had a nonzero corner.

v8.3.2
======

-  Dropped workaround for macOS that allowed it work without pdfminer.six,
   now a proper sdist release of pdfminer.six is available.

-  pikepdf 1.5.0 is now required.

v8.3.1
======

-  Fixed an issue where PDFs with malformed metadata would be rendered as
   blank pages. :issue:`398`.

v8.3.0
======

-  Improved the strategy for updating pages when a new image of the page
   was produced. We now attempt to preserve more content from the
   original file, for annotations in particular.
-  For PDFs with more than 100 pages and a sequence where one PDF page
   was replaced and one or more subsequent ones were skipped, an
   intermediate file would be corrupted while grafting OCR text, causing
   processing to fail. This is a regression, likely introduced in
   v8.2.4.
-  Previously, we resized the images produced by Ghostscript by a small
   number of pixels to ensure the output image size was an exactly what
   we wanted. Having discovered a way to get Ghostscript to produce the
   exact image sizes we require, we eliminated the resizing step.
-  Command line completions for ``bash`` are now available, in addition
   to ``fish``, both in ``misc/completion``. Package maintainers, please
   install these so users can take advantage.
-  Updated requirements.
-  pikepdf 1.3.0 is now required.

v8.2.4
======

-  Fixed a false positive while checking for a certain type of PDF that
   only Acrobat can read. We now more accurately detect Acrobat-only
   PDFs.
-  OCRmyPDF holds fewer open file handles and is more prompt about
   releasing those it no longer needs.
-  Minor optimization: we no longer traverse the table of contents to
   ensure all references in it are resolved, as changes to libqpdf have
   made this unnecessary.
-  pikepdf 1.2.0 is now required.

v8.2.3
======

-  Fixed that ``--mask-barcodes`` would occasionally leave a unwanted
   temporary file named ``junkpixt`` in the current working folder.
-  Fixed (hopefully) handling of Leptonica errors in an environment
   where a non-standard ``sys.stderr`` is present.
-  Improved help text for ``--verbose``.

v8.2.2
======

-  Fixed a regression from v8.2.0, an exception that occurred while
   attempting to report that ``unpaper`` or another optional dependency
   was unavailable.
-  In some cases, ``ocrmypdf [-c|--clean]`` failed to exit with an error
   when ``unpaper`` is not installed.

v8.2.1
======

-  This release was canceled.

v8.2.0
======

-  A major improvement to our Docker image is now available thanks to
   hard work contributed by @mawi12345. The new Docker image,
   ocrmypdf-alpine, is based on Alpine Linux, and includes most of the
   functionality of three existed images in a smaller package. This
   image will replace the main Docker image eventually but for now all
   are being built. `See documentation for
   details <https://ocrmypdf.readthedocs.io/en/latest/docker.html>`__.
-  Documentation reorganized especially around the use of Docker images.
-  Fixed a problem with PDF image optimization, where the optimizer
   would unnecessarily decompress and recompress PNG images, in some
   cases losing the benefits of the quantization it just had just
   performed. The optimizer is now capable of embedding PNG images into
   PDFs without transcoding them.
-  Fixed a minor regression with lossy JBIG2 image optimization. All
   JBIG2 candidates images were incorrectly placed into a single
   optimization group for the whole file, instead of grouping pages
   together. This usually makes a larger JBIG2Globals dictionary and
   results in inferior compression, so it worked less well than
   designed. However, quality would not be impacted. Lossless JBIG2 was
   entirely unaffected.
-  Updated dependencies, including pikepdf to 1.1.0. This fixes
   :issue:`358`.
-  The install-time version checks for certain external programs have
   been removed from setup.py. These tests are now performed at
   run-time.
-  The non-standard option to override install-time checks
   (``setup.py install --force``) is now deprecated and prints a
   warning. It will be removed in a future release.

v8.1.0
======

-  Added a feature, ``--unpaper-args``, which allows passing arbitrary
   arguments to ``unpaper`` when using ``--clean`` or ``--clean-final``.
   The default, very conservative unpaper settings are suppressed.
-  The argument ``--clean-final`` now implies ``--clean``. It was
   possible to issue ``--clean-final`` on its before this, but it would
   have no useful effect.
-  Fixed an exception on traversing corrupt table of contents entries
   (specifically, those with invalid destination objects)
-  Fixed an issue when using ``--tesseract-timeout`` and image
   processing features on a file with more than 100 pages.
   :issue:`347`
-  OCRmyPDF now always calls ``os.nice(5)`` to signal to operating
   systems that it is a background process.

v8.0.1
======

-  Fixed an exception when parsing PDFs that are missing a required
   field. :issue:`325`
-  pikepdf 1.0.5 is now required, to address some other PDF parsing
   issues.

v8.0.0
======

No major features. The intent of this release is to sever support for
older versions of certain dependencies.

**Breaking changes**

-  Dropped support for Tesseract 3.x. Tesseract 4.0 or newer is now
   required.
-  Dropped support for Python 3.5.
-  Some ``ocrmypdf.pdfa`` APIs that were deprecated in v7.x were
   removed. This functionality has been moved to pikepdf.

**Other changes**

-  Fixed an unhandled exception when attempting to mask barcodes.
   :issue:`322`
-  It is now possible to use ocrmypdf without pdfminer.six, to support
   distributions that do not have it or cannot currently use it (e.g.
   Homebrew). Downstream maintainers should include pdfminer.six if
   possible.
-  A warning is now issue when PDF/A conversion removes some XMP
   metadata from the input PDF. (Only a "whitelist" of certain XMP
   metadata types are allowed in PDF/A.)
-  Fixed several issues that caused PDF/As to be produced with
   nonconforming XMP metadata (would fail validation with veraPDF).
-  Fixed some instances where invalid DocumentInfo from a PDF cause XMP
   metadata creation to fail.
-  Fixed a few documentation problems.
-  pikepdf 1.0.2 is now required.

v7.4.0
======

-  ``--force-ocr`` may now be used with the new ``--threshold`` and
   ``--mask-barcodes`` features
-  pikepdf >= 0.9.1 is now required.
-  Changed metadata handling to pikepdf 0.9.1. As a result, metadata
   handling of non-ASCII characters in Ghostscript 9.25 or later is
   fixed.
-  chardet >= 3.0.4 is temporarily listed as required. pdfminer.six
   depends on it, but the most recent release does not specify this
   requirement.
   (:issue:`326`)
-  python-xmp-toolkit and libexempi are no longer required.
-  A new Docker image is now being provided for users who wish to access
   OCRmyPDF over a simple HTTP interface, instead of the command line.
-  Increase tolerance of PDFs that overflow or underflow the PDF
   graphics stack.
   (:issue:`325`)

v7.3.1
======

-  Fixed performance regression from v7.3.0; fast page analysis was not
   selected when it should be.
-  Fixed a few exceptions related to the new ``--mask-barcodes`` feature
   and improved argument checking
-  Added missing detection of TrueType fonts that lack a Unicode mapping

v7.3.0
======

-  Added a new feature ``--redo-ocr`` to detect existing OCR in a file,
   remove it, and redo the OCR. This may be particularly helpful for
   anyone who wants to take advantage of OCR quality improvements in
   Tesseract 4.0. Note that OCR added by OCRmyPDF before version 3.0
   cannot be detected since it was not properly marked as invisible text
   in the earliest versions. OCR that constructs a font from visible
   text, such as Adobe Acrobat's ClearScan.
-  OCRmyPDF's content detection is generally more sophisticated. It
   learns more about the contents of each PDF and makes better
   recommendations:

   -  OCRmyPDF can now detect when a PDF contains text that cannot be
      mapped to Unicode (meaning it is readable to human eyes but
      copy-pastes as gibberish). In these cases it recommends
      ``--force-ocr`` to make the text searchable.
   -  PDFs containing vector objects are now rendered at more
      appropriate resolution for OCR.
   -  We now exit with an error for PDFs that contain Adobe LiveCycle
      Designer's dynamic XFA forms. Currently the open source community
      does not have tools to work with these files.
   -  OCRmyPDF now warns when a PDF that contains Adobe AcroForms, since
      such files probably do not need OCR. It can work with these files.

-  Added three new **experimental** features to improve OCR quality in
   certain conditions. The name, syntax and behavior of these arguments
   is subject to change. They may also be incompatible with some other
   features.

   -  ``--remove-vectors`` which strips out vector graphics. This can
      improve OCR quality since OCR will not search artwork for readable
      text; however, it currently removes "text as curves" as well.
   -  ``--mask-barcodes`` to detect and suppress barcodes in files. We
      have observed that barcodes can interfere with OCR because they
      are "text-like" but not actually textual.
   -  ``--threshold`` which uses a more sophisticated thresholding
      algorithm than is currently in use in Tesseract OCR. This works
      around a `known issue in Tesseract
      4.0 <https://github.com/tesseract-ocr/tesseract/issues/1990>`__
      with dark text on bright backgrounds.

-  Fixed an issue where an error message was not reported when the
   installed Ghostscript was very old.
-  The PDF optimizer now saves files with object streams enabled when
   the optimization level is ``--optimize 1`` or higher (the default).
   This makes files a little bit smaller, but requires PDF 1.5. PDF 1.5
   was first released in 2003 and is broadly supported by PDF viewers,
   but some rudimentary PDF parsers such as PyPDF2 do not understand
   object streams. You can use the command line tool
   ``qpdf --object-streams=disable`` or
   `pikepdf <https://github.com/pikepdf/pikepdf>`__ library to remove
   them.
-  New dependency: pdfminer.six 20181108. Note this is a fork of the
   Python 2-only pdfminer.
-  Deprecation notice: At the end of 2018, we will be ending support for
   Python 3.5 and Tesseract 3.x. OCRmyPDF v7 will continue to work with
   older versions.

v7.2.1
======

-  Fixed compatibility with an API change in pikepdf 0.3.5.
-  A kludge to support Leptonica versions older than 1.72 in the test
   suite was dropped. Older versions of Leptonica are likely still
   compatible. The only impact is that a portion of the test suite will
   be skipped.

v7.2.0
======

**Lossy JBIG2 behavior change**

A user reported that ocrmypdf was in fact using JBIG2 in **lossy**
compression mode. This was not the intended behavior. Users should
`review the technical concerns with JBIG2 in lossy
mode <https://abbyy.technology/en:kb:tip:jbig2_compression_and_ocr>`__
and decide if this is a concern for their use case.

JBIG2 lossy mode does achieve higher compression ratios than any other
monochrome compression technology; for large text documents the savings
are considerable. JBIG2 lossless still gives great compression ratios
and is a major improvement over the older CCITT G4 standard.

Only users who have reviewed the concerns with JBIG2 in lossy mode
should opt-in. As such, lossy mode JBIG2 is only turned on when the new
argument ``--jbig2-lossy`` is issued. This is independent of the setting
for ``--optimize``.

Users who did not install an optional JBIG2 encoder are unaffected.

(Thanks to user 'bsdice' for reporting this issue.)

**Other issues**

-  When the image optimizer quantizes an image to 1 bit per pixel, it
   will now attempt to further optimize that image as CCITT or JBIG2,
   instead of keeping it in the "flate" encoding which is not efficient
   for 1 bpp images.
   (:issue:`297`)
-  Images in PDFs that are used as soft masks (i.e. transparency masks
   or alpha channels) are now excluded from optimization.
-  Fixed handling of Tesseract 4.0-rc1 which now accepts invalid
   Tesseract configuration files, which broke the test suite.

v7.1.0
======

-  Improve the performance of initial text extraction, which is done to
   determine if a file contains existing text of some kind or not. On
   large files, this initial processing is now about 20x times faster.
   (:issue:`299`)
-  pikepdf 0.3.3 is now required.
-  Fixed :issue:`231`, a
   problem with JPEG2000 images where image metadata was only available
   inside the JPEG2000 file.
-  Fixed some additional Ghostscript 9.25 compatibility issues.
-  Improved handling of KeyboardInterrupt error messages.
   (:issue:`301`)
-  README.md is now served in GitHub markdown instead of
   reStructuredText.

v7.0.6
======

-  Blacklist Ghostscript 9.24, now that 9.25 is available and fixes many
   regressions in 9.24.

v7.0.5
======

-  Improve capability with Ghostscript 9.24, and enable the JPEG
   passthrough feature when this version in installed.
-  Ghostscript 9.24 lost the ability to set PDF title, author, subject
   and keyword metadata to Unicode strings. OCRmyPDF will set ASCII
   strings and warn when Unicode is suppressed. Other software may be
   used to update metadata. This is a short term work around.
-  PDFs generated by Kodak Capture Desktop, or generally PDFs that
   contain indirect references to null objects in their table of
   contents, would have an invalid table of contents after processing by
   OCRmyPDF that might interfere with other viewers. This has been
   fixed.
-  Detect PDFs generated by Adobe LiveCycle, which can only be displayed
   in Adobe Acrobat and Reader currently. When these are encountered,
   exit with an error instead of performing OCR on the "Please wait"
   error message page.

v7.0.4
======

-  Fixed exception thrown when trying to optimize a certain type of PNG
   embedded in a PDF with the ``-O2``
-  Update to pikepdf 0.3.2, to gain support for optimizing some
   additional image types that were previously excluded from
   optimization (CMYK and grayscale). Fixes
   :issue:`285`.

v7.0.3
======

-  Fixed :issue:`284`, an error
   when parsing inline images that have are also image masks, by
   upgrading pikepdf to 0.3.1

v7.0.2
======

-  Fixed a regression with ``--rotate-pages`` on pages that already had
   rotations applied.
   (:issue:`279`)
-  Improve quality of page rotation in some cases by rasterizing a
   higher quality preview image.
   (:issue:`281`)

v7.0.1
======

-  Fixed compatibility with img2pdf >= 0.3.0 by rejecting input images
   that have an alpha channel
-  Add forward compatibility for pikepdf 0.3.0 (unrelated to img2pdf)
-  Various documentation updates for v7.0.0 changes

v7.0.0
======

-  The core algorithm for combining OCR layers with existing PDF pages
   has been rewritten and improved considerably. PDFs are no longer
   split into single page PDFs for processing; instead, images are
   rendered and the OCR results are grafted onto the input PDF. The new
   algorithm uses less temporary disk space and is much more performant
   especially for large files.
-  New dependency: `pikepdf <https://github.com/pikepdf/pikepdf>`__.
   pikepdf is a powerful new Python PDF library driving the latest
   OCRmyPDF features, built on the QPDF C++ library (libqpdf).
-  New feature: PDF optimization with ``-O`` or ``--optimize``. After
   OCR, OCRmyPDF will perform image optimizations relevant to OCR PDFs.

   -  If a JBIG2 encoder is available, then monochrome images will be
      converted, with the potential for huge savings on large black and
      white images, since JBIG2 is far more efficient than any other
      monochrome (bi-level) compression. (All known US patents related
      to JBIG2 have probably expired, but it remains the responsibility
      of the user to supply a JBIG2 encoder such as
      `jbig2enc <https://github.com/agl/jbig2enc>`__. OCRmyPDF does not
      implement JBIG2 encoding.)
   -  If ``pngquant`` is installed, OCRmyPDF will optionally use it to
      perform lossy quantization and compression of PNG images.
   -  The quality of JPEGs can also be lowered, on the assumption that a
      lower quality image may be suitable for storage after OCR.
   -  This image optimization component will eventually be offered as an
      independent command line utility.
   -  Optimization ranges from ``-O0`` through ``-O3``, where ``0``
      disables optimization and ``3`` implements all options. ``1``, the
      default, performs only safe and lossless optimizations. (This is
      similar to GCC's optimization parameter.) The exact type of
      optimizations performed will vary over time.

-  Small amounts of text in the margins of a page, such as watermarks,
   page numbers, or digital stamps, will no longer prevent the rest of a
   page from being OCRed when ``--skip-text`` is issued. This behavior
   is based on a heuristic.
-  Removed features

   -  The deprecated ``--pdf-renderer tesseract`` PDF renderer was
      removed.
   -  ``-g``, the option to generate debug text pages, was removed
      because it was a maintenance burden and only worked in isolated
      cases. HOCR pages can still be previewed by running the
      hocrtransform.py with appropriate settings.

-  Removed dependencies

   -  ``PyPDF2``
   -  ``defusedxml``
   -  ``PyMuPDF``

-  The ``sandwich`` PDF renderer can be used with all supported versions
   of Tesseract, including that those prior to v3.05 which don't support
   ``-c textonly``. (Tesseract v4.0.0 is recommended and more
   efficient.)
-  ``--pdf-renderer auto`` option and the diagnostics used to select a
   PDF renderer now work better with old versions, but may make
   different decisions than past versions.
-  If everything succeeds but PDF/A conversion fails, a distinct return
   code is now returned (``ExitCode.pdfa_conversion_failed (10)``) where
   this situation previously returned
   ``ExitCode.invalid_output_pdf (4)``. The latter is now returned only
   if there is some indication that the output file is invalid.
-  Notes for downstream packagers

   -  There is also a new dependency on ``python-xmp-toolkit`` which in
      turn depends on ``libexempi3``.
   -  It may be necessary to separately ``pip install pycparser`` to
      avoid `another Python 3.7
      issue <https://github.com/eliben/pycparser/pull/135>`__.

v6.2.5
======

-  Disable a failing test due to Tesseract 4.0rc1 behavior change.
   Previously, Tesseract would exit with an error message if its
   configuration was invalid, and OCRmyPDF would intercept this message.
   Now Tesseract issues a warning, which OCRmyPDF v6.2.5 may relay or
   ignore. (In v7.x, OCRmyPDF will respond to the warning.)
-  This release branch no longer supports using the optional PyMuPDF
   installation, since it was removed in v7.x.
-  This release branch no longer supports macOS. macOS users should
   upgrade to v7.x.

v6.2.4
======

-  Backport Ghostscript 9.25 compatibility fixes, which removes support
   for setting Unicode metadata
-  Backport blacklisting Ghostscript 9.24
-  Older versions of Ghostscript are still supported

v6.2.3
======

-  Fixed compatibility with img2pdf >= 0.3.0 by rejecting input images
   that have an alpha channel
-  This version will be included in Ubuntu 18.10

v6.2.2
======

-  Backport compatibility fixes for Python 3.7 and ruffus 2.7.0 from
   v7.0.0
-  Backport fix to ignore masks when deciding what colors are on a page
-  Backport some minor improvements from v7.0.0: better argument
   validation and warnings about the Tesseract 4.0.0 ``--user-words``
   regression

v6.2.1
======

-  Fixed recent versions of Tesseract (after 4.0.0-beta1) not being
   detected as supporting the ``sandwich`` renderer (:issue:`271`).

v6.2.0
======

-  **Docker**: The Docker image ``ocrmypdf-tess4`` has been removed. The
   main Docker images, ``ocrmypdf`` and ``ocrmypdf-polyglot`` now use
   Ubuntu 18.04 as a base image, and as such Tesseract 4.0.0-beta1 is
   now the Tesseract version they use. There is no Docker image based on
   Tesseract 3.05 anymore.
-  Creation of PDF/A-3 is now supported. However, there is no ability to
   attach files to PDF/A-3.
-  Lists more reasons why the file size might grow.
-  Fixed :issue:`262`,
   ``--remove-background`` error on PDFs contained colormapped
   (paletted) images.
-  Fixed another XMP metadata validation issue, in cases where the input
   file's creation date has no timezone and the creation date is not
   overridden.

v6.1.5
======

-  Fixed :issue:`253`, a
   possible division by zero when using the ``hocr`` renderer.
-  Fixed incorrectly formatted ``<xmp:ModifyDate>`` field inside XMP
   metadata for PDF/As. veraPDF flags this as a PDF/A validation
   failure. The error is caused the timezone and final digit of the
   seconds of modified time to be omitted, so at worst the modification
   time stamp is rounded to the nearest 10 seconds.

v6.1.4
======

-  Fixed :issue:`248`
   ``--clean`` argument may remove OCR from left column of text on
   certain documents. We now set ``--layout none`` to suppress this.
-  The test cache was updated to reflect the change above.
-  Change test suite to accommodate Ghostscript 9.23's new ability to
   insert JPEGs into PDFs without transcoding.
-  XMP metadata in PDFs is now examined using ``defusedxml`` for safety.
-  If an external process exits with a signal when asked to report its
   version, we now print the system error message instead of suppressing
   it. This occurred when the required executable was found but was
   missing a shared library.
-  qpdf 7.0.0 or newer is now required as the test suite can no longer
   pass without it.

Notes
-----

-  An apparent `regression in Ghostscript
   9.23 <https://bugs.ghostscript.com/show_bug.cgi?id=699216>`__ will
   cause some ocrmypdf output files to become invalid in rare cases; the
   workaround for the moment is to set ``--force-ocr``.

v6.1.3
======

-  Fixed :issue:`247`,
   ``/CreationDate`` metadata not copied from input to output.
-  A warning is now issued when Python 3.5 is used on files with a large
   page count, as this case is known to regress to single core
   performance. The cause of this problem is unknown.

v6.1.2
======

-  Upgrade to PyMuPDF v1.12.5 which includes a more complete fix to
   :issue:`239`.
-  Add ``defusedxml`` dependency.

v6.1.1
======

-  Fixed text being reported as found on all pages if PyMuPDF is not
   installed.

v6.1.0
======

-  PyMuPDF is now an optional but recommended dependency, to alleviate
   installation difficulties on platforms that have less access to
   PyMuPDF than the author anticipated. (For version 6.x only) install
   OCRmyPDF with ``pip install ocrmypdf[fitz]`` to use it to its full
   potential.
-  Fixed ``FileExistsError`` that could occur if OCR timed out while it
   was generating the output file.
   (:issue:`218`)
-  Fixed table of contents/bookmarks all being redirected to page 1 when
   generating a PDF/A (with PyMuPDF). (Without PyMuPDF the table of
   contents is removed in PDF/A mode.)
-  Fixed "RuntimeError: invalid key in dict" when table of
   contents/bookmarks titles contained the character ``)``.
   (:issue:`239`)
-  Added a new argument ``--skip-repair`` to skip the initial PDF repair
   step if the PDF is already well-formed (because another program
   repaired it).

v6.0.0
======

-  The software license has been changed to GPLv3 [it has since changed again].
   Test resource files and some individual sources may have other licenses.
-  OCRmyPDF now depends on
   `PyMuPDF <https://pymupdf.readthedocs.io/en/latest/installation/>`__.
   Including PyMuPDF is the primary reason for the change to GPLv3.
-  Other backward incompatible changes

   -  The ``OCRMYPDF_TESSERACT``, ``OCRMYPDF_QPDF``, ``OCRMYPDF_GS`` and
      ``OCRMYPDF_UNPAPER`` environment variables are no longer used.
      Change ``PATH`` if you need to override the external programs
      OCRmyPDF uses.
   -  The ``ocrmypdf`` package has been moved to ``src/ocrmypdf`` to
      avoid issues with accidental import.
   -  The function ``ocrmypdf.exec.get_program`` was removed.
   -  The deprecated module ``ocrmypdf.pageinfo`` was removed.
   -  The ``--pdf-renderer tess4`` alias for ``sandwich`` was removed.

-  Fixed an issue where OCRmyPDF failed to detect existing text on
   pages, depending on how the text and fonts were encoded within the
   PDF. (:issue:`233,232`)
-  Fixed an issue that caused dramatic inflation of file sizes when
   ``--skip-text --output-type pdf`` was used. OCRmyPDF now removes
   duplicate resources such as fonts, images and other objects that it
   generates. (:issue:`237`)
-  Improved performance of the initial page splitting step. Originally
   this step was not believed to be expensive and ran in a process.
   Large file testing revealed it to be a bottleneck, so it is now
   parallelized. On a 700 page file with quad core machine, this change
   saves about 2 minutes. (:issue:`234`)
-  The test suite now includes a cache that can be used to speed up test
   runs across platforms. This also does not require computing
   checksums, so it's faster. (:issue:`217`)

v5.7.0
======

-  Fixed an issue that caused poor CPU utilization on machines with more
   than 4 cores when running Tesseract 4. (Related to :issue:`217`.)
-  The 'hocr' renderer has been improved. The 'sandwich' and 'tesseract'
   renderers are still better for most use cases, but 'hocr' may be
   useful for people who work with the PDF.js renderer in English/ASCII
   languages. (:issue:`225`)

   -  It now formats text in a matter that is easier for certain PDF
      viewers to select and extract copy and paste text. This should
      help macOS Preview and PDF.js in particular.
   -  The appearance of selected text and behavior of selecting text is
      improved.
   -  The PDF content stream now uses relative moves, making it more
      compact and easier for viewers to determine when two words on the
      same line.
   -  It can now deal with text on a skewed baseline.
   -  Thanks to @cforcey for the pull request, @jbreiden for many
      helpful suggestions, @ctbarbour for another round of improvements,
      and @acaloiaro for an independent review.

v5.6.3
======

-  Suppress two debug messages that were too verbose

v5.6.2
======

-  Development branch accidentally tagged as release. Do not use.

v5.6.1
======

-  Fixed :issue:`219`: change
   how the final output file is created to avoid triggering permission
   errors when the output is a special file such as ``/dev/null``
-  Fixed test suite failures due to a qpdf 8.0.0 regression and Python
   3.5's handling of symlink
-  The "encrypted PDF" error message was different depending on the type
   of PDF encryption. Now a single clear message appears for all types
   of PDF encryption.
-  ocrmypdf is now in Homebrew. Homebrew users are advised to the
   version of ocrmypdf in the official homebrew-core formulas rather
   than the private tap.
-  Some linting

v5.6.0
======

-  Fixed :issue:`216`: preserve
   "text as curves" PDFs without rasterizing file
-  Related to the above, messages about rasterizing are more consistent
-  For consistency versions minor releases will now get the trailing .0
   they always should have had.

v5.5
====

-  Add new argument ``--max-image-mpixels``. Pillow 5.0 now raises an
   exception when images may be decompression bombs. This argument can
   be used to override the limit Pillow sets.
-  Fixed output page cropped when using the sandwich renderer and OCR is
   skipped on a rotated and image-processed page
-  A warning is now issued when old versions of Ghostscript are used in
   cases known to cause issues with non-Latin characters
-  Fixed a few parameter validation checks for ``-output-type pdfa-1`` and
   ``pdfa-2``

v5.4.4
======

-  Fixed :issue:`181`: fix
   final merge failure for PDFs with more pages than the system file
   handle limit (``ulimit -n``)
-  Fixed :issue:`200`: an
   uncommon syntax for formatting decimal numbers in a PDF would cause
   qpdf to issue a warning, which ocrmypdf treated as an error. Now this
   the warning is relayed.
-  Fixed an issue where intermediate PDFs would be created at version 1.3
   instead of the version of the original file. It's possible but
   unlikely this had side effects.
-  A warning is now issued when older versions of qpdf are used since
   issues like
   :issue:`200` cause
   qpdf to infinite-loop
-  Address issue
   :issue:`140`: if
   Tesseract outputs invalid UTF-8, escape it and print its message
   instead of aborting with a Unicode error
-  Adding previously unlisted setup requirement, pytest-runner
-  Update documentation: fix an error in the example script for Synology
   with Docker images, improved security guidance, advised
   ``pip install --user``

v5.4.3
======

-  If a subprocess fails to report its version when queried, exit
   cleanly with an error instead of throwing an exception
-  Added test to confirm that the system locale is Unicode-aware and
   fail early if it's not
-  Clarified some copyright information
-  Updated pinned requirements.txt so the homebrew formula captures more
   recent versions

v5.4.2
======

-  Fixed a regression from v5.4.1 that caused sidecar files to be
   created as empty files

v5.4.1
======

-  Add workaround for Tesseract v4.00alpha crash when trying to obtain
   orientation and the latest language packs are installed

v5.4
====

-  Change wording of a deprecation warning to improve clarity
-  Added option to generate PDF/A-1b output if desired
   (``--output-type pdfa-1``); default remains PDF/A-2b generation
-  Update documentation

v5.3.3
======

-  Fixed missing error message that should occur when trying to force
   ``--pdf-renderer sandwich`` on old versions of Tesseract
-  Update copyright information in test files
-  Set system ``LANG`` to UTF-8 in Dockerfiles to avoid UTF-8 encoding
   errors

v5.3.2
======

-  Fixed a broken test case related to language packs

v5.3.1
======

-  Fixed wrong return code given for missing Tesseract language packs
-  Fixed "brew audit" crashing on Travis when trying to auto-brew

v5.3
====

-  Added ``--user-words`` and ``--user-patterns`` arguments which are
   forwarded to Tesseract OCR as words and regular expressions
   respective to use to guide OCR. Supplying a list of subject-domain
   words should assist Tesseract with resolving words.
   (:issue:`165`)
-  Using a non Latin-1 language with the "hocr" renderer now warns about
   possible OCR quality and recommends workarounds
   (:issue:`176`)
-  Output file path added to error message when that location is not
   writable
   (:issue:`175`)
-  Otherwise valid PDFs with leading whitespace at the beginning of the
   file are now accepted

v5.2
====

-  When using Tesseract 3.05.01 or newer, OCRmyPDF will select the
   "sandwich" PDF renderer by default, unless another PDF renderer is
   specified with the ``--pdf-renderer`` argument. The previous behavior
   was to select ``--pdf-renderer=hocr``.
-  The "tesseract" PDF renderer is now deprecated, since it can cause
   problems with Ghostscript on Tesseract 3.05.00
-  The "tess4" PDF renderer has been renamed to "sandwich". "tess4" is
   now a deprecated alias for "sandwich".

v5.1
====

-  Files with pages larger than 200" (5080 mm) in either dimension are
   now supported with ``--output-type=pdf`` with the page size preserved
   (in the PDF specification this feature is called UserUnit scaling).
   Due to Ghostscript limitations this is not available in conjunction
   with PDF/A output.

v5.0.1
======

-  Fixed :issue:`169`,
   exception due to failure to create sidecar text files on some
   versions of Tesseract 3.04, including the jbarlow83/ocrmypdf Docker
   image

v5.0
====

-  Backward incompatible changes

      -  Support for Python 3.4 dropped. Python 3.5 is now required.
      -  Support for Tesseract 3.02 and 3.03 dropped. Tesseract 3.04 or
         newer is required. Tesseract 4.00 (alpha) is supported.
      -  The OCRmyPDF.sh script was removed.

-  Add a new feature, ``--sidecar``, which allows creating "sidecar"
   text files which contain the OCR results in plain text. These OCR
   text is more reliable than extracting text from PDFs. Closes
   :issue:`126`.

-  New feature: ``--pdfa-image-compression``, which allows overriding
   Ghostscript's lossy-or-lossless image encoding heuristic and making
   all images JPEG encoded or lossless encoded as desired. Fixes
   :issue:`163`.

-  Fixed :issue:`143`, added
   ``--quiet`` to suppress "INFO" messages

-  Fixed :issue:`164`, a typo

-  Removed the command line parameters ``-n`` and ``--just-print`` since
   they have not worked for some time (reported as Ubuntu bug
   `#1687308 <https://bugs.launchpad.net/ubuntu/+source/ocrmypdf/+bug/1687308>`__)

v4.5.6
======

-  Fixed :issue:`156`,
   'NoneType' object has no attribute 'getObject' on pages with no
   optional /Contents record. This should resolve all issues related to
   pages with no /Contents record.
-  Fixed :issue:`158`, ocrmypdf
   now stops and terminates if Ghostscript fails on an intermediate
   step, as it is not possible to proceed.
-  Fixed :issue:`160`,
   exception thrown on certain invalid arguments instead of error
   message

v4.5.5
======

-  Automated update of macOS homebrew tap
-  Fixed :issue:`154`, KeyError
   '/Contents' when searching for text on blank pages that have no
   /Contents record. Note: incomplete fix for this issue.

v4.5.4
======

-  Fixed ``--skip-big`` raising an exception if a page contains no images
   (:issue:`152`) (thanks
   to @TomRaz)
-  Fixed an issue where pages with no images might trigger "cannot write
   mode P as JPEG"
   (:issue:`151`)

v4.5.3
======

-  Added a workaround for Ghostscript 9.21 and probably earlier versions
   would fail with the error message "VMerror -25", due to a Ghostscript
   bug in XMP metadata handling
-  High Unicode characters (U+10000 and up) are no longer accepted for
   setting metadata on the command line, as Ghostscript may not handle
   them correctly.
-  Fixed an issue where the ``tess4`` renderer would duplicate content
   onto output pages if tesseract failed or timed out
-  Fixed ``tess4`` renderer not recognized when lossless reconstruction
   is possible

v4.5.2
======

-  Fixed :issue:`147`,
   ``--pdf-renderer tess4 --clean`` will produce an oversized page
   containing the original image in the bottom left corner, due to loss
   DPI information.
-  Make "using Tesseract 4.0" warning less ominous
-  Set up machinery for homebrew OCRmyPDF tap

v4.5.1
======

-  Fixed :issue:`137`,
   proportions of images with a non-square pixel aspect ratio would be
   distorted in output for ``--force-ocr`` and some other combinations
   of flags

v4.5
====

-  PDFs containing "Form XObjects" are now supported (issue
   :issue:`134`; PDF
   reference manual 8.10), and images they contain are taken into
   account when determining the resolution for rasterizing
-  The Tesseract 4 Docker image no longer includes all languages,
   because it took so long to build something would tend to fail
-  OCRmyPDF now warns about using ``--pdf-renderer tesseract`` with
   Tesseract 3.04 or lower due to issues with Ghostscript corrupting the
   OCR text in these cases

v4.4.2
======

-  The Docker images (ocrmypdf, ocrmypdf-polyglot, ocrmypdf-tess4) are
   now based on Ubuntu 16.10 instead of Debian stretch

   -  This makes supporting the Tesseract 4 image easier
   -  This could be a disruptive change for any Docker users who built
      customized these images with their own changes, and made those
      changes in a way that depends on Debian and not Ubuntu

-  OCRmyPDF now prevents running the Tesseract 4 renderer with Tesseract
   3.04, which was permitted in v4.4 and v4.4.1 but will not work

v4.4.1
======

-  To prevent a `TIFF output
   error <https://github.com/python-pillow/Pillow/issues/2206>`__ caused
   by img2pdf >= 0.2.1 and Pillow <= 3.4.2, dependencies have been
   tightened
-  The Tesseract 4.00 simultaneous process limit was increased from 1 to
   2, since it was observed that 1 lowers performance
-  Documentation improvements to describe the ``--tesseract-config``
   feature
-  Added test cases and fixed error handling for ``--tesseract-config``
-  Tweaks to setup.py to deal with issues in the v4.4 release

v4.4
====

-  Tesseract 4.00 is now supported on an experimental basis.

   -  A new rendering option ``--pdf-renderer tess4`` exploits Tesseract
      4's new text-only output PDF mode. See the documentation on PDF
      Renderers for details.
   -  The ``--tesseract-oem`` argument allows control over the Tesseract
      4 OCR engine mode (tesseract's ``--oem``). Use
      ``--tesseract-oem 2`` to enforce the new LSTM mode.
   -  Fixed poor performance with Tesseract 4.00 on Linux

-  Fixed an issue that caused corruption of output to stdout in some
   cases
-  Removed test for Pillow JPEG and PNG support, as the minimum
   supported version of Pillow now enforces this
-  OCRmyPDF now tests that the intended destination file is writable
   before proceeding
-  The test suite now requires ``pytest-helpers-namespace`` to run (but
   not install)
-  Significant code reorganization to make OCRmyPDF re-entrant and
   improve performance. All changes should be backward compatible for
   the v4.x series.

   -  However, OCRmyPDF's dependency "ruffus" is not re-entrant, so no
      Python API is available. Scripts should continue to use the
      command line interface.

v4.3.5
======

-  Update documentation to confirm Python 3.6.0 compatibility. No code
   changes were needed, so many earlier versions are likely supported.

v4.3.4
======

-  Fixed "decimal.InvalidOperation: quantize result has too many digits"
   for high DPI images

v4.3.3
======

-  Fixed PDF/A creation with Ghostscript 9.20 properly
-  Fixed an exception on inline stencil masks with a missing optional
   parameter

v4.3.2
======

-  Fixed a PDF/A creation issue with Ghostscript 9.20 (note: this fix
   did not actually work)

v4.3.1
======

-  Fixed an issue where pages produced by the "hocr" renderer after a
   Tesseract timeout would be rotated incorrectly if the input page was
   rotated with a /Rotate marker
-  Fixed a file handle leak in LeptonicaErrorTrap that would cause a
   "too many open files" error for files around hundred pages of pages
   long when ``--deskew`` or ``--remove-background`` or other Leptonica
   based image processing features were in use, depending on the system
   value of ``ulimit -n``
-  Ability to specify multiple languages for multilingual documents is
   now advertised in documentation
-  Reduced the file sizes of some test resources
-  Cleaned up debug output
-  Tesseract caching in test cases is now more cautious about false
   cache hits and reproducing exact output, not that any problems were
   observed

v4.3
====

-  New feature ``--remove-background`` to detect and erase the
   background of color and grayscale images
-  Better documentation
-  Fixed an issue with PDFs that draw images when the raster stack depth
   is zero
-  ocrmypdf can now redirect its output to stdout for use in a shell
   pipeline

   -  This does not improve performance since temporary files are still
      used for buffering
   -  Some output validation is disabled in this mode

v4.2.5
======

-  Fixed an issue
   (:issue:`100`) with
   PDFs that omit the optional /BitsPerComponent parameter on images
-  Removed non-free file milk.pdf

v4.2.4
======

-  Fixed an error
   (:issue:`90`) caused by
   PDFs that use stencil masks properly
-  Fixed handling of PDFs that try to draw images or stencil masks
   without properly setting up the graphics state (such images are now
   ignored for the purposes of calculating DPI)

v4.2.3
======

-  Fixed an issue with PDFs that store page rotation (/Rotate) in an
   indirect object
-  Integrated a few fixes to simplify downstream packaging (Debian)

   -  The test suite no longer assumes it is installed
   -  If running Linux, skip a test that passes Unicode on the command
      line

-  Added a test case to check explicit masks and stencil masks
-  Added a test case for indirect objects and linearized PDFs
-  Deprecated the OCRmyPDF.sh shell script

v4.2.2
======

-  Improvements to documentation

v4.2.1
======

-  Fixed an issue where PDF pages that contained stencil masks would
   report an incorrect DPI and cause Ghostscript to abort
-  Implemented stdin streaming

v4.2
====

-  ocrmypdf will now try to convert single image files to PDFs if they
   are provided as input
   (:issue:`15`)

   -  This is a basic convenience feature. It only supports a single
      image and always makes the image fill the whole page.
   -  For better control over image to PDF conversion, use ``img2pdf``
      (one of ocrmypdf's dependencies)

-  New argument ``--output-type {pdf|pdfa}`` allows disabling
   Ghostscript PDF/A generation

   -  ``pdfa`` is the default, consistent with past behavior
   -  ``pdf`` provides a workaround for users concerned about the
      increase in file size from Ghostscript forcing JBIG2 images to
      CCITT and transcoding JPEGs
   -  ``pdf`` preserves as much as it can about the original file,
      including problems that PDF/A conversion fixes

-  PDFs containing images with "non-square" pixel aspect ratios, such as
   200x100 DPI, are now handled and converted properly (fixing a bug
   that caused to be cropped)
-  ``--force-ocr`` rasterizes pages even if they contain no images

   -  supports users who want to use OCRmyPDF to reconstruct text
      information in PDFs with damaged Unicode maps (copy and paste text
      does not match displayed text)
   -  supports reinterpreting PDFs where text was rendered as curves for
      printing, and text needs to be recovered
   -  fixes issue
      :issue:`82`

-  Fixes an issue where, with certain settings, monochrome images in
   PDFs would be converted to 8-bit grayscale, increasing file size
   (:issue:`79`)
-  Support for Ubuntu 12.04 LTS "precise" has been dropped in favor of
   (roughly) Ubuntu 14.04 LTS "trusty"

   -  Some Ubuntu "PPAs" (backports) are needed to make it work

-  Support for some older dependencies dropped

   -  Ghostscript 9.15 or later is now required (available in Ubuntu
      trusty with backports)
   -  Tesseract 3.03 or later is now required (available in Ubuntu
      trusty)

-  Ghostscript now runs in "safer" mode where possible

v4.1.4
======

-  Bug fix: monochrome images with an ICC profile attached were
   incorrectly converted to full color images if lossless reconstruction
   was not possible due to other settings; consequence was increased
   file size for these images

v4.1.3
======

-  More helpful error message for PDFs with version 4 security handler
-  Update usage instructions for Windows/Docker users
-  Fixed order of operations for matrix multiplication (no effect on most
   users)
-  Add a few leptonica wrapper functions (no effect on most users)

v4.1.2
======

-  Replace IEC sRGB ICC profile with Debian's sRGB (from
   icc-profiles-free) which is more compatible with the MIT license
-  More helpful error message for an error related to certain types of
   malformed PDFs

v4.1
====

-  ``--rotate-pages`` now only rotates pages when reasonably confidence
   in the orientation. This behavior can be adjusted with the new
   argument ``--rotate-pages-threshold``
-  Fixed problems in error checking if ``unpaper`` is uninstalled or
   missing at run-time
-  Fixed problems with "RethrownJobError" errors during error handling
   that suppressed the useful error messages

v4.0.7
======

-  Minor correction to Ghostscript output settings

v4.0.6
======

-  Update install instructions
-  Provide a sRGB profile instead of using Ghostscript's

v4.0.5
======

-  Remove some verbose debug messages from v4.0.4
-  Fixed temporary that wasn't being deleted
-  DPI is now calculated correctly for cropped images, along with other
   image transformations
-  Inline images are now checked during DPI calculation instead of
   rejecting the image

v4.0.4
======

Released with verbose debug message turned on. Do not use. Skip to
v4.0.5.

v4.0.3
======

New features

-  Page orientations detected are now reported in a summary comment

Fixes

-  Show stack trace if unexpected errors occur
-  Treat "too few characters" error message from Tesseract as a reason
   to skip that page rather than abort the file
-  Docker: fix blank JPEG2000 issue by insisting on Ghostscript versions
   that have this fixed

v4.0.2
======

Fixes

-  Fixed compatibility with Tesseract 3.04.01 release, particularly its
   different way of outputting orientation information
-  Improved handling of Tesseract errors and crashes
-  Fixed use of chmod on Docker that broke most test cases

v4.0.1
======

Fixes

-  Fixed a KeyError if tesseract fails to find page orientation
   information

v4.0
====

New features

-  Automatic page rotation (``-r``) is now available. It uses ignores
   any prior rotation information on PDFs and sets rotation based on the
   dominant orientation of detectable text. This feature is fairly
   reliable but some false positives occur especially if there is not
   much text to work with.
   (:issue:`4`)
-  Deskewing is now performed using Leptonica instead of unpaper.
   Leptonica is faster and more reliable at image deskewing than
   unpaper.

Fixes

-  Fixed an issue where lossless reconstruction could cause some pages
   to be appear incorrectly if the page was rotated by the user in
   Acrobat after being scanned (specifically if it a /Rotate tag)
-  Fixed an issue where lossless reconstruction could misalign the
   graphics layer with respect to text layer if the page had been
   cropped such that its origin is not (0, 0)
   (:issue:`49`)

Changes

-  Logging output is now much easier to read
-  ``--deskew`` is now performed by Leptonica instead of unpaper
   (:issue:`25`)
-  libffi is now required
-  Some changes were made to the Docker and Travis build environments to
   support libffi
-  ``--pdf-renderer=tesseract`` now displays a warning if the Tesseract
   version is less than 3.04.01, the planned release that will include
   fixes to an important OCR text rendering bug in Tesseract 3.04.00.
   You can also manually install ./share/sharp2.ttf on top of pdf.ttf in
   your Tesseract tessdata folder to correct the problem.

v3.2.1
======

Changes

-  Fixed :issue:`47`
   "convert() got and unexpected keyword argument 'dpi'" by upgrading to
   img2pdf 0.2
-  Tweaked the Dockerfiles

v3.2
====

New features

-  Lossless reconstruction: when possible, OCRmyPDF will inject text
   layers without otherwise manipulating the content and layout of a PDF
   page. For example, a PDF containing a mix of vector and raster
   content would see the vector content preserved. Images may still be
   transcoded during PDF/A conversion. (``--deskew`` and
   ``--clean-final`` disable this mode, necessarily.)
-  New argument ``--tesseract-pagesegmode`` allows you to pass page
   segmentation arguments to Tesseract OCR. This helps for two column
   text and other situations that confuse Tesseract.
-  Added a new "polyglot" version of the Docker image, that generates
   Tesseract with all languages packs installed, for the polyglots among
   us. It is much larger.

Changes

-  JPEG transcoding quality is now 95 instead of the default 75. Bigger
   file sizes for less degradation.

v3.1.1
======

Changes

-  Fixed bug that caused incorrect page size and DPI calculations on
   documents with mixed page sizes

v3.1
====

Changes

-  Default output format is now PDF/A-2b instead of PDF/A-1b
-  Python 3.5 and macOS El Capitan are now supported platforms - no
   changes were needed to implement support
-  Improved some error messages related to missing input files
-  Fixed :issue:`20`: uppercase .PDF extension not accepted
-  Fixed an issue where OCRmyPDF failed to text that certain pages
   contained previously OCR'ed text, such as OCR text produced by
   Tesseract 3.04
-  Inserts /Creator tag into PDFs so that errors can be traced back to
   this project
-  Added new option ``--pdf-renderer=auto``, to let OCRmyPDF pick the
   best PDF renderer. Currently it always chooses the 'hocrtransform'
   renderer but that behavior may change.
-  Set up Travis CI automatic integration testing

v3.0
====

New features

-  Easier installation with a Docker container or Python's ``pip``
   package manager
-  Eliminated many external dependencies, so it's easier to setup
-  Now installs ``ocrmypdf`` to ``/usr/local/bin`` or equivalent for
   system-wide access and easier typing
-  Improved command line syntax and usage help (``--help``)
-  Tesseract 3.03+ PDF page rendering can be used instead for better
   positioning of recognized text (``--pdf-renderer tesseract``)
-  PDF metadata (title, author, keywords) are now transferred to the
   output PDF
-  PDF metadata can also be set from the command line (``--title``,
   etc.)
-  Automatic repairs malformed input PDFs if possible
-  Added test cases to confirm everything is working
-  Added option to skip extremely large pages that take too long to OCR
   and are often not OCRable (e.g. large scanned maps or diagrams);
   other pages are still processed (``--skip-big``)
-  Added option to kill Tesseract OCR process if it seems to be taking
   too long on a page, while still processing other pages
   (``--tesseract-timeout``)
-  Less common colorspaces (CMYK, palette) are now supported by
   conversion to RGB
-  Multiple images on the same PDF page are now supported

Changes

-  New, robust rewrite in Python 3.4+ with
   `ruffus <http://www.ruffus.org.uk/index.html>`__ pipelines
-  Now uses Ghostscript 9.14's improved color conversion model to
   preserve PDF colors
-  OCR text is now rendered in the PDF as invisible text. Previous
   versions of OCRmyPDF incorrectly rendered visible text with an image
   on top.
-  All "tasks" in the pipeline can be executed in parallel on any
   available CPUs, increasing performance
-  The ``-o DPI`` argument has been phased out, in favor of
   ``--oversample DPI``, in case we need ``-o OUTPUTFILE`` in the future
-  Removed several dependencies, so it's easier to install. We no longer
   use:

   -  GNU `parallel <https://www.gnu.org/software/parallel/>`__
   -  `ImageMagick <http://www.imagemagick.org/script/index.php>`__
   -  Python 2.7
   -  Poppler
   -  `MuPDF <http://mupdf.com/docs/>`__ tools
   -  shell scripts
   -  Java and `JHOVE <http://jhove.sourceforge.net/>`__
   -  libxml2

-  Some new external dependencies are required or optional, compared to
   v2.x:

   -  Ghostscript 9.14+
   -  `qpdf <http://qpdf.sourceforge.net/>`__ 5.0.0+
   -  `Unpaper <https://github.com/Flameeyes/unpaper>`__ 6.1 (optional)
   -  some automatically managed Python packages

Release candidates^

-  rc9:

   -  Fix
      :issue:`118`:
      report error if ghostscript iccprofiles are missing
   -  fixed another issue related to
      :issue:`111`: PDF
      rasterized to palette file
   -  add support image files with a palette
   -  don't try to validate PDF file after an exception occurs

-  rc8:

   -  Fix
      :issue:`111`:
      exception thrown if PDF is missing DocumentInfo dictionary

-  rc7:

   -  fix error when installing direct from pip, "no such file
      'requirements.txt'"

-  rc6:

   -  dropped libxml2 (Python lxml) since Python 3's internal XML parser
      is sufficient
   -  set up Docker container
   -  fix Unicode errors if recognized text contains Unicode characters
      and system locale is not UTF-8

-  rc5:

   -  dropped Java and JHOVE in favour of qpdf
   -  improved command line error output
   -  additional tests and bug fixes
   -  tested on Ubuntu 14.04 LTS

-  rc4:

   -  dropped MuPDF in favour of qpdf
   -  fixed some installer issues and errors in installation
      instructions
   -  improve performance: run Ghostscript with multithreaded rendering
   -  improve performance: use multiple cores by default
   -  bug fix: checking for wrong exception on process timeout

-  rc3: skipping version number intentionally to avoid confusion with
   Tesseract
-  rc2: first release for public testing to test-PyPI, Github
-  rc1: testing release process

Compatibility notes
===================

-  ``./OCRmyPDF.sh`` script is still available for now
-  Stacking the verbosity option like ``-vvv`` is no longer supported
-  The configuration file ``config.sh`` has been removed. Instead, you
   can feed a file to the arguments for common settings:

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

-  Handling of filenames containing spaces: fixed

Notes and known issues

-  Some dependencies may work with lower versions than tested, so try
   overriding dependencies if they are "in the way" to see if they work.
-  ``--pdf-renderer tesseract`` will output files with an incorrect page
   size in Tesseract 3.03, due to a bug in Tesseract.
-  PDF files containing "inline images" are not supported and won't be
   for the 3.0 release. Scanned images almost never contain inline
   images.

v2.2-stable (2014-09-29)
========================

OCRmyPDF versions 1 and 2 were implemented as shell scripts. OCRmyPDF
3.0+ is a fork that gradually replaced all shell scripts with Python
while maintaining the existing command line arguments. No one is
maintaining old versions.

For details on older versions, see the `final version of its release
notes <https://github.com/fritz-hh/OCRmyPDF/blob/7fd3dbdf42ca53a619412ce8add7532c5e81a9d1/RELEASE_NOTES.md>`__.
