======================
Using the OCRmyPDF API
======================

OCRmyPDF originated as a command line program and continues to have this
legacy, but parts of it can be imported and used in other Python
applications.

Some applications may want to consider running ocrmypdf from a
subprocess call anyway, as this provides isolation of its activities.

Example
=======

OCRmyPDF one high-level function to run its main engine from an
application. The parameters are symmetric to the command line arguments
and largely have the same functions.

.. code-block:: python

    import ocrmypdf

    ocrmypdf.ocr('input.pdf', 'output.pdf', deskew=True)

With a few exceptions, all of the command line arguments are available
and may be passed as equivalent keywords.

A few differences are that ``verbose`` and ``quiet`` are not available.
Instead, output should be managed by configuring logging.

Parent process requirements
---------------------------

The :func:`ocrmypdf.ocr` function runs OCRmyPDF similar to command line
execution. To do this, it will:

- create a monitoring thread
- create worker processes (forking itself)
- manage the signal flags of worker processes
- execute other subprocesses (forking and executing other programs)

The Python process that calls ``ocrmypdf.ocr()`` must be sufficiently
privileged to perform these actions. If it is not, ``ocrmypdf()`` will
fail.

There is no currently no option to manage how jobs are scheduled other
than the argument ``jobs=`` which will limit the number of worker
processes.

Forking a child process to call ``ocrmypdf.ocr()`` is suggested. That
way your application will survive and remain interactive even if
OCRmyPDF does not.

Logging
-------

OCRmyPDF will log under loggers named ``ocrmypdf``. In addition, it
imports ``pdfminer`` and ``PIL``, both of which post log messages under
those logging namespaces.

You can configure the logging as desired for your application or call
:func:`ocrmypdf.configure_logging` to configure logging the same way
OCRmyPDF itself does. The command line parameters such as ``--quiet``
and ``--verbose`` have no equivalents in the API; you must use the
provided configuration function or do configuration in a way that suits
your use case.

Progress monitoring
-------------------

OCRmyPDF uses the ``tqdm`` package to implement its progress bars.
:func:`ocrmypdf.configure_logging` will set up logging output to
``sys.stderr`` in a way that is compatible with the display of the
progress bar.

Exceptions
----------

OCRmyPDF may throw standard Python exceptions, ``ocrmypdf.exceptions.*``
exceptions, some exceptions related to multiprocessing, and
``KeyboardInterrupt``. The parent process should provide an exception
handler. OCRmyPDF will clean up its temporary files and worker processes
automatically when an exception occurs.

Programs that call OCRmyPDF should consider trapping KeyboardInterrupt
so that they allow OCR to terminate with the whole program terminating.

When OCRmyPDF succeeds conditionally, it returns an integer exit code.

Reference
---------

.. autofunction:: ocrmypdf.ocr

.. autoclass:: ocrmypdf.Verbosity
    :members:
    :undoc-members:

.. autoclass:: ocrmypdf.ExitCode
    :members:
    :undoc-members:

.. autofunction:: ocrmypdf.configure_logging
