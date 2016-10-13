RELEASE NOTES
=============

OCRmyPDF uses `semantic versioning <http://semver.org/>`_.


v4.2.5:
=======

-  Fixed an issue (#100) with PDFs that omit the optional /BitsPerComponent parameter on images
-  Removed non-free file milk.pdf


v4.2.4:
=======

-  Fixed an error (#90) caused by PDFs that use stencil masks properly
-  Fixed handling of PDFs that try to draw images or stencil masks without properly setting up the graphics state (such images are now ignored for the purposes of calculating DPI)

v4.2.3:
=======

-  Fixed an issue with PDFs that store page rotation (/Rotate) in an indirect object
-  Integrated a few fixes to simplify downstream packaging (Debian)

   +  The test suite no longer assumes it is installed
   +  If running Linux, skip a test that passes Unicode on the command line

-  Added a test case to check explicit masks and stencil masks
-  Added a test case for indirect objects and linearized PDFs
-  Deprecated the OCRmyPDF.sh shell script


v4.2.2:
=======

-  Improvements to documentation


v4.2.1:
=======

-  Fixed an issue where PDF pages that contained stencil masks would report an incorrect DPI and cause Ghostscript to abort
-  Implemented stdin streaming


v4.2:
=====

-  ocrmypdf will now try to convert single image files to PDFs if they are provided as input (#15)

   +  This is a basic convenience feature. It only supports a single image and always makes the image fill the whole page.
   +  For better control over image to PDF conversion, use ``img2pdf`` (one of ocrmypdf's dependencies)

-  New argument ``--output-type {pdf|pdfa}`` allows disabling Ghostscript PDF/A generation

   +  ``pdfa`` is the default, consistent with past behavior
   +  ``pdf`` provides a workaround for users concerned about the increase in file size from Ghostscript forcing JBIG2 images to CCITT and transcoding JPEGs
   +  ``pdf`` preserves as much as it can about the original file, including problems that PDF/A conversion fixes

-  PDFs containing images with "non-square" pixel aspect ratios, such as 200x100 DPI, are now handled and converted properly (fixing a bug that caused to be cropped)
-  ``--force-ocr`` rasterizes pages even if they contain no images

   +  supports users who want to use OCRmyPDF to reconstruct text information in PDFs with damaged Unicode maps (copy and paste text does not match displayed text)
   +  supports reinterpreting PDFs where text was rendered as curves for printing, and text needs to be recovered
   +  fixes issue #82

-  Fixes an issue where, with certain settings, monochrome images in PDFs would be converted to 8-bit grayscale, increasing file size (#79)
-  Support for Ubuntu 12.04 LTS "precise" has been dropped in favor of (roughly) Ubuntu 14.04 LTS "trusty" 

   +  Some Ubuntu "PPAs" (backports) are needed to make it work
      
-  Support for some older dependencies dropped

   +  Ghostscript 9.15 or later is now required (available in Ubuntu trusty with backports)
   +  Tesseract 3.03 or later is now required (available in Ubuntu trusty)

-  Ghostscript now runs in "safer" mode where possible

v4.1.4:
=======

-  Bug fix: monochrome images with an ICC profile attached were incorrectly converted to full color images if lossless reconstruction was not possible due to other settings; consequence was increased file size for these images


v4.1.3:
=======

-  More helpful error message for PDFs with version 4 security handler
-  Update usage instructions for Windows/Docker users
-  Fix order of operations for matrix multiplication (no effect on most users)
-  Add a few leptonica wrapper functions (no effect on most users)


v4.1.2:
=======

-  Replace IEC sRGB ICC profile with Debian's sRGB (from icc-profiles-free) which is more compatible with the MIT license
-  More helpful error message for an error related to certain types of malformed PDFs


v4.1:
=====

-  ``--rotate-pages`` now only rotates pages when reasonably confidence in the orientation. This behavior can be adjusted with the new argument ``--rotate-pages-threshold``
-  Fixed problems in error checking if ``unpaper`` is uninstalled or missing at run-time
-  Fixed problems with "RethrownJobError" errors during error handling that suppressed the useful error messages


v4.0.7:
=======

-  Minor correction to Ghostscript output settings


v4.0.6:
=======

-  Update install instructions
-  Provide a sRGB profile instead of using Ghostscript's


v4.0.5:
=======

-  Remove some verbose debug messages from v4.0.4
-  Fixed temporary that wasn't being deleted
-  DPI is now calculated correctly for cropped images, along with other image transformations
-  Inline images are now checked during DPI calculation instead of rejecting the image

v4.0.4:
=======

Released with verbose debug message turned on. Do not use. Skip to v4.0.5.


v4.0.3:
=======

New features
------------

-  Page orientations detected are now reported in a summary comment


Fixes
-----

-  Show stack trace if unexpected errors occur
-  Treat "too few characters" error message from Tesseract as a reason to skip that page rather than
   abort the file
-  Docker: fix blank JPEG2000 issue by insisting on Ghostscript versions that have this fixed


v4.0.2:
=======

Fixes
-----

-  Fixed compatibility with Tesseract 3.04.01 release, particularly its different way of outputting
   orientation information
-  Improved handling of Tesseract errors and crashes
-  Fixed use of chmod on Docker that broke most test cases


v4.0.1:
=======

Fixes
-----

-  Fixed a KeyError if tesseract fails to find page orientation information


v4.0:
=====

New features
------------

-  Automatic page rotation (``-r``) is now available. It uses ignores any prior rotation information
   on PDFs and sets rotation based on the dominant orientation of detectable text. This feature is
   fairly reliable but some false positives occur especially if there is not much text to work with. (#4) 
-  Deskewing is now performed using Leptonica instead of unpaper. Leptonica is faster and more reliable
   at image deskewing than unpaper.


Fixes
-----

-  Fixed an issue where lossless reconstruction could cause some pages to be appear incorrectly
   if the page was rotated by the user in Acrobat after being scanned (specifically if it a /Rotate tag)
-  Fixed an issue where lossless reconstruction could misalign the graphics layer with respect to
   text layer if the page had been cropped such that its origin is not (0, 0) (#49)


Changes
-------

-  Logging output is now much easier to read
-  ``--deskew`` is now performed by Leptonica instead of unpaper (#25)
-  libffi is now required
-  Some changes were made to the Docker and Travis build environments to support libffi
-  ``--pdf-renderer=tesseract`` now displays a warning if the Tesseract version is less than 3.04.01,
   the planned release that will include fixes to an important OCR text rendering bug in Tesseract 3.04.00.
   You can also manually install ./share/sharp2.ttf on top of pdf.ttf in your Tesseract tessdata folder
   to correct the problem.


v3.2.1:
=======

Changes
-------

-  Fixed issue #47 "convert() got and unexpected keyword argument 'dpi'" by upgrading to img2pdf 0.2
-  Tweaked the Dockerfiles


v3.2:
=====

New features
------------

-  Lossless reconstruction: when possible, OCRmyPDF will inject text layers without 
   otherwise manipulating the content and layout of a PDF page. For example, a PDF containing a mix
   of vector and raster content would see the vector content preserved. Images may still be transcoded
   during PDF/A conversion.  (``--deskew`` and ``--clean-final`` disable this mode, necessarily.)
-  New argument ``--tesseract-pagesegmode`` allows you to pass page segmentation arguments to Tesseract OCR.
   This helps for two column text and other situations that confuse Tesseract.
-  Added a new "polyglot" version of the Docker image, that generates Tesseract with all languages packs installed,
   for the polyglots among us. It is much larger.

Changes
-------

-  JPEG transcoding quality is now 95 instead of the default 75. Bigger file sizes for less degradation.



v3.1.1:
=======

Changes
-------

-  Fixed bug that caused incorrect page size and DPI calculations on documents with mixed page sizes

v3.1:
=====

Changes
-------

-  Default output format is now PDF/A-2b instead of PDF/A-1b
-  Python 3.5 and OS X El Capitan are now supported platforms - no changes were
   needed to implement support
-  Improved some error messages related to missing input files
-  Fixed issue #20 - uppercase .PDF extension not accepted
-  Fixed an issue where OCRmyPDF failed to text that certain pages contained previously OCR'ed text, 
   such as OCR text produced by Tesseract 3.04
-  Inserts /Creator tag into PDFs so that errors can be traced back to this project
-  Added new option ``--pdf-renderer=auto``, to let OCRmyPDF pick the best PDF renderer. 
   Currently it always chooses the 'hocrtransform' renderer but that behavior may change.
-  Set up Travis CI automatic integration testing

v3.0:
=====

New features
------------

-  Easier installation with a Docker container or Python's ``pip`` package manager 
-  Eliminated many external dependencies, so it's easier to setup
-  Now installs ``ocrmypdf`` to ``/usr/local/bin`` or equivalent for system-wide
   access and easier typing
-  Improved command line syntax and usage help (``--help``)
-  Tesseract 3.03+ PDF page rendering can be used instead for better positioning
   of recognized text (``--pdf-renderer tesseract``)
-  PDF metadata (title, author, keywords) are now transferred to the 
   output PDF
-  PDF metadata can also be set from the command line (``--title``, etc.)
-  Automatic repairs malformed input PDFs if possible
-  Added test cases to confirm everything is working
-  Added option to skip extremely large pages that take too long to OCR and are 
   often not OCRable (e.g. large scanned maps or diagrams); other pages are still
   processed (``--skip-big``)
-  Added option to kill Tesseract OCR process if it seems to be taking too long on
   a page, while still processing other pages (``--tesseract-timeout``)
-  Less common colorspaces (CMYK, palette) are now supported by conversion to RGB
-  Multiple images on the same PDF page are now supported

Changes
-------

-  New, robust rewrite in Python 3.4+ with ruffus_ pipelines
-  Now uses Ghostscript 9.14's improved color conversion model to preserve PDF colors
-  OCR text is now rendered in the PDF as invisible text. Previous versions of OCRmyPDF
   incorrectly rendered visible text with an image on top.
-  All "tasks" in the pipeline can be executed in parallel on any
   available CPUs, increasing performance
-  The ``-o DPI`` argument has been phased out, in favor of ``--oversample DPI``, in
   case we need ``-o OUTPUTFILE`` in the future
-  Removed several dependencies, so it's easier to install.  We no 
   longer use:
   
   - GNU parallel_
   - ImageMagick_
   - Python 2.7
   - Poppler
   - MuPDF_ tools
   - shell scripts
   - Java and JHOVE_
   - libxml2

-  Some new external dependencies are required or optional, compared to v2.x:

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
------------------

-  rc9:

   - fix issue #118: report error if ghostscript iccprofiles are missing
   - fixed another issue related to #111: PDF rasterized to palette file
   - add support image files with a palette
   - don't try to validate PDF file after an exception occurs

-  rc8:

   - fix issue #111: exception thrown if PDF is missing DocumentInfo dictionary

-  rc7:

   - fix error when installing direct from pip, "no such file 'requirements.txt'"

-  rc6:

   - dropped libxml2 (Python lxml) since Python 3's internal XML parser is sufficient
   - set up Docker container
   - fix Unicode errors if recognized text contains Unicode characters and system locale is not UTF-8

-  rc5:

   - dropped Java and JHOVE in favour of qpdf
   - improved command line error output
   - additional tests and bug fixes
   - tested on Ubuntu 14.04 LTS

-  rc4:

   - dropped MuPDF in favour of qpdf
   - fixed some installer issues and errors in installation instructions
   - improve performance: run Ghostscript with multithreaded rendering
   - improve performance: use multiple cores by default
   - bug fix: checking for wrong exception on process timeout 

-  rc3: skipping version number intentionally to avoid confusion with Tesseract
-  rc2: first release for public testing to test-PyPI, Github
-  rc1: testing release process

Compatibility notes
-------------------

-  ``./OCRmyPDF.sh`` script is still available for now
-  Stacking the verbosity option like ``-vvv`` is no longer supported

-  The configuration file ``config.sh`` has been removed.  Instead, you can
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
-----

-  Handling of filenames containing spaces: fixed

Notes and known issues
----------------------

-  Some dependencies may work with lower versions than tested, so try
   overriding dependencies if they are "in the way" to see if they work.

-  ``--pdf-renderer tesseract`` will output files with an incorrect page size in Tesseract 3.03,
   due to a bug in Tesseract.

-  PDF files containing "inline images" are not supported and won't be for the 3.0 release. Scanned
   images almost never contain inline images.


v2.2-stable (2014-09-29):
=========================

OCRmyPDF versions 1 and 2 were implemented as shell scripts. OCRmyPDF 3.0+ is a fork that gradually replaced all shell scripts with Python while maintaining the existing command line arguments. No one is maintaining old versions.

For details on older versions, see the `final version of its release notes <https://github.com/fritz-hh/OCRmyPDF/blob/7fd3dbdf42ca53a619412ce8add7532c5e81a9d1/RELEASE_NOTES.md>`_.