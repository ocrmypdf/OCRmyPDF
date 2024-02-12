.. SPDX-FileCopyrightText: 2022 James R. Barlow
..
.. SPDX-License-Identifier: CC-BY-SA-4.0

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

OCRmyPDF provides one high-level function to run its main engine from an
application. The parameters are symmetric to the command line arguments
and largely have the same functions.

.. code-block:: python

    import ocrmypdf

    if __name__ == '__main__':  # To ensure correct behavior on Windows and macOS
        ocrmypdf.ocr('input.pdf', 'output.pdf', deskew=True)

With some exceptions, all of the command line arguments are available
and may be passed as equivalent keywords.

A few differences are that ``verbose`` and ``quiet`` are not available.
Instead, output should be managed by configuring logging.

Parent process requirements
---------------------------

The :func:`ocrmypdf.ocr` function runs OCRmyPDF similar to command line
execution. To do this, it will:

- create worker processes or threads
- manage the signal flags of its worker processes
- execute other subprocesses (forking and executing other programs)

The Python process that calls :func:`ocrmypdf.ocr()` must be sufficiently
privileged to perform these actions.

There currently is no option to manage how jobs are scheduled other
than the argument ``jobs=`` which will limit the number of worker
processes.

Creating a child process to call :func:`ocrmypdf.ocr()` is suggested. That
way your application will survive and remain interactive even if
OCRmyPDF fails for any reason. For example:

.. code-block:: python

    from multiprocessing import Process

    def ocrmypdf_process():
        ocrmypdf.ocr('input.pdf', 'output.pdf')

    def call_ocrmypdf_from_my_app():
        p = Process(target=ocrmypdf_process)
        p.start()
        p.join()

Programs that call :func:`ocrmypdf.ocr()` should also install a SIGBUS signal
handler (except on Windows), to raise an exception if access to a memory
mapped file fails. OCRmyPDF may use memory mapping.

:func:`ocrmypdf.ocr()` will take a threading lock to prevent multiple runs of itself
in the same Python interpreter process. This is not thread-safe, because of how
OCRmyPDF's plugins and Python's library import system work. If you need to parallelize
OCRmyPDF, use processes.

.. warning::

    On Windows and macOS, the script that calls :func:`ocrmypdf.ocr()` must be
    protected by an "ifmain" guard (``if __name__ == '__main__'``). If you do
    not take at least one of these steps, process semantics will prevent
    OCRmyPDF from working correctly.

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

OCRmyPDF uses the ``rich`` package to implement its progress bars.
:func:`ocrmypdf.configure_logging` will set up logging output to
``sys.stderr`` in a way that is compatible with the display of the
progress bar. Use ``ocrmypdf.ocr(...progress_bar=False)`` to disable
the progress bar.

Standard output
---------------

OCRmyPDF is strict about not writing to standard output so that
users can safely use it in a pipeline and produce a valid output
file. A caller application will have to ensure it does not write to
standard output either, if it wants to be compatible with this
behavior and support piping to a file. Another benefit of running
OCRmyPDF in a child process, as recommended above, is that it will
not interfere with the parent process's standard output.

Exceptions
----------

OCRmyPDF may throw standard Python exceptions, ``ocrmypdf.exceptions.*``
exceptions, some exceptions related to multiprocessing, and
:exc:`KeyboardInterrupt`. The parent process should provide an exception
handler. OCRmyPDF will clean up its temporary files and worker processes
automatically when an exception occurs.

When OCRmyPDF succeeds conditionally, it returns an integer exit code.
