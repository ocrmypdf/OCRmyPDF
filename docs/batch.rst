================
Batch processing
================

This article provides information about running OCRmyPDF on multiple
files or configuring it as a service triggered by file system events.

Batch jobs
==========

Consider using the excellent `GNU
Parallel <https://www.gnu.org/software/parallel/>`__ to apply OCRmyPDF
to multiple files at once.

Both ``parallel`` and ``ocrmypdf`` will try to use all available
processors. To maximize parallelism without overloading your system with
processes, consider using ``parallel -j 2`` to limit parallel to running
two jobs at once.

This command will run all ocrmypdf all files named ``*.pdf`` in the
current directory and write them to the previous created ``output/``
folder. It will not search subdirectories.

The ``--tag`` argument tells parallel to print the filename as a prefix
whenever a message is printed, so that one can trace any errors to the
file that produced them.

.. code-block:: bash

   parallel --tag -j 2 ocrmypdf '{}' 'output/{}' ::: *.pdf

OCRmyPDF automatically repairs PDFs before parsing and gathering
information from them.

Directory trees
===============

This will walk through a directory tree and run OCR on all files in
place, printing the output in a way that makes

.. code-block:: bash

   find . -printf '%p' -name '*.pdf' -exec ocrmypdf '{}' '{}' \;

Alternatively, with a docker container (mounts a volume to the container
where the PDFs are stored):

.. code-block:: bash

   find . -printf '%p' -name '*.pdf' -exec docker run --rm -v <host dir>:<container dir> jbarlow83/ocrmypdf '<container dir>/{}' '<container dir>/{}' \;

This only runs one ``ocrmypdf`` process at a time. This variation uses
``find`` to create a directory list and ``parallel`` to parallelize runs
of ``ocrmypdf``, again updating files in place.

.. code-block:: bash

   find . -name '*.pdf' | parallel --tag -j 2 ocrmypdf '{}' '{}'

In a Windows batch file, use

.. code-block:: bat

   for /r %%f in (*.pdf) do ocrmypdf %%f %%f

Sample script
-------------

This user contributed script also provides an example of batch
processing.

.. literalinclude:: ../misc/batch.py
    :caption: misc/batch.py

Synology DiskStations
---------------------

Synology DiskStations (Network Attached Storage devices) can run the
Docker image of OCRmyPDF if the Synology `Docker
package <https://www.synology.com/en-global/dsm/packages/Docker>`__ is
installed. Attached is a script to address particular quirks of using
OCRmyPDF on one of these devices.

This is only possible for x86-based Synology products. Some Synology
products use ARM or Power processors and do not support Docker. Further
adjustments might be needed to deal with the Synology's relatively
limited CPU and RAM.

.. literalinclude:: ../misc/synology.py
    :caption: misc/synology.py - Sample script for Synology DiskStations

Huge batch jobs
---------------

If you have thousands of files to work with, contact the author.
Consulting work related to OCRmyPDF helps fund this open source project
and all inquiries are appreciated.

Hot (watched) folders
=====================

Watched folders with Docker
---------------------------

The OCRmyPDF Docker image includes a watcher service. This service can
be launched as follows:

.. code-block:: bash

    docker run \
        -v <path to files to convert>:/input \
        -v <path to store results>:/output \
        -e OCR_OUTPUT_DIRECTORY_YEAR_MONTH=1 \
        -e OCR_ON_SUCCESS_DELETE=1 \
        -e OCR_DESKEW=1 \
        -e PYTHONUNBUFFERED=1 \
        -it --entrypoint python3 \
        jbarlow83/ocrmypdf \
        watcher.py

This service will watch for a file that matches ``/input/\*.pdf`` and will
convert it to a OCRed PDF in ``/output/``. The parameters to this image are:

.. csv-table:: watcher.py parameters for Docker
    :header: "Parameter", "Description"
    :widths: 50, 50

    "``-v <path to files to convert>:/input``", "Files placed in this location will be OCRed"
    "``-v <path to store results>:/output``", "This is where OCRed files will be stored"
    "``-e OCR_OUTPUT_DIRECTORY_YEAR_MONTH=1``", "This will place files in the output in {output}/{year}/{month}/{filename}"
    "``-e OCR_ON_SUCCESS_DELETE=1``", "This will delete the input file if the exit code is 0 (OK)"
    "``-e OCR_DESKEW=1``", "This will enable deskew for crooked PDFs"
    "``-e PYTHONBUFFERED=1``", "This will force STDOUT to be unbuffered and allow you to see messages in docker logs"

This service relies on polling to check for changes to the filesystem. It
may not be suitable for some environments, such as filesystems shared on a
slow network.

A configuration manager such as Docker Compose could be used to ensure that the
service is always available.

.. literalinclude:: ../misc/docker-compose.example.yml
    :language: yaml
    :caption: misc/docker-compose.example.yml

Watched folders with watcher.py
-------------------------------

The watcher service may also be run natively, without Docker:

.. code-block:: bash

    pip3 install -r requirements/watcher.txt

    env OCR_INPUT_DIRECTORY=/mnt/input-pdfs \
        OCR_OUTPUT_DIRECTORY=/mnt/output-pdfs \
        OCR_OUTPUT_DIRECTORY_YEAR_MONTH=1 \
        python3 watcher.py

Watched folders with CLI
------------------------

To set up a "hot folder" that will trigger OCR for every file inserted,
use a program like Python
`watchdog <https://pypi.python.org/pypi/watchdog>`__ (supports all major
OS).

One could then configure a scanner to automatically place scanned files
in a hot folder, so that they will be queued for OCR and copied to the
destination.

.. code-block:: bash

   pip install watchdog

watchdog installs the command line program ``watchmedo``, which can be
told to run ``ocrmypdf`` on any .pdf added to the current directory
(``.``) and place the result in the previously created ``out/`` folder.

.. code-block:: bash

   cd hot-folder
   mkdir out
   watchmedo shell-command \
       --patterns="*.pdf" \
       --ignore-directories \
       --command='ocrmypdf "${watch_src_path}" "out/${watch_src_path}" ' \
       .  # don't forget the final dot

On file servers, you could configure watchmedo as a system service so it
will run all the time.

For more complex behavior you can write a Python script around to use
the watchdog API. You can refer to the watcher.py script as an example.

Caveats
-------

-  ``watchmedo`` may not work properly on a networked file system,
   depending on the capabilities of the file system client and server.
-  This simple recipe does not filter for the type of file system event,
   so file copies, deletes and moves, and directory operations, will all
   be sent to ocrmypdf, producing errors in several cases. Disable your
   watched folder if you are doing anything other than copying files to
   it.
-  If the source and destination directory are the same, watchmedo may
   create an infinite loop.
-  On BSD, FreeBSD and older versions of macOS, you may need to increase
   the number of file descriptors to monitor more files, using
   ``ulimit -n 1024`` to watch a folder of up to 1024 files.

Alternatives
------------

-  On Linux, `systemd user services <https://wiki.archlinux.org/index.php/Systemd/User>`__
   can be configured to automatically perform OCR on a collection of files.

-  `Watchman <https://facebook.github.io/watchman/>`__ is a more
   powerful alternative to ``watchmedo``.

macOS Automator
===============

You can use the Automator app with macOS, to create a Workflow or Quick
Action. Use a *Run Shell Script* action in your workflow. In the context
of Automator, the ``PATH`` may be set differently your Terminal's
``PATH``; you may need to explicitly set the PATH to include
``ocrmypdf``. The following example may serve as a starting point:

.. figure:: images/macos-workflow.png
    :alt: Example macOS Automator workflow

You may customize the command sent to ocrmypdf.
