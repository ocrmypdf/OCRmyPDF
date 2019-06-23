=====================
OCRmyPDF Docker image
=====================

OCRmyPDF is also available in a Docker image that packages recent
versions of all dependencies.

For users who already have Docker installed this may be an easy and
convenient option. However, it is less performant than a system
installation and may require Docker engine configuration.

OCRmyPDF needs a generous amount of RAM, CPU cores, temporary storage
space, whether running in a Docker container or on its own. It may be
necessary to ensure the container is provisioned with additional
resources.

.. _docker-install:

Installing the Docker image
===========================

If you have `Docker <https://docs.docker.com/>`__ installed on your
system, you can install a Docker image of the latest release.

The recommended OCRmyPDF Docker image is currently named
``ocrmypdf-alpine``:

.. code-block:: bash

   docker pull jbarlow83/ocrmypdf-alpine

Follow the Docker installation instructions for your platform. If you
can run this command successfully, your system is ready to download and
execute the image:

.. code-block:: bash

   docker run hello-world

OCRmyPDF will use all available CPU cores. By default, the VirtualBox
machine instance on Windows and macOS has only a single CPU core
enabled. Use the VirtualBox Manager to determine the name of your Docker
engine host, and then follow these optional steps to enable multiple
CPUs:

.. code-block:: bash

   # Optional step for Mac OS X users
   docker-machine stop "yourVM"
   VBoxManage modifyvm "yourVM" --cpus 2  # or whatever number of core is desired
   docker-machine start "yourVM"
   eval $(docker-machine env "yourVM")

Using the Docker image on the command line
==========================================

**Unlike typical Docker containers**, in this mode we are using the
OCRmyPDF Docker container is intended to be emphemeral – it runs for one
OCR job and then terminates, just like a command line program. We are
using Docker as a way of delivering an application, not a server.

To start a Docker container (instance of the image):

.. code-block:: bash

   docker tag jbarlow83/ocrmypdf-alpine ocrmypdf
   docker run --rm -i ocrmypdf (... all other arguments here...)

For convenience, create a shell alias to hide the Docker command. It is
easier to send the input file to file stdin and read the output from
stdout – this avoids the occasionally messy permission issues with
Docker entirely.

.. code-block:: bash

   alias ocrmypdf='docker run --rm -i ocrmypdf'
   ocrmypdf --version  # runs docker version
   ocrmypdf <input.pdf >output.pdf

Or in the wonderful `fish shell <https://fishshell.com/>`__:

.. code-block:: fish

   alias ocrmypdf 'docker run --rm ocrmypdf'
   funcsave ocrmypdf

Alternately, you could mount the local current working directory as a
Docker volume:

.. code-block:: bash

   docker run --rm -v $(pwd):/data ocrmypdf /data/input.pdf /data/output.pdf

.. _docker-lang-packs:

Adding languages to the Docker image
====================================

By default the Docker image includes English, German and Simplified
Chinese, the most popular languages for OCRmyPDF users based on
feedback. You may add other languages by creating a new Dockerfile based
on the public one:

.. code-block:: dockerfile

   FROM jbarlow83/ocrmypdf-alpine

   # Add French
   RUN apk add tesseract-ocr-data-fra

You can also copy training data to ``/usr/share/tessdata``.

Executing the test suite
========================

The OCRmyPDF test suite is installed with image. To run it:

.. code-block:: bash

   docker run --entrypoint python3 jbarlow83/ocrmypdf-alpine setup.py test

Accessing the shell
===================

``bash`` is not installed in the image. To use the busybox shell in the
Docker image:

.. code-block:: bash

   docker run -it --entrypoint busybox  jbarlow83/ocrmypdf-alpine sh

Using the OCRmyPDF web service wrapper
======================================

The OCRmyPDF Docker image includes an example, barebones HTTP web
service. The webservice may be launched as follows:

.. code-block:: bash

   docker run --entrypoint python3 -p 5000:5000 jbarlow83/ocrmypdf-alpine webservice.py

Unlike command line usage this program will open a socket and wait for
connections.

.. warning::

   The OCRmyPDF web service wrapper is intended for demonstration or
   development. It provides no security, no authentication, no
   protection against denial of service attacks, and no load balancing.
   The default Flask WSGI server is used, which is intended for
   development only. The server is single-threaded and so can respond to
   only one client at a time. While running OCR, it cannot respond to
   any other clients.

Clients must keep their open connection while waiting for OCR to
complete. This may entail setting a long timeout; this interface is more
useful for internal HTTP API calls.

Unlike the rest of OCRmyPDF, this web service is licensed under the
Affero GPLv3 (AGPLv3) since Ghostscript, a dependency of OCRmyPDF, is
also licensed in this way.

In addition to the above, please read our
:ref:`general remarks on using OCRmyPDF as a service <ocr-service>`.

Ubuntu-based Docker image
=========================

A Ubuntu-based OCRmyPDF image is also available. The main advantage this
image offers is that it supports manylinux Python wheels (which are not
supported on Alpine Linux). This may be useful for plugins.

.. code-block:: bash

   docker pull jbarlow83/ocrmypdf
