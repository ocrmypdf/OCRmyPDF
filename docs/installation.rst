===================
Installing OCRmyPDF
===================

.. |latest| image:: https://img.shields.io/pypi/v/ocrmypdf.svg
    :alt: OCRmyPDF latest released version on PyPI

|latest|

The easiest way to install OCRmyPDF is to follow the steps for your operating
system/platform, although sometimes this version may be out of date. This
installation guide provides information allowing you to compare the current
version to the one provided by your platform.

If you want to use the latest version of OCRmyPDF and all of its optional
dependencies, the easiest way to get that is install the Homebrew package. Homebrew
is best known as a macOS package manger, but also works for
`Linux and Windows Subsystem for Linux <https://docs.brew.sh/Homebrew-on-Linux>`__.
After Homebrew is installed, simply run ``brew install ocrmypdf``.

You can also use the more detailed procedures here to manually install OCRmyPDF
from source or with the ``pip`` package manager for binary wheels. The reason
for these varied steps is that OCRmyPDF requires third-party executables that are
not part of Python.

.. contents:: Platform-specific steps
    :depth: 2
    :local:

Installing on Linux
===================

Debian and Ubuntu 18.04 or newer
--------------------------------

.. |deb-stable| image:: https://repology.org/badge/version-for-repo/debian_stable/ocrmypdf.svg
    :alt: Debian 9 stable ("stretch")

.. |deb-testing| image:: https://repology.org/badge/version-for-repo/debian_testing/ocrmypdf.svg
    :alt: Debian 10 testing ("buster")

.. |deb-unstable| image:: https://repology.org/badge/version-for-repo/debian_unstable/ocrmypdf.svg
    :alt: Debian unstable

.. |ubu-1804| image:: https://repology.org/badge/version-for-repo/ubuntu_18_04/ocrmypdf.svg
    :alt: Ubuntu 18.04 LTS

.. |ubu-1810| image:: https://repology.org/badge/version-for-repo/ubuntu_18_10/ocrmypdf.svg
    :alt: Ubuntu 18.10

.. |ubu-1904| image:: https://repology.org/badge/version-for-repo/ubuntu_19_04/ocrmypdf.svg
    :alt: Ubuntu 19.04

.. |ubu-1910| image:: https://repology.org/badge/version-for-repo/ubuntu_19_10/ocrmypdf.svg
    :alt: Ubuntu 19.10

+-----------------------------------------------+
| **OCRmyPDF versions in Debian & Ubuntu**      |
+-----------------------------------------------+
| |latest|                                      |
+-----------------------------------------------+
| |deb-stable| |deb-testing| |deb-unstable|     |
+-----------------------------------------------+
| |ubu-1804| |ubu-1810| |ubu-1904| |ubu-1910|   |
+-----------------------------------------------+

Users of Debian 9 ("stretch") or later or Ubuntu 18.04 or later, including users
of Windows Subsystem for Linux, may simply

.. code-block:: bash

    apt-get install ocrmypdf

As indicated in the table above, Debian and Ubuntu releases may lag
behind the latest version. If the version available for your platform is
out of date, you could opt to install the latest version from source.
See `Installing HEAD revision from
sources <#installing-head-revision-from-sources>`__. Ubuntu 16.10 to 17.10
inclusive also had ocrmypdf, but these versions are end of life.

For full details on version availability for your platform, check the
`Debian Package Tracker <https://tracker.debian.org/pkg/ocrmypdf>`__ or
`Ubuntu launchpad.net <https://launchpad.net/ocrmypdf>`__.

.. note::

   OCRmyPDF for Debian and Ubuntu currently omit the JBIG2 encoder.
   OCRmyPDF works fine without it but will produce larger output files.
   If you build jbig2enc from source, ocrmypdf 7.0.0 and later will
   automatically detect it (specifically the ``jbig2`` binary) on the
   ``PATH``. To add JBIG2 encoding, see :ref:`jbig2`.

