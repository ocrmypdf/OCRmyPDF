RELEASE NOTES
=============

Please always read this file before installing the package

Download software here: https://github.com/jbarlow83/OCRmyPDF/tags

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

Fixes
-----

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

-  Show stack trace if unexpect errors occur
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

New features
------------

- None

Changes
-------

- Update to jhove v1.11
- Request the python library reportlab v3.0 or newer (So that we could remove a patch to the previous version of reportlab leading to issues for some users)

Fixes
-----

- Fix bug on Mac OS X (resolution of simlink to OCRmyPDF.sh script) (thanks to jbarlow83)
- Check if the input pdf file exists before to continue

Tested with
-----------

- Operating system: FreeBSD 9.2
- Dependencies:

   - parallel 20140822
   - poppler-utils 0.24.5
   - ImageMagick 6.8.9-4 2014-09-17
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.8
   - ghostcript (gs): 9.06
   - java: openjdk version "1.7.0_65"


v2.1-stable (2014-09-20):
=========================

New features
------------

-  None

Changes
-------

-  None

Fixes
-----

-  Allow execution via simlink
-  Add support for tesseract 3.03
-  Add support for newer version of reportlab
-  Lowered minimum version of gnu parallel
-  Various typo

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  parallel 20130222
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"

v2.0-stable (2014-01-25):
=========================

New features
------------

-  Check if the language(s) passed using the -l option is supported by
   tesseract (fixes #60)

Changes
-------

-  Allow OCRmyPDF to be used with tesseract 3.02.01, even though OCR
   might fail for few PDF file (see issue #28). Rationale: For some
   linux distribution, no newer version than tesseract 3.02.01 is
   available

Fixes
-----

-  More robust algorithm for checking the version of the installed
   tesseract package

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  parallel 20130222
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"

v2.0-rc2 (2014-01-16):
======================

New features
------------

-  None

Changes
-------

-  Size reduction of final PDF file: (fixes #50)
-  Support for monochrome (Black&White) images (massive size reduction
   in final PDF: >80%)
-  Reduced size of grayscale images (by 13% on test PDF file)
-  Preventing fi, fl ligatures does not require anymore to pass an
   additional config file to tesseract using the -C option (fixes #58)
-  Location of temporary folder according to content of environment
   variable TMPDIR.
-  Dependency to pdftk removed
-  Check for compatible versions of dependencies: (fixes #51)
-  parallel and tesseract
-  python libraries reportlab and lxml

Fixes
-----

-  Improved portability with various shells (dash, bash, tcsh) and OS
   (FreeBSD, MAC OSX, Linux) (fixes #59)
-  Corrected bug in case the input PDF file contains a space character
   (fixes #48)
-  Prevent spurious error message in case there is no image in a PDF
   page
-  Prevent collision of temporary folder names (fixes #57)

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  parallel 20130222
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"

v2.0-rc1 (2014-01-07):
======================

New features
------------

-  Huge performance improvement on machines having multiple CPU/cores
   (processing of several pages concurrently) (fixes #18)
-  By default prevent from processing a PDF file already containing
   fonts (i.e. text)(it can be overridden with the -f flag) (fixes #16)
-  Warn if the resolution is too low to get reasonable OCR results
   (fixes #37)
-  New option (-o) to perform automatic oversampling if the image
   resolution is too low. This can improve OCR results.
-  Warn if using a tesseract version older than v3.02.02 (as older
   versions are known to produce invalid output) (fixes #41)
-  Echo version of the installed dependencies (e.g. tesseract) in debug
   mode in order to ease support (fixes #35)
-  Echo the arguments passed to the script in debug mode to ease support

Changes
-------

-  In debug mode: The debug page is now placed after the respective
   "normal" page
-  Reduced disk space usage in temporary folder if -d (deskew) or -c
   (cleanup) options are not selected
-  New file src/config.sh containing various configuration parameters
-  Documentation of the tesseract config file "tess-cfg/no\_ligature"
   improved
-  Improved consistency of the temporary file names

Fixes
-----

-  Improved robustness:
-  in case vertical resolution differs from horizontal resolution (fixes
   #38)
-  in case a PDF page contains more than one image (fixes #36)
-  Fix a problem occurring if python 3 is the standard interpreter
   (fixes #33)
-  Fix a problem occurring if the input PDF file contains special
   characters like "#" (fixes #34)

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  parallel 20130222
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  pdftk 1.45
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"

v1.1-stable (2014-01-06):
=========================

New features
------------

-  N/A

Changes
-------

-  N/A

Fixes
-----

-  Fixed syntax error (bashism) leading to an error message on certain
   systems (fixes #42)

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  pdftk 1.45
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"

v1.0-stable (2013-05-06):
=========================

New features
------------

-  In debug mode: compute and echo time required for processing (fixes
   #26)

Changes
-------

-  Removed feature to add metadata in final pdf file (because it lead to
   to final PDF file that does not comply to the PDF/A-1 format)
-  Removed feature to set same owner & permissions in final PDF file
   than in input file
-  Removed many unused jhove files (e.g. documentation, \*.java and
   \*.class files)

Fixes
-----

-  Correction to handle correctly path and input PDF files having spaces
   (fixes #31)
-  Resolutions (x/y) that are nearly equal are now supported (fixes #25)
-  Fix compatibility issue with Ubuntu server 12.04 / Ubuntu server
   10.04 / Linux Mint 13 Maya and probably other Linux distributions
   (fixes #27)
-  Commit missing jhove files (\*.jar mainly) due to wrong .gitignore

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  pdftk 1.45
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"

v1.0-rc2 (2013-04-29):
======================

New features
------------

-  Keep temporary files if debug mode is set (fixes #22)
-  Set same owner & permissions in final PDF file than in input file
   (fixes #9)
-  Added metadata in final pdf file (fixes #4)

Changes
-------

-  N/A

Fixes
-----

-  Fixed wrong image cropping when deskew option is activated
-  Exit with error message if page size is not found in hocr file (fixes
   #21)
-  Various minor fixes in log messages

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  pdftk 1.45
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"

v1.0-rc1 (2013-04-26):
======================

New features
------------

-  First release candidate

Changes
-------

-  N/A

Fixes
-----

-  N/A

Tested with
-----------

-  Operating system: FreeBSD 9.1
-  Dependencies:
-  poppler-utils 0.22.2
-  ImageMagick 6.8.0-7 2013-03-30
-  Unpaper 0.3
-  tesseract 3.02.02
-  Python 2.7.3
-  pdftk 1.45
-  ghoscript (gs): 9.06
-  java: openjdk version "1.7.0\_17"
