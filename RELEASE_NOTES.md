RELEASE NOTES
=============

Please always read this file before installing the package

Download software here: https://github.com/fritz-hh/OCRmyPDF/tags

v2.0-stable (2014-01-25):
=======

New features
------------

- Check if the language(s) passed using the -l option is supported by tesseract (fixes #60)

Changes
-------

- Allow OCRmyPDF to be used with tesseract 3.02.01, even though OCR might fail for few PDF file (see issue #28). Rationale: For some linux distribution, no newer version than tesseract 3.02.01 is available

Fixes
-----

- More robust algorithm for checking the version of the installed tesseract package

Tested with
-----------

- Operating system: FreeBSD 9.1
- Dependencies:
   - parallel 20130222
   - poppler-utils 0.22.2
   - ImageMagick 6.8.0-7 2013-03-30
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.3
   - ghoscript (gs): 9.06
   - java: openjdk version "1.7.0_17"

v2.0-rc2 (2014-01-16):
=======
   
New features
------------

- None

Changes
-------

- Size reduction of final PDF file: (fixes #50)
   - Support for monochrome (Black&White) images (massive size reduction in final PDF: >80%)
   - Reduced size of grayscale images (by 13% on test PDF file)
- Preventing fi, fl ligatures does not require anymore to pass an additional config file to tesseract using the -C option (fixes #58)
- Location of temporary folder according to content of environment variable TMPDIR.
- Dependency to pdftk removed
- Check for compatible versions of dependencies: (fixes #51)
   - parallel and tesseract
   - python libraries reportlab and lxml

Fixes
-----

- Improved portability with various shells (dash, bash, tcsh) and OS (FreeBSD, MAC OSX, Linux) (fixes #59)
- Corrected bug in case the input PDF file contains a space character (fixes #48)
- Prevent spurious error message in case there is no image in a PDF page
- Prevent collision of temporary folder names (fixes #57)

Tested with
-----------

- Operating system: FreeBSD 9.1
- Dependencies:
   - parallel 20130222
   - poppler-utils 0.22.2
   - ImageMagick 6.8.0-7 2013-03-30
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.3
   - ghoscript (gs): 9.06
   - java: openjdk version "1.7.0_17"

v2.0-rc1 (2014-01-07):
====

New features
------------

- Huge performance improvement on machines having multiple CPU/cores (processing of several pages concurrently) (fixes #18)
- By default prevent from processing a PDF file already containing fonts (i.e. text)(it can be overridden with the -f flag) (fixes #16)
- Warn if the resolution is too low to get reasonable OCR results (fixes #37)
- New option (-o) to perform automatic oversampling if the image resolution is too low. This can improve OCR results.
- Warn if using a tesseract version older than v3.02.02 (as older versions are known to produce invalid output) (fixes #41)
- Echo version of the installed dependencies (e.g. tesseract) in debug mode in order to ease support (fixes #35)
- Echo the arguments passed to the script in debug mode to ease support

Changes
-------

- In debug mode: The debug page is now placed after the respective "normal" page
- Reduced disk space usage in temporary folder if -d (deskew) or -c (cleanup) options are not selected
- New file src/config.sh containing various configuration parameters
- Documentation of the tesseract config file "tess-cfg/no_ligature" improved 
- Improved consistency of the temporary file names

Fixes
-----

- Improved robustness:
   - in case vertical resolution differs from horizontal resolution (fixes #38)
   - in case a PDF page contains more than one image (fixes #36)
- Fix a problem occurring if python 3 is the standard interpreter (fixes #33)
- Fix a problem occurring if the input PDF file contains special characters like "#" (fixes #34)

Tested with
-----------

- Operating system: FreeBSD 9.1
- Dependencies:
   - parallel 20130222
   - poppler-utils 0.22.2
   - ImageMagick 6.8.0-7 2013-03-30
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.3
   - pdftk 1.45
   - ghoscript (gs): 9.06
   - java: openjdk version "1.7.0_17"

v1.1-stable (2014-01-06):
====

New features
------------

- N/A

Changes
-------

- N/A

Fixes
-----

- Fixed syntax error (bashism) leading to an error message on certain systems (fixes #42)

Tested with
-----------

- Operating system: FreeBSD 9.1
- Dependencies:
   - poppler-utils 0.22.2
   - ImageMagick 6.8.0-7 2013-03-30
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.3
   - pdftk 1.45
   - ghoscript (gs): 9.06
   - java: openjdk version "1.7.0_17"

v1.0-stable (2013-05-06):
====

New features
------------

- In debug mode: compute and echo time required for processing (fixes #26)

Changes
-------

- Removed feature to add metadata in final pdf file (because it lead to to final PDF file that does not comply to the PDF/A-1 format)
- Removed feature to set same owner & permissions in final PDF file than in input file
- Removed many unused jhove files (e.g. documentation, *.java and *.class files)

Fixes
-----

- Correction to handle correctly path and input PDF files having spaces (fixes #31)
- Resolutions (x/y) that are nearly equal are now supported (fixes #25)
- Fix compatibility issue with Ubuntu server 12.04 / Ubuntu server 10.04 / Linux Mint 13 Maya and probably other Linux distributions (fixes #27)
- Commit missing jhove files (*.jar mainly) due to wrong .gitignore

Tested with
-----------

- Operating system: FreeBSD 9.1
- Dependencies:
   - poppler-utils 0.22.2
   - ImageMagick 6.8.0-7 2013-03-30
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.3
   - pdftk 1.45
   - ghoscript (gs): 9.06
   - java: openjdk version "1.7.0_17"

v1.0-rc2 (2013-04-29):
====

New features
------------

- Keep temporary files if debug mode is set (fixes #22)
- Set same owner & permissions in final PDF file than in input file (fixes #9)
- Added metadata in final pdf file (fixes #4)

Changes
-------

- N/A

Fixes
-----

- Fixed wrong image cropping when deskew option is activated
- Exit with error message if page size is not found in hocr file (fixes #21)
- Various minor fixes in log messages

Tested with
-----------

- Operating system: FreeBSD 9.1
- Dependencies:
   - poppler-utils 0.22.2
   - ImageMagick 6.8.0-7 2013-03-30
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.3
   - pdftk 1.45
   - ghoscript (gs): 9.06
   - java: openjdk version "1.7.0_17"

v1.0-rc1 (2013-04-26):
====

New features
------------

- First release candidate

Changes
-------

- N/A

Fixes
-----

- N/A

Tested with
-----------

- Operating system: FreeBSD 9.1
- Dependencies:
   - poppler-utils 0.22.2
   - ImageMagick 6.8.0-7 2013-03-30
   - Unpaper 0.3
   - tesseract 3.02.02
   - Python 2.7.3
   - pdftk 1.45
   - ghoscript (gs): 9.06
   - java: openjdk version "1.7.0_17"
