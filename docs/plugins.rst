.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

=======
Plugins
=======

    The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
    NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
    "OPTIONAL" in this document are to be interpreted as described in
    RFC 2119.

You can use plugins to customize the behavior of OCRmyPDF at certain points of
interest.

Currently, it is possible to:

- add new command line arguments
- override the decision for whether or not to perform OCR on a particular file
- modify the image is about to be sent for OCR
- modify the page image before it is converted to PDF
- replace the Tesseract OCR with another OCR engine that has similar behavior
- replace Ghostscript with another PDF to image converter (rasterizer) or
  PDF/A generator

OCRmyPDF plugins are based on the Python ``pluggy`` package and conform to its
conventions. Note that: plugins installed with as setuptools entrypoints are
not checked currently, because OCRmyPDF assumes you may not want to enable
plugins for all files.

Script plugins
==============

Script plugins may be called from the command line, by specifying the name of a file.
Script plugins may be convenient for informal or "one-off" plugins, when a certain
batch of files needs a special processing step for example.

.. code-block:: bash

    ocrmypdf --plugin ocrmypdf_example_plugin.py input.pdf output.pdf

Multiple plugins may be installed by issuing the ``--plugin`` argument multiple times.

Packaged plugins
================

Installed plugins may be installed into the same virtual environment as OCRmyPDF
is installed into. They may be invoked using Python standard module naming.
If you are intending to distribute a plugin, please package it.

.. code-block:: bash

    ocrmypdf --plugin ocrmypdf_fancypants.pockets.contents input.pdf output.pdf

OCRmyPDF does not automatically import plugins, because the assumption is that
plugins affect different files differently and you may not want them activated
all the time. The command line or ``ocrmypdf.ocr(plugin='...')`` must call
for them.

Third parties that wish to distribute packages for ocrmypdf should package them
as packaged plugins, and these modules should begin with the name ``ocrmypdf_``
similar to ``pytest`` packages such as ``pytest-cov`` (the package) and
``pytest_cov`` (the module).

.. note::

    We recommend plugin authors name their plugins with the prefix
    ``ocrmypdf-`` (for the package name on PyPI) and ``ocrmypdf_`` (for the
    module), just like pytest plugins. At the same time, please make it clear
    that your package is not official.

Setuptools plugins
==================

You can also create a plugin that OCRmyPDF will always automatically load if both are
installed in the same virtual environment, using a setuptools entrypoint.

Your package's ``pyproject.toml`` would need to contain the following, for a plugin
named ``ocrmypdf-exampleplugin``:

.. code-block:: toml

    [project]
    name = "ocrmypdf-exampleplugin"

    [project.entry-points."ocrmypdf"]
    exampleplugin = "exampleplugin.pluginmodule"

.. code-block:: ini

    # equivalent setup.cfg
    [options.entry_points]
    ocrmypdf =
        exampleplugin = exampleplugin.pluginmodule

Plugin requirements
===================

OCRmyPDF generally uses multiple worker processes. When a new worker is started,
Python will import all plugins again, including all plugins that were imported earlier.
This means that the global state of a plugin in one worker will not be shared with
other workers. As such, plugin hook implementations should be stateless, relying
only on their inputs. Hook implementations may use their input parameters to
to obtain a reference to shared state prepared by another hook implementation.
Plugins must expect that other instances of the plugin will be running
simultaneously.

The ``context`` object that is passed to many hooks can be used to share information
about a file being worked on. Plugins must write private, plugin-specific data to
a subfolder named ``{options.work_folder}/ocrmypdf-plugin-name``. Plugins MAY
read and write files in ``options.work_folder``, but should be aware that their
semantics are subject to change.

OCRmyPDF will delete ``options.work_folder`` when it has finished OCRing
a file, unless invoked with ``--keep-temporary-files``.

The documentation for some plugin hooks contain a detailed description of the
execution context in which they will be called.

Plugins should be prepared to work whether executed in worker threads or worker
processes. Generally, OCRmyPDF uses processes, but has a semi-hidden threaded
argument that simplifies debugging.


Plugin hooks
============

A plugin may provide the following hooks. Hooks must be decorated with
``ocrmypdf.hookimpl``, for example:

.. code-block:: python

    from ocrmpydf import hookimpl

    @hookimpl
    def add_options(parser):
        pass

The following is a complete list of hooks that are available, and when
they are called.

.. _firstresult:

**Note on firstresult hooks**

If multiple plugins install implementations for this hook, they will be called in
the reverse of the order in which they are installed (i.e., last plugin wins).
When each hook implementation is called in order, the first implementation that
returns a value other than ``None`` will "win" and prevent execution of all other
hooks. As such, you cannot "chain" a series of plugin filters together in this
way. Instead, a single hook implementation should be responsible for any such
chaining operations.

Examples
========

* OCRmyPDF's test suite contains several plugins that are used to simulate certain
  test conditions.
* `ocrmypdf-papermerge <https://github.com/papermerge/OCRmyPDF_papermerge>`_ is
  a production plugin that integrates OCRmyPDF and the Papermerge document
  management system.


Suppressing or overriding other plugins
---------------------------------------

.. autofunction:: ocrmypdf.pluginspec.initialize

Custom command line arguments
-----------------------------

.. autofunction:: ocrmypdf.pluginspec.add_options

.. autofunction:: ocrmypdf.pluginspec.check_options

Execution and progress reporting
--------------------------------

.. autoclass:: ocrmypdf.pluginspec.ProgressBar
    :members:
    :special-members: __init__, __enter__, __exit__

.. autoclass:: ocrmypdf.pluginspec.Executor
    :members:
    :special-members: __call__

.. autofunction:: ocrmypdf.pluginspec.get_logging_console

.. autofunction:: ocrmypdf.pluginspec.get_executor

.. autofunction:: ocrmypdf.pluginspec.get_progressbar_class

Applying special behavior before processing
-------------------------------------------

.. autofunction:: ocrmypdf.pluginspec.validate

PDF page to image
-----------------

.. autofunction:: ocrmypdf.pluginspec.rasterize_pdf_page

Modifying intermediate images
-----------------------------

.. autofunction:: ocrmypdf.pluginspec.filter_ocr_image

.. autofunction:: ocrmypdf.pluginspec.filter_page_image

.. autofunction:: ocrmypdf.pluginspec.filter_pdf_page

OCR engine
----------

.. autofunction:: ocrmypdf.pluginspec.get_ocr_engine

.. autoclass:: ocrmypdf.pluginspec.OcrEngine
    :members:

    .. automethod:: __str__

.. autoclass:: ocrmypdf.pluginspec.OrientationConfidence

PDF/A production
----------------

.. autofunction:: ocrmypdf.pluginspec.generate_pdfa

PDF optimization
----------------

.. autofunction:: ocrmypdf.pluginspec.optimize_pdf

.. autofunction:: ocrmypdf.pluginspec.is_optimization_enabled