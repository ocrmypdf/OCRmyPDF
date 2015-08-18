OCRmyPDF
========

OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to
be searched.

Main features
-------------

-  Generates a searchable
   `PDF/A <https://en.wikipedia.org/?title=PDF/A>`__ file from a regular PDF
   only containing images
-  Places OCRed text accurately below the image to ease copy / paste
-  Keeps the exact resolution of the original embedded images

   -  or if requested oversamples the images before OCRing so as to get
      better results

-  When possible, copies input images directly to output without transcoding them,
   to preserve image quality
-  Keeps file size about the same
-  If requested deskews and/or cleans the image before performing OCR
-  Validates input and output files
-  Provides debug mode to enable easy verification of the OCR results
-  Processes several pages in parallel when more than one CPU core is
   available
-  Uses Tesseract OCR engine

For details: please consult the `release notes <RELEASE_NOTES.rst>`__

Motivation
----------

I searched the web for a free command line tool to OCR PDF files on
Linux/UNIX: I found many, but none of them were really satisfying.

-  Either they produced PDF files with misplaced text under the image (making copy/paste impossible) 
-  Or they did not display correctly some escaped HTML characters located in the hOCR file produced by the OCR engine 
-  Or they changed the resolution of the embedded images
-  Or they generated PDF files having a ridiculous big size
-  Or they crashed when trying to OCR some of my PDF files
-  Or they did not produce valid PDF files (even though they were readable with my current PDF reader)
-  On top of that none of them produced PDF/A files (format dedicated for long time storage)

... so I decided to develop my own tool (using various existing scripts
as an inspiration)

Installation
------------

Download OCRmyPDF here: https://github.com/fritz-hh/OCRmyPDF/releases

You can install it to a Python virtual environment or system-wide. 


Installing dependencies on Mac OS X Yosemite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If it's not already present, `install Homebrew <http://brew.sh/>`__

Update Homebrew::

   brew update
   brew upgrade
   
Install the required Homebrew packages, if any are missing::

   brew install libpng openjpeg jbig2dec     # image libraries
   brew install qpdf
   brew install ghostscript
   brew install python3
   brew install libxml2
   brew install leptonica
   brew install tesseract
   
It is also recommended that install Pillow and confirm it can read and write JPEG and PNG files::

   pip3 install --upgrade pip
   pip3 install --upgrade pillow

To test that your dependencies are working, try this command::

   python3 -c "from PIL import Image; im = Image.new('1', (1, 1)); im.save('test.png'); im.save('test.jpg')"


Installing dependencies on Ubuntu 14.04 LTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Update apt-get::

   sudo apt-get update
   sudo apt-get upgrade
   
Install dependencies::

   sudo apt-get install \
      zlib1g-dev \
      libjpeg-dev \
      ghostscript \
      tesseract-ocr \
      qpdf \
      unpaper \
      python3-pip \
      python3-pil \
      python3-pytest \
      python3-reportlab
      
Installing HEAD revision from sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install the HEAD revision from sources in development mode::

   git clone -b master https://github.com/fritz-hh/OCRmyPDF.git
   cd OCRmyPDF
   pip3 install -e .
   
On certain Linux/UNIX platforms such as Ubuntu, you may need to use 
run the install command as superuser::

   sudo pip3 install -e .
   
Note that this will alter your system's Python distribution. If you prefer 
to not install as superuser, you can install the package in a Python virtual environment::

   git clone -b master https://github.com/fritz-hh/OCRmyPDF.git
   pyvenv venv
   source venv/bin/activate
   cd OCRmyPDF
   pip3 install -e .

If your platform does not have ``pip3``, make sure that Python 3.4+ and the `pip` 
package are installed.

To run the program::
   
   ocrmypdf --help

If not yet installed, the script will notify you about dependencies that
need to be installed. The script requires specific versions of the
dependencies. Older version than the ones mentioned in the release notes
are likely not to be compatible to OCRmyPDF.

Support
-------

In case you detect an issue, please:

-  Check if your issue is already known
-  If no problem report exists on github, please create one here:
   https://github.com/fritz-hh/OCRmyPDF/issues
-  Describe your problem thoroughly
-  Append the console output of the script when running the debug mode
   (-v 1 option)
-  If possible provide your input PDF file as well as the content of the
   temporary folder (using a file sharing service like
   www.file-upload.net)

Press & Media
-------------

-  `c't 1-2014, page 59 <http://www.heise.de/ct/inhalt/2014/1/58/>`__:
   Detailed presentation of OCRmyPDF v1.0 in the leading German IT
   magazine c't
-  `heise Open Source, 09/2014: Texterkennung mit
   OCRmyPDF <http://www.heise.de/-2356670>`__

Disclaimer
----------

The software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.
