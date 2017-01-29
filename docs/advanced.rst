Advanced features
=================

Control of OCR options
----------------------

OCRmyPDF provides many features to control the behavior of the OCR engine, Tesseract.

When OCR is skipped
"""""""""""""""""""

If a page in a PDF seems to have text, by default OCRmyPDF will exit without modifying the PDF. This is to ensure that PDFs that were previously OCRed or were "born digital" rather than scanned are not processed. 

If ``--skip-text`` is issued, then no OCR will be performed on pages that already have text. The page will be copied to the output. This may be useful for documents that contain both "born digital" and scanned content, or to use OCRmyPDF to normalize and convert to PDF/A regardless of their contents.

If ``--force-ocr`` is issued, then all pages will be rasterized to images, discarding any hidden OCR text, and rasterizing any printable text. This is useful for redoing OCR, for fixing OCR text with a damaged character map (text is selectable but not searchable), and destroying redacted information.


Time and image size limits
""""""""""""""""""""""""""

By default, OCRmyPDF permits tesseract to run for only three minutes (180 seconds) per page. This is usually more than enough time to find all text on a reasonably sized page with modern hardware. 

If a page is skipped, it will be inserted without OCR. If preprocessing was requested, the preprocessed image layer will be inserted.

If you want to adjust the amount of time spent on OCR, change ``--tesseract-timeout``.  You can also automatically skip images that exceed a certain number of megapixels with ``--skip-big``. (A 300 DPI, 8.5×11" page is 8.4 megapixels.)

.. code-block:: bash

	# Allow 300 seconds for OCR; skip any page larger than 50 megapixels
	ocrmypdf --tesseract-timeout 300 --skip-big 50 bigfile.pdf output.pdf

Overriding default tesseract
""""""""""""""""""""""""""""

OCRmyPDF checks the environment variable ``OCRMYPDF_TESSERACT`` for the full path *to the tesseract executable* first. 

For example, if you are testing tesseract 4.00 and don't wish to disturb your tesseract 3.04 installation, you can launch OCRmyPDF as follows:

.. code-block:: bash

	env \
		OCRMYPDF_TESSERACT=/home/user/src/tesseract4/api/tesseract \
		TESSDATA_PREFIX=/home/user/src/tesseract4 \
		ocrmypdf --pdf-renderer tess4 --tesseract-oem 2 input.pdf output.pdf

* ``TESSDATA_PREFIX`` directs tesseract 4.0 to use LSTM training data. This is a tesseract environment variable.
* ``--pdf-renderer tess4`` takes advantage of new tesseract 4.0 PDF renderer in OCRmyPDF. (Tesseract 4.0 only.)
* ``--tesseract-oem 1`` requests tesseract 4.0's new LSTM engine. (Tesseract 4.0 only.)

Overriding other support programs
"""""""""""""""""""""""""""""""""

In addition to tesseract, OCRmyPDF uses the following external binaries:

* ``gs`` (Ghostscript)
* ``unpaper``
* ``qpdf``

In each case OCRmyPDF will check the environment variable ``OCRMYPDF_{program}`` before asking the system to find ``{program}`` on the PATH. For example, you could redirect OCRmyPDF to ``OCRMYPDF_GS`` to override Ghostscript.

Changing tesseract configuration variables
""""""""""""""""""""""""""""""""""""""""""

You can override tesseract's default `control parameters <https://github.com/tesseract-ocr/tesseract/wiki/ControlParams>`_ with a configuration file.

As an example, this configuration will disable Tesseract's dictionary for current language. Normally the dictionary is helpful for interpolating words that are unclear, but it may interfere with OCR if the document does not contain many words (for example, a list of part numbers).

Create a file named "no-dict.cfg" with these contents:

::

	load_system_dawg 0
	language_model_penalty_non_dict_word 0
	language_model_penalty_non_freq_dict_word 0

then run ocrmypdf as follows (along with any other desired arguments):

.. code-block:: bash

	ocrmypdf --tesseract-config no-dict.cfg input.pdf output.pdf

.. warning::

	Some combinations of control parameters will break Tesseract or break assumptions that OCRmyPDF makes about Tesseract's output.


Changing the PDF renderer
-------------------------

rasterizing
  Converting a PDF to an image for display.

rendering
  Creating a new PDF from other data (such as an existing PDF).


OCRmyPDF has three PDF renderers: ``hocr``, ``tesseract`` and ``tess4``. The renderer may be selected using ``--pdf-renderer``. The default is ``auto`` which lets OCRmyPDF select the renderer to use. Currently, ``auto`` always selects ``hocr``. 

The ``hocr`` renderer
"""""""""""""""""""""

The ``hocr`` renderer is the default because it works in most cases. In this mode the whole PDF is rasterized, the raster image is run through OCR to generate a .hocr file, which is an HTML-like file that specifies the location of all identified words.

The .hocr file is then rendered as a PDF and merged with the image layer.

The image layer is copied from the original PDF page if possible, avoiding potentially lossy transcoding or loss of other PDF information. If preprocessing is specified, then the image layer is a new PDF.

This is the only option for tesseract 3.02 and older.


The ``tesseract`` renderer
""""""""""""""""""""""""""

The tesseract renderer uses tesseract's capability to produce a PDF directly. In version 3, tesseract automatically combined the image layer and text, meaning that this mode *always* transcodes and loses potentially loses image quality and other PDF information.

It does a much better job on non-Latin text.

In a future release this will become the "tess3" renderer and ultimately will be dropped.


The ``tess4`` renderer
""""""""""""""""""""""

The tess4 renderer uses tesseract 4.00 alpha's text-only PDF feature added in January 2017. This combines the advantages of the tesseract and hocr renderers, transcoding the image layer only if required by preprocessing options.

Ghostscript PDF/A still sometimes inserts spaces between words when the tess4 renderer is used, affecting search quality.  ``--output-pdf pdf`` may be used to avoid this issue.