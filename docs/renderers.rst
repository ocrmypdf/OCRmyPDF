PDF Renderers
=============

rasterizing
  Converting a PDF to an image for display.

rendering
  Creating a new PDF from other data (such as an existing PDF).


OCRmyPDF has three PDF renderers: ``hocr``, ``tesseract`` and ``tess4``. The renderer may be selected using ``--pdf-renderer``. The default is ``auto`` which lets OCRmyPDF select the renderer to use. Currently it always uses ``hocr``. 

The hocr renderer
-----------------

The ``hocr`` renderer is the default because it works in most cases. In this mode the whole PDF is rasterized, the raster image is run through OCR to generate a .hocr file, which is an HTML-like file that specifies the location of all identified words.

The .hocr file is then rendered as a PDF and merged with the image layer.

The image layer is copied from the original PDF page if possible, avoiding potentially lossy transcoding or loss of other PDF information. If preprocessing is specified, then the image layer is a new PDF.

This is the only option for tesseract 3.02 and older.


The tesseract renderer
----------------------

The tesseract renderer uses tesseract's capability to produce a PDF directly. In version 3, tesseract automatically combined the image layer and text, meaning that this mode always transcodes and loses potentially loses quality and other PDF information.

It does a much better job on non-Latin text.

In a future release this will become the "tess3" renderer and ultimately will be dropped.


The tess4 renderer
------------------

The tess4 renderer uses tesseract 4.00 alpha's text-only PDF feature added in January 2017. This combines the advantages of the tesseract and hocr renderers, transcoding the image layer only if required by preprocessing options.

Ghostscript PDF/A still sometimes inserts spaces between words when the tess4 renderer is used, affecting search quality.  ``--output-pdf pdf`` may be used to avoid this issue.