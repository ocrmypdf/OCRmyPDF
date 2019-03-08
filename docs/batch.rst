Batch processing
================

This article provides information about running OCRmyPDF on multiple files or configuring it as a service triggered by file system events.

Batch jobs
----------

Consider using the excellent `GNU Parallel <https://www.gnu.org/software/parallel/>`_ to apply OCRmyPDF to multiple files at once.

Both ``parallel`` and ``ocrmypdf`` will try to use all available processors. To maximize parallelism without overloading your system with processes, consider using ``parallel -j 2`` to limit parallel to running two jobs at once.

This command will run all ocrmypdf all files named ``*.pdf`` in the current directory and write them to the previous created ``output/`` folder. It will not search subdirectories.

The ``--tag`` argument tells parallel to print the filename as a prefix whenever a message is printed, so that one can trace any errors to the file that produced them.

.. code-block:: bash

	parallel --tag -j 2 ocrmypdf '{}' 'output/{}' ::: *.pdf

OCRmyPDF automatically repairs PDFs before parsing and gathering information from them.

Directory trees
---------------

This will walk through a directory tree and run OCR on all files in place, printing the output in a way that makes

.. code-block:: bash

	find . -printf '%p' -name '*.pdf' -exec ocrmypdf '{}' '{}' \;
	
Alternatively, with a docker container (mounts a volume to the container where the PDFs are stored):

.. code-block:: bash

	find . -printf '%p' -name '*.pdf' -exec docker run --rm -v <host dir>:<container dir> jbarlow83/ocrmypdf-alpine '<container dir>/{}' '<container dir>/{}' \;

This only runs one ``ocrmypdf`` process at a time. This variation uses ``find`` to create a directory list and ``parallel`` to parallelize runs of ``ocrmypdf``, again updating files in place.

.. code-block:: bash

	find . -name '*.pdf' | parallel --tag -j 2 ocrmypdf '{}' '{}'


Sample script
"""""""""""""

This user contributed script also provides an example of batch processing.

