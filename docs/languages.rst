.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _lang-packs:

====================================
Installing additional language packs
====================================

OCRmyPDF uses Tesseract for OCR, and relies on its language packs for all languages.
On most platforms, English is installed with Tesseract by default, but not always.

Tesseract supports `most
languages <https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc#languages>`__.
Languages are identified by standardized three-letter codes (called ISO 639-2 Alpha-3).
Tesseract's documentation also lists the three-letter code for your language.
Some are anglicized, e.g. Spanish is ``spa`` rather than ``esp``, while others
are not, e.g. German is ``deu`` and French is ``fra``.

Language packs (strictly speaking, Tesseract "traineddata" files) generally correspond
to the language in question, but different language packs are used in certain
situations. For German, the "Fraktur" language pack can assist with reading older
materials in the Fraktur typeface family (``deu_frak``). Some communities have changed
their script from Cyrillic to Latin; the Cyrillic version of Uzbek is available
as ``uzb_cyrl`` and the Latin version is ``uzb``.

After you have installed a language pack, you can use it with ``ocrmypdf -l <language>``,
for example ``ocrmypdf -l spa``. For multilingual documents, you can specify
all languages to be expected, e.g. ``ocrmypdf -l eng+fra`` for English and French.
English is assumed by default unless other language(s) are specified.

For Linux users, you can often find packages that provide language
packs.

Platform install steps
======================

Debian and Ubuntu (apt)
-----------------------

.. code-block:: bash

   # Display a list of all Tesseract language packs
   apt-cache search tesseract-ocr

   # Install Chinese Simplified language pack
   apt-get install tesseract-ocr-chi-sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as
to what languages it should search for. Multiple languages can be
requested using either ``-l eng+fra`` (English and French) or
``-l eng -l fra``.

Fedora
------

.. code-block:: bash

   # Display a list of all Tesseract language packs
   dnf search tesseract

   # Install Chinese Simplified language pack
   dnf install tesseract-langpack-chi_sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as
to what languages it should search for. Multiple languages can be
requested using either ``-l eng+fra`` (English and French) or
``-l eng -l fra``.

Archlinux
------

.. code-block:: bash

   # Display a list of all Tesseract language packs
   pacman -Ss tesseract-data

   # Install German language pack
   pacman -S tesseract-data-deu

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as
to what languages it should search for. Multiple languages can be
requested using either ``-l eng+fra`` (English and French) or
``-l eng -l fra``.

Gentoo
------

On Gentoo the package ``app-text/tessdata_fast``, which ``app-text/tesseract`` depends on, handles Tesseract languages.
It accepts USE flags to select what languages should be installed, these can be set in ``/etc/portage/package.use``.
Alternatively one can globally set the `L10N use extension <https://wiki.gentoo.org/wiki/Localization/Guide#L10N>`__ in ``/etc/portage/make.conf``.
This enables these languages for all packages (e.g. including aspell).

.. code-block:: bash

   # Display a list of all Tesseract language packs
   equery uses app-text/tessdata_fast

   # Add English and German language support for Tesseract only
   echo 'app-text/tessdata_fast l10n_de l10n_en' >> /etc/portage/package.use

   # Add global English and German language support (the `l10n_` from equery has to be omitted)
   echo L10N="de en" >> /etc/portage/make.conf

   # update system to reflect changed USE flags
   emerge --update --deep --newuse @world

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as
to what languages it should search for. Multiple languages can be
requested using either ``-l eng+fra`` (English and French) or
``-l eng -l fra``.

macOS
-----

You can install additional language packs by
:ref:`installing Tesseract using Homebrew with all language packs <macos-all-languages>`.

Docker
------

Users of the OCRmyPDF Docker image should install language packs into a
derived Docker image as
:ref:`described in that section <docker-lang-packs>`.

Windows
-------

The Tesseract installer provided by Chocolatey currently includes only English language.
To install other languages, download the respective language pack (``.traineddata`` file)
from https://github.com/tesseract-ocr/tessdata/ and place it in
``C:\\Program Files\\Tesseract-OCR\\tessdata`` (or wherever Tesseract OCR is installed).

Custom language packs
=====================

If you have fine-tuned or trained Tesseract and generated custom trained data, you can
copy your ``customlang.traineddata`` file into your Tesseract "tessdata" folder, and
then use the ``-l customlang`` argument to tell OCRmyPDF to pass that language on to
Tesseract.
