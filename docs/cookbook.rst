Cookbook
========

Basic examples
--------------

Help!
"""""

ocrmypdf has built-in help.

.. code-block:: bash

    ocrmypdf --help


Add an OCR layer and convert to PDF/A
"""""""""""""""""""""""""""""""""""""

.. code-block:: bash

    ocrmypdf input.pdf output.pdf

Add an OCR layer and output a standard PDF
""""""""""""""""""""""""""""""""""""""""""

.. code-block:: bash

    ocrmypdf --output-type pdf input.pdf output.pdf

Create a PDF/A with all color and grayscale images converted to JPEG
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

.. code-block:: bash

    ocrmypdf --output-type pdfa --pdfa-image-compression jpeg input.pdf output.pdf

Modify a file in place
""""""""""""""""""""""

The file will only be overwritten if OCRmyPDF is successful.

.. code-block:: bash

    ocrmypdf myfile.pdf myfile.pdf

Correct page rotation
"""""""""""""""""""""

OCR will attempt to automatic correct the rotation of each page. This can help fix a scanning job that contains a mix of landscape and portrait pages.

.. code-block:: bash

    ocrmypdf --rotate-pages myfile.pdf myfile.pdf

You can increase (decrease) the parameter ``--rotate-pages-threshold`` to make page rotation more (less) aggressive.

If the page is "just a little off horizontal", like a crooked picture, then you want ``--deskew``. ``--rotate-pages`` is for when the cardinal angle is wrong.


OCR languages other than English
""""""""""""""""""""""""""""""""

By default OCRmyPDF assumes the document is English.

.. code-block:: bash

    ocrmypdf -l fra LeParisien.pdf LeParisien.pdf
    ocrmypdf -l eng+fra Bilingual-English-French.pdf Bilingual-English-French.pdf

Language packs must be installed for all languages specified. See :ref:`Installing additional language packs <lang-packs>`.


Produce PDF and text file containing OCR text
"""""""""""""""""""""""""""""""""""""""""""""

This produces a file named "output.pdf" and a companion text file named "output.txt".

.. code-block:: bash

    ocrmypdf --sidecar output.txt input.pdf output.pdf

OCR images, not PDFs
--------------------

If you are starting with images, you can just use Tesseract 3.04 or later directly to convert images to PDFs:

.. code-block:: bash

    tesseract my-image.jpg output-prefix pdf

.. code-block:: bash

    # When there are multiple images
    tesseract text-file-containing-list-of-image-filenames.txt output-prefix pdf

Tesseract's PDF output is quite good – OCRmyPDF uses it internally by default. However, OCRmyPDF has many features not available in Tesseract like like image processing, metadata control, and PDF/A generation.

Use a program like `img2pdf <https://gitlab.mister-muffin.de/josch/img2pdf>`_ to convert your images to PDFs, and then pipe the results to run ocrmypdf.  The `-` tells ocrmypdf to read standard input.

.. code-block:: bash

    img2pdf my-images*.jpg | ocrmypdf - myfile.pdf

``img2pdf`` is recommended because it does an excellent job at generating PDFs without transcoding images.

For convenience, OCRmyPDF can also convert single images to PDFs on its own. If the resolution (dots per inch, DPI) of an image is not set or is incorrect, it can be overridden with ``--image-dpi``. (As 1 inch is 2.54 cm, 1 dpi = 0.39 dpcm).

.. code-block:: bash

    ocrmypdf --image-dpi 300 image.png myfile.pdf

If you have multiple images, you must use ``img2pdf`` to convert the images to PDF.

.. note::

    ImageMagick ``convert`` can also convert a group of images to PDF, but in the author's experience it takes a long time, transcodes unnecessarily and gives poor results.


Image processing
----------------

OCRmyPDF perform some image processing on each page of a PDF, if desired.  The same processing is applied to each page.  It is suggested that the user review files after image processing as these commands might remove desirable content, especially from poor quality scans.

* ``--rotate-pages`` attempts to determine the correct orientation for each page and rotates the page if necessary.

* ``--remove-background`` attempts to detect and remove a noisy background from grayscale or color images.  Monochrome images are ignored. This should not be used on documents that contain color photos as it may remove them.