Fedora 29 or newer
------------------

.. |fedora-29| image:: https://repology.org/badge/version-for-repo/fedora_29/ocrmypdf.svg
    :alt: Fedora 29

.. |fedora-30| image:: https://repology.org/badge/version-for-repo/fedora_30/ocrmypdf.svg
    :alt: Fedora 30

.. |fedora-rawhide| image:: https://repology.org/badge/version-for-repo/fedora_rawhide/ocrmypdf.svg
    :alt: Fedore Rawhide

+-----------------------------------------------+
| **OCRmyPDF version**                          |
+-----------------------------------------------+
| |latest|                                      |
+-----------------------------------------------+
| |fedora-29| |fedora-30| |fedora-rawhide|      |
+-----------------------------------------------+

Users of Fedora 29 or later may simply

.. code-block:: bash

    dnf install ocrmypdf

For full details on version availability, check the `Fedora Package
Tracker <https://apps.fedoraproject.org/packages/ocrmypdf>`__.

If the version available for your platform is out of date, you could opt
to install the latest version from source. See `Installing HEAD revision
from sources <#installing-head-revision-from-sources>`__.

.. note::

   OCRmyPDF for Fedora currently omits the JBIG2 encoder due to patent
   issues. OCRmyPDF works fine without it but will produce larger output
   files. If you build jbig2enc from source, ocrmypdf 7.0.0 and later
   will automatically detect it on the ``PATH``. To add JBIG2 encoding,
   see `Installing the JBIG2 encoder <jbig2>`__.

.. _ubuntu-lts-latest:

Installing the latest version on Ubuntu 18.04 LTS
-------------------------------------------------

Ubuntu 18.04 includes ocrmypdf 6.1.2 - you can install that with ``apt``, but
it is quite old now. To install a more recent version, first install several
system dependencies:

.. code-block:: bash

    sudo apt-get -y update
    sudo apt-get -y install \
        ghostscript \
        icc-profiles-free \
        liblept5 \
        libxml2 \
        pngquant \
        python3-cffi \
        python3-distutils \
        python3-pkg-resources \
        python3-reportlab \
        qpdf \
        tesseract-ocr \
        zlib1g

We will need a newer version of ``pip`` then was available for Ubuntu 18.04:

.. code-block:: bash

    wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

Then install the most recent ocrmypdf for the local user and set the
user's ``PATH`` to check for the user's Python packages.

.. code-block:: bash

    export PATH=$HOME/.local/bin:$PATH
    python3 -m pip install --user ocrmypdf

To add JBIG2 encoding, see :ref:`jbig2`.

Ubuntu 16.04 LTS
----------------

No package is available for Ubuntu 16.04. OCRmyPDF 8.0 and newer require
Python 3.6. Ubuntu 16.04 ships Python 3.5, but you can install Python
3.6 on it. Or, you can skip Python 3.6 and install OCRmyPDF 7.x or older
- for that procedure, please see the installation documentation for the
version of OCRmyPDF you plan to use.

**Install system packages for OCRmyPDF**

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install -y software-properties-common python-software-properties
    sudo add-apt-repository -y \
        ppa:jonathonf/python-3.6 \
        ppa:alex-p/tesseract-ocr
    sudo apt-get update
    sudo apt-get install -y \
        ghostscript \
        libexempi3 \
        libffi6 \
        pngquant \
        python3.6 \
        qpdf \
        tesseract-ocr \
        unpaper

This will install a Python 3.6 binary at ``/usr/bin/python3.6``
alongside the system's Python 3.5. Do not remove the system Python. This
will also install Tesseract 4.0 from a PPA, since the version available
in Ubuntu 16.04 is too old for OCRmyPDF.

Now install pip for Python 3.6. This will install the Python 3.6 version
of ``pip`` at ``/usr/local/bin/pip``.

.. code-block:: bash

    curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6