.. code-block:: python

	#!/usr/bin/env python3
	# Walk through directory tree, replacing all files with OCR'd version
	# Contributed by DeliciousPickle@github

	import logging
	import os
	import subprocess
	import sys

	script_dir = os.path.dirname(os.path.realpath(__file__))
	print(script_dir + '/ocr-tree.py: Start')

	if len(sys.argv) > 1:
	    start_dir = sys.argv[1]
	else:
	    start_dir = '.'

	if len(sys.argv) > 2:
	    log_file = sys.argv[2]
	else:
	    log_file = script_dir + '/ocr-tree.log'

	logging.basicConfig(
			level=logging.INFO, format='%(asctime)s %(message)s',
			filename=log_file, filemode='w')

	for dir_name, subdirs, file_list in os.walk(start_dir):
	    logging.info('\n')
	    logging.info(dir_name + '\n')
	    os.chdir(dir_name)
	    for filename in file_list:
	        file_ext = os.path.splitext(filename)[1]
	        if file_ext == '.pdf':
	            full_path = dir_name + '/' + filename
	            print(full_path)
	            cmd = ["ocrmypdf",  "--deskew", filename, filename]
	            logging.info(cmd)
	            proc = subprocess.run(
	            	cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	            result = proc.stdout
	            if proc.returncode == 6:
	                print("Skipped document because it already contained text")
	            elif proc.returncode == 0:
	                print("OCR complete")
	            logging.info(result)

API
"""

OCRmyPDF is currently supported as a command line interface. This means that even if you are using OCRmyPDF in a Python script, you should run it in a subprocess rather importing the ocrmypdf package.

The reason for this limitation is that the `ruffus <https://github.com/bunbun/ruffus/>`_ library that OCRmyPDF depends on is unfortunately not reentrant. OCRmyPDF works by defining each operation it does as a ruffus task that takes one or more files as input and generates one or more files as output. As such ruffus is fairly fundamental.

(If you find individual functions implemented in OCRmyPDF useful (such as ``ocrmypdf.pdfinfo``), you can use these if you wish to.)


Synology DiskStations
"""""""""""""""""""""

Synology DiskStations (Network Attached Storage devices) can run the Docker image of OCRmyPDF if the Synology `Docker package <https://www.synology.com/en-global/dsm/packages/Docker>`_ is installed. Attached is a script to address particular quirks of using OCRmyPDF on one of these devices.

This is only possible for x86-based Synology products. Some Synology products use ARM or Power processors and do not support Docker. Further adjustments might be needed to deal with the Synology's relatively limited CPU and RAM.

.. code-block:: python

	#!/bin/env python3
	# Contributed by github.com/Enantiomerie

	# script needs 2 arguments
	# 1. source dir with *.pdf - default is location of script
	# 2. move dir where *.pdf and *_OCR.pdf are moved to

	import logging
	import os
	import subprocess
	import sys
	import time
	import shutil

	script_dir = os.path.dirname(os.path.realpath(__file__))
	timestamp = time.strftime("%Y-%m-%d-%H%M_")
	log_file = script_dir + '/' + timestamp + 'ocrmypdf.log'
	logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', filename=log_file, filemode='w')

	if len(sys.argv) > 1:
	    start_dir = sys.argv[1]
	else:
	    start_dir = '.'

	for dir_name, subdirs, file_list in os.walk(start_dir):
	    logging.info('\n')
	    logging.info(dir_name + '\n')
	    os.chdir(dir_name)
	    for filename in file_list:
	        file_ext = os.path.splitext(filename)[1]
	        if file_ext == '.pdf':
	            full_path = dir_name + '/' + filename
	            file_noext = os.path.splitext(filename)[0]
	            timestamp_OCR = time.strftime("%Y-%m-%d-%H%M_OCR_")
	            filename_OCR = timestamp_OCR + file_noext + '.pdf'
	            docker_mount = dir_name + ':/home/docker'
	# create string for pdf processing
	# diskstation needs a user:group docker:docker. find uid:gid of your diskstation docker:docker with id docker.
	# use this uid:gid in -u flag
	# rw rights for docker:docker at source dir are also necessary
	# the script is processed as root user via chron
	            cmd = ['docker', 'run', '--rm', '-v', docker_mount, '-u=1030:65538', 'jbarlow83/ocrmypdf', , '--deskew' , filename, filename_OCR]
	            logging.info(cmd)
	            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	            result = proc.stdout.read()
	            logging.info(result)
	            full_path_OCR = dir_name + '/' + filename_OCR
	            os.chmod(full_path_OCR, 0o666)
	            os.chmod(full_path, 0o666)
	            full_path_OCR_archive = sys.argv[2]
	            full_path_archive = sys.argv[2] + '/no_ocr'
	            shutil.move(full_path_OCR,full_path_OCR_archive)
	            shutil.move(full_path, full_path_archive)
	logging.info('Finished.\n')

Huge batch jobs
"""""""""""""""

If you have thousands of files to work with, contact the author. Consulting work related to OCRmyPDF helps fund this open source project and all inquiries are appreciated.

Hot (watched) folders
---------------------

To set up a "hot folder" that will trigger OCR for every file inserted, use a program like Python `watchdog <https://pypi.python.org/pypi/watchdog>`_ (supports all major OS).

One could then configure a scanner to automatically place scanned files in a hot folder, so that they will be queued for OCR and copied to the destination.

.. code-block:: bash

	pip install watchdog

watchdog installs the command line program ``watchmedo``, which can be told to run ``ocrmypdf`` on any .pdf added to the current directory (``.``) and place the result in the previously created ``out/`` folder.

.. code-block:: bash

	cd hot-folder
	mkdir out
	watchmedo shell-command \
		--patterns="*.pdf" \
		--ignore-directories \
		--command='ocrmypdf "${watch_src_path}" "out/${watch_src_path}" ' \
		.  # don't forget the final dot

For more complex behavior you can write a Python script around to use the watchdog API.

On file servers, you could configure watchmedo as a system service so it will run all the time.

Caveats
"""""""

* ``watchmedo`` may not work properly on a networked file system, depending on the capabilities of the file system client and server.
* This simple recipe does not filter for the type of file system event, so file copies, deletes and moves, and directory operations, will all be sent to ocrmypdf, producing errors in several cases. Disable your watched folder if you are doing anything other than copying files to it.
* If the source and destination directory are the same, watchmedo may create an infinite loop.
* On BSD, FreeBSD and older versions of macOS, you may need to increase the number of file descriptors to monitor more files, using ``ulimit -n 1024`` to watch a folder of up to 1024 files.

Alternatives
""""""""""""

* `Watchman <https://facebook.github.io/watchman/>`_ is a more powerful alternative to ``watchmedo``.

macOS Automator
---------------

You can use the Automator app with macOS, to create a Workflow or Quick Action. Use a *Run Shell Script* action in your workflow. In the context of Automator, the ``PATH`` may be set differently your Terminal's ``PATH``; you may need to explicitly set the PATH to include ``ocrmypdf``. The following example may serve as a starting point:

.. image:: images/macos-workflow.png
	:alt: Example macOS Automator script

You may customize the command sent to ocrmypdf.
