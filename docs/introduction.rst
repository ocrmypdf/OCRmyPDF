Introduction
============

OCRmyPDF is a Python 3 package that adds OCR layers to PDFs.


About OCR
---------

`Optical character recognition <https://en.wikipedia.org/wiki/Optical_character_recognition>`_ is technology that converts images of typed or handwritten text, such as in a scanned document, to computer text that can be searched and copied.

OCRmyPDF uses `Tesseract <https://github.com/tesseract-ocr/tesseract>`_, the best available open source OCR engine, to perform OCR.

.. _raster-vector:

About PDFs
----------

PDFs are page description files that attempts to preserve a layout exactly. They can contain `vector graphic files <http://vector-conversions.com/vectorizing/raster_vs_vector.html>`_ that can contain raster objects such as scanned images. Because PDFs can contain multiple pages (unlike many image formats) and can contain fonts and text, it is a good formats for exchanging scanned documents.

.. image:: bitmap_vs_svg.svg

A PDF page might contain multiple images, even if it only appears to have one image.  Some scanners or scanning software will segment pages into monochromatic text and color regions for example, to improve the compression ratio and appearance of the page.

Rasterizing a PDF is the process of generating an image suitable for display or analyzing with an OCR engine.  OCR engines like Tesseract work with images, not vector objects.


About PDF/A
-----------

`PDF/A <https://en.wikipedia.org/wiki/PDF/A>`_ is an ISO-standardized subset of the full PDF specification that is designed for archiving (the 'A' stands for Archive).  PDF/A differs from PDF primarily by omitting features that would make it difficult to read the file in the future, such as embedded Javascript, video, audio and references to external fonts.  All fonts and resources needed to interpret the PDF must be contained within it. Because PDF/A disables Javascript and other types of embedded content, it is probably more secure.

There are various conformance levels and versions, such as "PDF/A-2b".

Generally speaking, the best format for scanned documents is PDF/A. Some governments and jurisdictions, US Courts in particular, `mandate the use of PDF/A <https://pdfblog.com/2012/02/13/what-is-pdfa/>`_ for scanned documents.

Since most people who scan documents are interested in reading them indefinitely into the future, OCRmyPDF generates PDF/A-2b by default.

PDF/A has a few drawbacks.  Some PDF viewers include an alert that the file is a PDF/A, which may confuse some users.  It also tends to produce larger files than PDF, because it embeds certain resources even if they are commonly available. PDF/A files can be digitally signed, but may not be encrypted, to ensure they can be read in the future.  Fortunately, converting from PDF/A to a regular PDF is trivial, and any PDF viewer can view PDF/A.


What OCRmyPDF does
------------------

OCRmyPDF analyzes each page of a PDF to determine the colorspace and resolution (DPI) needed to capture all of the information on that page without losing content.  It uses `Ghostscript <http://ghostscript.com/>`_ to rasterize the page, and then performs on OCR on the rasterized image.  It is not enough to simply extract the images from each page and run OCR on them individually.  Of course one could use Ghostscript or another PDF rasterizer and then pass the image to Tesseract.  OCRmyPDF automates this process and produces a minimally changed output file that contains the same information, colorspace and resolution.

The Tesseract OCR engine can output 'hOCR' files, which are XML files that contain a description of the text it found on the page.  OCRmyPDF will render a new PDF that contains only the hidden text layer, and merge this with the original page.

Alternately, OCRmyPDF can use the Tesseract OCR engine to directly output PDFs for each page, then merge them.

By default, OCRmyPDF will convert the file to a PDF/A.  This behavior can be disabled with the ``--output-type pdf`` argument.

Depending on the settings selected, OCRmyPDF may "graft" the OCR layer into the existing PDF, or reconstruct a visually equivalent new PDF.


Limitations
-----------

OCRmyPDF is limited by the Tesseract OCR engine.  As such it experiences these limitations, as do any other programs that rely on Tesseract:

* The OCR is not as accurate as commercial solutions such as Abbyy.
* It is not capable of recognizing handwriting.
* It may find gibberish and report this as OCR output.
* If a document contains languages outside of those given in the ``-l LANG`` arguments, results may be poor.
* It is not always good at analyzing the natural reading order of documents. For example, it may fail to recognize that a document contains two columns and join text across the columns.
* Poor quality scans may produce poor quality OCR. Garbage in, garbage out.
  
OCRmyPDF is also limited by the PDF specification:

* PDF encodes the position of text glyphs but does not encode document structure.  There is no markup that divides a document in sections, paragraphs, sentences, or even words (since blank spaces are not represented). As such all elements of document structure including the spaces between words must be derived heuristically.  Some PDF viewers do a better job of this than others.

Ghostscript also imposes some limitations:

* PDFs containing JBIG2-encoded content will be converted to CCITT Group4 encoding, which has lower compression ratios, if Ghostscript PDF/A is enabled.
  
OCRmyPDF is currently not designed to be used as a Python API; it is designed to be run as a command line tool. ``import ocrmypf`` currently attempts to process the command line on ``sys.argv`` at import time so it has side effects that will interfere with its use as a package. The API it presents should not be considered stable.