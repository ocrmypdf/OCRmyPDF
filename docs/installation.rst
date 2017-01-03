Installation
============

Installing on Debian and Ubuntu
-------------------------------

Users of Debian 9 ("stretch") or later or Ubuntu 16.10 or later may simply

.. code-block:: bash

	apt-get install ocrmypdf

.. _Docker:

Installing the Docker image
---------------------------

For many users, installing the Docker image will be easier than installing all of OCRmyPDF's dependencies. For Windows, it is the only option.

If you have `Docker <https://docs.docker.com/>`_ installed on your system, you can install
a Docker image of the latest release.

Follow the Docker installation instructions for your platform.  If you can run this command
successfully, your system is ready to download and execute the image:

.. code-block:: bash

   docker run hello-world
   
OCRmyPDF will use all available CPU cores.  By default, the VirtualBox machine instance on Windows and OS X has only a single CPU core enabled. Use the VirtualBox Manager to determine the name of your Docker engine host, and then follow these optional steps to enable multiple CPUs:

.. code-block:: bash

   # Optional step for Mac OS X users
   docker-machine stop "yourVM"
   VBoxManage modifyvm "yourVM" --cpus 2  # or whatever number of core is desired
   docker-machine start "yourVM"
   eval $(docker-machine env "yourVM")

Assuming you have a Docker engine running somewhere, you can run these commands to download
the image:

.. code-block:: bash

   docker pull jbarlow83/ocrmypdf

Then tag it to give a more convenient name, just ocrmypdf:

.. code-block:: bash

   docker tag jbarlow83/ocrmypdf ocrmypdf

.. _docker-polyglot:

This image contains language packs for English, French, Spanish and German. The alternative "polyglot" image provides `all available language packs <https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc#languages>`_:

.. code-block:: bash

   # Alternative step: If you need all language packs
   docker pull jbarlow83/ocrmypdf-polyglot
   docker tag jbarlow83/ocrmypdf-polyglot ocrmypdf

You can then run ocrmypdf using the command:

.. code-block:: bash

   docker run --rm ocrmypdf --help
  
To execute the OCRmyPDF on a local file, you must `provide a writable volume to the Docker image <https://docs.docker.com/userguide/dockervolumes/>`_, and both the input and output file must be inside the writable volume.  This example command uses the current working directory as the writable volume:

.. code-block:: bash

   docker run --rm -v "$(pwd):/home/docker" <other docker arguments>   ocrmypdf <your arguments to ocrmypdf>

In this worked example, the current working directory contains an input file called ``test.pdf`` and the output will go to ``output.pdf``: 

.. code-block:: bash

   docker run --rm -v "$(pwd):/home/docker"   ocrmypdf --skip-text test.pdf output.pdf

.. note:: The working directory should be a writable local volume or Docker may not have permission to access it.

Note that ``ocrmypdf`` has its own separate ``-v VERBOSITYLEVEL`` argument to control debug verbosity. All Docker arguments should before the ``ocrmypdf`` image name and all arguments to ``ocrmypdf`` should be listed after.


Installing on macOS (formerly Mac OS X)
---------------------------------------

These instructions probably work on all macOS supported by Homebrew. OCRmyPDF is known to work on Yosemite and El Capitan, and regularly tested on El Capitan.

If it's not already present, `install Homebrew <http://brew.sh/>`_.

Update Homebrew:

.. code-block:: bash

   brew update
   
Install or upgrade the required Homebrew packages, if any are missing:

.. code-block:: bash

   brew install libpng openjpeg jbig2dec libtiff     # image libraries
   brew install qpdf
   brew install ghostscript
   brew install python3
   brew install libxml2 libffi leptonica
   brew install unpaper   # optional
   
Python 3.4, 3.5 and 3.6 are supported.

Install the required Tesseract OCR engine with the language packs you plan to use:
   
.. code-block:: bash

   brew install tesseract                       # Option 1: for English, French, German, Spanish

.. _macos-all-languages:

.. code-block:: bash
   
   brew install tesseract --with-all-languages  # Option 2: for all language packs 
   
Update the homebrew pip and install Pillow:

.. code-block:: bash

   pip3 install --upgrade pip
   pip3 install --upgrade pillow

You can then install OCRmyPDF from PyPI:

.. code-block:: bash

   pip3 install ocrmypdf

The command line program should now be available:

.. code-block:: bash

   ocrmypdf --help

Installing on Ubuntu 14.04 LTS
------------------------------

Installing on Ubuntu 14.04 LTS (trusty) is more difficult than some other options, because of bugs in Python package installation.