**Install OCRmyPDF**

OCRmyPDF requires the locale to be set for UTF-8. **On some minimal
Ubuntu installations**, such as the Ubuntu 16.04 Docker images it may be
necessary to set the locale.

.. code-block:: bash

    # Optional: Only need to set these if they are not already set
    export LC_ALL=C.UTF-8
    export LANG=C.UTF-8

Now install OCRmyPDF for the current user, and ensure that the ``PATH``
environment variable contains ``$HOME/.local/bin``.

.. code-block:: bash

    export PATH=$HOME/.local/bin:$PATH
    pip3 install --user ocrmypdf

To add JBIG2 encoding, see :ref:`jbig2`.

Ubuntu 14.04 LTS
----------------

Installing on Ubuntu 14.04 LTS (trusty) is more difficult than some
other options, because of its age. Several backports are required. For
explanations of some steps of this procedure, see the similar steps for
Ubuntu 16.04.

Install system dependencies:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install \
        software-properties-common python-software-properties \
        zlib1g-dev \
        libexempi3 \
        libjpeg-dev \
        libffi-dev \
        pngquant \
        qpdf

We will need backports of Ghostscript 9.16, libav-11 (for unpaper 6.1),
Tesseract 4.00 (alpha), and Python 3.6. This will replace Ghostscript
and Tesseract 3.x on your system. Python 3.6 will be installed alongside
the system Python 3.4.

If you prefer to not modify your system in this matter, consider using a
Docker container.

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

The optional dependency ``unpaper`` is only available at 0.4.2 in Ubuntu 14.04,
and no backports are available. Previously the author maintained a backported
.deb package for unpaper 6.1, but since Ubuntu 14.04 is now end of life, this is
not supported. As such, ``unpaper`` is not available on Ubuntu 14.04 or must by
compiled by hand.

To add JBIG2 encoding, see :ref:`jbig2`.

Arch Linux (AUR)
----------------

.. image:: https://repology.org/badge/version-for-repo/aur/ocrmypdf.svg
    :alt: ArchLinux
    :target: https://repology.org/metapackage/ocrmypdf

There is an `Arch User Repository (AUR) package for OCRmyPDF
<https://aur.archlinux.org/packages/ocrmypdf/>`__.

Installing AUR packages as root is not allowed, so you must first `setup a
non-root user
<https://wiki.archlinux.org/index.php/Users_and_groups#User_management>`__ and
`configure sudo <https://wiki.archlinux.org/index.php/Sudo#Configuration>`__.
The standard Docker image, ``archlinux/base:latest``, does **not** have a
non-root user configured, so users of that image must follow these guides. If
you are using a VM image, such as `the official Vagrant image
<https://app.vagrantup.com/archlinux/boxes/archlinux>`__, this work may already
be completed for you.

Next you should install the `base-devel package group
<https://www.archlinux.org/groups/x86_64/base-devel/>`__. This includes the
standard tooling needed to build packages, such as a compiler and binary tools.

.. code-block:: bash

   sudo pacman -S base-devel

The OCRmyPDF package depends on `the python-pdfminer.six AUR package
<https://aur.archlinux.org/packages/python-pdfminer.six/>`__.  Dependencies on
AUR packages are not automatically resolved, so this package must be manually
installed first.

.. code-block:: bash

   curl -O https://aur.archlinux.org/cgit/aur.git/snapshot/python-pdfminer.six.tar.gz
   tar xvzf python-pdfminer.six.tar.gz
   cd python-pdfminer.six
   makepkg -sri

With that complete you can then repeat the same series of steps for the
OCRmyPDF package.

.. code-block:: bash

   curl -O https://aur.archlinux.org/cgit/aur.git/snapshot/ocrmypdf.tar.gz
   tar xvzf ocrmypdf.tar.gz
   cd ocrmypdf
   makepkg -sri

