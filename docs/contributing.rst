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

We use PEP8, ``black`` for code formatting and ``isort`` for import sorting. The
settings for these programs are in ``pyproject.toml`` and ``setup.cfg``. Pull
requests should follow the style guide. One difference we use from "black" style
is that strings shown to the user are always in double quotes (``"``) and strings
for internal uses are in single quotes (``'``).

Tests
=====

New features should come with tests that confirm their correctness.

New Python dependencies
=======================

If you are proposing a change that will require a new Python dependency, we
prefer dependencies that are already packaged by Debian or Red Hat. This makes
life much easier for our downstream package maintainers.

Python dependencies must also be license-compatible. GPLv3 or AGPLv3 are likely
incompatible with the project's license, but LGPLv3 is compatible.

New non-Python dependencies
===========================

OCRmyPDF uses several external programs (Tesseract, Ghostscript and others) for
its functionality. In general we prefer to avoid adding new external programs.

Style guide: Is it OCRmyPDF or ocrmypdf?
========================================

The program/project is OCRmyPDF and the name of the executable or library is ocrmypdf.

Known ports/packagers
=====================

OCRmyPDF has been ported to many platforms already. If you are interesting in
porting to a new platform, check with
`Repology <https://repology.org/projects/?search=ocrmypdf>`__ to see the status
of that platform.

Packager maintainers, please ensure that the command line completion scripts in
``misc/`` are installed.

Copyright and license
=====================

For contributions over 10 lines of code, please include your name to list of
copyright holders for that file. The core program is licensed under MPL-2.0,
test files and documentation under CC-BY-SA 4.0, and miscellaneous files under
MIT. Please contribute code only that you wrote and you have the permission to
contribute or license to us.
