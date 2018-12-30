Installation
============

.. |latest| image:: https://img.shields.io/pypi/v/ocrmypdf.svg
    :alt: OCRmyPDF latest released version on PyPI

|latest|

The easiest way to install OCRmyPDF to follow the steps for your operating system/platform.

If you want to use the latest version of OCRmyPDF, your best bet is to install the most recent version your platform provides, and then upgrade that version by installing the Python binary wheels.

.. contents:: Platform-specific steps
    :depth: 2
    :local:

Installing on Linux
-------------------

Debian and Ubuntu 16.10 or newer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. |deb-stable| image:: https://repology.org/badge/version-for-repo/debian_stable/ocrmypdf.svg
    :alt: Debian 9 stable ("stretch")

.. |deb-testing| image:: https://repology.org/badge/version-for-repo/debian_testing/ocrmypdf.svg
    :alt: Debian 10 testing ("buster")

.. |deb-unstable| image:: https://repology.org/badge/version-for-repo/debian_unstable/ocrmypdf.svg
    :alt: Debian unstable

.. |ubu-1710| image:: https://repology.org/badge/version-for-repo/ubuntu_17_10/ocrmypdf.svg
    :alt: Ubuntu 17.10

.. |ubu-1804| image:: https://repology.org/badge/version-for-repo/ubuntu_18_04/ocrmypdf.svg
    :alt: Ubuntu 18.04 LTS

.. |ubu-1810| image:: https://repology.org/badge/version-for-repo/ubuntu_18_10/ocrmypdf.svg
    :alt: Ubuntu 18.10


+-------------------------------------------+
| **OCRmyPDF versions in Debian & Ubuntu**  |
+-------------------------------------------+
| |latest|                                  |
+-------------------------------------------+
| |deb-stable| |deb-testing| |deb-unstable| |
+-------------------------------------------+
| |ubu-1710| |ubu-1804| |ubu-1810|          |
+-------------------------------------------+

Users of Debian 9 ("stretch") or later or Ubuntu 16.10 or later may simply

.. code-block:: bash

    apt-get install ocrmypdf

As indicated in the table above, Debian and Ubuntu releases may lag behind the latest version. If the version available for your platform is out of date, you could opt to install the latest version from source. See `Installing HEAD revision from sources`_.

For full details on version availability for your platform, check the `Debian Package Tracker <https://tracker.debian.org/pkg/ocrmypdf>`_ or `Ubuntu launchpad.net <https://launchpad.net/ocrmypdf>`_.

.. note::

    OCRmyPDF for Debian and Ubuntu currently omit the JBIG2 encoder. OCRmyPDF works fine without it but will produce larger output files. If you build jbig2enc from source, ocrmypdf 7.0.0 and later will automatically detect it (specifically the ``jbig2`` binary) on the ``PATH``. To add JBIG2 encoding, see :ref:`jbig2`.

Fedora 29 or newer
^^^^^^^^^^^^^^^^^^

.. |fedora-29| image:: https://repology.org/badge/version-for-repo/fedora29/ocrmypdf.svg
    :alt: Fedora 29

.. |fedora-rawhide| image:: https://repology.org/badge/version-for-repo/fedora_rawhide/ocrmypdf.svg
    :alt: Fedore Rawhide


+------------------------------+
| **OCRmyPDF version**         |
+------------------------------+
| |latest|                     |
+------------------------------+
| |fedora-29| |fedora-rawhide| |
+------------------------------+

Users of Fedora 29 later may simply

.. code-block:: bash

    dnf install ocrmypdf

For full details on version availability, check the `Fedora Package Tracker
<https://apps.fedoraproject.org/packages/ocrmypdf>`_.

If the version available for your platform is out of date, you could opt to
install the latest version from source. See `Installing HEAD revision from
sources`_.

.. note::

    OCRmyPDF for Fedora currently omits the JBIG2 encoder due to patent issues.
    OCRmyPDF works fine without it but will produce larger output files. If you
    build jbig2enc from source, ocrmypdf 7.0.0 and later will automatically
    detect it on the ``PATH``. To add JBIG2 encoding, see `Installing the JBIG2
    encoder`_.

Installing the latest version on Ubuntu 18.04 LTS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ubuntu 18.04 includes ocrmypdf 6.1.2. To install a more recent version, first
install the system version to get most of the dependencies:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install \
        ocrmypdf \
        python3-pip

There are a few dependency changes between ocrmypdf 6.1.2 and 7.x. Let's get
these, too.

.. code-block:: bash

    sudo apt-get install \
        libexempi3 \
        pngquant

Then install the most recent ocrmypdf for the local user and set the user's ``PATH`` to check for the user's Python packages.

