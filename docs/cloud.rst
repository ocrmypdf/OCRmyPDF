.. SPDX-FileCopyrightText: 2023 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0


.. _ocr-service:

==================
Online deployments
==================

OCRmyPDF is designed to be used as a command line tool, but it can be
used in a web service. This document describes some considerations for
doing so.

A basic web service implementation is provided in the source code
repository, as ``misc/webservice.py``. It is only demonstration quality
and is not intended for production use.

OCRmyPDF is not designed for use as a public web service where a
malicious user could upload a chosen PDF. In particular, it is not
necessarily secure against PDF malware or PDFs that cause denial of
service. For further discussino of security, see :ref:`security`.

OCRmyPDF relies on Ghostscript, and therefore, if deployed
online one should be prepared to comply with Ghostscript's Affero GPL
license, and any other licenses.

Setting aside these concerns, a side effect of OCRmyPDF is that it may
incidentally sanitize PDFs containing certain types of malware. It
repairs the PDF with pikepdf/libqpdf, which could correct malformed PDF
structures that are part of an attack. When PDF/A output is selected
(the default), the input PDF is partially reconstructed by Ghostscript.
When ``--force-ocr`` is used, all pages are rasterized and reconverted
to PDF, which could remove malware in embedded images.

Limiting CPU usage
------------------

OCRmyPDF will attempt to use all available CPUs and storage, so
executing ``nice ocrmypdf`` or limiting the number of jobs with the
``--jobs`` argument may ensure the server remains responsive. Another option
would be to run OCRmyPDF jobs inside a Docker container, a virtual machine,
or a cloud instance, which can impose its own limits on CPU usage and be
terminated "from orbit" if it fails to complete.

Temporary storage requirements
------------------------------

OCRmyPDF will use a large amount of temporary storage for its work,
proportional to the total number of pixels needed to rasterize the PDF.
The raster image of a 8.5×11" color page at 300 DPI takes 25 MB
uncompressed; OCRmyPDF saves its intermediates as PNG, but that still
means it requires about 9 MB per intermediate based on average
compression ratios. Multiple intermediates per page are also required,
depending on the command line given. A rule of thumb would be to allow
100 MB of temporary storage per page in a file – meaning that a small
cloud servers or small VM partitions should be provisioned with plenty
of extra space, if say, a 500 page file might be sent.

To change the temporary directory, see :ref:`tmpdir`.

On Amazon Web Services or other cloud vendors, consider setting your
temporary directory to `empheral
storage <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html>`__.

Timeouts
--------

To prevent excessively long OCR jobs consider setting
``--tesseract-timeout`` and/or ``--skip-big`` arguments. ``--skip-big``
is particularly helpful if your PDFs include documents such as reports
on standard page sizes with large images attached - often large images
are not worth OCR'ing anyway.

Document management systems
---------------------------

If you are looking for a full document management system, consider
`paperless-ngx <https://github.com/paperless-ngx/paperless-ngx>`__,
which is a web application that uses OCRmyPDF to automatically OCR and
archive documents.

Commercial OCR alternatives
---------------------------

The author also provides professional services that include OCR and
building databases around PDFs, and is happy to provide consultation.

Abbyy Cloud OCR is viable commercial alternative with a web services
API. Amazon Textract, Google Cloud Vision, and Microsoft Azure
Computer Vision provide advanced OCR but have less PDF rendering capability.