Add new "apt" repositories needed for backports of Ghostscript 9.16 and libav-11, which supports unpaper 6.1. This will replace Ghostscript on your system.

.. code-block:: bash

   sudo add-apt-repository ppa:vshn/ghostscript -y 
   sudo add-apt-repository ppa:heyarje/libav-11 -y

Update apt-get:

.. code-block:: bash

   sudo apt-get update
   sudo apt-get upgrade
   
Install system dependencies:

.. code-block:: bash

   sudo apt-get install \
      zlib1g-dev \
      libjpeg-dev \
      libffi-dev \
      libavformat56 libavcodec56 libavutil54 \
      ghostscript \
      tesseract-ocr \
      qpdf \
      python3-pip \
      python3-pil \
      python3-pytest \
      python3-reportlab

If you wish install OCRmyPDF to the system Python, then install as follows (note this installs new packages
into your system Python, which could interfere with other programs):

.. code-block:: bash

   sudo pip3 install ocrmypdf
   
If you wish to install OCRmyPDF to a virtual environment to isolate the system Python, you can
follow these steps.  This includes a workaround `for a known, unresolved issue in Ubuntu 14.04's ensurepip
package <http://www.thefourtheye.in/2014/12/Python-venv-problem-with-ensurepip-in-Ubuntu.html>`_:

.. code-block:: bash

   sudo apt-get install python3-venv
   python3 -m venv venv-ocrmypdf --without-pip
   source venv-ocrmypdf/bin/activate
   wget -O - -o /dev/null https://bootstrap.pypa.io/get-pip.py | python
   deactivate
   python3 -m venv --system-site-packages venv-ocrmypdf
   source venv-ocrmypdf/bin/activate
   pip install ocrmypdf

These installation instructions omit the optional dependency ``unpaper``, which is only available at version 0.4.2 in Ubuntu 14.04. The author could not find a backport of ``unpaper``, and created a .deb package to do the job of installing unpaper 6.1 (for x86 64-bit only):

.. code-block:: bash

   wget -q https://dl.dropboxusercontent.com/u/28971240/unpaper_6.1-1.deb -O unpaper_6.1-1.deb
   sudo dpkg -i unpaper_6.1-1.deb


Installing on Windows
---------------------

Direct installation on Windows is not possible.  Install the _`Docker` container as described above.  Ensure that your command prompt can run the docker "hello world" container.

Running on Windows
~~~~~~~~~~~~~~~~~~

The command line syntax to run ocrmypdf from a command prompt will resemble:

.. code-block:: bat

   docker run -v /c/Users/sampleuser:/home/docker ocrmypdf --skip-text test.pdf output.pdf

where /c/Users/sampleuser is a Unix representation of the Windows path C:\\Users\\sampleuser, assuming a user named "sampleuser" is running ocrmypdf on a file in their home directory, and the files "test.pdf" and "output.pdf" are in the sampleuser folder. The Windows user must have read and write permissions.
      
Installing HEAD revision from sources
-------------------------------------

If you have ``git`` and ``python3.4`` or ``python3.5`` installed, you can install from source. When the ``pip`` installer runs,
it will alert you if dependencies are missing.

To install the HEAD revision from sources in the current Python 3 environment:

.. code-block:: bash

   pip3 install git+https://github.com/jbarlow83/OCRmyPDF.git

Or, to install in `development mode <https://pythonhosted.org/setuptools/setuptools.html#development-mode>`_,  allowing customization of OCRmyPDF, use the ``-e`` flag:

.. code-block:: bash

   pip3 install -e git+https://github.com/jbarlow83/OCRmyPDF.git
   
On certain Linux distributions such as Ubuntu, you may need to use 
run the install command as superuser:

.. code-block:: bash

   sudo pip3 install [-e] git+https://github.com/jbarlow83/OCRmyPDF.git
   
Note that this will alter your system's Python distribution. If you prefer 
to not install as superuser, you can install the package in a Python virtual environment:

.. code-block:: bash

   git clone -b master https://github.com/jbarlow83/OCRmyPDF.git
   python3 -m venv
   source venv/bin/activate
   cd OCRmyPDF
   pip3 install .

However, ``ocrmypdf`` will only be accessible on the system PATH after
you activate the virtual environment.

To run the program:

.. code-block:: bash
   
   ocrmypdf --help

If not yet installed, the script will notify you about dependencies that
need to be installed. The script requires specific versions of the
dependencies. Older version than the ones mentioned in the release notes
are likely not to be compatible to OCRmyPDF.
