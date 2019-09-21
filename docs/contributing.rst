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
settings for programs are in ``pyproject.toml`` and ``setup.cfg``.

Tests
=====

New features should come with tests that confirm their correctness.

New Python dependencies
=======================

If you are proposing a change that will require a new Python dependency, we
prefer dependencies that are already packaged by Debian or Red Hat. This makes
life much easier for our downstream package maintainers.

Python dependencies must also be GPLv3 compatible.

New non-Python dependencies
===========================

OCRmyPDF uses several external programs (Tesseract, Ghostscript and others) for
its functionality. In general we prefer to avoid adding new external programs.