At this point you will have a working install of OCRmyPDF, but the Tesseract
install won’t include any OCR language data. You can install `the
tesseract-data package group
<https://www.archlinux.org/groups/any/tesseract-data/>`__ to add all supported
languages, or use that package listing to identify the appropriate package for
your desired language.

.. code-block:: bash

   sudo pacman -S tesseract-data-eng

As an alternative to this manual procedure, consider using an `AUR helper
<https://wiki.archlinux.org/index.php/AUR_helpers>`__. Such a tool will
automatically fetch, build and install the AUR package, resolve dependencies
(including dependencies on AUR packages), and ease the upgrade procedure.

If you have any difficulties with installation, check the repository package
page.

.. note::

    The OCRmyPDF AUR package currently omits the JBIG2 encoder. OCRmyPDF works
    fine without it but will produce larger output files. The encoder is
    available from `the jbig2enc-git AUR package
    <https://aur.archlinux.org/packages/jbig2enc-git/>`__ and may be installed
    using the same series of steps as for the installation of the pdfminer.six
    and OCRmyPDF AUR packages. Alternatively, it may be built manually from
    source following the instructions in `Installing the JBIG2 encoder
    <jbig2>`__.  If JBIG2 is installed, OCRmyPDF 7.0.0 and later will
    automatically detect it.

Alpine Linux
------------

.. image:: https://repology.org/badge/version-for-repo/alpine_edge/ocrmypdf.svg
    :alt: Alpine Linux
    :target: https://repology.org/metapackage/ocrmypdf

To install OCRmyPDF for Alpine Linux:

.. code-block:: bash

    apk add ocrmypdf

Other Linux packages
--------------------

See the
`Repology <https://repology.org/metapackage/ocrmypdf/versions>`__ page.

In general, first install the OCRmyPDF package for your system, then
optionally use the procedure `Installing with Python
pip <#installing-with-python-pip>`__ to install a more recent version.

Installing on macOS
===================

Homebrew
--------

.. image:: https://img.shields.io/homebrew/v/ocrmypdf.svg
    :alt: homebrew
    :target: http://brewformulas.org/Ocrmypdf

OCRmyPDF is now a standard `Homebrew <https://brew.sh>`__ formula. To
install on macOS:

.. code-block:: bash

    brew install ocrmypdf

This will include only the English language pack. If you need other
languages you can optionally install them all:

.. code-block:: bash

    brew install tesseract-lang  # Optional: Install all language packs

.. note::

   Users who previously installed OCRmyPDF on macOS using
   ``pip install ocrmypdf`` should remove the pip version
   (``pip3 uninstall ocrmypdf``) before switching to the Homebrew
   version.

.. note::

   Users who previously installed OCRmyPDF from the private tap should
   switch to the mainline version (``brew untap jbarlow83/ocrmypdf``)
   and install from there.

Manual installation on macOS
----------------------------

These instructions probably work on all macOS supported by Homebrew.

If it's not already present, `install Homebrew <http://brew.sh/>`__.

Update Homebrew:

.. code-block:: bash

    brew update

Install or upgrade the required Homebrew packages, if any are missing.
To do this, download the ``Brewfile`` that lists all of the dependencies
to the current directory, and run ``brew bundle`` to process them
(installing or upgrading as needed). ``Brewfile`` is a plain text file.

.. code-block:: bash

    wget https://github.com/jbarlow83/OCRmyPDF/raw/master/.travis/Brewfile
    brew bundle

This will include the English, French, German and Spanish language
packs. If you need other languages you can optionally install them all:

.. _macos-all-languages:

   .. code-block:: bash

    brew install tesseract-lang  # Option 2: for all language packs

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

Installing on FreeBSD
=====================

.. image:: https://repology.org/badge/version-for-repo/freebsd/python:ocrmypdf.svg
    :alt: FreeBSD
    :target: https://repology.org/project/python:ocrmypdf/versions

