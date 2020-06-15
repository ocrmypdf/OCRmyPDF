=======
Plugins
=======

You can use plugins to customize the behavior of OCRmyPDF at certain points of
interest.

Currently, it is possible to:

- add new command line arguments
- override the decision for whether or not to perform OCR on a particular file
- modify the image is about to be sent for OCR
- modify the page image before it is converted to PDF

OCRmyPDF plugins are based on the Python ``pluggy`` package and conform to its
conventions. Note that: plugins installed with as setuptools entrypoints are
not checked currently, because OCRmyPDF assumes you may not want to enable
plugins for all files. Also, plugins must be functions, not classes.

How plugins are imported
========================

Plugins are imported on demand, by the OCRmyPDF worker process that needs to use
them. As such, plugins cannot share state with other plugins, cannot rely on
their module's or the interpreter's global state, and should expect asynchronous
copies of themselves to be running. Plugins can write intermediate files to the
folder specified in ``options.work_folder``.

Plugins should work whether executed in threads or processes.

Script plugins
==============

Script plugins may be called from the command line, by specifying the name of a file.

.. code-block:: bash

    ocrmypdf --plugin example_plugin.py input.pdf output.pdf

Multiple plugins may be called by issuing the ``--plugin`` argument multiple times.

Packaged plugins
================

Installed plugins may be installed into the same virtual environment as OCRmyPDF
is installed into. They may be invoked using Python standard module naming.

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

Plugin hooks
============

A plugin may provide the following hooks. Hooks should be decorated with
``ocrmypdf.hookimpl``, for example:

.. code-block:: python

    from ocrmpydf import hookimpl

    @hookimpl
    def add_options(parser):
        pass

The following is a complete list of hooks that may be installed and when
they are called.

.. automodule:: ocrmypdf.pluginspec
    :members:
