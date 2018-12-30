Advanced features
=================

Control of OCR options
----------------------

OCRmyPDF provides many features to control the behavior of the OCR engine, Tesseract.

When OCR is skipped
"""""""""""""""""""

If a page in a PDF seems to have text, by default OCRmyPDF will exit without modifying the PDF. This is to ensure that PDFs that were previously OCRed or were "born digital" rather than scanned are not processed.

If ``--skip-text`` is issued, then no OCR will be performed on pages that already have text. The page will be copied to the output. This may be useful for documents that contain both "born digital" and scanned content, or to use OCRmyPDF to normalize and convert to PDF/A regardless of their contents.

If ``--redo-ocr`` is issued, then a detailed text analysis is performed. Text is categorized as either visible or invisible. Invisible text (OCR) is stripped out. Then an image of each page is created with visible text masked out. The page image is sent for OCR, and any additional text is inserted as OCR. If a file contains a mix of text and bitmap images that contain text, OCRmyPDF will locate the additional text in images without disrupting the existing text.

If ``--force-ocr`` is issued, then all pages will be rasterized to images, discarding any hidden OCR text, and rasterizing any printable text. This is useful for redoing OCR, for fixing OCR text with a damaged character map (text is selectable but not searchable), and destroying redacted information. Any forms and vector graphics will be rasterized as well.


Time and image size limits
""""""""""""""""""""""""""

By default, OCRmyPDF permits tesseract to run for three minutes (180 seconds) per page. This is usually more than enough time to find all text on a reasonably sized page with modern hardware.

If a page is skipped, it will be inserted without OCR. If preprocessing was requested, the preprocessed image layer will be inserted.

If you want to adjust the amount of time spent on OCR, change ``--tesseract-timeout``.  You can also automatically skip images that exceed a certain number of megapixels with ``--skip-big``. (A 300 DPI, 8.5×11" page is 8.4 megapixels.)

.. code-block:: bash

    # Allow 300 seconds for OCR; skip any page larger than 50 megapixels
    ocrmypdf --tesseract-timeout 300 --skip-big 50 bigfile.pdf output.pdf

Overriding default tesseract
""""""""""""""""""""""""""""

OCRmyPDF checks the system ``PATH`` for the ``tesseract`` binary.

Some relevant environment variables that influence Tesseract's behavior include:

.. envvar:: TESSDATA_PREFIX

    Overrides the path to Tesseract's data files. This can allow simultaneous installation of the "best" and "fast" training data sets. OCRmyPDF does not manage this environment variable.

.. envvar:: OMP_THREAD_LIMIT

    Controls the number of threads Tesseract will use. OCRmyPDF will manage this environment if it is not already set. (Currently, it will set it to 1 because this gives the best results in testing.)

For example, if you have a development build of Tesseract don't wish to use the system installation, you can launch OCRmyPDF as follows:

.. code-block:: bash

    env \
        PATH=/home/user/src/tesseract/api:$PATH \
        TESSDATA_PREFIX=/home/user/src/tesseract \
        ocrmypdf input.pdf output.pdf

In this example ``TESSDATA_PREFIX`` is required to redirect Tesseract to an alternate folder for its "tessdata" files.


Overriding other support programs
"""""""""""""""""""""""""""""""""

In addition to tesseract, OCRmyPDF uses the following external binaries:

* ``gs`` (Ghostscript)
* ``unpaper``
* ``qpdf``

In each case OCRmyPDF will search the ``PATH`` environment variable to locate the binaries.


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


OCRmyPDF has these PDF renderers: ``sandwich`` and ``hocr``. The renderer may be selected using ``--pdf-renderer``. The default is ``auto`` which lets OCRmyPDF select the renderer to use. Currently, ``auto`` always selects ``sandwich``.

The ``sandwich`` renderer
"""""""""""""""""""""""""

The ``sandwich`` renderer uses Tesseract's new text-only PDF feature, which produces a PDF page that lays out the OCR in invisible text. This page is then "sandwiched" onto the original PDF page, allowing lossless application of OCR even to PDF pages that contain other vector objects.

Currently this is the best renderer for most uses, however it is implemented in Tesseract so OCRmyPDF cannot influence it. Currently some problematic PDF viewers like Mozilla PDF.js and macOS Preview have problems with segmenting its text output, and mightrunseveralwordstogether.

When image preprocessing features like ``--deskew`` are used, the original PDF will be rendered as a full page and the OCR layer will be placed on top.

The ``hocr`` renderer
"""""""""""""""""""""

The ``hocr`` renderer works with older versions of Tesseract. The image layer is copied from the original PDF page if possible, avoiding potentially lossy transcoding or loss of other PDF information. If preprocessing is specified, then the image layer is a new PDF.

Unlike ``sandwich`` this renderer is implemented within OCRmyPDF; anyone looking to customize how OCR is presented should look here. A major disadvantage of this renderer is it not capable of correctly handling text outside the Latin alphabet. Pull requests to improve the situation are welcome.

Currently, this renderer has the best compatibility with Mozilla's PDF.js viewer.

This works in all versions of Tesseract.

The ``tesseract`` renderer
""""""""""""""""""""""""""

The ``tesseract`` renderer was removed. OCRmyPDF's new approach to text layer grafting makes it functionally equivalent to ``sandwich``.

Return code policy
------------------

OCRmyPDF writes all messages to ``stderr``.  ``stdout`` is reserved for piping
output files.  ``stdin`` is reserved for piping input files.

The return codes generated by the OCRmyPDF are considered part of the stable
user interface.  They may be imported from ``ocrmypdf.exceptions``.

.. list-table:: Return codes
    :widths: 5 35 60
    :header-rows: 1

    *	- Code
        - Name
        - Interpretation
    *	- 0
        - ``ExitCode.ok``
        - Everything worked as expected.
    *	- 1
        - ``ExitCode.bad_args``
        - Invalid arguments, exited with an error.
    *	- 2
        - ``ExitCode.input_file``
        - The input file does not seem to be a valid PDF.
    *	- 3
        - ``ExitCode.missing_dependency``
        - An external program required by OCRmyPDF is missing.
    *	- 4
        - ``ExitCode.invalid_output_pdf``
        - An output file was created, but it does not seem to be a valid PDF. The file will be available.
    *	- 5
        - ``ExitCode.file_access_error``
        - The user running OCRmyPDF does not have sufficient permissions to read the input file and write the output file.
    *	- 6
        - ``ExitCode.already_done_ocr``
        - The file already appears to contain text so it may not need OCR. See output message.
    *	- 7
        - ``ExitCode.child_process_error``
        - An error occurred in an external program (child process) and OCRmyPDF cannot continue.
    *	- 8
        - ``ExitCode.encrypted_pdf``
        - The input PDF is encrypted. OCRmyPDF does not read encrypted PDFs. Use another program such as ``qpdf`` to remove encryption.
    *	- 9
        - ``ExitCode.invalid_config``
        - A custom configuration file was forwarded to Tesseract using ``--tesseract-config``, and Tesseract rejected this file.
    *   - 10
        - ``ExitCode.pdfa_conversion_failed``
        - A valid PDF was created, PDF/A conversion failed. The file will be available.
    *	- 15
        - ``ExitCode.other_error``
        - Some other error occurred.
    *	- 130
        - ``ExitCode.ctrl_c``
        - The program was interrupted by pressing Ctrl+C.
