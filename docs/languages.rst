.. _lang-packs:

====================================
Installing additional language packs
====================================

OCRmyPDF uses Tesseract for OCR, and relies on its language packs for all languages.
On most platforms, English is installed with Tesseract by default, but not always.

Tesseract supports `most
languages <https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc#languages>`__.
Languages are identified by standardized three-letter codes (called ISO 639-2 Alpha-3).
Tesseract's documentation also lists the three-letter code for your language.
Some are anglicized, e.g. Spanish is ``spa`` rather than ``esp``, while others
are not, e.g. German is ``deu``.

After you have installed a language pack, you can use it ``ocrmypdf -l <language>``,
for example ``ocrmypdf -l spa``. For multilingual documents, you can specify
all languages to be expected, e.g. ``ocrmypdf -l eng+fra`` for English and French.
English is assumed by default unless other language(s) are specified.

For Linux users, you can often find packages that provide language
packs:

Debian and Ubuntu users
=======================

.. code-block:: bash

   # Display a list of all Tesseract language packs
   apt-cache search tesseract-ocr

   # Install Chinese Simplified language pack
   apt-get install tesseract-ocr-chi-sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as
to what languages it should search for. Multiple languages can be
requested using either ``-l eng+fre`` (English and French) or
``-l eng -l fre``.

Fedora users
============

.. code-block:: bash

   # Display a list of all Tesseract language packs
   dnf search tesseract

   # Install Chinese Simplified language pack
   dnf install tesseract-langpack-chi_sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as
to what languages it should search for. Multiple languages can be
requested using either ``-l eng+fre`` (English and French) or
``-l eng -l fre``.

macOS users
===========

You can install additional language packs by
:ref:`installing Tesseract using Homebrew with all language packs <macos-all-languages>`.

Docker users
============

Users of the OCRmyPDF Docker image should install language packs into a
derived Docker image as
:ref:`described in that section <docker-lang-packs>`.

Windows users
=============

The Tesseract installer provided by Chocolatey currently includes only English language. 
To install other languages, download the respective language pack (``.traineddata`` file) 
from https://github.com/tesseract-ocr/tessdata/ and place it in 
``C:\\Program Files\\Tesseract-OCR\\tessdata`` (or wherever Tesseract OCR is installed).