.. code-block:: bash

    export PATH=$HOME/.local/bin:$PATH
    pip3 install --user ocrmypdf

To add JBIG2 encoding, see :ref:`jbig2`.

Ubuntu 16.04 LTS
^^^^^^^^^^^^^^^^

No package is currently available for Ubuntu 16.04, but you can install the dependencies manually:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install \
        ghostscript \
        libexempi3 \
        pngquant \
        python3-cffi \
        python3-pip \
        qpdf \
        tesseract-ocr \
        unpaper

If you wish install OCRmyPDF for the current user, and ensure that the ``PATH``
environment variable contains ``$HOME/.local/bin``.

.. code-block:: bash

    export PATH=$HOME/.local/bin:$PATH
    pip3 install --user ocrmypdf

Alternately, you can install ocrmypdf system-wide. (Not recommended.)

.. code-block:: bash

    sudo pip3 install ocrmypdf

At your option, you may upgrade Ubuntu 16.04 LTS to Tesseract 4.0 for improved OCR results.

.. code-block:: bash

    sudo apt-get install -y software-properties-common python-software-properties
    sudo add-apt-repository ppa:alex-p/tesseract-ocr -y
    sudo apt-get update
    sudo apt-get upgrade tesseract-ocr

To add JBIG2 encoding, see :ref:`jbig2`.

Ubuntu 14.04 LTS
^^^^^^^^^^^^^^^^

Installing on Ubuntu 14.04 LTS (trusty) is more difficult than some other options, because it is older and does not provide ``pip``.

Update apt-get:

.. code-block:: bash

    sudo apt-get update

Install system dependencies:

.. code-block:: bash

    sudo apt-get install \
        software-properties-common python-software-properties \
        zlib1g-dev \
        libexempi3 \
        libjpeg-dev \
        libffi-dev \
        pngquant \
        qpdf

We will need backports of Ghostscript 9.16, libav-11 (for unpaper 6.1), Tesseract 4.00 (alpha), and Python 3.6. This will replace Ghostscript and Tesseract 3.x on your system. Python 3.6 will be installed alongside the system Python 3.4.

If you prefer to not modify your system in this matter, consider using a Docker container.

.. code-block:: bash

    sudo add-apt-repository ppa:vshn/ghostscript -y
    sudo add-apt-repository ppa:heyarje/libav-11 -y
    sudo add-apt-repository ppa:alex-p/tesseract-ocr -y
    sudo add-apt-repository ppa:jonathonf/python-3.6 -y

    sudo apt-get update

    sudo apt-get install \
        python3.6-dev \
        ghostscript \
        tesseract-ocr \
        tesseract-ocr-eng \
        libavformat56 libavcodec56 libavutil54 \
        wget

Now we need to install ``pip`` and let it install ocrmypdf:

.. code-block:: bash

    curl https://bootstrap.pypa.io/ez_setup.py -o - | python3.6 && python3.6 -m easy_install pip
    pip3.6 install ocrmypdf

The ``wget`` command will download a program and run it.

These installation instructions omit the optional dependency ``unpaper``, which is only available at version 0.4.2 in Ubuntu 14.04. The author could not find a backport of ``unpaper``, and created a .deb package to do the job of installing unpaper 6.1 (for x86 64-bit only):

.. code-block:: bash

    wget -q 'https://www.dropbox.com/s/vaq0kbwi6e6au80/unpaper_6.1-1.deb?raw=1' -O unpaper_6.1-1.deb
    sudo dpkg -i unpaper_6.1-1.deb

To add JBIG2 encoding, see :ref:`jbig2`.

ArchLinux
^^^^^^^^^

.. image:: https://repology.org/badge/version-for-repo/aur/ocrmypdf.svg
    :alt: ArchLinux
    :target: https://repology.org/metapackage/ocrmypdf

The author is aware of an `ArchLinux User Repository package for ocrmypdf <https://aur.archlinux.org/packages/ocrmypdf/>`_. You can use the following command.

.. code-block:: bash

    yaourt -S ocrmypdf

If you have any difficulties with installation, check the repository package page.

Other Linux packages
^^^^^^^^^^^^^^^^^^^^

See the `Repology <https://repology.org/metapackage/ocrmypdf/versions>`_ page.

In general, first install the OCRmyPDF package for your system, then optionally use the procedure `Installing with Python pip`_ to install a more recent version.

Installing on macOS
-------------------

Homebrew
^^^^^^^^

.. image:: https://img.shields.io/homebrew/v/ocrmypdf.svg
    :alt: homebrew
    :target: http://brewformulas.org/Ocrmypdf

OCRmyPDF is now a standard `Homebrew <https://brew.sh>`_ formula. To install on macOS:

