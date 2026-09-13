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
    fedora_43: |-
      :::{image} https://repology.org/badge/version-for-repo/fedora_43/ocrmypdf.svg
      :alt: Fedora 43
      :::
    fedora_44: |-
      :::{image} https://repology.org/badge/version-for-repo/fedora_44/ocrmypdf.svg
      :alt: Fedora 44
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
    ubu_2604: |-
      :::{image} https://repology.org/badge/version-for-repo/ubuntu_26_04/ocrmypdf.svg
      :alt: Ubuntu 26.04 LTS
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
* - Alpine Linux
  - ``apk add ocrmypdf``
* - macOS (MacPorts)
  - ``port install ocrmypdf``
* - FreeBSD
  - ``pkg install py311-ocrmypdf``
:::

More detailed procedures are outlined below. If you want to do a manual
install, or install a more recent version than your platform provides, read on.

If your operating system is older than those listed here, we recommend
installing OCRmyPDF with [Homebrew](#homebrew-linux), or using the
[Docker image](docker).

:::{contents} Platform-specific steps
:depth: 2
:local: true
:::

## Installing on Linux

### Debian 12 or newer and Ubuntu 22.04 or newer

:::{list-table}
:header-rows: 1

* - OCRmyPDF versions in Debian & Ubuntu
* - {{ latest }}
* - {{ deb_12 }} {{ deb_13 }} {{ deb_unstable }}
* - {{ ubu_2204 }} {{ ubu_2404 }} {{ ubu_2604 }}
:::

Users of Debian or Ubuntu may simply

```bash
apt install ocrmypdf
```

As indicated in the table above, Debian and Ubuntu releases may lag
behind the latest version, sometimes by several major versions. If the version
available for your platform is out of date, see
[Installing the latest version on Debian and Ubuntu](#ubuntu-lts-latest).

For full details on version availability for your platform, check the
[Debian Package Tracker](https://tracker.debian.org/pkg/ocrmypdf) or
[Ubuntu launchpad.net](https://launchpad.net/ocrmypdf).

:::{note}
The Debian and Ubuntu OCRmyPDF packages do not install the JBIG2 encoder.
OCRmyPDF works fine without it but will produce larger output files.
On Debian 13 or newer and Ubuntu 24.04 or newer, the encoder is packaged and
can be installed with `apt install jbig2`. On older releases, you can build
jbig2enc from source; OCRmyPDF will automatically detect it on the `PATH`.
See {ref}`jbig2`.
:::

(ubuntu-lts-latest)=

### Installing the latest version on Debian and Ubuntu

Debian and Ubuntu include an older version of OCRmyPDF - you can install that
with `apt install ocrmypdf`. To install the latest version, we recommend
installing the system package first, which brings in Tesseract, Ghostscript
and other system dependencies, and then using
[uv](https://docs.astral.sh/uv/) to install the latest OCRmyPDF from PyPI:

```bash
# Install system dependencies first
sudo apt-get update
sudo apt-get -y install ocrmypdf

# Install uv, if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the latest OCRmyPDF
uv tool install ocrmypdf
```

uv installs the `ocrmypdf` command in `~/.local/bin`. Open a new terminal
(or run `uv tool update-shell`) so that it is on your `PATH`, and then run
`ocrmypdf --version` to confirm that the latest version is used rather than the
older system version in `/usr/bin`.

If your system Python is too old for the latest OCRmyPDF, as on Ubuntu 22.04,
uv will download a suitable version of Python automatically.

To upgrade later:

```bash
uv tool upgrade ocrmypdf
```

:::{tip}
Ubuntu 22.04 ships Tesseract 4.1.1, which is the oldest version OCRmyPDF
supports. Tesseract 5 gives better results; it is available for Ubuntu LTS
releases from the
[alex-p/tesseract-ocr5 PPA](https://launchpad.net/~alex-p/+archive/ubuntu/tesseract-ocr5):
`sudo add-apt-repository ppa:alex-p/tesseract-ocr5`. Newer Debian and Ubuntu
releases already include Tesseract 5.
:::

Alternatively, use Homebrew on Linux for a full-featured installation (see
{ref}`homebrew-linux`).

To add JBIG2 encoding, on Debian 13 or newer and Ubuntu 24.04 or newer run
`sudo apt install jbig2`; otherwise see {ref}`jbig2`.

### Older Debian and Ubuntu releases

Ubuntu 22.04 LTS and Debian 12 are the oldest releases OCRmyPDF supports.
Ubuntu 20.04 and Debian 11 have reached the end of standard support, and their
Python, Tesseract and Ghostscript are too old for current OCRmyPDF. Consider
upgrading to a supported release.

If you cannot upgrade, the most convenient way to install a recent version of
OCRmyPDF is to use Homebrew on Linux:

```bash
brew install ocrmypdf
```

See {ref}`homebrew-linux` for more information on using Homebrew on Linux.
Alternatively, run OCRmyPDF from the [Docker image](docker), which carries its
own up-to-date dependencies.

### Fedora

:::{list-table}
:header-rows: 1

* - OCRmyPDF version
* - {{latest}}
* - {{fedora_43}} {{fedora_44}} {{fedora_rawhide}}
:::

Users of Fedora may simply

```bash
dnf install ocrmypdf tesseract-osd
```

`tesseract-osd` is not installed automatically, but OCRmyPDF needs it for
automatic page rotation (`--rotate-pages`). Tesseract language packs are named
`tesseract-langpack-<language>`, for example `tesseract-langpack-deu`.

For full details on version availability, check the [Fedora Package
Tracker](https://packages.fedoraproject.org/pkgs/ocrmypdf/ocrmypdf/).

If the version available for your platform is out of date, install the
system package first to satisfy system dependencies, then use uv to install
the latest version:

```bash
# Install system dependencies first
sudo dnf install ocrmypdf tesseract-osd

# Install uv, if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the latest OCRmyPDF
uv tool install ocrmypdf
```

Open a new terminal (or run `uv tool update-shell`) so that `~/.local/bin` is on
your `PATH`, then confirm the version with `ocrmypdf --version`. To install
from source instead, see [Installing HEAD revision from
sources](#installing-head-revision-from-sources).

:::{note}
OCRmyPDF for Fedora currently omits the JBIG2 encoder, and Fedora does not
package it. All JBIG2 patents expired in 2017. OCRmyPDF works fine without it
but will produce larger output files. If you build jbig2enc from source,
OCRmyPDF will automatically detect it on the `PATH`. To add JBIG2 encoding,
see {ref}`jbig2`.
:::

### RHEL, CentOS Stream, AlmaLinux and Rocky Linux 9 and 10

There is no OCRmyPDF package for Red Hat Enterprise Linux or its derivatives,
either in the base repositories or in EPEL. Install the system dependencies
from the base (AppStream) repositories:

```bash
sudo dnf install ghostscript tesseract tesseract-osd tesseract-langpack-eng
```

Other Tesseract languages are available as `tesseract-langpack-<language>`,
for example `tesseract-langpack-deu`.

The optional dependencies `unpaper` and, on version 9, `pngquant` are available
from [EPEL](https://docs.fedoraproject.org/en-US/epel/getting-started/). Once
EPEL is enabled:

```bash
sudo dnf install unpaper pngquant  # pngquant: version 9 only
```

Then install uv, if not already installed, and use it to install OCRmyPDF:

```bash
# Install uv, if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the latest OCRmyPDF
uv tool install ocrmypdf
```

RHEL 9's default Python 3.9 is too old for OCRmyPDF; uv will download a
suitable version of Python automatically. Open a new terminal (or run
`uv tool update-shell`) so that `~/.local/bin` is on your `PATH`, then confirm
the version with `ocrmypdf --version`.

To add JBIG2 encoding, see {ref}`Installing the JBIG2 encoder <jbig2>`.

### Arch Linux (AUR)

:::{image} https://repology.org/badge/version-for-repo/aur/ocrmypdf.svg
:alt: ArchLinux
:target: https://repology.org/metapackage/ocrmypdf
:::

There is an [Arch User Repository (AUR) package for OCRmyPDF](https://aur.archlinux.org/packages/ocrmypdf/).
OCRmyPDF is not in the official Arch repositories, but its dependencies,
including Tesseract and its language data, are.

Installing AUR packages as root is not allowed, so you must first [setup a
non-root user](https://wiki.archlinux.org/title/Users_and_groups#User_management) and
[configure sudo](https://wiki.archlinux.org/title/Sudo#Configuration).
The official Docker image, `archlinux:latest`, does **not** have a
non-root user configured, so users of that image must follow these guides.

Next you should install the [base-devel package group](https://archlinux.org/packages/core/any/base-devel/). This includes the
standard tooling needed to build packages, such as a compiler and binary tools.

```bash
sudo pacman -S --needed base-devel git
```

Now you are ready to install the OCRmyPDF package.

```bash
git clone https://aur.archlinux.org/ocrmypdf.git
cd ocrmypdf
makepkg -sri
```

At this point you will have a working install of OCRmyPDF, but the Tesseract
install won’t include any OCR language data. You can install [the
tesseract-data packages](https://archlinux.org/packages/?q=tesseract-data) to add
supported languages. For example, for English:

```bash
sudo pacman -S tesseract-data-eng
```

As an alternative to this manual procedure, consider using an [AUR helper](https://wiki.archlinux.org/title/AUR_helpers). Such a tool will
automatically fetch, build and install the AUR package, resolve dependencies
(including dependencies on AUR packages), and ease the upgrade procedure.

If you have any difficulties with installation, check the repository package
page.

:::{note}
The JBIG2 encoder is an optional dependency of the OCRmyPDF AUR package.
OCRmyPDF works fine without it but will produce larger output files. The
encoder is available from [the jbig2enc AUR package](https://aur.archlinux.org/packages/jbig2enc/)
and may be installed using the same series of steps as for the OCRmyPDF AUR
package. Alternatively, it may be built manually from source following the
instructions in {ref}`Installing the JBIG2 encoder <jbig2>`. If jbig2enc is
installed, OCRmyPDF will automatically detect it.
:::

### Alpine Linux

:::{image} https://repology.org/badge/version-for-repo/alpine_edge/ocrmypdf.svg
:alt: Alpine Linux
:target: https://repology.org/metapackage/ocrmypdf
:::

OCRmyPDF is in the Alpine Linux `community` repository. To install it:

```bash
apk add ocrmypdf
```

If the version available for your Alpine release is out of date, consider the
Alpine-based [Docker image](docker), `jbarlow83/ocrmypdf-alpine`.

### Gentoo Linux

:::{image} https://repology.org/badge/version-for-repo/gentoo_ovl_guru/ocrmypdf.svg
:alt: Gentoo Linux
:target: https://repology.org/metapackage/ocrmypdf
:::

OCRmyPDF is available from the [GURU](https://wiki.gentoo.org/wiki/Project:GURU)
overlay, which must be enabled first. To install OCRmyPDF on Gentoo Linux, use
the following commands:

```bash
emerge --ask --noreplace app-eselect/eselect-repository dev-vcs/git
eselect repository enable guru
emaint sync --repo guru
emerge --ask app-text/OCRmyPDF
```

### Other Linux packages

OCRmyPDF is also packaged for other distributions, including NixOS (`ocrmypdf`),
Void Linux (`python3-ocrmypdf`) and openSUSE Tumbleweed. See the
[Repology](https://repology.org/metapackage/ocrmypdf/versions) page for a full
list.

In general, first install the OCRmyPDF package for your system to satisfy
system dependencies, then optionally use the procedure [Installing with
uv](#installing-with-python-pip) to install a more recent version:

```bash
# Install uv, if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the latest OCRmyPDF
uv tool install ocrmypdf
```

:::{note}
The OCRmyPDF Snap package (`snap install ocrmypdf`) has not been updated since
2024 and is several major versions behind. We do not recommend it.
:::

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

This includes Tesseract, Ghostscript, jbig2enc, pngquant, unpaper and all
required dependencies. English language support is included by default. For
other languages:

```bash
brew install tesseract-lang  # Optional: Install all language packs
```

To upgrade later:

```bash
brew upgrade ocrmypdf
```

:::{tip}
**For Linux users:** Homebrew on Linux is an excellent choice when your
distribution's package is outdated, your distribution is too old for current
OCRmyPDF, or its package is missing optional dependencies like jbig2enc,
pngquant, or unpaper. Homebrew provides a consistent, full-featured
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
the appropriate tesseract [language ports](https://ports.macports.org/search/?q=tesseract-&name=on),
which are named `tesseract-<language>`. For example, for German:

```bash
sudo port install tesseract-deu
```

### Manual installation on macOS

These instructions are for installing a more current version of OCRmyPDF than
is available from Homebrew. Note that Homebrew versions usually track
releases fairly closely.

If it's not already present, [install Homebrew](https://brew.sh/).

Update Homebrew and install OCRmyPDF's dependencies, without OCRmyPDF itself:

```bash
brew update
brew install --only-dependencies ocrmypdf
```

Homebrew's Tesseract includes English only. If you need other languages you
can optionally install them all:

(macos-all-languages)=

```bash
brew install tesseract-lang  # Optional: for all language packs
```

Install uv, if not already installed, and use it to install OCRmyPDF:

```bash
# Install uv, if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the latest OCRmyPDF
uv tool install ocrmypdf
```

Open a new terminal (or run `uv tool update-shell`) so that `~/.local/bin` is
on your `PATH`. The command line program should now be available:

```bash
ocrmypdf --help
```

To upgrade later, run `uv tool upgrade ocrmypdf`.

## Installing on Windows

### Native Windows

% If you have a Windows that is not the Home edition, you can use Windows Sandbox to test on a blank Windows instance.
% https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/

:::{note}
Administrator privileges will be required for some of these steps.
:::

You must install the following for Windows:

- Tesseract 64-bit
- Ghostscript 64-bit (recommended; required for some PDF/A conversions)
- uv, which installs OCRmyPDF and, if needed, a suitable Python

Using the [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
package manager:

```powershell
winget install -e --id tesseract-ocr.tesseract
winget install -e --id astral-sh.uv
```

If you prefer not to use winget for uv, you can install it with its
standalone installer instead:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Ghostscript is not available from winget. You will need to install it manually,
[since it does not support automated installs
anymore](https://artifex.com/news/ghostscript-10.01.0-disabling-silent-install-option):

- [Ghostscript download page](https://ghostscript.com/releases/gsdnld.html)

Or alternately, using the [Chocolatey](https://chocolatey.org/) package
manager, install the following when running in an Administrator command
prompt:

```powershell
choco install tesseract
choco install ghostscript
choco install pngquant  # optional
```

and then install uv using either of the commands above.

Either set of commands will install the required software. At the moment there
is no single command to install OCRmyPDF and all of its dependencies on
Windows.

Open a new command prompt or PowerShell window, so that the newly installed
programs are on your `PATH`, and install OCRmyPDF. (This can be performed by a
user or Administrator.)

```powershell
uv tool install ocrmypdf
```

Open another new window, then confirm that OCRmyPDF is available:

```powershell
ocrmypdf --version
```

If the `ocrmypdf` command is not found, run `uv tool update-shell` and open a
new window. To upgrade later, run `uv tool upgrade ocrmypdf`.

OCRmyPDF will check the Windows Registry and standard locations in your Program Files
for third party software it needs (specifically, Tesseract and Ghostscript). To
override the versions OCRmyPDF selects, you can modify the `PATH` environment
variable. [Follow these directions](https://www.computerhope.com/issues/ch000549.htm#dospath)
to change the PATH.

:::{warning}
32-bit Windows is not supported.
:::

### Windows Subsystem for Linux

1. Install Ubuntu 24.04 or 26.04 LTS for Windows Subsystem for Linux, if not
   already installed.
2. Follow the procedure to install {ref}`the latest OCRmyPDF on Ubuntu <ubuntu-lts-latest>`.
3. In the Ubuntu (WSL) terminal, create a symlink so that the latest version is
   found when OCRmyPDF is run from Windows:

```bash
sudo ln -s ~/.local/bin/ocrmypdf /usr/local/bin/ocrmypdf
```

Then, from the Windows command prompt, confirm that the expected version from
PyPI ({{ latest }}) is installed:

```powershell
wsl ocrmypdf --version
```

You can then run OCRmyPDF in the Windows command prompt or Powershell, prefixing
`wsl`, and call it from Windows programs or batch files.

### Cygwin64

:::{warning}
Cygwin installation is not tested. uv is not available for Cygwin, and some
of OCRmyPDF's Python dependencies, such as pikepdf, pypdfium2 and uharfbuzz,
have no Cygwin binaries and must be compiled from source, which may fail. We
recommend using Windows Subsystem for Linux, the Docker image, or native
Windows instead.
:::

First install the following prerequisite Cygwin packages using `setup-x86_64.exe`:

```
python312 (or later)
python312-devel
python312-pip
python312-lxml
python312-imaging

   (where 312 should match the version of Python you installed)

gcc-g++
ghostscript
libexempi-devel
libffi-devel
pngquant
qpdf
libqpdf-devel
tesseract-ocr
tesseract-ocr-devel
```

Then open a Cygwin terminal (i.e. `mintty`), and install OCRmyPDF into a
virtual environment:

```bash
python3.12 -m venv --system-site-packages ~/ocrmypdf-venv
~/ocrmypdf-venv/bin/python -m pip install ocrmypdf
~/ocrmypdf-venv/bin/ocrmypdf --version
```

The optional dependency "unpaper" is currently not available under Cygwin.
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
pkg install py311-ocrmypdf
```

To install a more recent version, first install the system version with `pkg`
to satisfy system dependencies, then install uv from packages and use it to
install OCRmyPDF:

```bash
pkg install uv
uv tool install ocrmypdf
```

Some Python dependencies do not publish binaries for FreeBSD and will be
compiled from source, so this may require additional development packages.

## Installing the Docker image

For some users, installing the Docker image will be easier than
installing all of OCRmyPDF's dependencies. It is also a good option if your
operating system is too old to run current OCRmyPDF.

See [Installing the Docker image](docker) for more information.

(installing-with-python-pip)=

## Installing with uv (recommended)

We recommend using [uv](https://docs.astral.sh/uv/) for installing OCRmyPDF from PyPI.
uv is a fast, modern Python package manager that installs command line tools
in isolated environments, and can download a suitable version of Python if
your system's Python is too old.

For best results, first install [your platform's
version](https://repology.org/metapackage/ocrmypdf/versions) of
`ocrmypdf` using the instructions elsewhere in this document to satisfy system
dependencies. Then use uv to get the latest OCRmyPDF version.

On macOS and Linux:

```bash
# Install uv, if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the latest OCRmyPDF
uv tool install ocrmypdf
```

On Windows:

```powershell
# Install uv, if not already installed
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install the latest OCRmyPDF
uv tool install ocrmypdf
```

Open a new terminal (or run `uv tool update-shell`) so that the `ocrmypdf`
command is on your `PATH`. Use `ocrmypdf --version` to confirm what version was
installed, and `uv tool upgrade ocrmypdf` to upgrade later.

To use OCRmyPDF as a Python library in your own project, add it as a
dependency of that project instead:

```bash
uv add ocrmypdf
```

### Installing with pipx

If you already use pipx for isolated command-line tool installations, it works
as well:

```bash
pipx install ocrmypdf
```

(requirements-for-pip-and-head-install)=

### Requirements for uv and source installs

OCRmyPDF currently requires these external programs and libraries to be
installed, and must be satisfied using the operating system package
manager. uv and other Python package managers cannot provide them.

:::{versionchanged} 17.0.0
Ghostscript is now optional. pypdfium2 can be used for PDF rasterization,
and verapdf can validate speculative PDF/A conversion.
:::

The following versions are required:

- Python 3.11 or newer (3.12+ recommended; uv can install it for you)
- Tesseract 4.1.1 or newer
- One of: Ghostscript 9.54+ **or** pypdfium2 (Python package)
- One of: Ghostscript 9.54+ **or** verapdf (for PDF/A output)
- fpdf2 2.8 or newer (Python package)
- uharfbuzz (Python package)
- fonts-noto or equivalent (system package, recommended)
- jbig2enc 0.28 or newer (optional)
- pngquant 2.12.2 or newer (optional)
- unpaper 6.1 or newer (optional)

:::{note}
For the best user experience, install both Ghostscript and pypdfium2. pypdfium2 is
faster for rasterization, while Ghostscript is required for certain PDF/A
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
legacy hOCR-based renderer. They are Python packages, installed automatically
when you install OCRmyPDF with uv.

**fonts-noto** (or an equivalent comprehensive font package) is recommended
for proper text rendering, especially for non-Latin scripts. OCRmyPDF bundles
a Latin font only, and discovers the rest from the fonts installed on your
system.

- Debian/Ubuntu: `apt install fonts-noto`
- Fedora: `dnf install google-noto-fonts-all`
- macOS with Homebrew: Homebrew has no single Noto package; each family is a
  separate cask. Install at least
  `brew install --cask font-noto-sans font-noto-serif`, plus a cask per
  additional script you OCR, for example
  `brew install --cask font-noto-sans-arabic font-noto-sans-cjk`. Run
  `brew search font-noto` to list them all.

If OCRmyPDF warns that no installed font has glyphs for some of the text, the
message names the characters it could not render, for example
`'Ꮳ' U+13E3 CHEROKEE LETTER TSA`. Install the Noto font for that script — here,
`fonts-noto-core` on Debian or `font-noto-sans-cherokee` on Homebrew. The text
layer remains searchable and copyable either way; only its appearance when
highlighted in a PDF viewer is affected.

**pypdfium2** provides fast PDF page rasterization using the pdfium library
(the same library used by Google Chrome). It is installed automatically when
you install OCRmyPDF with uv, although some distribution packages of OCRmyPDF
omit it. When present, it is preferred over Ghostscript due to better
performance.

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
unfortunately, the `uv tool install` command cannot satisfy all of them.

(installing-head-revision-from-sources)=

## Installing HEAD revision from sources

If you have `git` and uv installed, you can install from source. uv will
alert you if Python dependencies cannot be installed; OCRmyPDF will alert you
at runtime if system dependencies are missing.

If you prefer to build everything from source, you will need to [build
pikepdf from
source](https://pikepdf.readthedocs.io/en/latest/installation.html#building-from-source).
First ensure you can build and install pikepdf.

To install the latest development version as a command line tool:

```bash
# Install uv, if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

uv tool install git+https://github.com/ocrmypdf/OCRmyPDF.git
```

Or, to work from a local checkout allowing customization:

```bash
git clone -b main https://github.com/ocrmypdf/OCRmyPDF.git
cd OCRmyPDF
uv sync
```

This creates a virtual environment in `.venv` and installs OCRmyPDF in
editable mode along with its dependencies. Run the program with `uv run`, or
activate the environment:

```bash
uv run ocrmypdf --help

# or
source .venv/bin/activate
ocrmypdf --help
```

Note: when installed this way, `ocrmypdf` will only be accessible through
`uv run` or when the virtual environment is activated.

If not yet installed, the script will notify you about dependencies that
need to be installed. The script requires specific versions of the
dependencies. Older version than the ones mentioned in the release notes
are likely not to be compatible to OCRmyPDF.

## Optional Features

OCRmyPDF provides optional features and development tools. We recommend using `uv` as your package manager.

### Installing User Features

User features are available as optional dependencies (extras). When
installing OCRmyPDF as a tool:

```bash
uv tool install "ocrmypdf[watcher]"                # File watching service
uv tool install "ocrmypdf[webservice]"             # Streamlit web UI
uv tool install "ocrmypdf[watcher,webservice]"     # Multiple features
```

Or, from a local source checkout:

```bash
uv sync --extra watcher        # File watching service
uv sync --extra webservice     # Streamlit web UI
uv sync --extra watcher --extra webservice  # Multiple features
```

### Development Tools

Development tools use dependency groups:

```bash
# Testing infrastructure
uv sync --group test

# Documentation building
uv sync --group docs

# Enhanced Streamlit development
uv sync --group streamlit-dev

# All development groups
uv sync --all-groups
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
