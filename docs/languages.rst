.. _lang-packs:

Installing additional language packs
====================================

OCRmyPDF uses Tesseract for OCR, and relies on its language packs for languages other than English. 

Tesseract supports `most languages <https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc#languages>`_.

For Linux users, you can often find packages that provide language packs:

Debian and Ubuntu users
-----------------------

.. code-block:: bash

   # Display a list of all Tesseract language packs
   apt-cache search tesseract-ocr

   # Install Chinese Simplified language pack
   apt-get install tesseract-ocr-chi-sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as to what languages it should search for. Multiple
languages can be requested using either ``-l eng+fre`` (English and French) or ``-l eng -l fre``.

Fedora users
------------

.. code-block:: bash

   # Display a list of all Tesseract language packs
   dnf search tesseract

   # Install Chinese Simplified language pack
   dnf install tesseract-langpack-chi_sim

You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as to
what languages it should search for. Multiple languages can be requested using
either ``-l eng+fre`` (English and French) or ``-l eng -l fre``.

macOS users
-----------

You can install additional language packs by :ref:`installing Tesseract using Homebrew with all language packs <macos-all-languages>`.

Docker users
------------

Users of the Docker image may use the alternative :ref:`"polyglot" container <docker-polyglot>` which includes all languages.

Adding individual language packs to a Docker image
""""""""""""""""""""""""""""""""""""""""""""""""""

If you wish to add a single language pack, you could do the following:

* Download the desired ``.trainedata`` file from the `tessdata <https://github.com/tesseract-ocr/tessdata>`_ repository. Let's use Hebrew in this example (``heb.traineddata``)

* Copy the file to ``/home/user/downloads/heb.traineddata``.

* Create a new container based on the ocrmypdf-tess4 image and jump into it with a terminal:

.. code-block:: bash

	host$ docker run  -v /home/user/downloads:/home/docker -it --entrypoint /bin/bash ocrmypdf-tess4

* Put the file where Tesseract expects it:

.. code-block:: bash

	docker$ cp /home/docker/heb.traineddata /usr/share/tesseract-ocr/tessdata

* Note the container id, and save it as a new image (in this example, ``ocrmypdf-tess4-heb``)

.. code-block:: bash

    host$ docker commit <container_id> ocrmypdf-tess4-heb