.. code-block:: bash

    brew install ocrmypdf

.. note::

    Users who previously installed OCRmyPDF on macOS using ``pip install ocrmypdf`` should remove the pip version (``pip3 uninstall ocrmypdf``) before switching to the Homebrew version.

.. note::

    Users who previously installed OCRmyPDF from the private tap should switch to the mainline version (``brew untap jbarlow83/ocrmypdf``) and install from there.

Manual installation on macOS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These instructions probably work on all macOS supported by Homebrew.

If it's not already present, `install Homebrew <http://brew.sh/>`_.

Update Homebrew:

.. code-block:: bash

    brew update

Install or upgrade the required Homebrew packages, if any are missing. To do this, download the ``Brewfile`` that lists all of the dependencies to the current directory, and run ``brew bundle`` to process them (installing or upgrading as needed). ``Brewfile`` is a plain text file.

.. code-block:: bash

    wget https://github.com/jbarlow83/OCRmyPDF/raw/master/.travis/Brewfile
    brew bundle

This will include the English, French, German and Spanish language packs. If you need other languages you can optionally install them all:

.. _macos-all-languages:

.. code-block:: bash

    brew install tesseract --with-all-languages  # Option 2: for all language packs

Update the homebrew pip:

.. code-block:: bash

    pip3 install --upgrade pip

You can then install OCRmyPDF from PyPI, for the current user:

.. code-block:: bash

    pip3 install --user ocrmypdf

or system-wide:

.. code-block:: bash

    pip3 install ocrmypdf

The command line program should now be available:

.. code-block:: bash

    ocrmypdf --help

.. _docker-install:

Installing the Docker image
---------------------------

For some users, installing the Docker image will be easier than installing all of OCRmyPDF's dependencies. For Windows, it is the only option.

If you have `Docker <https://docs.docker.com/>`_ installed on your system, you can install a Docker image of the latest release.

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

Assuming you have a Docker engine running, you can download one of the three available images:

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
        - ``docker pull jbarlow83/ocrmypdf-polyglot``
        - All language packs, and a simple HTTP wrapper allowing OCRmyPDF to be used as a web service. Note that this component is licensed under AGPLv3.

For example:

.. code-block:: bash

    docker pull jbarlow83/ocrmypdf

Then tag it to give a more convenient name, just ocrmypdf:

.. code-block:: bash

    docker tag jbarlow83/ocrmypdf ocrmypdf

.. _docker-polyglot:

The alternative "polyglot" image provides `all available language packs <https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc#languages>`_.

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

In some environments the permissions associated with Docker can be complex to configure. The process that executes Docker may end up not having the permissions to write the specified file system. In that case one can stream the file into and out of the Docker process and avoid all permission hassles, using ``-`` as the input and output filename:

.. code-block:: bash

    docker run --rm -i   ocrmypdf <other arguments to ocrmypdf> - - <input.pdf >output.pdf

For convenience, a shell alias can hide the docker command:

.. code-block:: bash

    alias ocrmypdf='docker run --rm -v "$(pwd):/home/docker" ocrmypdf'
    ocrmypdf --version  # runs docker version

Or in the wonderful `fish shell <https://fishshell.com/>`_:

.. code-block:: fish

    alias ocrmypdf 'docker run --rm -v (pwd):/home/docker ocrmypdf'
    funcsave ocrmypdf

.. note::

    The ocrmypdf Docker images are designed for application delivery, to enable use of OCRmyPDF without fussing with dependencies. ``docker run --rm`` argument tells Docker to delete the container after it runs, because each container is only good for a single job. The Docker image is not designed for use as a persistent web service or for use on Amazon EC2 Container Service (AWS ECS).

Installing on Windows
---------------------

Direct installation on Windows is not possible.  `Install the Docker <docker-install_>`_ container as described above.  Ensure that your command prompt can run the docker "hello world" container.

It would probably not be too difficult to run on Windows.  The main reason this has been avoided is the difficulty of packaging and installing the various non-Python dependencies: Tesseract, QPDF, Ghostscript, Leptonica.  Pull requests to add or improve Windows support would be quite welcome.


Running on Windows
~~~~~~~~~~~~~~~~~~

The command line syntax to run ocrmypdf from a command prompt will resemble:

.. code-block:: bat

    docker run -v /c/Users/sampleuser:/home/docker ocrmypdf --skip-text test.pdf output.pdf

where /c/Users/sampleuser is a Unix representation of the Windows path C:\\Users\\sampleuser, assuming a user named "sampleuser" is running ocrmypdf on a file in their home directory, and the files "test.pdf" and "output.pdf" are in the sampleuser folder. The Windows user must have read and write permissions.

