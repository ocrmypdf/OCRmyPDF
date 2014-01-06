RELEASE NOTES
=============

Please always read this file before installing the package

Download software here: https://github.com/fritz-hh/OCRmyPDF/tags

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
