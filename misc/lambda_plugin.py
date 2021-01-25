# © 2021 James R Barlow: https://github.com/jbarlow83
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Alternate executor to support OCRmyPDF in AWS Lambda"""


import logging
import logging.handlers
import multiprocessing
import os
import queue
import signal
import sys
import threading
from contextlib import suppress
from itertools import islice, repeat, takewhile, zip_longest
from multiprocessing import Pipe, Process, process
from multiprocessing.connection import Connection, wait
from typing import Callable, Iterable, Optional, Union
from unittest.mock import Mock

from ocrmypdf import hookimpl
from ocrmypdf.exceptions import InputFileError

pool_lock = threading.Lock()


def split_every(n: int, iterable: Iterable):
    iterator = iter(iterable)
    return takewhile(bool, (list(islice(iterator, n)) for _ in repeat(None)))


def log_listener(q):
    """Listen to the worker processes and forward the messages to logging

    For simplicity this is a thread rather than a process. Only one process
    should actually write to sys.stderr or whatever we're using, so if this is
    made into a process the main application needs to be directed to it.

    See https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
    """

    while True:
        try:
            record = q.get()
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


def process_loop(
    conn: Connection, user_init: Callable[[], None], loglevel, task, task_args
):
    """Initialize a process pool worker"""

    # Ignore SIGINT (our parent process will kill us gracefully)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Install SIGBUS handler (so our parent process can abort somewhat gracefully)
    with suppress(AttributeError):  # Windows and Cygwin do not have SIGBUS
        # Windows and Cygwin do not have pthread_sigmask or SIGBUS
        signal.signal(signal.SIGBUS, process_sigbus)

    # Reconfigure the root logger for this process to send all messages to a queue
    # h = logging.handlers.QueueHandler(q)
    # root = logging.getLogger()
    # root.setLevel(loglevel)
    # root.handlers = []
    # root.addHandler(h)

    user_init()

    for args in task_args:
        try:
            result = task(*args)
        except Exception as e:
            return  # for now
        else:
            conn.send(result)

    conn.close()
    return


def exec_progress_pool(
    *,
    use_threads: bool,
    max_workers: int,
    tqdm_kwargs: dict,
    worker_initializer: Optional[Callable],
    task: Callable,
    task_arguments: Optional[Iterable] = None,
    task_finished: Callable,
):

    if not worker_initializer:

        def _noop():
            return

        worker_initializer = _noop

    with pool_lock:
        _exec_progress_pool(
            max_workers=max_workers,
            worker_initializer=worker_initializer,
            task=task,
            task_arguments=task_arguments,
            task_finished=task_finished,
        )


def _exec_progress_pool(
    *,
    max_workers: int,
    worker_initializer: Callable,
    task: Callable,
    task_arguments: Optional[Iterable] = None,
    task_finished: Callable,
):
    pbar = Mock()

    task_arguments = list(task_arguments)
    grouped_args = list(zip_longest(*list(split_every(max_workers, task_arguments))))

    processes = []
    connections = []
    for n in range(max_workers):
        parent_conn, child_conn = Pipe()

        worker_args = [args for args in grouped_args[n] if args is not None]
        process = Process(
            target=process_loop,
            args=(
                child_conn,
                worker_initializer,
                logging.getLogger("").level,
                task,
                worker_args,
            ),
        )
        process.daemon = True
        processes.append(process)
        connections.append(parent_conn)

    for process in processes:
        process.start()

    while connections:
        for r in wait(connections):
            try:
                msg = r.recv()
            except EOFError:
                connections.remove(r)
            else:
                if task_finished:
                    task_finished(msg, pbar)

    for process in processes:
        process.join()


@hookimpl
def get_parallel_executor():
    return exec_progress_pool
