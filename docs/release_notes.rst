Release notes
=============

OCRmyPDF uses `semantic versioning <http://semver.org/>`_ for its command line interface.

The OCRmyPDF package itself does not contain a public API, although it is fairly stable and breaking changes are usually timed with a major release. A future release will clearly define the stable public API.

v5.7.0
------

-   Fixed an issue that caused poor CPU utilization on machines more than 4 cores when running Tesseract 4. (Related to issue #217.)

-   The 'hocr' renderer has been improved. The 'sandwich' and 'tesseract' renderers are still better for most use cases, but 'hocr' may be useful for people who work with the PDF.js renderer in English/ASCII languages. (#225)

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

-   Fix issue #219: change how the final output file is created to avoid triggering permission errors when the output is a special file such as ``/dev/null``
-   Fix test suite failures due to a qpdf 8.0.0 regression and Python 3.5's handling of symlink
-   The "encrypted PDF" error message was different depending on the type of PDF encryption. Now a single clear message appears for all types of PDF encryption.
-   ocrmypdf is now in Homebrew. Homebrew users are advised to the version of ocrmypdf in the official homebrew-core formulas rather than the private tap.
-   Some linting


v5.6.0
------

-   Fix issue #216: preserve "text as curves" PDFs without rasterizing file
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

-   Fix issue #181: fix final merge failure for PDFs with more pages than the system file handle limit (``ulimit -n``)
-   Fix issue #200: an uncommon syntax for formatting decimal numbers in a PDF would cause qpdf to issue a warning, which ocrmypdf treated as an error. Now this the warning is relayed.
-   Fix an issue where intermediate PDFs would be created at version 1.3 instead of the version of the original file. It's possible but unlikely this had side effects.
-   A warning is now issued when older versions of qpdf are used since issues like #200 cause qpdf to infinite-loop
-   Address issue #140: if Tesseract outputs invalid UTF-8, escape it and print its message instead of aborting with a Unicode error 
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

-   Added ``--user-words`` and ``--user-patterns`` arguments which are forwarded to Tesseract OCR as words and regular expressions respective to use to guide OCR. Supplying a list of subject-domain words should assist Tesseract with resolving words. (#165)
-   Using a non Latin-1 language with the "hocr" renderer now warns about possible OCR quality and recommends workarounds (#176)
-   Output file path added to error message when that location is not writable (#175)
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

-   Fixed issue #169, exception due to failure to create sidecar text files on some versions of Tesseract 3.04, including the jbarlow83/ocrmypdf Docker image


v5.0
----

-   Backward incompatible changes

     + Support for Python 3.4 dropped. Python 3.5 is now required.
     + Support for Tesseract 3.02 and 3.03 dropped. Tesseract 3.04 or newer is required. Tesseract 4.00 (alpha) is supported.
     + The OCRmyPDF.sh script was removed.

-   Add a new feature, ``--sidecar``, which allows creating "sidecar" text files which contain the OCR results in plain text. These OCR text is more reliable than extracting text from PDFs. Closes #126.
-   New feature: ``--pdfa-image-compression``, which allows overriding Ghostscript's lossy-or-lossless image encoding heuristic and making all images JPEG encoded or lossless encoded as desired. Fixes #163.
-   Fixed issue #143, added ``--quiet`` to suppress "INFO" messages
-   Fixed issue #164, a typo
-   Removed the command line parameters ``-n`` and ``--just-print`` since they have not worked for some time (reported as Ubuntu bug `#1687308 <https://bugs.launchpad.net/ubuntu/+source/ocrmypdf/+bug/1687308>`_)


v4.5.6
------

-   Fixed issue #156, 'NoneType' object has no attribute 'getObject' on pages with no optional /Contents record.  This should resolve all issues related to pages with no /Contents record.
-   Fixed issue #158, ocrmypdf now stops and terminates if Ghostscript fails on an intermediate step, as it is not possible to proceed.
-   Fixed issue #160, exception thrown on certain invalid arguments instead of error message


v4.5.5
------

-   Automated update of macOS homebrew tap
-   Fixed issue #154, KeyError '/Contents' when searching for text on blank pages that have no /Contents record.  Note: incomplete fix for this issue.


v4.5.4
------

-   Fix ``--skip-big`` raising an exception if a page contains no images (#152) (thanks to @TomRaz)
-   Fix an issue where pages with no images might trigger "cannot write mode P as JPEG" (#151)


v4.5.3
------

-   Added a workaround for Ghostscript 9.21 and probably earlier versions would fail with the error message "VMerror -25", due to a Ghostscript bug in XMP metadata handling
-   High Unicode characters (U+10000 and up) are no longer accepted for setting metadata on the command line, as Ghostscript may not handle them correctly.
-   Fixed an issue where the ``tess4`` renderer would duplicate content onto output pages if tesseract failed or timed out
-   Fixed ``tess4`` renderer not recognized when lossless reconstruction is possible


v4.5.2
------

-   Fix issue #147. ``--pdf-renderer tess4 --clean`` will produce an oversized page containing the original image in the bottom left corner, due to loss DPI information.
-   Make "using Tesseract 4.0" warning less ominous
-   Set up machinery for homebrew OCRmyPDF tap


v4.5.1
------

-   Fix issue #137, proportions of images with a non-square pixel aspect ratio would be distorted in output for ``--force-ocr`` and some other combinations of flags


v4.5
----

-   Exotic PDFs containing "Form XObjects" are now supported (issue #134; PDF reference manual 8.10), and images they contain are taken into account when determining the resolution for rasterizing
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

-   Fixed an issue (#100) with PDFs that omit the optional /BitsPerComponent parameter on images
-   Removed non-free file milk.pdf


v4.2.4
------

-   Fixed an error (#90) caused by PDFs that use stencil masks properly
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

-   ocrmypdf will now try to convert single image files to PDFs if they are provided as input (#15)

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
    +  fixes issue #82

-   Fixes an issue where, with certain settings, monochrome images in PDFs would be converted to 8-bit grayscale, increasing file size (#79)
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
^^^^^^^^^^^^

-   Page orientations detected are now reported in a summary comment


Fixes
^^^^^

-   Show stack trace if unexpected errors occur
-   Treat "too few characters" error message from Tesseract as a reason to skip that page rather than
    abort the file
-   Docker: fix blank JPEG2000 issue by insisting on Ghostscript versions that have this fixed


v4.0.2
------

Fixes
^^^^^

-   Fixed compatibility with Tesseract 3.04.01 release, particularly its different way of outputting
    orientation information
-   Improved handling of Tesseract errors and crashes
-   Fixed use of chmod on Docker that broke most test cases


v4.0.1
------

Fixes
^^^^^

-   Fixed a KeyError if tesseract fails to find page orientation information


v4.0
----

New features
^^^^^^^^^^^^

-   Automatic page rotation (``-r``) is now available. It uses ignores any prior rotation information
    on PDFs and sets rotation based on the dominant orientation of detectable text. This feature is
    fairly reliable but some false positives occur especially if there is not much text to work with. (#4) 
-   Deskewing is now performed using Leptonica instead of unpaper. Leptonica is faster and more reliable
    at image deskewing than unpaper.


Fixes
^^^^^

-   Fixed an issue where lossless reconstruction could cause some pages to be appear incorrectly
    if the page was rotated by the user in Acrobat after being scanned (specifically if it a /Rotate tag)
-   Fixed an issue where lossless reconstruction could misalign the graphics layer with respect to
    text layer if the page had been cropped such that its origin is not (0, 0) (#49)


Changes
^^^^^^^

-   Logging output is now much easier to read
-   ``--deskew`` is now performed by Leptonica instead of unpaper (#25)
-   libffi is now required
-   Some changes were made to the Docker and Travis build environments to support libffi
-   ``--pdf-renderer=tesseract`` now displays a warning if the Tesseract version is less than 3.04.01,
    the planned release that will include fixes to an important OCR text rendering bug in Tesseract 3.04.00.
    You can also manually install ./share/sharp2.ttf on top of pdf.ttf in your Tesseract tessdata folder
    to correct the problem.


v3.2.1
------

Changes
^^^^^^^

-   Fixed issue #47 "convert() got and unexpected keyword argument 'dpi'" by upgrading to img2pdf 0.2
-   Tweaked the Dockerfiles


v3.2
----

New features
^^^^^^^^^^^^

-   Lossless reconstruction: when possible, OCRmyPDF will inject text layers without 
    otherwise manipulating the content and layout of a PDF page. For example, a PDF containing a mix
    of vector and raster content would see the vector content preserved. Images may still be transcoded
    during PDF/A conversion.  (``--deskew`` and ``--clean-final`` disable this mode, necessarily.)
-   New argument ``--tesseract-pagesegmode`` allows you to pass page segmentation arguments to Tesseract OCR.
    This helps for two column text and other situations that confuse Tesseract.
-   Added a new "polyglot" version of the Docker image, that generates Tesseract with all languages packs installed,
    for the polyglots among us. It is much larger.

Changes
^^^^^^^

-   JPEG transcoding quality is now 95 instead of the default 75. Bigger file sizes for less degradation.



v3.1.1
------

Changes
^^^^^^^

-   Fixed bug that caused incorrect page size and DPI calculations on documents with mixed page sizes

v3.1
----

Changes
^^^^^^^

-   Default output format is now PDF/A-2b instead of PDF/A-1b
-   Python 3.5 and macOS El Capitan are now supported platforms - no changes were
    needed to implement support
-   Improved some error messages related to missing input files
-   Fixed issue #20 - uppercase .PDF extension not accepted
-   Fixed an issue where OCRmyPDF failed to text that certain pages contained previously OCR'ed text, 
    such as OCR text produced by Tesseract 3.04
-   Inserts /Creator tag into PDFs so that errors can be traced back to this project
-   Added new option ``--pdf-renderer=auto``, to let OCRmyPDF pick the best PDF renderer. 
    Currently it always chooses the 'hocrtransform' renderer but that behavior may change.
-   Set up Travis CI automatic integration testing

v3.0
----

New features
^^^^^^^^^^^^

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
^^^^^^^

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

Release candidates
^^^^^^^^^^^^^^^^^^

-   rc9:

    - fix issue #118: report error if ghostscript iccprofiles are missing
    - fixed another issue related to #111: PDF rasterized to palette file
    - add support image files with a palette
    - don't try to validate PDF file after an exception occurs

-   rc8:

    - fix issue #111: exception thrown if PDF is missing DocumentInfo dictionary

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
^^^^^

-   Handling of filenames containing spaces: fixed

Notes and known issues
^^^^^^^^^^^^^^^^^^^^^^

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