`Bash on Ubuntu on Windows <https://github.com/Microsoft/BashOnWindows>`_ should also be a viable route for running the OCRmyPDF Docker container.


Installing with Python pip
--------------------------

OCRmyPDF is delivered by PyPI because it is a convenient way to install the latest version. However, PyPI and ``pip`` cannot address the fact that ``ocrmypdf`` depends on certain non-Python system libraries and programs being instsalled.

For best results, first install `your platform's version <https://repology.org/metapackage/ocrmypdf/versions>`_ of ``ocrmypdf``, using the instructions elsewhere in this document. Then you can use ``pip`` to get the latest version if your platform version is out of date. Chances are that this will satisfy most dependencies.

Use ``ocrmypdf --version`` to confirm what version was installed.

Then you can install the latest OCRmyPDF from the Python wheels. First try:

.. code-block:: bash

    pip3 install --user ocrmypdf

You should then be able to run ``ocrmypdf --version`` and see that the latest version was located.

Since ``pip3 install --user`` does not work correctly on some platforms, notably Ubuntu 16.04 and older, and the Homebrew version of Python, instead use this for a system wide installation:

.. code-block:: bash

    pip3 install ocrmypdf

Requirements for pip and HEAD install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OCRmyPDF currently requires these external programs and libraries to be installed, and must be satisfied using the operating system package manager. ``pip`` cannot provide them.

- Python 3.6 or newer
- Ghostscript 9.15 or newer
- qpdf 8.1.0 or newer
- Tesseract 4.0.0-alpha or newer

As of ocrmypdf 7.2.1, the following versions are recommended:

- Python 3.7
- Ghostscript 9.23 or newer
- qpdf 8.2.1
- Tesseract 4.0.0 or newer
- jbig2enc 0.29 or newer
- pngquant 2.5 or newer
- unpaper 6.1

jbig2enc, pngquant, and unpaper are optional. If missing certain features are disabled. OCRmyPDF will discover them as soon as they are available.

**jbig2enc**, if present, will be used to optimize the encoding of monochrome images.  This can significantly reduce the file size of the output file.  It is not required.  `jbig2enc <https://github.com/agl/jbig2enc>`_ is not generally available for Ubuntu or Debian due to lingering concerns about patent issues, but can easily be built from source. To add JBIG2 encoding, see :ref:`jbig2`.

**pngquant**, if present, is optionally used to optimize the encoding of PNG-style images in PDFs (actually, any that are that losslessly encoded) by lossily quantizing to a smaller color palette. It is only activated then the ``--optimize`` argument is ``2`` or ``3``.

**unpaper**, if present, enables the ``--clean`` and ``--clean-final`` command line options.

These are in addition to the Python packaging dependencies, meaning that unfortunately, the ``pip install`` command cannot satisfy all of them.


Installing HEAD revision from sources
-------------------------------------

If you have ``git`` and Python 3.6 or newer installed, you can install from source. When the ``pip`` installer runs, it will alert you if dependencies are missing.

If you prefer to build every from source, you will need to `build pikepdf from source <https://pikepdf.readthedocs.io/en/latest/installation.html#building-from-source>`_. First ensure you can build and install pikepdf.

To install the HEAD revision from sources in the current Python 3 environment:

.. code-block:: bash

    pip3 install git+https://github.com/jbarlow83/OCRmyPDF.git

Or, to install in `development mode <https://pythonhosted.org/setuptools/setuptools.html#development-mode>`_,  allowing customization of OCRmyPDF, use the ``-e`` flag:

.. code-block:: bash

    pip3 install -e git+https://github.com/jbarlow83/OCRmyPDF.git

You may find it easiest to install in a virtual environment, rather than system-wide:

.. code-block:: bash

    git clone -b master https://github.com/jbarlow83/OCRmyPDF.git
    python3 -m venv
    source venv/bin/activate
    cd OCRmyPDF
    pip3 install .

However, ``ocrmypdf`` will only be accessible on the system PATH
when you activate the virtual environment.

To run the program:

.. code-block:: bash

    ocrmypdf --help

If not yet installed, the script will notify you about dependencies that
need to be installed. The script requires specific versions of the
dependencies. Older version than the ones mentioned in the release notes
are likely not to be compatible to OCRmyPDF.

For development
~~~~~~~~~~~~~~~

To install all of the development and test requirements:

.. code-block:: bash

    git clone -b master https://github.com/jbarlow83/OCRmyPDF.git
    python3 -m venv
    source venv/bin/activate
    cd OCRmyPDF
    pip install -e .
    pip install -r requirements/dev.txt -r requirements/test.txt

To add JBIG2 encoding, see :ref:`jbig2`.
