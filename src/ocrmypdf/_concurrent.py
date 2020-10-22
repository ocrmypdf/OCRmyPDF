# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import logging.handlers
import multiprocessing
import os
import signal
import sys
import threading
from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool
from typing import Callable, Iterable, Optional

from tqdm import tqdm

from ocrmypdf.exceptions import InputFileError


def log_listener(queue):
    """Listen to the worker processes and forward the messages to logging

    For simplicity this is a thread rather than a process. Only one process
    should actually write to sys.stderr or whatever we're using, so if this is
    made into a process the main application needs to be directed to it.

    See https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
    """

    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:  # pylint: disable=broad-except
            import traceback  # pylint: disable=import-outside-toplevel

            print("Logging problem", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def process_sigbus(*args):
    raise InputFileError("A worker process lost access to an input file")


def process_init(queue, user_init, loglevel):
    """Initialize a process pool worker"""

    # Ignore SIGINT (our parent process will kill us gracefully)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Install SIGBUS handler (so our parent process can abort somewhat gracefully)
    if hasattr(signal, 'SIGBUS'):
        signal.signal(signal.SIGBUS, process_sigbus)

    # Reconfigure the root logger for this process to send all messages to a queue
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.setLevel(loglevel)
    root.handlers = []
    root.addHandler(h)

    if user_init:
        user_init()


def thread_init(_queue, user_init, _loglevel):
    # As a thread, block SIGBUS so the main thread deals with it...
    if hasattr(signal, 'SIGBUS'):
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGBUS})
    if user_init:
        user_init()


def exec_progress_pool(
    *,
    use_threads: bool,
    max_workers: int,
    tqdm_kwargs: dict,
    task_initializer: Optional[Callable] = None,
    task: Optional[Callable] = None,
    task_arguments: Optional[Iterable] = None,
    task_finished: Optional[Callable] = None,
):
    log_queue: multiprocessing.Queue = multiprocessing.Queue(-1)
    listener = threading.Thread(target=log_listener, args=(log_queue,))

    if use_threads:
        pool_class = ThreadPool
        initializer = thread_init
    else:
        pool_class = ProcessPool
        initializer = process_init
    listener.start()

    with tqdm(**tqdm_kwargs) as pbar:
        pool = pool_class(
            processes=max_workers,
            initializer=initializer,
            initargs=(log_queue, task_initializer, logging.getLogger("").level),
        )
        try:
            results = pool.imap_unordered(task, task_arguments)
            while True:
                try:
                    result = results.next()
                    if task_finished:
                        task_finished(result, pbar)
                    else:
                        pbar.update()
                except StopIteration:
                    break
        except KeyboardInterrupt:
            # Terminate pool so we exit instantly
            pool.terminate()
            # Don't try listener.join() here, will deadlock
            raise
        except Exception:
            if not os.environ.get("PYTEST_CURRENT_TEST", ""):
                # Unless inside pytest, exit immediately because no one wants
                # to wait for child processes to finalize results that will be
                # thrown away. Inside pytest, we want child processes to exit
                # cleanly so that they output an error messages or coverage data
                # we need from them.
                pool.terminate()
            raise
        finally:
            # Terminate log listener
            log_queue.put_nowait(None)
            pool.close()
            pool.join()

    listener.join()