FreeBSD 11.3, 12.0, 12.1-RELEASE and 13.0-CURRENT are supported. Other
versions likely work but have not been tested.

.. code-block:: bash

    pkg install py37-ocrmypdf

To install a more recent version, you could attempt to first install the system
version with ``pkg``, then use ``pip install --user ocrmypdf``.

Installing the Docker image
===========================

For some users, installing the Docker image will be easier than
installing all of OCRmyPDF's dependencies.

See `OCRmyPDF Docker Image <docker>`__ for more information.

Installing on Windows
=====================

.. warning::

    Native Windows support is new. Consider it "beta" software. Some
    functionality is missing or may be more difficult to enable. If you need a
    production-ready solution, use Windows Subsystem for Linux or a Docker
    image.

.. note::

    Administrator privileges will be required for some of these steps.

You must install the following for Windows:

* Python 3.7 (64-bit)
* Tesseract 4.0 or later
* Ghostscript 9.50 or later

You can install these with the Chocolatey package manager:

* ``choco install python3``
* ``choco install --pre tesseract``
* ``choco install ghostscript``

Also consider adding:

* ``choco install pngquant``

Windows 10 64-bit and 64-bit versions of applications are recommended. Earlier
versions of Windows and 32-bit versions of these programs are not tested, and not
supported at this time.

OCRmyPDF will check for Tesseract-OCR and Ghostscript in your Program Files folder.
If they are in some other location, you may need to modify the ``PATH``
environment variable so Tesseract, Ghostscript, and other any optional executables can
be found. You can enter it in the command line or
`follow these directions <https://www.computerhope.com/issues/ch000549.htm#dospath>`_
to make the change persistent and system-wide.

You may then use pip to install ocrmypdf:

* ``pip install ocrmypdf``

Installing on Windows Subsystem for Linux
=========================================

#. Install Ubuntu 18.04 for Windows Subsystem for Linux, if not already installed.
#. Follow the procedure to install :ref:`OCRmyPDF on Ubuntu 18.04 <ubuntu-lts-latest>`.
#. Open the Windows command prompt and create a symlink:

.. code-block:: powershell

    wsl sudo ln -s  /home/user/.local/bin/ocrmypdf /usr/local/bin/ocrmypdf

Then confirm that the expected version from PyPI (|latest|) is installed:

.. code-block:: powershell

    wsl ocrmypdf --version

You can then run OCRmyPDF in the Windows command prompt or Powershell, prefixing
``wsl``, and call it from Windows programs or batch files.

Docker
^^^^^^

You can also :ref:`Install the Docker <docker-install>` container on Windows. Ensure that
your command prompt can run the docker "hello world" container.

Installing with Python pip
==========================

OCRmyPDF is delivered by PyPI because it is a convenient way to install
the latest version. However, PyPI and ``pip`` cannot address the fact
that ``ocrmypdf`` depends on certain non-Python system libraries and
programs being instsalled.

For best results, first install `your platform's
version <https://repology.org/metapackage/ocrmypdf/versions>`__ of
``ocrmypdf``, using the instructions elsewhere in this document. Then
you can use ``pip`` to get the latest version if your platform version
is out of date. Chances are that this will satisfy most dependencies.

Use ``ocrmypdf --version`` to confirm what version was installed.

Then you can install the latest OCRmyPDF from the Python wheels. First
try:

.. code-block:: bash

    pip3 install --user ocrmypdf

You should then be able to run ``ocrmypdf --version`` and see that the
latest version was located.

Since ``pip3 install --user`` does not work correctly on some platforms,
notably Ubuntu 16.04 and older, and the Homebrew version of Python,
instead use this for a system wide installation:

.. code-block:: bash

    pip3 install ocrmypdf

Requirements for pip and HEAD install
-------------------------------------

OCRmyPDF currently requires these external programs and libraries to be
installed, and must be satisfied using the operating system package
manager. ``pip`` cannot provide them.

