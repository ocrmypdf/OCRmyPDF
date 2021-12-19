# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import logging.handlers
import multiprocessing
import os
import queue
import signal
import sys
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from contextlib import suppress
from multiprocessing.pool import Pool, ThreadPool
from typing import Callable, Iterable, Type, Union

from tqdm import tqdm

from ocrmypdf import Executor, hookimpl
from ocrmypdf._logging import TqdmConsole
from ocrmypdf.exceptions import InputFileError
from ocrmypdf.helpers import remove_all_log_handlers

FuturesExecutorClass = Union[Type[ThreadPoolExecutor], Type[ProcessPoolExecutor]]
Queue = Union[multiprocessing.Queue, queue.Queue]
UserInit = Callable[[], None]
WorkerInit = Callable[[Queue, UserInit, int], None]


def log_listener(q: Queue):
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


def process_init(q: Queue, user_init: UserInit, loglevel) -> None:
    """Initialize a process pool worker"""

    # Ignore SIGINT (our parent process will kill us gracefully)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Install SIGBUS handler (so our parent process can abort somewhat gracefully)
    with suppress(AttributeError):  # Windows and Cygwin do not have SIGBUS
        # Windows and Cygwin do not have pthread_sigmask or SIGBUS
        signal.signal(signal.SIGBUS, process_sigbus)

    # Remove any log handlers that belong to the parent process
    root = logging.getLogger()
    remove_all_log_handlers(root)

    # Set up our single log handler to forward messages to the parent
    root.setLevel(loglevel)
    root.addHandler(logging.handlers.QueueHandler(q))

    user_init()
    return


def thread_init(q: Queue, user_init: UserInit, loglevel) -> None:
    # As a thread, block SIGBUS so the main thread deals with it...
    with suppress(AttributeError):
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGBUS})

    user_init()
    return


class StandardExecutor(Executor):
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
        if use_threads:
            log_queue: Queue = queue.Queue(-1)
            executor_class: FuturesExecutorClass = ThreadPoolExecutor
            initializer: WorkerInit = thread_init
        else:
            log_queue = multiprocessing.Queue(-1)
            executor_class = ProcessPoolExecutor
            initializer = process_init

        # Regardless of whether we use_threads for worker processes, the log_listener
        # must be a thread. Make sure we create the listener after the worker pool,
        # so that it does not get forked into the workers.
        listener = threading.Thread(target=log_listener, args=(log_queue,))
        listener.start()

        with self.pbar_class(**tqdm_kwargs) as pbar, executor_class(
            max_workers=max_workers,
            initializer=initializer,
            initargs=(log_queue, worker_initializer, logging.getLogger("").level),
        ) as executor:
            futures = [executor.submit(task, args) for args in task_arguments]
            try:
                for future in as_completed(futures):
                    result = future.result()
                    task_finished(result, pbar)
            except KeyboardInterrupt:
                # Terminate pool so we exit instantly
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            except Exception:
                if not os.environ.get("PYTEST_CURRENT_TEST", ""):
                    # Normally we shutdown without waiting for other child workers
                    # on error, because there is no point in waiting for them. Their
                    # results will be discard. But if the condition above is True,
                    # then we are running in pytest, and we want everything to exit
                    # as cleanly as possible so that we get good error messages.
                    executor.shutdown(wait=False, cancel_futures=True)
                raise
            finally:
                # Terminate log listener
                log_queue.put_nowait(None)

        # When the above succeeds, wait for the listener thread to exit. (If
        # an exception occurs, we don't try to join, in case it deadlocks.)
        listener.join()


@hookimpl
def get_executor(progressbar_class):
    return StandardExecutor(pbar_class=progressbar_class)


@hookimpl
def get_progressbar_class():
    return tqdm


@hookimpl
def get_logging_console():
    return logging.StreamHandler(stream=TqdmConsole(sys.stderr))
