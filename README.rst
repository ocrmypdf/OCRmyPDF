OCRmyPDF
========

OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to
be searched or copy-pasted.

.. code-block:: bash

   ocrmypdf                      # it's a scriptable command line program
      -l eng+fra                 # it supports multiple languages
      --rotate-pages             # it can fix pages that are misrotated
      --deskew                   # it can deskew crooked PDFs!
      --title "My PDF"           # it can change output metadata
      --jobs 4                   # it uses multiple cores by default
      --output-type pdfa         # it produces PDF/A by default
      input_scanned.pdf          # takes PDF input (or images)
      output_searchable.pdf      # produces validated PDF output


Main features
-------------

-  Generates a searchable
   `PDF/A <https://en.wikipedia.org/?title=PDF/A>`_ file from a regular PDF
-  Places OCR text accurately below the image to ease copy / paste
-  Keeps the exact resolution of the original embedded images
-  When possible, inserts OCR information as a "lossless" operation without rendering vector information
-  Keeps file size about the same
-  If requested deskews and/or cleans the image before performing OCR
-  Validates input and output files
-  Provides debug mode to enable easy verification of the OCR results
-  Processes pages in parallel when more than one CPU core is
   available
-  Uses `Tesseract OCR <https://github.com/tesseract-ocr/tesseract>`_ engine
-  Supports more than `100 languages <https://github.com/tesseract-ocr/tessdata>`_ recognized by Tesseract
-  Battle-tested on thousands of PDFs, a test suite and continuous integration

For details: please consult the `release notes <RELEASE_NOTES.rst>`_.

Motivation
----------

I searched the web for a free command line tool to OCR PDF files on
Linux/UNIX: I found many, but none of them were really satisfying.

-  Either they produced PDF files with misplaced text under the image (making copy/paste impossible) 
-  Or they did not handle accents and multilingual characters
-  Or they changed the resolution of the embedded images
-  Or they generated ridiculously large PDF files
-  Or they crashed when trying to OCR some of my PDF files
-  Or they did not produce valid PDF files (even though they were readable with my current PDF reader)
-  On top of that none of them produced PDF/A files (format dedicated for long time storage)

...so I decided to develop my own tool (using various existing scripts
as an inspiration). 

Installation
------------

Linux, UNIX, and macOS are supported. Windows is not directly supported but there is a Docker image available that runs on Windows.

Users of Debian 9 or later or Ubuntu 16.10 or later may simply
``apt-get install ocrmypdf``.

For everyone else, `see our documentation <https://ocrmypdf.readthedocs.io/en/latest/installation.html>`_ for installation steps.

Languages
---------

OCRmyPDF uses Tesseract for OCR, and relies on its language packs. For Linux users,
you can often find packages that provide language packs:

.. code-block:: bash

   # Display a list of all Tesseract language packs
   apt-cache search tesseract-ocr

   # Debian/Ubuntu users
   apt-get install tesseract-ocr-chi-sim  # Example: Install Chinese Simplified language back
   
You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as to what languages it should search for. Multiple
languages can be requested.

Documentation and support
-------------------------

Once ocrmypdf is installed, the built-in help which explains the command syntax and options can be accessed via:

.. code-block:: bash

   ocrmypdf --help

Our `documentation is served on Read the Docs <https://ocrmypdf.readthedocs.io/en/latest/index.html>`_.

If you detect an issue, please:

-  Check whether your issue is already known
-  If no problem report exists on github, please create one here:
   https://github.com/jbarlow83/OCRmyPDF/issues
-  Describe your problem thoroughly
-  Append the console output of the script when running the debug mode
   (``-v 1`` option)
-  If possible provide your input PDF file as well as the content of the
   temporary folder (using a file sharing service like Dropbox)

Press & Media
-------------

-  `c't 1-2014, page 59 <http://heise.de/-2279695>`_:
   Detailed presentation of OCRmyPDF v1.0 in the leading German IT
   magazine c't
-  `heise Open Source, 09/2014: Texterkennung mit
   OCRmyPDF <http://heise.de/-2356670>`_

Disclaimer
----------

The software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.
