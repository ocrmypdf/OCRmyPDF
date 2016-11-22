PDF Security Issues
===================

	OCRmyPDF should only be used on PDFs you trust. It is not designed to protect you against malware. 

Recognizing that many users have an interest in handling PDFs and applying OCR to PDFs they did not generate themselves, this article discusses the security implications of PDFs and how users can protect themselves.

The disclaimer applies: this software has no warranties of any kind.

PDFs may contain malware
------------------------

PDF is a rich, complex file format. The official PDF 1.7 specification, ISO 32000:2008, is hundreds of packages long and references several annexes each of which are similar in length. PDFs can contain video, audio, JavaScript and other programming, and forms. In some cases, they can open internet connections to pre-selected URLs. All of these possible attack vectors.

In short, PDFs `may contain viruses <https://security.stackexchange.com/questions/64052/can-a-pdf-file-contain-a-virus>`_.

This `article <https://theinvisiblethings.blogspot.ca/2013/02/converting-untrusted-pdfs-into-trusted.html>`_ describes a method which allows potentially hostile PDFs to be viewed and rasterized safely in a disposable virtual machine. A trusted PDF created in this manner is converted to images and loses all information making it searchable. OCRmyPDF could be used restore searchability.

How OCRmyPDF processes PDFs
---------------------------

OCRmyPDF must open and interpret your PDF in order to insert an OCR layer. First, it runs all PDFs through `qpdf <https://github.com/qpdf/qpdf>`_, a program that repairs PDFs with syntax errors. This is done because, in the author's experience, a significant number of PDFs in the wild especially those created by scanners are not well-formed files. qpdf makes it more likely that OCRmyPDF will succeed, but offers no security guarantees. qpdf is also used to split the PDF into single page PDFs.

After qpdf, OCRmyPDF examines each page using `PyPDF2 <https://github.com/mstamy2/PyPDF2>`_. This library also has no warranties or guarantees.

Finally, OCRmyPDF rasterizes each page of the PDF using `Ghostscript <http://ghostscript.com/>`_ in ``-dSAFER`` mode. 

Depending on the options specified, OCRmyPDF may graft the OCR layer into the existing PDF or it may essentially reconstruct ("re-fry") a visually identical PDF that may be quite different at the binary level. That said, OCRmyPDF is not a tool designed for sanitizing PDFs.

Using OCRmyPDF online
---------------------

OCRmyPDF is not designed to be deployed "as a service", in a setting where a user/attacker could upload a file for OCR processing online. It is not designed to be secure in this case.

Abbyy Cloud OCR is a viable commercial alternative with a web services API. The author also provides professional services that include OCR and building databases around PDFs, and is happy to provide consultation.

Password protection, digital signatures and certification
---------------------------------------------------------

OCRmyPDF cannot remove password protection from a PDF. ``qpdf``, one of its dependencies, has this capability. After OCR is applied, password protection is not permitted on PDF/A documents but the file can be converted to regular PDF.

Many programs exist which are capable of inserting an image of someone's signature. On its own, this offers no security guarantees. It is trivial to remove the signature image and apply it to other files. This practice offers no real security.

Important documents can be digitally signed and certified to attest to their authorship. OCRmyPDF cannot do this. Open source tools such as pdfbox (Java) have this capability as does Adobe Acrobat. 