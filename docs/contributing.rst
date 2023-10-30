.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

=======================
Contributing guidelines
=======================

Contributions are welcome!

Big changes
===========

Please open a new issue to discuss or propose a major change. Not only is it fun
to discuss big ideas, but we might save each other's time too. Perhaps some of the
work you're contemplating is already half-done in a development branch.

Code style
==========

We use PEP8, ``black`` for code formatting and ``ruff`` for everything else. The
settings for these programs are in ``pyproject.toml``. Pull
requests should follow the style guide. One difference we use from "black" style
is that strings shown to the user are always in double quotes (``"``) and strings
for internal uses are in single quotes (``'``).

Tests
=====

New features should come with tests that confirm their correctness.

New dependencies
================

If you are proposing a change that will require a new dependency, we
prefer dependencies that are already packaged by Debian or Red Hat. This makes
life much easier for our downstream package maintainers. A package that is only
available on PyPI or GitHub, and not more widely packaged, may not be accepted.

We are unlikely to accept a dependency on CUDA or other GPU-based libraries,
because these are still difficult to package and install on many systems.
We recommend implementing these changes as plugins.

Python dependencies must also be license-compatible. GPLv3 or AGPLv3 are likely
incompatible with the project's license, but LGPLv3 is compatible.

New non-Python dependencies
===========================

OCRmyPDF uses several external programs (Tesseract, Ghostscript and others) for
its functionality. In general we prefer to avoid adding new external programs,
and if we are to add external programs, we prefer those that are already
packaged by Debian or Red Hat.

Plugins
=======

Some new features may be a good fit for a plugin. Plugins are a way to add
features to OCRmyPDF without adding them to the core program. Plugins are
installed separately from OCRmyPDF. They are written in Python and can be
installed from PyPI. See the `plugin documentation <https://ocrmypdf.readthedocs.io/en/latest/plugins.html>`_.

We are happy to link users to your plugin from the documentation.

Style guide: Is it OCRmyPDF or ocrmypdf?
========================================

The program/project is OCRmyPDF and the name of the executable or library is ocrmypdf.

Copyright and license
=====================

For contributions over 10 lines of code, please add your name to list of
copyright holders for that file. The core program is licensed under MPL-2.0,
test files and documentation under CC-BY-SA 4.0, and miscellaneous files under
MIT, with a few minor exceptions. Please contribute only content that you own
or have the right to contribute under these licenses.
