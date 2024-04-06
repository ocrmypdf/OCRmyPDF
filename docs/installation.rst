.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

===================
Installing OCRmyPDF
===================

.. |latest| image:: https://img.shields.io/pypi/v/ocrmypdf.svg
    :alt: OCRmyPDF latest released version on PyPI

|latest|

The easiest way to install OCRmyPDF is to follow the steps for your operating
system/platform. This version may be out of date, however.

These platforms have one-liner installs:

+-------------------------------+-----------------------------------------+
| Debian, Ubuntu                | ``apt install ocrmypdf``                |
+-------------------------------+-----------------------------------------+
| Windows Subsystem for Linux   | ``apt install ocrmypdf``                |
+-------------------------------+-----------------------------------------+
| Fedora                        | ``dnf install ocrmypdf tesseract-osd``  |
+-------------------------------+-----------------------------------------+
| macOS (Homebrew)              | ``brew install ocrmypdf``               |
+-------------------------------+-----------------------------------------+
| macOS (MacPorts)              | ``port install ocrmypdf``               |
+-------------------------------+-----------------------------------------+
| LinuxBrew                     | ``brew install ocrmypdf``               |
+-------------------------------+-----------------------------------------+
| FreeBSD                       | ``pkg install textproc/py-ocrmypdf``    |
+-------------------------------+-----------------------------------------+
| Conda (WSL, macOS, Linux)     | ``conda install ocrmypdf``              |
+-------------------------------+-----------------------------------------+
| Snap (snapcraft packaging)    | ``snap install ocrmypdf``               |
+-------------------------------+-----------------------------------------+

More detailed procedures are outlined below. If you want to do a manual
install, or install a more recent version than your platform provides, read on.

.. contents:: Platform-specific steps
    :depth: 2
    :local:

Installing on Linux
===================

Debian and Ubuntu 20.04 or newer
--------------------------------

.. |deb-11| image:: https://repology.org/badge/version-for-repo/debian_11/ocrmypdf.svg
    :alt: Debian 11

.. |deb-12| image:: https://repology.org/badge/version-for-repo/debian_12/ocrmypdf.svg
    :alt: Debian 12

.. |deb-unstable| image:: https://repology.org/badge/version-for-repo/debian_unstable/ocrmypdf.svg
    :alt: Debian unstable

.. |ubu-2004| image:: https://repology.org/badge/version-for-repo/ubuntu_20_04/ocrmypdf.svg
    :alt: Ubuntu 20.04 LTS

.. |ubu-2204| image:: https://repology.org/badge/version-for-repo/ubuntu_22_04/ocrmypdf.svg
    :alt: Ubuntu 22.04 LTS

+-----------------------------------------------+
| **OCRmyPDF versions in Debian & Ubuntu**      |
+-----------------------------------------------+
| |latest|                                      |
+-----------------------------------------------+
| |deb-11| |deb-12| |deb-unstable|              |
+-----------------------------------------------+
| |ubu-2004| |ubu-2204|                         |
+-----------------------------------------------+

Users of Debian or Ubuntu may simply

.. code-block:: bash

    apt install ocrmypdf

As indicated in the table above, Debian and Ubuntu releases may lag
behind the latest version. If the version available for your platform is
out of date, you could opt to install the latest version from source.
See `Installing HEAD revision from
sources <#installing-head-revision-from-sources>`__.

For full details on version availability for your platform, check the
`Debian Package Tracker <https://tracker.debian.org/pkg/ocrmypdf>`__ or
`Ubuntu launchpad.net <https://launchpad.net/ocrmypdf>`__.

.. note::

   OCRmyPDF for Debian and Ubuntu currently omit the JBIG2 encoder.
   OCRmyPDF works fine without it but will produce larger output files.
   If you build jbig2enc from source, ocrmypdf will
   automatically detect it (specifically the ``jbig2`` binary) on the
   ``PATH``. To add JBIG2 encoding, see :ref:`jbig2`.

Fedora
------

.. |fedora-38| image:: https://repology.org/badge/version-for-repo/fedora_38/ocrmypdf.svg
    :alt: Fedora 38

.. |fedora-39| image:: https://repology.org/badge/version-for-repo/fedora_39/ocrmypdf.svg
    :alt: Fedora 39

.. |fedora-rawhide| image:: https://repology.org/badge/version-for-repo/fedora_rawhide/ocrmypdf.svg
    :alt: Fedore Rawhide

+-----------------------------------------------+
| **OCRmyPDF version**                          |
+-----------------------------------------------+
| |latest|                                      |
+-----------------------------------------------+
| |fedora-38| |fedora-39| |fedora-rawhide|      |
+-----------------------------------------------+

