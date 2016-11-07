.. _lang-packs:

Installing additional language packs
====================================

OCRmyPDF uses Tesseract for OCR, and relies on its language packs for languages other than English. 

Tesseract supports `most languages <https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc#languages>`_.

For Linux users, you can often find packages that provide language packs:

Debian and Ubuntu users
-----------------------

.. code-block:: bash

   # Display a list of all Tesseract language packs
   apt-cache search tesseract-ocr

   # Debian/Ubuntu users
   apt-get install tesseract-ocr-chi-sim  # Example: Install Chinese Simplified language back
   
You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as to what languages it should search for. Multiple
languages can be requested using either ``-l eng+fre`` (English and French) or ``-l eng -l fre``.

Mac OS X (macOS) users
----------------------

You can install additional language packs by :ref:`installing Tesseract using Homebrew with all language packs <macos-all-languages>`.

Docker users
------------

Users of the Docker image may use the alternative :ref:`"polyglot" container <docker-polyglot>` which includes all languages.

Known limitations
-----------------

As of v4.2, users of ocrmypdf working languages outside the Latin alphabet should use the following syntax:

.. code-block:: bash

	ocrmypdf -l eng+gre --output-type pdf --pdf-renderer tesseract

The reasons for this are:

* The latest version of Ghostscript (9.19 as of this writing) has unfixed bugs in Unicode handling that generate invalid character maps, so Ghostscript cannot be used for PDF/A conversion
* The default "hocr" PDF renderer does not handle Asian fonts properly