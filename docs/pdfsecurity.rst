.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

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
open internet connections to pre-selected URLs. All of these are possible
attack vectors.

In short, PDFs `may contain
viruses <https://security.stackexchange.com/questions/64052/can-a-pdf-file-contain-a-virus>`__.

If you do not trust a PDF or its source, do not open it or use OCRmyPDF
on it. Consider using a Docker container or virtual machine to isolate
an untrusted PDF from your system.

How OCRmyPDF processes PDFs
===========================

OCRmyPDF must open and interpret your PDF in order to insert an OCR
layer. First, it runs all PDFs through
`pikepdf <https://github.com/pikepdf/pikepdf>`__, a library based on
`QPDF <https://github.com/qpdf/qpdf>`__, a program that repairs PDFs
with syntax errors. This is done because, in the author's experience, a
significant number of PDFs in the wild, especially those created by
scanners, are not well-formed files. QPDF makes it more likely that
OCRmyPDF will succeed, but offers no security guarantees. QPDF is also
used to split the PDF into single page PDFs.

Finally, OCRmyPDF rasterizes each page of the PDF using
`Ghostscript <http://ghostscript.com/>`__ in ``-dSAFER`` mode.

Depending on the options specified, OCRmyPDF may graft the OCR layer
into the existing PDF or it may essentially reconstruct ("re-fry") a
visually identical PDF that may be quite different at the binary level.
That said, OCRmyPDF is not a tool designed for sanitizing PDFs.

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
