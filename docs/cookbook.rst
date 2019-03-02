Cookbook
========

Basic examples
--------------

Help!
^^^^^

ocrmypdf has built-in help.

.. code-block:: bash

    ocrmypdf --help


Add an OCR layer and convert to PDF/A
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    ocrmypdf input.pdf output.pdf

Add an OCR layer and output a standard PDF
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    ocrmypdf --output-type pdf input.pdf output.pdf

Create a PDF/A with all color and grayscale images converted to JPEG
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    ocrmypdf --output-type pdfa --pdfa-image-compression jpeg input.pdf output.pdf

Modify a file in place
^^^^^^^^^^^^^^^^^^^^^^

The file will only be overwritten if OCRmyPDF is successful.

.. code-block:: bash

    ocrmypdf myfile.pdf myfile.pdf

Correct page rotation
^^^^^^^^^^^^^^^^^^^^^

OCR will attempt to automatic correct the rotation of each page. This can help fix a scanning job that contains a mix of landscape and portrait pages.

.. code-block:: bash

    ocrmypdf --rotate-pages myfile.pdf myfile.pdf

You can increase (decrease) the parameter ``--rotate-pages-threshold`` to make page rotation more (less) aggressive.

If the page is "just a little off horizontal", like a crooked picture, then you want ``--deskew``. ``--rotate-pages`` is for when the cardinal angle is wrong.

OCR languages other than English
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

OCRmyPDF assumes the document is in English unless told otherwise. OCR quality may be poor if the wrong language is used.

.. code-block:: bash

    ocrmypdf -l fra LeParisien.pdf LeParisien.pdf
    ocrmypdf -l eng+fra Bilingual-English-French.pdf Bilingual-English-French.pdf

Language packs must be installed for all languages specified. See :ref:`Installing additional language packs <lang-packs>`.

Unfortunately, the Tesseract OCR engine has no ability to detect the language when it is unknown.

Produce PDF and text file containing OCR text
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This produces a file named "output.pdf" and a companion text file named "output.txt".

.. code-block:: bash

    ocrmypdf --sidecar output.txt input.pdf output.pdf

OCR images, not PDFs
^^^^^^^^^^^^^^^^^^^^

Option: use Tesseract
"""""""""""""""""""""

If you are starting with images, you can just use Tesseract directly to convert images to PDFs:

.. code-block:: bash

    tesseract my-image.jpg output-prefix pdf

.. code-block:: bash

    # When there are multiple images
    tesseract text-file-containing-list-of-image-filenames.txt output-prefix pdf

Tesseract's PDF output is quite good – OCRmyPDF uses it internally, in some cases. However, OCRmyPDF has many features not available in Tesseract like image processing, metadata control, and PDF/A generation.

Option: use img2pdf
"""""""""""""""""""

You can also use a program like `img2pdf <https://gitlab.mister-muffin.de/josch/img2pdf>`_ to convert your images to PDFs, and then pipe the results to run ocrmypdf.  The ``-`` tells ocrmypdf to read standard input.

.. code-block:: bash

    img2pdf my-images*.jpg | ocrmypdf - myfile.pdf

``img2pdf`` is recommended because it does an excellent job at generating PDFs without transcoding images.

Option: use OCRmyPDF (single images only)
"""""""""""""""""""""""""""""""""""""""""

For convenience, OCRmyPDF can also convert single images to PDFs on its own. If the resolution (dots per inch, DPI) of an image is not set or is incorrect, it can be overridden with ``--image-dpi``. (As 1 inch is 2.54 cm, 1 dpi = 0.39 dpcm).

.. code-block:: bash

    ocrmypdf --image-dpi 300 image.png myfile.pdf

If you have multiple images, you must use ``img2pdf`` to convert the images to PDF.

