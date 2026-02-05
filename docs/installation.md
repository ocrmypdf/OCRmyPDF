---
myst:
  substitutions:
    deb_12: |-
      :::{image} https://repology.org/badge/version-for-repo/debian_12/ocrmypdf.svg
      :alt: Debian 12
      :::
    deb_13: |-
      :::{image} https://repology.org/badge/version-for-repo/debian_13/ocrmypdf.svg
      :alt: Debian 13
      :::
    deb_unstable: |-
      :::{image} https://repology.org/badge/version-for-repo/debian_unstable/ocrmypdf.svg
      :alt: Debian unstable
      :::
    fedora_40: |-
      :::{image} https://repology.org/badge/version-for-repo/fedora_40/ocrmypdf.svg
      :alt: Fedora 40
      :::
    fedora_41: |-
      :::{image} https://repology.org/badge/version-for-repo/fedora_41/ocrmypdf.svg
      :alt: Fedora 41
      :::
    fedora_rawhide: |-
      :::{image} https://repology.org/badge/version-for-repo/fedora_rawhide/ocrmypdf.svg
      :alt: Fedora Rawhide
      :::
    latest: |-
      :::{image} https://img.shields.io/pypi/v/ocrmypdf.svg
      :alt: OCRmyPDF latest released version on PyPI
      :::
    ubu_2204: |-
      :::{image} https://repology.org/badge/version-for-repo/ubuntu_22_04/ocrmypdf.svg
      :alt: Ubuntu 22.04 LTS
      :::
    ubu_2404: |-
      :::{image} https://repology.org/badge/version-for-repo/ubuntu_24_04/ocrmypdf.svg
      :alt: Ubuntu 24.04 LTS
      :::
---

% SPDX-FileCopyrightText: 2022 James R. Barlow
% SPDX-License-Identifier: CC-BY-SA-4.0

# Installing OCRmyPDF

(latest)=

The easiest way to install OCRmyPDF is to follow the steps for your operating
system/platform. This version may be out of date, however.

These platforms have one-liner installs:

:::{list-table}
:header-rows: 0

* - Homebrew (macOS and Linux)
  - ``brew install ocrmypdf``
* - Debian, Ubuntu
  - ``apt install ocrmypdf``
* - Windows Subsystem for Linux
  - ``apt install ocrmypdf``
* - Fedora
  - ``dnf install ocrmypdf tesseract-osd``
* - macOS (MacPorts)
  - ``port install ocrmypdf``
* - FreeBSD
  - ``pkg install textproc/py-ocrmypdf``
* - Snap (snapcraft packaging)
  - ``snap install ocrmypdf``
:::

More detailed procedures are outlined below. If you want to do a manual
install, or install a more recent version than your platform provides, read on.

:::{contents} Platform-specific steps
:depth: 2
:local: true
:::

## Installing on Linux

### Debian and Ubuntu 22.04 or newer

:::{list-table}
:header-rows: 1

* - OCRmyPDF versions in Debian & Ubuntu
* - {{ latest }}
* - {{ deb_12 }} {{ deb_13 }} {{ deb_unstable }}
* - {{ ubu_2204 }} {{ ubu_2404 }}
:::

Users of Debian or Ubuntu may simply

```bash
apt install ocrmypdf
```