-  Python 3.6 or newer
-  Ghostscript 9.15 or newer
-  qpdf 8.1.0 or newer
-  Tesseract 4.0.0-beta or newer

As of ocrmypdf 7.2.1, the following versions are recommended:

-  Python 3.7 or 3.8
-  Ghostscript 9.23 or newer
-  qpdf 8.2.1
-  Tesseract 4.0.0 or newer
-  jbig2enc 0.29 or newer
-  pngquant 2.5 or newer
-  unpaper 6.1

jbig2enc, pngquant, and unpaper are optional. If missing certain
features are disabled. OCRmyPDF will discover them as soon as they are
available.

**jbig2enc**, if present, will be used to optimize the encoding of
monochrome images. This can significantly reduce the file size of the
output file. It is not required.
`jbig2enc <https://github.com/agl/jbig2enc>`__ is not generally
available for Ubuntu or Debian due to lingering concerns about patent
issues, but can easily be built from source. To add JBIG2 encoding, see
:ref:`jbig2`.

**pngquant**, if present, is optionally used to optimize the encoding of
PNG-style images in PDFs (actually, any that are that losslessly
encoded) by lossily quantizing to a smaller color palette. It is only
activated then the ``--optimize`` argument is ``2`` or ``3``.

**unpaper**, if present, enables the ``--clean`` and ``--clean-final``
command line options.

These are in addition to the Python packaging dependencies, meaning that
unfortunately, the ``pip install`` command cannot satisfy all of them.

Installing HEAD revision from sources
=====================================

If you have ``git`` and Python 3.6 or newer installed, you can install
from source. When the ``pip`` installer runs, it will alert you if
dependencies are missing.

If you prefer to build every from source, you will need to `build
pikepdf from
source <https://pikepdf.readthedocs.io/en/latest/installation.html#building-from-source>`__.
First ensure you can build and install pikepdf.

To install the HEAD revision from sources in the current Python 3
environment:

.. code-block:: bash

    pip3 install git+https://github.com/jbarlow83/OCRmyPDF.git

Or, to install in `development
mode <https://pythonhosted.org/setuptools/setuptools.html#development-mode>`__,
allowing customization of OCRmyPDF, use the ``-e`` flag:

.. code-block:: bash

    pip3 install -e git+https://github.com/jbarlow83/OCRmyPDF.git

You may find it easiest to install in a virtual environment, rather than
system-wide:

.. code-block:: bash

    git clone -b master https://github.com/jbarlow83/OCRmyPDF.git
    python3 -m venv
    source venv/bin/activate
    cd OCRmyPDF
    pip3 install .

However, ``ocrmypdf`` will only be accessible on the system PATH when
you activate the virtual environment.

To run the program:

.. code-block:: bash

    ocrmypdf --help

If not yet installed, the script will notify you about dependencies that
need to be installed. The script requires specific versions of the
dependencies. Older version than the ones mentioned in the release notes
are likely not to be compatible to OCRmyPDF.

For development
---------------

To install all of the development and test requirements:

.. code-block:: bash

    git clone -b master https://github.com/jbarlow83/OCRmyPDF.git
    python3 -m venv
    source venv/bin/activate
    cd OCRmyPDF
    pip install -e .
    pip install -r requirements/dev.txt -r requirements/test.txt

To add JBIG2 encoding, see :ref:`jbig2`.

Shell completions
=================

Completions for ``bash`` and ``fish`` are available in the project's
``misc/completion`` folder. The ``bash`` completions are likely ``zsh``
compatible but this has not been confirmed. Package maintainers, please
install these at the appropriate locations for your system.

To manually install the ``bash`` completion, copy
``misc/completion/ocrmypdf.bash`` to ``/etc/bash_completion.d/ocrmypdf``
(rename the file).

To manually install the ``fish`` completion, copy
``misc/completion/ocrmypdf.fish`` to
``~/.config/fish/completions/ocrmypdf.fish``.
