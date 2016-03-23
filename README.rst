OCRmyPDF
========

OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to
be searched.

Main features
-------------

-  Generates a searchable
   `PDF/A <https://en.wikipedia.org/?title=PDF/A>`__ file from a regular PDF
-  Places OCR text accurately below the image to ease copy / paste
-  Keeps the exact resolution of the original embedded images
-  When possible, inserts OCR information as a "lossless" operation without rendering vector information
-  Keeps file size about the same
-  If requested deskews and/or cleans the image before performing OCR
-  Validates input and output files
-  Provides debug mode to enable easy verification of the OCR results
-  Processes pages in parallel when more than one CPU core is
   available
-  Uses `Tesseract OCR <https://github.com/tesseract-ocr/tesseract>`__ engine
-  Supports the `39 languages <https://code.google.com/p/tesseract-ocr/downloads/list>`__ recognized by Tesseract
-  Battle-tested on thousands of PDFs, a test suite and continuous integration

For details: please consult the `release notes <RELEASE_NOTES.rst>`__.

Motivation
----------

I searched the web for a free command line tool to OCR PDF files on
Linux/UNIX: I found many, but none of them were really satisfying.

-  Either they produced PDF files with misplaced text under the image (making copy/paste impossible) 
-  Or they did not display correctly some escaped HTML characters located in the hOCR file produced by the OCR engine 
-  Or they changed the resolution of the embedded images
-  Or they generated PDF files having a ridiculous big size
-  Or they crashed when trying to OCR some of my PDF files
-  Or they did not produce valid PDF files (even though they were readable with my current PDF reader)
-  On top of that none of them produced PDF/A files (format dedicated for long time storage)

... so I decided to develop my own tool (using various existing scripts
as an inspiration)

Installation
------------

Download OCRmyPDF here: https://github.com/jbarlow83/OCRmyPDF/releases

You can install it to a Python virtual environment or system-wide. 

Debian and Ubuntu
~~~~~~~~~~~~~~~~~

Users of Debian 9 or later or Ubuntu 16.10 or later may simply
``apt-get install ocrmypdf``.

Installing the Docker image
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For many users, installing the Docker image will be easier than installing all of OCRmyPDF's dependencies. For Windows, it is the only option.

If you have `Docker <https://docs.docker.com/>`__ installed on your system, you can install
a Docker image of the latest release.

Follow the Docker installation instructions for your platform.  If you can run this command
successfully, your system is ready to download and execute the image::

   docker run hello-world
   
OCRmyPDF will use all available CPU cores.  By default, the VirtualBox machine instance on Windows and OS X has only a single CPU core enabled. Use the VirtualBox Manager to determine the name of your Docker engine host, and then follow these optional steps to enable multiple CPUs::

   # Optional step for Mac OS X users
   docker-machine stop "yourVM"
   VBoxManage modifyvm "yourVM" --cpus 2  # or whatever number of core is desired
   docker-machine start "yourVM"
   eval $(docker-machine env "yourVM")

Assuming you have a Docker engine running somewhere, you can run these commands to download
the image::

   docker pull jbarlow83/ocrmypdf

Then tag it to give a more convenient name, just ocrmypdf::

   docker tag jbarlow83/ocrmypdf ocrmypdf

This image contains language packs for English, French, Spanish and German. The alternative "polyglot" image provides `all available language packs <https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc#languages>`__::

   # Alternative step: If you need all language packs
   docker pull jbarlow83/ocrmypdf-polyglot
   docker tag jbarlow83/ocrmypdf-polyglot ocrmypdf

You can then run ocrmypdf using the command::

   docker run ocrmypdf --help
  
To execute the OCRmyPDF on a local file, you must `provide a writable volume to the Docker image <https://docs.docker.com/userguide/dockervolumes/>`__, such as this in this template::

   docker run -v "$(pwd):/home/docker" <other docker arguments>   ocrmypdf <your arguments to ocrmypdf>

In this worked example, the current working directory contains an input file called ``test.pdf`` and the output will go to ``output.pdf``:: 

   docker run -v "$(pwd):/home/docker"   ocrmypdf --skip-text test.pdf output.pdf

Note that ``ocrmypdf`` has its own separate ``-v VERBOSITYLEVEL`` argument to control debug verbosity. All Docker arguments should before the ``ocrmypdf`` image name and all arguments to ``ocrmypdf`` should be listed after.


Installing on Mac OS X
~~~~~~~~~~~~~~~~~~~~~~

These instructions probably work on all Mac OS X versions later than 10.7 (Lion). OCRmyPDF is known to work on Yosemite and El Capitan, and regularly tested on El Capitan.

If it's not already present, `install Homebrew <http://brew.sh/>`__.

Update Homebrew::

   brew update
   
Install or upgrade the required Homebrew packages, if any are missing::

   brew install libpng openjpeg jbig2dec     # image libraries
   brew install qpdf
   brew install ghostscript
   brew install python3
   brew install libxml2 libffi leptonica
   brew install unpaper    # optional
   brew install tesseract
   