As indicated in the table above, Debian and Ubuntu releases may lag
behind the latest version. If the version available for your platform is
out of date, you could opt to install the latest version from source.
See [Installing HEAD revision from
sources](#installing-head-revision-from-sources).

For full details on version availability for your platform, check the
[Debian Package Tracker](https://tracker.debian.org/pkg/ocrmypdf) or
[Ubuntu launchpad.net](https://launchpad.net/ocrmypdf).

:::{note}
OCRmyPDF for Debian and Ubuntu currently omit the JBIG2 encoder.
OCRmyPDF works fine without it but will produce larger output files.
All JBIG2 patents expired in 2017, so if you build jbig2enc from source,
OCRmyPDF will automatically detect it on the `PATH`.
To add JBIG2 encoding, see {ref}`jbig2`.
:::

### Fedora

:::{list-table}
:header-rows: 1

* - OCRmyPDF version
* - {{latest}}
* - {{fedora_40}} {{fedora_41}} {{fedora_rawhide}}
:::

Users of Fedora may simply

```bash
dnf install ocrmypdf tesseract-osd
```

For full details on version availability, check the [Fedora Package
Tracker](https://packages.fedoraproject.org/pkgs/ocrmypdf/ocrmypdf/).

If the version available for your platform is out of date, you could opt
to install the latest version from source. See [Installing HEAD revision
from sources](#installing-head-revision-from-sources).

:::{note}
OCRmyPDF for Fedora currently omits the JBIG2 encoder. All JBIG2 patents
expired in 2017. OCRmyPDF works fine without it but will produce larger
output files. If you build jbig2enc from source, OCRmyPDF will automatically
detect it on the `PATH`. To add JBIG2 encoding, see {ref}`jbig2`.
:::

(ubuntu-lts-latest)=

### RHEL 9

Prepare the environment by getting Python 3.12:

```bash
dnf install python3.12 python3.12-pip
```

Then, follow [Requirements for pip and HEAD install](#requirements-for-pip-and-head-install) to install dependencies:

```bash
dnf install ghostscript tesseract
```

and build ocrmypdf in virtual environment:

```bash
python3.12 -m venv .venv
```

To add JBIG2 encoding, see {ref}`Installing the JBIG2 encoder <jbig2>`.

Note Fedora packages for language data haven't been branched for RHEL/EPEL, but you can get traineddata files directly from [tesseract](https://github.com/tesseract-ocr/tessdata/) and place them in `/usr/share/tesseract/tessdata`.

### Installing the latest version on Ubuntu 22.04/24.04 LTS

Ubuntu includes an older version of OCRmyPDF - you can install that with
`apt install ocrmypdf`. To install the latest version, we recommend using uv:

```bash
# Install system dependencies first
sudo apt-get update
sudo apt-get -y install ocrmypdf

# Install uv and upgrade to the latest OCRmyPDF
pip install uv
uv pip install --user --upgrade ocrmypdf
```

Alternatively, use Homebrew on Linux for a full-featured installation (see below).

To add JBIG2 encoding, see {ref}`jbig2`.

### Ubuntu 20.04 LTS (and other older distributions)

:::{note}
Ubuntu 20.04 is approaching end of life. Consider upgrading to Ubuntu 22.04 or 24.04 LTS.
:::

For older distributions, the most convenient way to install a recent version of
OCRmyPDF is to use Homebrew on Linux:

```bash
brew install ocrmypdf
```

See {ref}`homebrew-linux` for more information on using Homebrew on Linux.

### Arch Linux (AUR)

:::{image} https://repology.org/badge/version-for-repo/aur/ocrmypdf.svg
:alt: ArchLinux
:target: https://repology.org/metapackage/ocrmypdf
:::

There is an [Arch User Repository (AUR) package for OCRmyPDF](https://aur.archlinux.org/packages/ocrmypdf/).

Installing AUR packages as root is not allowed, so you must first [setup a
non-root user](https://wiki.archlinux.org/index.php/Users_and_groups#User_management) and
[configure sudo](https://wiki.archlinux.org/index.php/Sudo#Configuration).
The standard Docker image, `archlinux/base:latest`, does **not** have a
non-root user configured, so users of that image must follow these guides. If
you are using a VM image, such as [the official Vagrant image](https://app.vagrantup.com/archlinux/boxes/archlinux), this work may already
be completed for you.

Next you should install the [base-devel package group](https://archlinux.org/packages/core/any/base-devel/). This includes the
standard tooling needed to build packages, such as a compiler and binary tools.

```bash
sudo pacman -S --needed base-devel
```

Now you are ready to install the OCRmyPDF package.

```bash
curl -O https://aur.archlinux.org/cgit/aur.git/snapshot/ocrmypdf.tar.gz
tar xvzf ocrmypdf.tar.gz
cd ocrmypdf
makepkg -sri
```

At this point you will have a working install of OCRmyPDF, but the Tesseract
install won’t include any OCR language data. You can install [the
tesseract-data package group](https://www.archlinux.org/groups/any/tesseract-data/) to add all supported
languages, or use that package listing to identify the appropriate package for
your desired language.

```bash
sudo pacman -S tesseract-data-eng
```

As an alternative to this manual procedure, consider using an [AUR helper](https://wiki.archlinux.org/index.php/AUR_helpers). Such a tool will
automatically fetch, build and install the AUR package, resolve dependencies
(including dependencies on AUR packages), and ease the upgrade procedure.

If you have any difficulties with installation, check the repository package
page.

:::{note}
The OCRmyPDF AUR package currently omits the JBIG2 encoder. OCRmyPDF works
fine without it but will produce larger output files. The encoder is
available from [the jbig2enc-git AUR package](https://aur.archlinux.org/packages/jbig2enc-git/) and may be installed
using the same series of steps as for the installation OCRmyPDF AUR
package. Alternatively, it may be built manually from source following the
instructions in {ref}`Installing the JBIG2 encoder <jbig2>`. If JBIG2 is
installed, OCRmyPDF 7.0.0 and later will automatically detect it.
:::

### Alpine Linux

:::{image} https://repology.org/badge/version-for-repo/alpine_edge/ocrmypdf.svg
:alt: Alpine Linux
:target: https://repology.org/metapackage/ocrmypdf
:::

To install OCRmyPDF for Alpine Linux:

```bash
apk add ocrmypdf
```

### Gentoo Linux

:::{image} https://repology.org/badge/version-for-repo/gentoo_ovl_guru/ocrmypdf.svg
:alt: Gentoo Linux
:target: https://repology.org/metapackage/ocrmypdf
:::

To install OCRmyPDF on Gentoo Linux, use the following commands:

```bash
eselect repository enable guru
emaint sync --repo guru
emerge --ask app-text/OCRmyPDF
```

### Other Linux packages

See the
[Repology](https://repology.org/metapackage/ocrmypdf/versions) page.

In general, first install the OCRmyPDF package for your system, then
optionally use the procedure [Installing with Python
pip](#installing-with-python-pip) to install a more recent version.

(homebrew-linux)=

## Installing with Homebrew (macOS and Linux)

:::{image} https://img.shields.io/homebrew/v/ocrmypdf.svg
:alt: homebrew
:target: https://formulae.brew.sh/formula/ocrmypdf
:::

[Homebrew](https://brew.sh) provides a full-featured OCRmyPDF installation
on both macOS and Linux with all recommended dependencies. This is often
the easiest way to get a complete, up-to-date installation.

```bash
brew install ocrmypdf
```

This includes Tesseract, Ghostscript, and all required dependencies. English
language support is included by default. For other languages:

```bash
brew install tesseract-lang  # Optional: Install all language packs
```

:::{tip}
**For Linux users:** Homebrew on Linux is an excellent choice when your
distribution's package is outdated or missing optional dependencies like
jbig2enc, pngquant, or unpaper. Homebrew provides a consistent, full-featured
installation that works across many Linux distributions.

Install Homebrew on Linux: https://brew.sh
:::

## Installing on macOS

### Homebrew

See {ref}`homebrew-linux` above - the installation is identical on macOS.

### MacPorts

:::{image} https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fports.macports.org%2Fapi%2Fv1%2Fports%2Focrmypdf%2F%3Fformat%3Djson&query=version&label=MacPorts
:alt: Macports Version Information
:target: https://ports.macports.org/port/ocrmypdf
:::

OCRmyPDF is included in MacPorts:

```bash
sudo port install ocrmypdf
```

Note that while this will install tesseract you will need to install
the appropriate tesseract [language ports](https://ports.macports.org/search/?selected_facets=categories_exact%3Atextproc&installed_file=&q=tesseract&name=on).

### Manual installation on macOS

These instructions are for installing a more current version of OCRmyPDF than
is available from Homebrew. Note that Homebrew versions usually track
releases fairly closely.

If it's not already present, [install Homebrew](http://brew.sh/).

Update Homebrew and install dependencies:

```bash
brew update
```

Install or upgrade the required Homebrew packages, if any are missing.
To do this, use `brew edit ocrmypdf` to obtain a recent list of Homebrew
dependencies. You could also check the `.workflows/build.yml`.

This will include the English, French, German and Spanish language
packs. If you need other languages you can optionally install them all:

(macos-all-languages)=

> ```bash
> brew install tesseract-lang  # Option 2: for all language packs
> ```

Install uv and OCRmyPDF:

```bash
pip install uv
uv pip install --user ocrmypdf
```

The command line program should now be available:

```bash
ocrmypdf --help
```

## Installing on Windows

### Native Windows

% If you have a Windows that is not the Home edition, you can use Windows Sandbox to test on a blank Windows instance.
% https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/

:::{note}
Administrator privileges will be required for some of these steps.
:::

You must install the following for Windows:

- Python 64-bit
- Tesseract 64-bit
- Ghostscript 64-bit

Using the [winget](https://docs.microsoft.com/en-us/windows/package-manager/winget/)
package manager:

- `winget install -e --id Python.Python.3.12`
- `winget install -e --id UB-Mannheim.TesseractOCR`

You will need to install Ghostscript manually, [since it does not support automated
installs anymore](https://artifex.com/news/ghostscript-10.01.0-disabling-silent-install-option).

- [Ghostscript download page](https://ghostscript.com/releases/gsdnld.html).\`

(Or alternately, using the [Chocolatey](https://chocolatey.org/) package manager, install
the following when running in an Administrator command prompt):

- `choco install python3`
- `choco install --pre tesseract`
- `choco install pngquant` (optional)

Either set of commands will install the required software. At the moment there is no
single command to install Windows.

You may then use `pip` to install ocrmypdf. (This can performed by a user or
Administrator.):

- `python3 -m pip install ocrmypdf`

% The Windows Python versions do not place any python or python3 executable in the path.
% They add the py launcher to the path:
% https://docs.python.org/3/using/windows.html#python-launcher-for-windows

If you installed Python using WinGet, then use the following command instead:

- `py -m pip install ocrmypdf`

and use:

- `py -m ocrmypdf`

To start OCRmyPDF.

If you intend to use more Python software on your Windows machine, consider the use of
[pipx](https://pipx.pypa.io/stable/) or a similar tool to create isolated Python
environments for each Python software that you want to use.

OCRmyPDF will check the Windows Registry and standard locations in your Program Files
for third party software it needs (specifically, Tesseract and Ghostscript). To
override the versions OCRmyPDF selects, you can modify the `PATH` environment
variable. [Follow these directions](https://www.computerhope.com/issues/ch000549.htm#dospath)
to change the PATH.

:::{warning}
32-bit Windows is not supported.
:::

### Windows Subsystem for Linux

1. Install Ubuntu 22.04 for Windows Subsystem for Linux, if not already installed.
2. Follow the procedure to install {ref}`OCRmyPDF on Ubuntu 22.04 <ubuntu-lts-latest>`.
3. Open the Windows command prompt and create a symlink:

```powershell
wsl sudo ln -s  /home/$USER/.local/bin/ocrmypdf /usr/local/bin/ocrmypdf
```

Then confirm that the expected version from PyPI ({{ latest }}) is installed:

```powershell
wsl ocrmypdf --version
```

You can then run OCRmyPDF in the Windows command prompt or Powershell, prefixing
`wsl`, and call it from Windows programs or batch files.

### Cygwin64

First install the the following prerequisite Cygwin packages using `setup-x86_64.exe`:

```
python311 (or later)
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
```

Then open a Cygwin terminal (i.e. `mintty`), run the following commands. Note
that if you are using the version of `pip` that was installed with the Cygwin
Python package, the command name will be `pip3`. If you have since updated
`pip` (with, for instance `pip3 install --upgrade pip`) the the command is
likely just `pip` instead of `pip3`:

```bash
pip3 install wheel
pip3 install ocrmypdf
```

The optional dependency "unpaper" that is currently not available under Cygwin.
Without it, certain options such as `--clean` will produce an error message.
However, the OCR-to-text-layer functionality is available.

### Docker

You can also [Install the Docker image](docker) on Windows. Ensure that
your command prompt can run the docker "hello world" container.

## Installing on FreeBSD

:::{image} https://repology.org/badge/version-for-repo/freebsd/ocrmypdf.svg
:alt: FreeBSD
:target: https://repology.org/project/ocrmypdf/versions
:::

```bash
pkg install textproc/py-ocrmypdf
```

To install a more recent version, you could attempt to first install the system
version with `pkg`, then use `pip install --user ocrmypdf`.

## Installing the Docker image

For some users, installing the Docker image will be easier than
installing all of OCRmyPDF's dependencies.

See [Installing the Docker image](docker) for more information.

(installing-with-python-pip)=

## Installing with uv (recommended)

We recommend using [uv](https://docs.astral.sh/uv/) for installing OCRmyPDF from PyPI.
uv is a fast, modern Python package manager that provides better dependency resolution
and consistent behavior across all platforms.

For best results, first install [your platform's
version](https://repology.org/metapackage/ocrmypdf/versions) of
`ocrmypdf` using the instructions elsewhere in this document to satisfy system
dependencies. Then use uv to get the latest OCRmyPDF version.

```bash
# Install uv if you don't have it
pip install uv

# Install ocrmypdf in a virtual environment (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install ocrmypdf

# Or install globally
uv pip install --system ocrmypdf
```

Use `ocrmypdf --version` to confirm what version was installed.

### Installing with pip

If you prefer pip, you can still use it:

```bash
pip install --user ocrmypdf
```

(If the message appears `Requirement already satisfied: ocrmypdf in...`,
you will need to use `pip install --user --upgrade ocrmypdf`.)

### Installing with pipx

Some users may prefer pipx for isolated command-line tool installations:

```bash
pipx install ocrmypdf
```

Or run without permanent installation:

```bash
pipx run ocrmypdf
```

(requirements-for-pip-and-head-install)=

### Requirements for pip and HEAD install

OCRmyPDF currently requires these external programs and libraries to be
installed, and must be satisfied using the operating system package
manager. `pip` cannot provide them.

:::{versionchanged} 17.0.0
Ghostscript is now optional. pypdfium2 can be used for PDF rasterization,
and verapdf can validate speculative PDF/A conversion.
:::

The following versions are required:

- Python 3.11 or newer (3.12+ recommended)
- Tesseract 4.1.1 or newer
- One of: Ghostscript 9.54+ **or** pypdfium2 (Python package)
- One of: Ghostscript 9.54+ **or** verapdf (for PDF/A output)
- fpdf2 2.8 or newer (Python package)
- uharfbuzz (Python package)
- fonts-noto or equivalent (system package, recommended)
- jbig2enc 0.29 or newer (optional)
- pngquant 2.5 or newer (optional)
- unpaper 6.1 (optional)

:::{note}
For the best user experience, install both Ghostscript and pypdfium2. pypdfium2 is
faster for rasterization, while Ghostscript provides is required for certain PDF/A
conversions.
:::

**Dependency summary:**

| Feature | Option 1 | Option 2 | Notes |
|---------|----------|----------|-------|
| PDF rasterization | pypdfium2 (Python) | Ghostscript (binary) | pypdfium2 preferred when available |
| PDF/A conversion | verapdf + pikepdf | Ghostscript | verapdf validates speculative conversion |
| Text rendering | fpdf2 + uharfbuzz | - | Required |
| OCR | tesseract-ocr | `--ocr-engine none` | Can be skipped entirely |

**Minimum viable installation:**
tesseract-ocr + (pypdfium2 OR Ghostscript) + fpdf2 + uharfbuzz

**Recommended installation:**
tesseract-ocr + pypdfium2 + Ghostscript + verapdf + fpdf2 + uharfbuzz + fonts-noto + unpaper + pngquant + jbig2enc

We recommend 64-bit versions of all software. (32-bit versions are not
supported, although on Linux, they may still work.)

**fpdf2** and **uharfbuzz** are required dependencies that provide the text
layer rendering engine. fpdf2 generates the PDF text layer, while uharfbuzz
provides text shaping for proper multilingual support. These replace the
legacy hOCR-based renderer. Install with: `pip install fpdf2 uharfbuzz`

**fonts-noto** (or an equivalent comprehensive font package) is recommended
for proper text rendering, especially for non-Latin scripts. On Debian/Ubuntu:
`apt install fonts-noto`. On Fedora: `dnf install google-noto-fonts-common`.
On macOS with Homebrew: `brew install font-noto`.

**pypdfium2**, if present, provides fast PDF page rasterization using
the pdfium library (the same library used by Google Chrome). It is
preferred over Ghostscript when available due to better performance.
Install with: `pip install pypdfium2`

**verapdf**, if present, enables fast speculative PDF/A conversion.
OCRmyPDF attempts to create PDF/A by adding metadata and ICC profiles
using pikepdf, then validates with verapdf. If validation passes,
Ghostscript is skipped entirely. See your distribution's package manager
or visit [verapdf.org](https://verapdf.org/).

**jbig2enc**, if present, will be used to optimize the encoding of
monochrome images. This can significantly reduce the file size of the
output file. It is not required.
[jbig2enc](https://github.com/agl/jbig2enc) is not available in some
distributions due to historical patent concerns, but all JBIG2 patents
expired in 2017. It can easily be built from source. To add JBIG2 encoding,
see {ref}`jbig2`.

:::{warning}
Lossy JBIG2 encoding (`--jbig2-lossy`) has been removed in v17.0.0 due to
well-documented risks of character substitution errors. Only lossless
JBIG2 compression is now supported.
:::

**pngquant**, if present, is optionally used to optimize the encoding of
PNG-style images in PDFs (actually, any that are that losslessly
encoded) by lossily quantizing to a smaller color palette. It is only
activated then the `--optimize` argument is `2` or `3`.

**unpaper**, if present, enables the `--clean` and `--clean-final`
command line options.

These are in addition to the Python packaging dependencies, meaning that
unfortunately, the `pip install` command cannot satisfy all of them.

(installing-head-revision-from-sources)=

## Installing HEAD revision from sources

If you have `git` and Python 3.12 or newer installed, you can install
from source. (Python 3.11 is supported but 3.12+ is recommended.) When the `pip` installer runs, it will alert you if
dependencies are missing.

If you prefer to build every from source, you will need to [build
pikepdf from
source](https://pikepdf.readthedocs.io/en/latest/installation.html#building-from-source).
First ensure you can build and install pikepdf.

We recommend using uv to install from sources:

```bash
git clone -b main https://github.com/ocrmypdf/OCRmyPDF.git
cd OCRmyPDF
pip install uv  # If not already installed
uv sync
```

This creates a virtual environment and installs all dependencies. Activate
the environment to use ocrmypdf:

```bash
source .venv/bin/activate
ocrmypdf --help
```

Alternatively, install directly from GitHub using pip:

```bash
pip install git+https://github.com/ocrmypdf/OCRmyPDF.git
```

Or, to install in editable mode allowing customization:

```bash
git clone -b main https://github.com/ocrmypdf/OCRmyPDF.git
cd OCRmyPDF
pip install -e .
```

Note: `ocrmypdf` will only be accessible when the virtual environment
is activated.

To run the program:

```bash
ocrmypdf --help
```

If not yet installed, the script will notify you about dependencies that
need to be installed. The script requires specific versions of the
dependencies. Older version than the ones mentioned in the release notes
are likely not to be compatible to OCRmyPDF.

## Optional Features

OCRmyPDF provides optional features and development tools. We recommend using `uv` as your package manager.

### Installing User Features

User features are available as optional dependencies. Install them with `uv` (recommended) or `pip`:

```bash
# Using uv (recommended)
uv sync --extra watcher        # File watching service
uv sync --extra webservice     # Streamlit web UI
uv sync --extra watcher --extra webservice  # Multiple features

# Using pip (also works)
pip install ocrmypdf[watcher]
pip install ocrmypdf[webservice]
pip install ocrmypdf[watcher,webservice]
```

### Development Tools (uv only)

Development tools use dependency groups:

```bash
# Testing infrastructure
uv sync --group test

# Documentation building
uv sync --group docs

# Enhanced Streamlit development
uv sync --group streamlit-dev

# All development groups
uv sync
```

**Why use uv?**

- Modern, fast Python package manager
- Required for development (testing, docs)
- Better dependency resolution
- Consistent across all platforms

Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` or visit https://docs.astral.sh/uv/

### For development

To install all of the development and test requirements:

```bash
git clone -b main https://github.com/ocrmypdf/OCRmyPDF.git
cd OCRmyPDF
uv sync --all-groups
```

To add JBIG2 encoding, see {ref}`jbig2`.

## Shell completions

Completions for `bash` and `fish` are available in the project's
`misc/completion` folder. The `bash` completions are likely `zsh`
compatible but this has not been confirmed. Package maintainers, please
install these at the appropriate locations for your system.

To manually install the `bash` completion, copy
`misc/completion/ocrmypdf.bash` to `/etc/bash_completion.d/ocrmypdf`
(rename the file).

To manually install the `fish` completion, copy
`misc/completion/ocrmypdf.fish` to
`~/.config/fish/completions/ocrmypdf.fish`.

## Note on 32-bit support

We don't support any 32-bit system, including 32-bit Python or 32-bit
Ghostscript on Windows.