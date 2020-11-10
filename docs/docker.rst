.. _docker:

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

If you can run this command successfully, your system is ready to download and
execute the image:

.. code-block:: bash

   docker run hello-world

The recommended OCRmyPDF Docker image is currently named ``ocrmypdf``:

.. code-block:: bash

   docker pull jbarlow83/ocrmypdf


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

See the Docker documentation for
`adjusting memory and CPU on other platforms <https://docs.docker.com/config/containers/resource_constraints/>`__.

Using the Docker image on the command line
==========================================

**Unlike typical Docker containers**, in this section the OCRmyPDF Docker
container is emphemeral – it runs for one OCR job and terminates, just like a
command line program. We are using Docker to deliver an application (as opposed
to the more conventional case, where a Docker container runs as a server).

To start a Docker container (instance of the image):

.. code-block:: bash

   docker tag jbarlow83/ocrmypdf ocrmypdf
   docker run --rm -i ocrmypdf (... all other arguments here...) - -

For convenience, create a shell alias to hide the Docker command. It is
easier to send the input file as stdin and read the output from
stdout – **this avoids the messy permission issues with Docker entirely**.

.. code-block:: bash

   alias docker_ocrmypdf='docker run --rm -i ocrmypdf'
   docker_ocrmypdf --version  # runs docker version
   docker_ocrmypdf - - <input.pdf >output.pdf

Or in the wonderful `fish shell <https://fishshell.com/>`__:

.. code-block:: fish

   alias docker_ocrmypdf 'docker run --rm ocrmypdf'
   funcsave docker_ocrmypdf

Alternately, you could mount the local current working directory as a
Docker volume:

.. code-block:: bash

   alias docker_ocrmypdf='docker run --rm  -i --user "$(id -u):$(id -g)" --workdir /data -v "$PWD:/data" ocrmypdf'
   docker_ocrmypdf /data/input.pdf /data/output.pdf

.. _docker-lang-packs:

Adding languages to the Docker image
====================================

By default the Docker image includes English, German, Simplified Chinese,
French, Portuguese and Spanish, the most popular languages for OCRmyPDF
users based on feedback. You may add other languages by creating a new
Dockerfile based on the public one:

.. code-block:: dockerfile

   FROM jbarlow83/ocrmypdf

   # Add French
   RUN apt install tesseract-ocr-fra

You can also copy training data to ``/usr/share/tesseract-ocr/<tesseract version>/tessdata``.

Executing the test suite
========================

The OCRmyPDF test suite is installed with image. To run it:

.. code-block:: bash

   docker run --entrypoint python3  jbarlow83/ocrmypdf -m pytest

Accessing the shell
===================

To use the bash shell in the Docker image:

.. code-block:: bash

   docker run -it --entrypoint bash  jbarlow83/ocrmypdf

Using the OCRmyPDF web service wrapper
======================================

The OCRmyPDF Docker image includes an example, barebones HTTP web
service. The webservice may be launched as follows:

.. code-block:: bash

   docker run --entrypoint python3 -p 5000:5000  jbarlow83/ocrmypdf webservice.py

This will configure the machine to listen on port 5000. On Linux machines
this is port 5000 of localhost. On macOS or Windows machines running
Docker, this is port 5000 of the virtual machine that runs your Docker
images. You can find its IP address using the command ``docker-machine ip``.

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
Affero GPLv3 (AGPLv3) since Ghostscript is also licensed in this way.

In addition to the above, please read our
:ref:`general remarks on using OCRmyPDF as a service <ocr-service>`.
