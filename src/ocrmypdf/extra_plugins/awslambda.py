# © 2021 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Alternate executor to support OCRmyPDF in AWS Lambda"""


import logging
import logging.handlers
import signal
from contextlib import suppress
from enum import Enum, auto
from itertools import islice, repeat, takewhile, zip_longest
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection, wait
from typing import Callable, Iterable, Optional
from unittest.mock import Mock

from ocrmypdf import Executor, hookimpl
from ocrmypdf.exceptions import InputFileError


class MessageType(Enum):
    exception = auto()
    result = auto()
    complete = auto()


def split_every(n: int, iterable: Iterable):
    iterator = iter(iterable)
    return takewhile(bool, (list(islice(iterator, n)) for _ in repeat(None)))


def process_sigbus(*args):
    raise InputFileError("A worker process lost access to an input file")


class ConnectionLogHandler(logging.handlers.QueueHandler):
    def __init__(self, conn: Connection) -> None:
        super().__init__(None)
        self.conn = conn

    def enqueue(self, record):
        self.conn.send(('log', record))


def process_loop(
    conn: Connection, user_init: Callable[[], None], loglevel, task, task_args
):
    """Initialize a process pool worker"""

    # Install SIGBUS handler (so our parent process can abort somewhat gracefully)
    with suppress(AttributeError):  # Windows and Cygwin do not have SIGBUS
        # Windows and Cygwin do not have pthread_sigmask or SIGBUS
        signal.signal(signal.SIGBUS, process_sigbus)

    # Reconfigure the root logger for this process to send all messages to a queue
    h = ConnectionLogHandler(conn)
    root = logging.getLogger()
    root.setLevel(loglevel)
    root.handlers = []
    root.addHandler(h)

    user_init()

    for args in task_args:
        try:
            result = task(args)
        except Exception as e:
            conn.send((MessageType.exception, e))
            break
        else:
            conn.send((MessageType.result, result))

    conn.send((MessageType.complete, None))
    conn.close()
    return


class LambdaExecutor(Executor):
    def _execute(
        self,
        *,
        use_threads: bool,
        max_workers: int,
        tqdm_kwargs: dict,
        worker_initializer: Callable,
        task: Callable,
        task_arguments: Iterable,
        task_finished: Callable,
    ):
        pbar = Mock()

        if use_threads and max_workers == 1:
            for args in task_arguments:
                result = task(args)
                task_finished(result, pbar)
            return

        self._lambda_pool_impl(
            max_workers=max_workers,
            worker_initializer=worker_initializer,
            task=task,
            task_arguments=task_arguments,
            task_finished=task_finished,
            pbar=pbar,
        )

    def _lambda_pool_impl(
        self,
        *,
        max_workers: int,
        worker_initializer: Callable,
        task: Callable,
        task_arguments: Iterable,
        task_finished: Callable,
        pbar,
    ):
        task_arguments = list(task_arguments)
        grouped_args = list(
            zip_longest(*list(split_every(max_workers, task_arguments)))
        )
        if not grouped_args:
            return

        processes = []
        connections = []
        for chunk in grouped_args:
            parent_conn, child_conn = Pipe()

            worker_args = [args for args in chunk if args is not None]
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
                    msg_type, msg = r.recv()
                except EOFError:
                    connections.remove(r)
                    continue

                if msg_type == MessageType.result:
                    if task_finished:
                        task_finished(msg, pbar)
                elif msg_type == 'log':
                    record = msg
                    logger = logging.getLogger(record.name)
                    logger.handle(record)
                elif msg_type == MessageType.complete:
                    connections.remove(r)
                elif msg_type == MessageType.exception:
                    for process in processes:
                        process.terminate()
                    raise msg

        for process in processes:
            process.join()


@hookimpl
def get_executor():
    return LambdaExecutor()
