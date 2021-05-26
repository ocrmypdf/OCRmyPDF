===================
PDF security issues
===================

   OCRmyPDF should only be used on PDFs you trust. It is not designed to
   protect you against malware.

Recognizing that many users have an interest in handling PDFs and
applying OCR to PDFs they did not generate themselves, this article
discusses the security implications of PDFs and how users can protect
themselves.

The disclaimer applies: this software has no warranties of any kind.

PDFs may contain malware
========================

PDF is a rich, complex file format. The official PDF 1.7 specification,
ISO 32000:2008, is hundreds of pages long and references several annexes
each of which are similar in length. PDFs can contain video, audio, XML,
JavaScript and other programming, and forms. In some cases, they can
open internet connections to pre-selected URLs. All of these possible
attack vectors.

In short, PDFs `may contain
viruses <https://security.stackexchange.com/questions/64052/can-a-pdf-file-contain-a-virus>`__.

This
`article <https://theinvisiblethings.blogspot.ca/2013/02/converting-untrusted-pdfs-into-trusted.html>`__
describes a high-paranoia method which allows potentially hostile PDFs
to be viewed and rasterized safely in a disposable virtual machine. A
trusted PDF created in this manner is converted to images and loses all
information making it searchable and losing all compression. OCRmyPDF
could be used restore searchability.

How OCRmyPDF processes PDFs
===========================

OCRmyPDF must open and interpret your PDF in order to insert an OCR
layer. First, it runs all PDFs through
`pikepdf <https://github.com/pikepdf/pikepdf>`__, a library based on
`qpdf <https://github.com/qpdf/qpdf>`__, a program that repairs PDFs
with syntax errors. This is done because, in the author's experience, a
significant number of PDFs in the wild especially those created by
scanners are not well-formed files. qpdf makes it more likely that
OCRmyPDF will succeed, but offers no security guarantees. qpdf is also
used to split the PDF into single page PDFs.

Finally, OCRmyPDF rasterizes each page of the PDF using
`Ghostscript <http://ghostscript.com/>`__ in ``-dSAFER`` mode.

Depending on the options specified, OCRmyPDF may graft the OCR layer
into the existing PDF or it may essentially reconstruct ("re-fry") a
visually identical PDF that may be quite different at the binary level.
That said, OCRmyPDF is not a tool designed for sanitizing PDFs.

.. _ocr-service:

Using OCRmyPDF online or as a service
=====================================

OCRmyPDF is not designed for use as a public web service where a
malicious user could upload a chosen PDF. In particular, it is not
necessarily secure against PDF malware or PDFs that cause denial of
service. OCRmyPDF relies on Ghostscript, and therefore, if deployed
online one should be prepared to comply with Ghostscript's Affero GPL
license, and any other licenses.

Setting aside these concerns, a side effect of OCRmyPDF is it may
incidentally sanitize PDFs that contain certain types of malware. It
repairs the PDF with pikepdf/libqpdf, which could correct malformed PDF
structures that are part of an attack. When PDF/A output is selected
(the default), the input PDF is partially reconstructed by Ghostscript.
When ``--force-ocr`` is used, all pages are rasterized and reconverted
to PDF, which could remove malware in embedded images.

OCRmyPDF should be relatively safe to use in a trusted intranet, with
some considerations:

Limiting CPU usage
------------------

OCRmyPDF will attempt to use all available CPUs and storage, so
executing ``nice ocrmypdf`` or limiting the number of jobs with the
``-j`` argument may ensure the server remains available. Another option
would be run OCRmyPDF jobs inside a Docker container, a virtual machine,
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

To check temporary storage usage on actual files, run
``ocrmypdf -k ...`` which will preserve and print the path to temporary
storage when the job is done.

To change where temporary files are stored, change the ``TMPDIR``
environment variable for ocrmypdf's environment. (Python's
``tempfile.gettempdir()`` returns the root directory in which temporary
files will be stored.) For example, one could redirect ``TMPDIR`` to a
large RAM disk to avoid wear on HDD/SSD and potentially improve
performance. On Amazon Web Services, ``TMPDIR`` can be set to `empheral
storage <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html>`__.

Timeouts
--------

To prevent excessively long OCR jobs consider setting
``--tesseract-timeout`` and/or ``--skip-big`` arguments. ``--skip-big``
is particularly helpful if your PDFs include documents such as reports
on standard page sizes with large images attached - often large images
are not worth OCR'ing anyway.

Commercial alternatives
-----------------------

The author also provides professional services that include OCR and
building databases around PDFs, and is happy to provide consultation.

Abbyy Cloud OCR is a viable commercial alternative with a web services
API.

Password protection, digital signatures and certification
=========================================================

Password protected PDFs usually have two passwords, and owner and user
password. When the user password is set to empty, PDF readers will open
the file automatically and marked it as "(SECURED)". While not as
reliable as a digital signature, this indicates that whoever set the
password approved of the file at that time. When the user password is
set, the document cannot be viewed without the password.

Either way, OCRmyPDF does not remove passwords from PDFs and exits with
an error on encountering them.

``qpdf`` can remove passwords. If the owner and user password are set, a
password is required for ``qpdf``. If only the owner password is set, then the
password can be stripped, even if one does not have the owner password.

After OCR is applied, password protection is not permitted on PDF/A
documents but the file can be converted to regular PDF.

Many programs exist which are capable of inserting an image of someone's
signature. On its own, this offers no security guarantees. It is trivial
to remove the signature image and apply it to other files. This practice
offers no real security.

Important documents can be digitally signed and certified to attest to
their authorship. OCRmyPDF cannot do this. Open source tools such as
pdfbox (Java) have this capability as does Adobe Acrobat.