Users of Fedora may simply

.. code-block:: bash

    dnf install ocrmypdf tesseract-osd

For full details on version availability, check the `Fedora Package
Tracker <https://packages.fedoraproject.org/pkgs/ocrmypdf/ocrmypdf/>`__.

If the version available for your platform is out of date, you could opt
to install the latest version from source. See `Installing HEAD revision
from sources <#installing-head-revision-from-sources>`__.

.. note::

   OCRmyPDF for Fedora currently omits the JBIG2 encoder due to patent
   issues. OCRmyPDF works fine without it but will produce larger output
   files. If you build jbig2enc from source, ocrmypdf 7.0.0 and later
   will automatically detect it on the ``PATH``. To add JBIG2 encoding,
   see :ref:`Installing the JBIG2 encoder <jbig2>`.

.. _ubuntu-lts-latest:

RHEL 9
------

Prepare the environment by getting Python 3.11:

.. code-block:: bash

    dnf install python3.11 python3.11-pip

Then, follow `Requirements for pip and HEAD install <#requirements-for-pip-and-head-install>`__ to instal dependencies:

.. code-block:: bash

    dnf install ghostscript tesseract

and build ocrmypdf in virtual environment:

.. code-block:: bash

    python3.11 -m venv .venv

To add JBIG2 encoding, see :ref:`Installing the JBIG2 encoder <jbig2>`.

Note Fedora packages for language data haven't been branched for RHEL/EPEL, but you can get traineddata files directly from `tesseract
<https://github.com/tesseract-ocr/tessdata/>`__ and place them in ``/usr/share/tesseract/tessdata``.

Installing the latest version on Ubuntu 22.04 LTS
-------------------------------------------------

Ubuntu 22.04 includes ocrmypdf 13.4.0 - you can install that with
``apt install ocrmypdf``. To install a more recent version for the current
user, follow these steps:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get -y install ocrmypdf python3-pip

    pip install --user --upgrade ocrmypdf

If you get the message ``WARNING: The script ocrmypdf is installed in
'/home/$USER/.local/bin' which is not on PATH.``, you may need to re-login
or open a new shell, or manually adjust your PATH.

To add JBIG2 encoding, see :ref:`jbig2`.

Ubuntu 20.04 LTS
----------------

Ubuntu 20.04 includes ocrmypdf 9.6.0 - you can install that with ``apt``. The
most convenient way to install recent OCRmyPDF on older Ubuntu is to use
Homebrew on Linux (Linuxbrew).

.. code-block:: bash

    brew install ocrmypdf

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
<https://archlinux.org/packages/core/any/base-devel/>`__. This includes the
standard tooling needed to build packages, such as a compiler and binary tools.

.. code-block:: bash

   sudo pacman -S base-devel

Now you are ready to install the OCRmyPDF package.

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
    using the same series of steps as for the installation OCRmyPDF AUR
    package. Alternatively, it may be built manually from source following the
    instructions in :ref:`Installing the JBIG2 encoder <jbig2>`.  If JBIG2 is
    installed, OCRmyPDF 7.0.0 and later will automatically detect it.

Alpine Linux
------------

.. image:: https://repology.org/badge/version-for-repo/alpine_edge/ocrmypdf.svg
    :alt: Alpine Linux
    :target: https://repology.org/metapackage/ocrmypdf

To install OCRmyPDF for Alpine Linux:

.. code-block:: bash

    apk add ocrmypdf

Gentoo Linux
------------

.. image:: https://repology.org/badge/version-for-repo/gentoo_ovl_guru/ocrmypdf.svg
    :alt: Gentoo Linux
    :target: https://repology.org/metapackage/ocrmypdf

To install OCRmyPDF on Gentoo Linux, use the following commands:

.. code-block:: bash

    eselect repository enable guru
    emaint sync --repo guru
    emerge --ask app-text/OCRmyPDF

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
    :target: https://formulae.brew.sh/formula/ocrmypdf

OCRmyPDF is now a standard `Homebrew <https://brew.sh>`__ formula. To
install on macOS:

.. code-block:: bash

    brew install ocrmypdf

This will include only the English language pack. If you need other
languages you can optionally install them all:

.. code-block:: bash

    brew install tesseract-lang  # Optional: Install all language packs

MacPorts
--------

.. image:: https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fports.macports.org%2Fapi%2Fv1%2Fports%2Focrmypdf%2F%3Fformat%3Djson&query=version&label=MacPorts
   :alt: Macports Version Information
   :target: https://ports.macports.org/port/ocrmypdf

OCRmyPDF is includes in MacPorts:

.. code-block:: bash

    sudo port install ocrmypdf

Note that while this will install tesseract you will need to install
the appropriate tesseract `language ports <https://ports.macports.org/search/?selected_facets=categories_exact%3Atextproc&installed_file=&q=tesseract&name=on>`__. 

Manual installation on macOS
----------------------------

These instructions probably work on all macOS supported by Homebrew, and are
for installing a more current version of OCRmyPDF than is available from
Homebrew. Note that the Homebrew versions usually track the release versions
fairly closely.

If it's not already present, `install Homebrew <http://brew.sh/>`__.

Update Homebrew:

.. code-block:: bash

    brew update

Install or upgrade the required Homebrew packages, if any are missing.
To do this, use ``brew edit ocrmypdf`` to obtain a recent list of Homebrew
dependencies. You could also check the ``.workflows/build.yml``.

This will include the English, French, German and Spanish language
packs. If you need other languages you can optionally install them all:

.. _macos-all-languages:

   .. code-block:: bash

    brew install tesseract-lang  # Option 2: for all language packs

Update the homebrew pip:

.. code-block:: bash

    pip install --upgrade pip

You can then install OCRmyPDF from PyPI for the current user:

.. code-block:: bash

    pip install --user ocrmypdf

The command line program should now be available:

.. code-block:: bash

    ocrmypdf --help

Installing on Windows
=====================

Native Windows
--------------

.. note::

    Administrator privileges will be required for some of these steps.

You must install the following for Windows:

* Python 64-bit
* Tesseract 64-bit
* Ghostscript 64-bit

Using the `winget <https://docs.microsoft.com/en-us/windows/package-manager/winget/>`_
package manager:

* ``winget install -e --id Python.Python.3.11``
* ``winget install -e --id UB-Mannheim.TesseractOCR``

You will need to install Ghostscript manually, `since it does not support automated
installs anymore <https://artifex.com/news/ghostscript-10.01.0-disabling-silent-install-option>`_.

* `Ghostscript download page <https://ghostscript.com/releases/gsdnld.html>`_.`

(Or alternately, using the `Chocolatey <https://chocolatey.org/>`_ package manager, install
the following when running in an Administrator command prompt):

* ``choco install python3``
* ``choco install --pre tesseract``
* ``choco install pngquant`` (optional)

Either set of commands will install the required software. At the moment there is no
single command to install Windows.

You may then use ``pip`` to install ocrmypdf. (This can performed by a user or
Administrator.):

* ``python3 -m pip install ocrmypdf``

OCRmyPDF will check the Windows Registry and standard locations in your Program Files
for third party software it needs (specifically, Tesseract and Ghostscript). To
override the versions OCRmyPDF selects, you can modify the ``PATH`` environment
variable. `Follow these directions <https://www.computerhope.com/issues/ch000549.htm#dospath>`_
to change the PATH.

.. warning::

    As of early 2021, users have reported problems with the Microsoft Store version of
    Python and OCRmyPDF. These issues affect many other third party Python packages.
    Please download Python from Python.org or a package manager instead of the
    Microsoft Store version.

.. warning::

    32-bit Windows is not supported.

Windows Subsystem for Linux
---------------------------

#. Install Ubuntu 22.04 for Windows Subsystem for Linux, if not already installed.
#. Follow the procedure to install :ref:`OCRmyPDF on Ubuntu 22.04 <ubuntu-lts-latest>`.
#. Open the Windows command prompt and create a symlink:

.. code-block:: powershell

    wsl sudo ln -s  /home/$USER/.local/bin/ocrmypdf /usr/local/bin/ocrmypdf

Then confirm that the expected version from PyPI (|latest|) is installed:

.. code-block:: powershell

    wsl ocrmypdf --version

You can then run OCRmyPDF in the Windows command prompt or Powershell, prefixing
``wsl``, and call it from Windows programs or batch files.

Cygwin64
--------

First install the the following prerequisite Cygwin packages using ``setup-x86_64.exe``::

    python310 (or later)
    python3?-devel
    python3?-pip
    python3?-lxml
    python3?-imaging

       (where 3? means match the version of python3 you installed)

    gcc-g++
    ghostscript
    libexempi3
    libexempi-devel
    libffi6
    libffi-devel
    pngquant
    qpdf
    libqpdf-devel
    tesseract-ocr
    tesseract-ocr-devel

Then open a Cygwin terminal (i.e. ``mintty``), run the following commands. Note
that if you are using the version of ``pip`` that was installed with the Cygwin
Python package, the command name will be ``pip3``.  If you have since updated
``pip`` (with, for instance ``pip3 install --upgrade pip``) the the command is
likely just ``pip`` instead of ``pip3``:

.. code-block:: bash

    pip3 install wheel
    pip3 install ocrmypdf

The optional dependency "unpaper" that is currently not available under Cygwin.
Without it, certain options such as ``--clean`` will produce an error message.
However, the OCR-to-text-layer functionality is available.

Docker
------

You can also :ref:`Install the Docker <docker>` container on Windows. Ensure that
your command prompt can run the docker "hello world" container.

Installing on FreeBSD
=====================

.. image:: https://repology.org/badge/version-for-repo/freebsd/ocrmypdf.svg
    :alt: FreeBSD
    :target: https://repology.org/project/ocrmypdf/versions

.. code-block:: bash

    pkg install textproc/py-ocrmypdf

To install a more recent version, you could attempt to first install the system
version with ``pkg``, then use ``pip install --user ocrmypdf``.

Installing the Docker image
===========================

For some users, installing the Docker image will be easier than
installing all of OCRmyPDF's dependencies.

See :ref:`docker` for more information.

Installing with Python pip
==========================

OCRmyPDF is delivered by PyPI because it is a convenient way to install
the latest version. However, PyPI and ``pip`` cannot address the fact
that ``ocrmypdf`` depends on certain non-Python system libraries and
programs being installed.

For best results, first install `your platform's
version <https://repology.org/metapackage/ocrmypdf/versions>`__ of
``ocrmypdf``, using the instructions elsewhere in this document. Then
you can use ``pip`` to get the latest version if your platform version
is out of date. Chances are that this will satisfy most dependencies.

Use ``ocrmypdf --version`` to confirm what version was installed.

Then you can install the latest OCRmyPDF from the Python wheels. First
try:

.. code-block:: bash

    pip install --user ocrmypdf

(If the message appears ``Requirement already satisfied: ocrmypdf in...``,
you will need to use ``pip install --user --upgrade ocrmypdf``.)

You should then be able to run ``ocrmypdf --version`` and see that the
latest version was located.

Installing with pipx
====================

Some users may prefer pipx. As with the method above, you will need to
satisfy all non-Python dependencies. Then if pipx is installed, you
can use

.. code-block:: bash

    pipx run ocrmypdf

(If not installed, pipx will install first.)

Requirements for pip and HEAD install
-------------------------------------

OCRmyPDF currently requires these external programs and libraries to be
installed, and must be satisfied using the operating system package
manager. ``pip`` cannot provide them.

The following versions are required:

-  Python 3.10 or newer
-  Ghostscript 9.54 or newer
-  Tesseract 4.1.1 or newer
-  jbig2enc 0.29 or newer
-  pngquant 2.5 or newer
-  unpaper 6.1

We recommend 64-bit versions of all software. (32-bit versions are not
supported, although on Linux, they may still work.)

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

If you have ``git`` and Python 3.10 or newer installed, you can install
from source. When the ``pip`` installer runs, it will alert you if
dependencies are missing.

If you prefer to build every from source, you will need to `build
pikepdf from
source <https://pikepdf.readthedocs.io/en/latest/installation.html#building-from-source>`__.
First ensure you can build and install pikepdf.

To install the HEAD revision from sources in the current Python 3
environment:

.. code-block:: bash

    pip install git+https://github.com/ocrmypdf/OCRmyPDF.git

Or, to install in `development
mode <https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#working-in-development-mode>`__,
allowing customization of OCRmyPDF, use the ``-e`` flag:

.. code-block:: bash

    pip install -e git+https://github.com/ocrmypdf/OCRmyPDF.git

You may find it easiest to install in a virtual environment, rather than
system-wide:

.. code-block:: bash

    git clone -b main https://github.com/ocrmypdf/OCRmyPDF.git
    python3 -m venv .venv
    source .venv/bin/activate
    cd OCRmyPDF
    pip install .

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

    git clone -b main https://github.com/ocrmypdf/OCRmyPDF.git
    python -m .venv
    source .venv/bin/activate
    cd OCRmyPDF
    pip install -e .[test]

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

Note on 32-bit support
======================

Many Python libraries no longer provide 32-bit binary wheels for Linux. This
includes many of the libraries that OCRmyPDF depends on, such as
Pillow. The easiest way to express this to end users is to say we don't
support 32-bit Linux.

However, if your Linux distribution still supports 32-bit binaries, you
can still install and use OCRmyPDF. A warning message will appear.
In practice, OCRmyPDF may need more than 32-bit memory space to run when
large documents are processed, so there are practical limitations to what
users can accomplish with it. Still, for the common use case of an 32-bit
ARM NAS or Raspberry Pi processing small documents, it should work.