* ``--deskew`` will correct pages were scanned at a skewed angle by rotating them back into place.  Skew determination and correction is performed using `Postl's variance of line sums <http://www.leptonica.com/skew-measurement.html>`_ algorithm as implemented in `Leptonica <http://www.leptonica.com/index.html>`_.

* ``--clean`` uses `unpaper <https://www.flameeyes.eu/projects/unpaper>`_ to clean up pages before OCR, but does not alter the final output.  This makes it less likely that OCR will try to find text in background noise.

* ``--clean-final`` uses unpaper to clean up pages before OCR and inserts the page into the final output.  You will want to review each page to ensure that unpaper did not remove something important.

.. note::

    In many cases image processing will rasterize PDF pages as images, potentially losing quality.

.. warning::

    ``--clean-final`` and ``-remove-background`` may leave undesirable visual artifacts in some images where their algorithms have shortcomings. Files should be visually reviewed after using these options.


OCR and correct document skew (crooked scan)
""""""""""""""""""""""""""""""""""""""""""""

Deskew:

.. code-block:: bash

    ocrmypdf --deskew input.pdf output.pdf

Image processing commands can be combined. The order in which options are given does not matter. OCRmyPDF always applies the steps of the image processing pipeline in the same order (rotate, remove background, deskew, clean).

.. code-block:: bash

    ocrmypdf --deskew --clean --rotate-pages input.pdf output.pdf


Don't actually OCR my PDF
"""""""""""""""""""""""""

If you set ``--tesseract-timeout 0`` OCRmyPDF will apply its image processing without performing OCR, if all you want to is to apply image processing or PDF/A conversion.

.. code-block:: bash

    ocrmypdf --tesseract-timeout=0 --remove-background input.pdf output.pdf


Redo OCR
""""""""

To redo OCR on a file OCRed with other OCR software or a previous version of OCRmyPDF and/or Tesseract, you may use the ``--force-ocr`` argument. Normally, OCRmyPDF does not modify files that already appear to contain OCR text.

.. code-block:: bash

    ocrmypdf --force-ocr input.pdf output.pdf

Note that the method above will force rasterization of all pages, potentially reducing quality or losing vector content.

To ensure quality is preserved, one could extract all of the images and rebuild the PDF for a lossless transformation. This recipe does not work when PDFs contain multiple images per page, as many do in practice. It will also lose any page rotation information.

.. code-block:: bash

    pdfimages -all old-ocr.pdf prefix  # extract all images
    img2pdf -o temp.pdf prefix*        # construct new PDF from the images
    # review the new PDF to ensure it visually matches the old one
    ocrmypdf --output-type pdf temp.pdf new-ocr.pdf

``--output-type pdf`` is used here to avoid using Ghostscript which will also rasterize images.


Improving OCR quality
---------------------

The `Image processing`_ features can improve OCR quality.

Rotating pages and deskewing helps to ensure that the page orientation is correct before OCR begins. Removing the background and/or cleaning the page can also improve results. The ``--oversample DPI`` argument can be specified to resample images to higher resolution before attempting OCR; this can improve results as well.

OCR quality will suffer if the resolution of input images is not correct (since the range of pixel sizes that will be checked for possible fonts will also be incorrect).


PDF optimization
----------------

By default OCRmyPDF will attempt to perform lossless optimizations on the images inside PDFs after OCR is complete. Optimization is performed even if no OCR text is found.

The ``--optimize N`` (short form ``-O``) argument controls optimization, where ``N`` ranges from 0 to 3. ``--optimize 0`` disables optimizations. ``1`` enables lossless optimizations that can be performed safely with no quality loss. ``2`` enables lossy optimizations such as image color quantizations. ``3`` enables more aggressive optimizations and targets a lower JPEG quality.

Optimization is improved when a JBIG2 encoder is available and when ``pngquant`` is installed. If either of these components are missing, then some types of images will not be optimized.

Currently optimization attempts to find more efficient encodings for images. The types of optimization available may expand over time. By default, OCRmyPDF compresses data streams inside PDFs, and will change inefficient encodings to more modern versions. A program like ``qpdf`` can be used to change encodings, e.g. to inspect the internals fo a PDF.

.. code-block:: bash

    ocrmypdf --optimize 3 in.pdf out.pdf  # Make it small

Some users may consider enabling lossy JBIG2. See: :ref:`jbig2-lossy`.
