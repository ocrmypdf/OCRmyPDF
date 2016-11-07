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


OCR languages other than English
""""""""""""""""""""""""""""""""

By default OCRmyPDF assumes the document is English. 

.. code-block:: bash

	ocrmypdf -l fre LeParisien.pdf LeParisien.pdf
	ocrmypdf -l eng+fre Bilingual-English-French.pdf Bilingual-English-French.pdf

Language packs must be installed for all languages specified. See :ref:`Installing additional language packs <lang-packs>`.


OCR images, not PDFs
--------------------

Use a program like `img2pdf <https://gitlab.mister-muffin.de/josch/img2pdf>`_ to convert your images to PDFs, and then pipe the results to run ocrmypdf:

.. code-block:: bash

	img2pdf my-images*.jpg | ocrmypdf - myfile.pdf

If given a single image as input, OCRmyPDF will try converting it to a PDF on its own.  This feature may be removed at some point, because OCRmyPDF does not specialize in converting images to PDFs.

You can also use Tesseract 3.04+ directly to convert single page images or multi-page TIFFs to PDF:

.. code-block:: bash

	tesseract my-image.jpg output-prefix pdf 

Image processing
----------------

OCRmyPDF perform some image processing on each page of a PDF, if desired.  The same processing is applied to each page.  It is suggested that the user review files after image processing as these commands might remove desirable content, especially from poor quality scans.

* ``--rotate-pages`` attempts to determine the correct orientation for each page and rotates the page if necessary.

* ``--remove-background`` attempts to detect and remove a noisy background from grayscale or color images.  Monochrome images are ignored. This should not be used on documents that contain color photos as it may remove them.

* ``--deskew`` will correct pages were scanned at a skewed angle by rotating them back into place.  Skew determination and correction is performed using `Postl's variance of line sums <http://www.leptonica.com/skew-measurement.html>`_ algorithm as implemented in `Leptonica <http://www.leptonica.com/index.html>`_.
  
* ``--clean`` uses `unpaper <https://www.flameeyes.eu/projects/unpaper>`_ to clean up pages before OCR, but does not alter the final output.  This makes it less likely that OCR will try to find text in background noise.

* ``--clean-final`` uses unpaper to clean up pages before OCR and inserts the page into the final output.  You will want to review each page to ensure that unpaper did not remove something important.


OCR and correct document skew (crooked scan)
""""""""""""""""""""""""""""""""""""""""""""

.. code-block:: bash

	ocrmypdf --deskew input.pdf output.pdf


Hot (watched) folders
---------------------

To set up a "hot folder" that will trigger an OCR operation for every file inserted, use a program like Python `watchdog <https://pypi.python.org/pypi/watchdog>`_ (supports all major OS).

.. code-block:: bash

	pip install watchdog

watchdog installs the command line program ``watchmedo``, which can be told to run ``ocrmypdf`` on any .pdf added to the current directory (``.``) and place the result in the previously created ``out/`` folder.

.. code-block:: bash

	cd hot-folder
	mkdir out
	watchmedo shell-command \
		--patterns="*.pdf" \
		--ignore-directories \
		--command='ocrmypdf "${watch_src_path}" "out/${watch_src_path}" ' \
		.  # don't forget the final dot

For more complex behavior you can write a Python script around to use the watchdog API.

On file servers, you could configure watchmedo as a system service so it will run all the time.

Caveats
"""""""

* ``watchmedo`` may not work properly on a networked file system, depending on the capabilities of the file system client and server.
* This simple recipe does not filter for the type of file system event, so file copies, deletes and moves, and directory operations, will all be sent to ocrmypdf, producing errors in several cases. Disable your watched folder if you are doing anything other than copying files to it.
* If the source and destination directory are the same, watchmedo may create an infinite loop.


Batch jobs
----------

Consider using the excellent `GNU Parallel <https://www.gnu.org/software/parallel/>`_ to apply OCRmyPDF to multiple files at once.

Both ``parallel`` and ``ocrmypdf`` will try to use all available processors. To maximize parallelism without overloading your system with processes, consider using ``parallel -j 2`` to limit parallel to running two jobs at once.

This command will run all ocrmypdf all files named ``*.pdf`` in the current directory and write them to the previous created ``output/`` folder.

.. code-block:: bash

	parallel -j 2 ocrmypdf '{}' 'output/{}' ::: *.pdf

If you have thousands of files to work with, contact the author.
 
