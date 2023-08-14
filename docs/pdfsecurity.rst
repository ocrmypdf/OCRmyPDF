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

Password protected PDFs
=======================

Password protected PDFs usually have two passwords, and owner and user
password. When the user password is set to empty, PDF readers will open
the file automatically and mark it as "(SECURED)". Password security can
also request certain restrictions on the PDF, but anyone can remove these
restrictions if they have either the owner *or* user password. Passwords
mainly present a barrier for casual users.

OCRmyPDF cannot remove passwords from PDFs. If you want to remove a
password from a PDF, you must use other software, such as ``qpdf``.

If the owner and user password are set, a
password is required for ``qpdf``. If only the owner password is set, then the
password can be stripped, even if one does not have the owner password. To
remove the password from a using QPDF, use:

.. code-block:: bash

   qpdf --decrypt --password='abc123' input.pdf no_password.pdf

Then you can run OCRmyPDF on the file.

In its default mode, OCRmyPDF generates PDF/A. Passwords may not be set on PDF/A
documents. If you want to set a password on the output PDF, you must
specify ``--output-type pdf``.

Signature images
================

Many programs exist which are capable of inserting an image of someone's
signature. On its own, this offers no security guarantees. It is trivial
to remove the signature image and apply it to other files. This practice
offers no real security.

Digital signatures
==================

Important documents can be digitally signed and certified to attest to
their authorship, approval or execution of a legal agreement. OCRmyPDF
will detect signed PDFs and will not modify them, unless the
``--invalidate-digital-signatures`` option is used, which will
invalidate any signatures. (The signature may still be present in the PDF
if opened, but PDF readers will not validate it.)

A digital signature adds a cryptographic hash of the document to the
document, so tamper protection is provided. That also precludes OCRmyPDF
from modifying the document and preserving the signature.

Digital signatures are not the same as a signature image. A digital
signature is a cryptographic hash of the document that is encrypted with
the author's private key. The signature is decrypted with the author's
public key. The public key is usually distributed by a certificate
authority. The signature is then verified by the PDF reader. If the
document is modified, the signature will be invalidated.

Certificate-encrypted PDFs
==========================

PDFs can be encrypted with a certificate. This is a more secure form of
encryption than a password. The certificate is usually issued by a
certificate authority. A certificate is used to encrypt the document using
the public key for the benefit of a specific recipient who possesses
the private key.

OCRmyPDF cannot open certificate-encrypted PDFs. If you have the
certificate, you can use other PDF software, such as Acrobat, to
decrypt the PDF.