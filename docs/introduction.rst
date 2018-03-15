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

PDFs are page description files that attempts to preserve a layout exactly. They  contain `vector graphics <http://vector-conversions.com/vectorizing/raster_vs_vector.html>`_ that can contain raster objects such as scanned images. Because PDFs can contain multiple pages (unlike many image formats) and can contain fonts and text, it is a good formats for exchanging scanned documents.

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

OCRmyPDF analyzes each page of a PDF to determine the colorspace and resolution (DPI) needed to capture all of the information on that page without losing content.  It uses `Ghostscript <http://ghostscript.com/>`_ to rasterize the page, and then performs on OCR on the rasterized image to create an OCR "layer". The layer is then grafted back onto the original PDF.

While one can use a program like Ghostscript or ImageMagick to get an image and put the image through Tesseract, that actually creates a new PDF and many details may be lost. OCRmyPDF can produce a minimally changed PDF as output.

OCRmyPDF also some image processing options like deskew which improve the appearance of files and quality of OCR. When these are used, the OCR layer is grafted onto the processed image instead.

By default, OCRmyPDF produces archival PDFs – PDF/A, which are a stricter subset of PDF features designed for long term archives. If regular PDFs are desired, this can be disabled with ``--output-type pdf``.


Why you shouldn't do this manually
----------------------------------

A PDF is similar to an HTML file, in that it contains document structure along with images.  Sometimes a PDF does nothing more than present a full page image, but often there is additional content that would be lost.

A manual process could work like either of these:

1. Rasterize each page as an image, OCR the images, and combine the output into a PDF. This preserves the layout of each page, but resamples all images (possibly losing quality, increasing file size, introducing compression artifacts, etc.).

2. Extract each image, OCR, and combine the output into a PDF. This loses the context in which images are used in the PDF, meaning that cropping, rotation and scaling of pages may be lost. Some scanned PDFs use multiple images segmented into black and white, grayscale and color regions, with stencil masks to prevent overlap, as this can enhance the appearance of a file while reducing file size. Clearly, reassembling these images will be easy. This also loses and text or vector art on any pages in a PDF with both scanned and pure digital content.

In the case of a PDF that is nothing other than a container of images (no rotation, scaling, cropping, one image per page), the second approach can be lossless.

OCRmyPDF uses several strategies depending on input options and the input PDF itself, but generally speaking it rasterizes a page for OCR and then grafts the OCR back onto the original. As such it can handle complex PDFs and still preserve their contents as much as possible.


Limitations
-----------

OCRmyPDF is limited by the Tesseract OCR engine.  As such it experiences these limitations, as do any other programs that rely on Tesseract:

* The OCR is not as accurate as commercial solutions such as Abbyy.
* It is not capable of recognizing handwriting.
* It may find gibberish and report this as OCR output.
* If a document contains languages outside of those given in the ``-l LANG`` arguments, results may be poor.
* It is not always good at analyzing the natural reading order of documents. For example, it may fail to recognize that a document contains two columns and join text across the columns.
* Poor quality scans may produce poor quality OCR. Garbage in, garbage out.
* PDFs that use transparent layers are not currently checked in the test suite, so they may not work correctly.
  
OCRmyPDF is also limited by the PDF specification:

* PDF encodes the position of text glyphs but does not encode document structure.  There is no markup that divides a document in sections, paragraphs, sentences, or even words (since blank spaces are not represented). As such all elements of document structure including the spaces between words must be derived heuristically.  Some PDF viewers do a better job of this than others.
* Because some popular open source PDF viewers have a particularly hard time with spaces betweem words, OCRmyPDF appends a space to each text element as a workaround. While this mixes document structure with graphical information that ideally should be left to the PDF viewer to interpret, it improves compatibility with some viewers and does not cause problems for better ones.

Ghostscript also imposes some limitations:

* PDFs containing JBIG2-encoded content will be converted to CCITT Group4 encoding, which has lower compression ratios, if Ghostscript PDF/A is enabled.
* PDFs containing JPEG 2000-encoded content will be converted to JPEG encoding, which may introduce compression artifacts, if Ghostscript PDF/A is enabled.
* Ghostscript may transcode grayscale and color images, either lossy to lossless or lossless to lossy, based on an internal algorithm. This behavior can be suppressed by setting ``--pdfa-image-compression`` to ``jpeg`` or ``lossless`` to set all images to one type or the other. Ghostscript has no option to maintain the input image's format.
  
OCRmyPDF is currently not designed to be used as a Python API; it is designed to be run as a command line tool. ``import ocrmypf`` currently attempts to process the command line on ``sys.argv`` at import time so it has side effects that will interfere with its use as a package. The API it presents should not be considered stable.


Similar programs
----------------

To the author's knowledge, OCRmyPDF is the most feature-rich and thoroughly tested command line OCR PDF conversion tool. If it does not meet your needs, contributions and suggestions are welcome. If not, consider one of these similar open source programs:

* pdf2pdfocr
* pdfsandwich
* pypdfocr
* pdfbeads

If you are looking for a micro web-frontend for OCRmyPDF, consider the third-party `OCRmyPDF-web <https://github.com/sseemayer/OCRmyPDF-web>`_. Bear in mind that OCRmyPDF is not designed to be secure against malware-bearing PDFs (see `Using OCRmyPDF online`_).

