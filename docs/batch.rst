Batch processing
================

This article provides information about running OCRmyPDF on multiple files or configuring it as a service triggered by file system events.

Batch jobs
----------

Consider using the excellent `GNU Parallel <https://www.gnu.org/software/parallel/>`_ to apply OCRmyPDF to multiple files at once.

Both ``parallel`` and ``ocrmypdf`` will try to use all available processors. To maximize parallelism without overloading your system with processes, consider using ``parallel -j 2`` to limit parallel to running two jobs at once.

This command will run all ocrmypdf all files named ``*.pdf`` in the current directory and write them to the previous created ``output/`` folder.

.. code-block:: bash

	parallel -j 2 ocrmypdf '{}' 'output/{}' ::: *.pdf

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
	            proc = subprocess.Popen(
	            	cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	            result = proc.stdout.read()
	            if proc.returncode == 6:
	                print("Skipped document because it already contained text")
	            elif proc.returncode == 0:
	                print("OCR complete")
	            logging.info(result)

API
"""

OCRmyPDF is currently supported as a command line interface. Due to limitations in one of the libraries OCRmyPDF depends on, it is not yet usable as an API.


Huge batch jobs
"""""""""""""""

If you have thousands of files to work with, contact the author.


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


