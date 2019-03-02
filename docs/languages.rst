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

   # Install Chinese Simplified language pack
   apt-get install tesseract-ocr-chi-sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as to what languages it should search for. Multiple
languages can be requested using either ``-l eng+fre`` (English and French) or ``-l eng -l fre``.

Fedora users
------------

.. code-block:: bash

   # Display a list of all Tesseract language packs
   dnf search tesseract

   # Install Chinese Simplified language pack
   dnf install tesseract-langpack-chi_sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as to
what languages it should search for. Multiple languages can be requested using
either ``-l eng+fre`` (English and French) or ``-l eng -l fre``.

macOS users
-----------

You can install additional language packs by :ref:`installing Tesseract using Homebrew with all language packs <macos-all-languages>`.

Docker users
------------

Users of the OCRmyPDF Docker image should install language packs into a derived Docker image as :ref:`described in that section <docker-lang-packs>`.