Not recommended
"""""""""""""""

We caution against using ImageMagick or Ghostscript to convert images to PDF, since they may transcode images or produce downsampled images, sometimes without warning.

Image processing
----------------

OCRmyPDF perform some image processing on each page of a PDF, if desired.  The same processing is applied to each page.  It is suggested that the user review files after image processing as these commands might remove desirable content, especially from poor quality scans.

* ``--rotate-pages`` attempts to determine the correct orientation for each page and rotates the page if necessary.

* ``--remove-background`` attempts to detect and remove a noisy background from grayscale or color images.  Monochrome images are ignored. This should not be used on documents that contain color photos as it may remove them.

* ``--deskew`` will correct pages were scanned at a skewed angle by rotating them back into place.  Skew determination and correction is performed using `Postl's variance of line sums <http://www.leptonica.com/skew-measurement.html>`_ algorithm as implemented in `Leptonica <http://www.leptonica.com/index.html>`_.

* ``--clean`` uses `unpaper <https://www.flameeyes.eu/projects/unpaper>`_ to clean up pages before OCR, but does not alter the final output.  This makes it less likely that OCR will try to find text in background noise.

* ``--clean-final`` uses unpaper to clean up pages before OCR and inserts the page into the final output.  You will want to review each page to ensure that unpaper did not remove something important.

* ``--mask-barcodes`` will suppress any barcodes detected in a page image. Barcodes are known to confuse Tesseract OCR and interfere with the recognition of text on the same baseline as a barcode. The output file will contain the unaltered image of the barcode.

.. note::

    In many cases image processing will rasterize PDF pages as images, potentially losing quality.

.. warning::

    ``--clean-final`` and ``-remove-background`` may leave undesirable visual artifacts in some images where their algorithms have shortcomings. Files should be visually reviewed after using these options.

Example: OCR and correct document skew (crooked scan)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Deskew:

.. code-block:: bash

    ocrmypdf --deskew input.pdf output.pdf

Image processing commands can be combined. The order in which options are given does not matter. OCRmyPDF always applies the steps of the image processing pipeline in the same order (rotate, remove background, deskew, clean).

.. code-block:: bash

    ocrmypdf --deskew --clean --rotate-pages input.pdf output.pdf


Don't actually OCR my PDF
-------------------------

If you set ``--tesseract-timeout 0`` OCRmyPDF will apply its image processing without performing OCR, if all you want to is to apply image processing or PDF/A conversion.

.. code-block:: bash

    ocrmypdf --tesseract-timeout=0 --remove-background input.pdf output.pdf


Redo existing OCR
-----------------

To redo OCR on a file OCRed with other OCR software or a previous version of OCRmyPDF and/or Tesseract, you may use the ``--redo-ocr`` argument. (Normally, OCRmyPDF will exit with an error if asked to modify a file with OCR.)

This may be helpful for users who want to take advantage of accuracy improvements in Tesseract 4.0 for files they previously OCRed with an earlier version of Tesseract and OCRmyPDF.

.. code-block:: bash

    ocrmypdf --redo-ocr input.pdf output.pdf

This method will replace OCR without rasterizing, reducing quality or removing vector content. If a file contains a mix of pure digital text and OCR, digital text will be ignored and OCR will be replaced. As such this mode is incompatible with image processing options, since they alter the appearance of the file.

In some cases, existing OCR cannot be detected or replaced. Files produced by OCRmyPDF v2.2 or earlier, for example, are internally represented as having visible text with an opaque image drawn on top. This situation cannot be detected.

If ``--redo-ocr`` does not work, you can use ``--force-ocr``, which will force rasterization of all pages, potentially reducing quality or losing vector content.

Improving OCR quality
---------------------

The `Image processing`_ features can improve OCR quality.

Rotating pages and deskewing helps to ensure that the page orientation is correct before OCR begins. Removing the background and/or cleaning the page can also improve results. The ``--oversample DPI`` argument can be specified to resample images to higher resolution before attempting OCR; this can improve results as well.

OCR quality will suffer if the resolution of input images is not correct (since the range of pixel sizes that will be checked for possible fonts will also be incorrect).

PDF optimization
----------------

By default OCRmyPDF will attempt to perform lossless optimizations on the images inside PDFs after OCR is complete. Optimization is performed even if no OCR text is found.

The ``--optimize N`` (short form ``-O``) argument controls optimization, where ``N`` ranges from 0 to 3 inclusive, analogous to the optimization levels in the GCC compiler.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Level
        - Comments
    *   - ``--optimize 0``
        - Disables optimization.
    *   - ``--optimize 1``
        - Enables lossless optimizations, such as transcoding images to more
          efficient formats. Also compress other uncompressed objects in the
          PDF and enables the more efficient "object streams" within the PDF.
    *   - ``--optimize 2``
        - All of the above, and enables lossy optimizations and color quantization.
    *   - ``--optimize 3``
        - All of the above, and enables more aggressive optimizations and targets lower image quality.

Optimization is improved when a JBIG2 encoder is available and when ``pngquant`` is installed. If either of these components are missing, then some types of images cannot be optimized.

The types of optimization available may expand over time. By default, OCRmyPDF compresses data streams inside PDFs, and will change inefficient compression modes to more modern versions. A program like ``qpdf`` can be used to change encodings, e.g. to inspect the internals fo a PDF.

.. code-block:: bash

    ocrmypdf --optimize 3 in.pdf out.pdf  # Make it small

Some users may consider enabling lossy JBIG2. See: :ref:`jbig2-lossy`.
