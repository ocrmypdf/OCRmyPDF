.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

===========
Performance
===========

Some users have noticed that current versions of OCRmyPDF do not run as quickly
as some older versions (specifically 6.x and older). This is because OCRmyPDF
added image optimization as a postprocessing step, and it is enabled by default.

Speed
=====

If running OCRmyPDF quickly is your main goal, you can use settings such as:

* ``--optimize 0`` to disable file size optimization
* ``--output-type pdf`` to disable PDF/A generation
* ``--fast-web-view 999999`` to disable fast web view optimization
* ``--skip-big`` to skip large images, if some pages have large images

You can also avoid:

* ``--force-ocr``
* Image preprocessing
