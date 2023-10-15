.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

=============
API reference
=============

This page summarizes the rest of the public API. Generally speaking this
should be mainly of interest to plugin developers.

ocrmypdf
========

.. autoclass:: ocrmypdf.PageContext
    :members:

.. autoclass:: ocrmypdf.PdfContext
    :members:

.. autoclass:: ocrmypdf.Verbosity
    :members:
    :undoc-members:

.. autofunction:: ocrmypdf.configure_logging

.. autofunction:: ocrmypdf.ocr

.. autofunction:: ocrmypdf.pdf_to_hocr

.. autofunction:: ocrmypdf.hocr_to_ocr_pdf

ocrmypdf.exceptions
===================

.. automodule:: ocrmypdf.exceptions
    :members:
    :undoc-members:

ocrmypdf.helpers
================

.. automodule:: ocrmypdf.helpers
    :members:
    :noindex: deprecated

    .. autodecorator:: deprecated

ocrmypdf.hocrtransform
======================

.. automodule:: ocrmypdf.hocrtransform
    :members:

ocrmypdf.pdfa
=============

.. automodule:: ocrmypdf.pdfa
    :members:

ocrmypdf.quality
================

.. automodule:: ocrmypdf.quality
    :members:

ocrmypdf.subprocess
===================

.. automodule:: ocrmypdf.subprocess
    :members:
