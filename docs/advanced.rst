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

OCRmyPDF checks the environment variable ``OCRMYPDF_TESSERACT`` for the full path *to the tesseract binary* first. 

.. envvar:: OCRMYPDF_TESSERACT

	Specify the location of the Tesseract binary.

.. envvar:: TESSDATA_PREFIX

	A Tesseract environment variable that overrides the path to Tesseract's data files.

For example, if you are testing tesseract 4.00 and don't wish to use an existing tesseract 3.04 installation, you can launch OCRmyPDF as follows:

.. code-block:: bash

	env \
		OCRMYPDF_TESSERACT=/home/user/src/tesseract4/api/tesseract \
		TESSDATA_PREFIX=/home/user/src/tesseract4 \
		ocrmypdf --tesseract-oem 2 input.pdf output.pdf

In this example ``TESSDATA_PREFIX`` directs tesseract 4.0 to use LSTM training data. ``--tesseract-oem 1`` requests tesseract 4.0's new LSTM engine. (Tesseract 4.0 only.)


Overriding other support programs
"""""""""""""""""""""""""""""""""

In addition to tesseract, OCRmyPDF uses the following external binaries:

* ``gs`` (Ghostscript)
* ``unpaper``
* ``qpdf``

In each case OCRmyPDF will check the environment variable ``OCRMYPDF_{program}`` before asking the system to find ``{program}`` on the PATH. For example, you could redirect OCRmyPDF to ``OCRMYPDF_GS`` to override Ghostscript. The full list is below:

.. envvar:: OCRMYPDF_GS

	Specify the location of the Ghostscript binary.

.. envvar:: OCRMYPDF_UNPAPER

	Specify the location of the unpaper binary.

.. envvar:: OCRMYPDF_QPDF

	Specify the location of the qpdf binary.


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


OCRmyPDF has three PDF renderers: ``sandwich``, ``hocr``, ``tesseract``. The renderer may be selected using ``--pdf-renderer``. The default is ``auto`` which lets OCRmyPDF select the renderer to use. Currently, ``auto`` selects ``sandwich`` for Tesseract 3.05.01 or newer, or ``hocr`` for older versions of Tesseract.

The ``sandwich`` renderer
"""""""""""""""""""""""""

The ``sandwich`` renderer uses Tesseract's new text-only PDF feature, which produces a PDF page that lays out the OCR in invisible text. This page is then "sandwiched" onto the original PDF page, allowing lossless application of OCR even to PDF pages that contain other vector objects.

When image preprocessing features like ``--deskew`` are used, the original PDF will be rendered as a full page and the OCR layer will be placed on top.

This renderer requires Tesseract 3.05.01 or newer.

The ``hocr`` renderer
"""""""""""""""""""""

The ``hocr`` renderer works with older versions of Tesseract. The image layer is copied from the original PDF page if possible, avoiding potentially lossy transcoding or loss of other PDF information. If preprocessing is specified, then the image layer is a new PDF.

This works in all versions of Tesseract.

The ``tesseract`` renderer
""""""""""""""""""""""""""

The ``tesseract`` renderer creates a PDF with the image and text layers precomposed, meaning that it always transcodes, loses image quality and rasterizes any vector objects. It does a better job on non-Latin text and document structure than ``hocr``.

If a PDF created with this renderer using Tesseract versions older than 3.05.00 is then passed through Ghostscript's pdfwrite feature, the OCR text *may* be corrupted. The ``--output-type=pdfa`` argument will produce a warning in this situation.

*This renderer is deprecated and will be removed whenever support for older versions of Tesseract is dropped.*
