OCRmyPDF Docker image
=====================

OCRmyPDF is also available in a Docker image that packages recent versions of all dependencies.

For users who already have Docker installed this may be an easy and convenient option. However, it is less performant than a system installation and may require Docker engine configuration.

OCRmyPDF needs a generous amount of RAM, CPU cores, and temporary storage space.

.. _docker-install:

Installing the Docker image
---------------------------

If you have `Docker <https://docs.docker.com/>`_ installed on your system, you can install a Docker image of the latest release.

The recommended OCRmyPDF Docker image is currently named ``ocrmypdf-alpine``:

.. code-block:: bash

    docker pull jbarlow83/ocrmypdf-alpine

Follow the Docker installation instructions for your platform.  If you can run this command successfully, your system is ready to download and execute the image:

.. code-block:: bash

    docker run hello-world

OCRmyPDF will use all available CPU cores.  By default, the VirtualBox machine instance on Windows and macOS has only a single CPU core enabled. Use the VirtualBox Manager to determine the name of your Docker engine host, and then follow these optional steps to enable multiple CPUs:

.. code-block:: bash

    # Optional step for Mac OS X users
    docker-machine stop "yourVM"
    VBoxManage modifyvm "yourVM" --cpus 2  # or whatever number of core is desired
    docker-machine start "yourVM"
    eval $(docker-machine env "yourVM")

Using the Docker image on the command line
------------------------------------------

**Unlike typical Docker containers**, in this mode we are using the OCRmyPDF Docker container is intended to be emphemeral – it runs for one OCR job and then terminates, just like a command line program. We are using Docker as a way of delivering an application, not a server.

To start a Docker container (instance of the image):

.. code-block:: bash

    docker tag jbarlow83/ocrmypdf-alpine ocrmypdf
    docker run --rm ocrmypdf (... all other arguments here...)

For convenience, create a shell alias to hide the Docker command:

.. code-block:: bash

    alias ocrmypdf='docker run --rm -v "$(pwd):/home/docker" ocrmypdf'
    ocrmypdf --version  # runs docker version

Or in the wonderful `fish shell <https://fishshell.com/>`_:

.. code-block:: fish

    alias ocrmypdf 'docker run --rm ocrmypdf'
    funcsave ocrmypdf

.. _docker-lang-packs:

Adding languages to the Docker image
------------------------------------

By default the Docker image includes English, German and Simplified Chinese, the most popular languages for OCRmyPDF users based on feedback. You may add other languages by creating a new Dockerfile based on the public one:

.. code-block:: dockerfile

    FROM jbarlow83/ocrmypdf-alpine

    # Add French
    RUN apk add tesseract-ocr-data-fra

Executing the test suite
------------------------

The OCRmyPDF test suite is installed with image.  To run it:

.. code-block:: bash

    docker run --entrypoint python3 jbarlow83/ocrmypdf-alpine setup.py test

Using the OCRmyPDF web service wrapper
--------------------------------------

The OCRmyPDF Docker image includes an example, barebones HTTP web service. The webservice may be launched as follows:

.. code-block:: bash

    docker run --entrypoint python3 -p 5000:5000 jbarlow83/ocrmypdf-alpine webservice.py

Unlike command line usage this program will open a socket and wait for connections.

.. warning::

    The OCRmyPDF web service wrapper is intended for demonstration or development. It provides no security, no authentication, no protection against denial of service attacks, and no load balancing. The default Flask WSGI server is used, which is intended for development only. The server is single-threaded and so can respond to only one client at a time. It cannot respond to clients while busy with OCR.

Clients must keep their open connection while waiting for OCR to complete. This may entail setting a long timeout; this interface is more useful for internal HTTP API calls.

Unlike the rest of OCRmyPDF, this web service is licensed under the Affero GPLv3 (AGPLv3) since Ghostscript, a dependency of OCRmyPDF, is also licensed in this way.

In addition to the above, please read our :ref:`general remarks on using OCRmyPDF as a service <ocr-service>`.

Legacy Ubuntu Docker images
---------------------------

Previously OCRmyPDF was delivered in several Docker images for different purposes, based on Ubuntu.

The Ubuntu-based images will be maintained for some time but should not be used for new deployments. They are as follows:

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Image name
        - Download command
        - Notes
    *   - ocrmypdf
        - ``docker pull jbarlow83/ocrmypdf``
        - Latest ocrmypdf with Tesseract 4.0.0-beta1 on Ubuntu 18.04. Includes English, French, German, Spanish, Portugeuse and Simplified Chinese.
    *   - ocrmypdf-polyglot
        - ``docker pull jbarlow83/ocrmypdf-polyglot``
        - As above, with all available language packs.
    *   - ocrmypdf-webservice
        - ``docker pull jbarlow83/ocrmypdf-webservice``
        - All language packs, and a simple HTTP wrapper allowing OCRmyPDF to be used as a web service. Note that this component is licensed under AGPLv3.

To execute the Ubuntu-based OCRmyPDF on a local file, you must `provide a writable volume to the Docker image <https://docs.docker.com/userguide/dockervolumes/>`_, and both the input and output file must be inside the writable volume. This limitation applies only to the legacy images.

This example command uses the current working directory as the writable volume:

.. code-block:: bash

    docker run --rm -v "$(pwd):/home/docker" <other docker arguments>   ocrmypdf <your arguments to ocrmypdf>

In this worked example, the current working directory contains an input file called ``test.pdf`` and the output will go to ``output.pdf``:

.. code-block:: bash

    docker run --rm -v "$(pwd):/home/docker"   ocrmypdf --skip-text test.pdf output.pdf

.. note:: The working directory should be a writable local volume or Docker may not have permission to access it.

Note that ``ocrmypdf`` has its own separate ``-v VERBOSITYLEVEL`` argument to control debug verbosity. All Docker arguments should before the ``ocrmypdf`` image name and all arguments to ``ocrmypdf`` should be listed after.

In some environments the permissions associated with Docker can be complex to configure. The process that executes Docker may end up not having the permissions to write the specified file system. In that case one can stream the file into and out of the Docker process and avoid all permission hassles, using ``-`` as the input and output filename:

.. code-block:: bash

    docker run --rm -i   ocrmypdf <other arguments to ocrmypdf> - - <input.pdf >output.pdf
