RELEASE NOTES
=============

Please always read this file before installing the package

Download software here: https://github.com/fritz-hh/OCRmyPDF/tags

v1.0-rc2 (2013-04-29):
====

New features
------------

- Keep temporary files if debug mode is set (fixes #22)
- Set same owner & permissions if final PDF file than in input file (fixes #9)
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