Update the homebrew pip and install Pillow::

   pip3 install --upgrade pip
   pip3 install --upgrade pillow

You can then install OCRmyPDF from PyPI::

   pip3 install ocrmypdf

The command line program should now be available::

   ocrmypdf --help

Installing on Ubuntu 14.04 LTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Installing on Ubuntu 14.04 LTS (trusty) is more difficult than other options, because of certain bugs in Python package installation.

Update apt-get::

   sudo apt-get update
   sudo apt-get upgrade
   
Install system dependencies::

   sudo apt-get install \
      zlib1g-dev \
      libjpeg-dev \
      libffi-dev \
      ghostscript \
      tesseract-ocr \
      qpdf \
      unpaper \
      python3-pip \
      python3-pil \
      python3-pytest \
      python3-reportlab

If you wish install OCRmyPDF to the system Python, then install as follows (note this installs new packages
into your system Python, which could interfere with other programs)::

   sudo pip3 install ocrmypdf
   
If you wish to install OCRmyPDF to a virtual environment to isolate system Python from modified, you can
follow these steps.  This includes a workaround `for a known, unresolved issue in Ubuntu 14.04's ensurepip
package <http://www.thefourtheye.in/2014/12/Python-venv-problem-with-ensurepip-in-Ubuntu.html>`__::

   sudo apt-get install python3-venv
   python3 -m venv venv-ocrmypdf --without-pip
   source venv-ocrmypdf/bin/activate
   wget -O - -o /dev/null https://bootstrap.pypa.io/get-pip.py | python
   deactivate
   pyvenv --system-site-packages venv-ocrmypdf
   source venv-ocrmypdf/bin/activate
   pip install ocrmypdf

Ubuntu 14.04 only installs ``unpaper`` version 0.4.2, which is not supported by OCRmyPDF because it is produces invalid output. This program is an optional dependency, and provides page deskewing and cleaning. See `Dockerfile <Dockerfile>`__ for an example of how to building unpaper 6.1 from source. If you choose to install unpaper later, OCRmyPDF will use the foremost version on the system PATH.

Installing on Windows
~~~~~~~~~~~~~~~~~~~~~

Direct installation on Windows is not possible.  Install the Docker container as described above.

      
Installing HEAD revision from sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have ``git`` and ``python3.4`` or ``python3.5`` installed, you can install from source. When the ``pip`` installer runs,
it will alert you if dependencies are missing.

To install the HEAD revision from sources in the current Python 3 environment::

   pip3 install git+https://github.com/jbarlow83/OCRmyPDF.git

Or, to install in `development mode <https://pythonhosted.org/setuptools/setuptools.html#development-mode>`__,  allowing customization of OCRmyPDF, use the ``-e`` flag::

   pip3 install -e git+https://github.com/jbarlow83/OCRmyPDF.git
   
On certain Linux distributions such as Ubuntu, you may need to use 
run the install command as superuser::

   sudo pip3 install [-e] git+https://github.com/jbarlow83/OCRmyPDF.git
   
Note that this will alter your system's Python distribution. If you prefer 
to not install as superuser, you can install the package in a Python virtual environment::

   git clone -b master https://github.com/jbarlow83/OCRmyPDF.git
   pyvenv venv
   source venv/bin/activate
   cd OCRmyPDF
   pip3 install .

However, ``ocrmypdf`` will only be accessible on the system PATH after
you activate the virtual environment.

To run the program::
   
   ocrmypdf --help

If not yet installed, the script will notify you about dependencies that
need to be installed. The script requires specific versions of the
dependencies. Older version than the ones mentioned in the release notes
are likely not to be compatible to OCRmyPDF.

Languages
---------

OCRmyPDF uses Tesseract for OCR, and relies on its language packs. For Linux users,
you can often find packages that provide language packs::

   # Debian/Ubuntu users
   sudo apt-get install tesseract-ocr-chi-sim
   
You can then pass the ``-l LANG`` argument to OCRmyPDF to give a hint as to what languages it should search for. Multiple
languages can be requested.

Support
-------

In case you detect an issue, please:

-  Check if your issue is already known
-  If no problem report exists on github, please create one here:
   https://github.com/jbarlow83/OCRmyPDF/issues
-  Describe your problem thoroughly
-  Append the console output of the script when running the debug mode
   (``-v 1`` option)
-  If possible provide your input PDF file as well as the content of the
   temporary folder (using a file sharing service like Dropbox)

Press & Media
-------------

-  `c't 1-2014, page 59 <http://heise.de/-2279695>`__:
   Detailed presentation of OCRmyPDF v1.0 in the leading German IT
   magazine c't
-  `heise Open Source, 09/2014: Texterkennung mit
   OCRmyPDF <http://heise.de/-2356670>`__

Disclaimer
----------

The software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.
