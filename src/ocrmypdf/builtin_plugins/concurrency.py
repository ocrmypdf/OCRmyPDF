# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""OCRmyPDF's multiprocessing/multithreading abstraction layer."""

from __future__ import annotations

import logging
import logging.handlers
import multiprocessing
import os
import queue
import signal
import sys
import threading
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from contextlib import suppress
from typing import Union

from rich.console import Console as RichConsole

from ocrmypdf import Executor, hookimpl
from ocrmypdf._logging import RichLoggingHandler
from ocrmypdf._progressbar import RichProgressBar
from ocrmypdf.exceptions import InputFileError
from ocrmypdf.helpers import remove_all_log_handlers

FuturesExecutorClass = Union[  # noqa: UP007
    type[ThreadPoolExecutor], type[ProcessPoolExecutor]
]
Queue = Union[multiprocessing.Queue, queue.Queue]  # noqa: UP007
UserInit = Callable[[], None]
WorkerInit = Callable[[Queue, UserInit, int], None]


def log_listener(q: Queue):
    """Listen to the worker processes and forward the messages to logging.

    For simplicity this is a thread rather than a process. Only one process
    should actually write to sys.stderr or whatever we're using, so if this is
    made into a process the main application needs to be directed to it.

    See:
    https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
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
    """Handle SIGBUS signal at the worker level."""
    raise InputFileError("A worker process lost access to an input file")


def process_init(q: Queue, user_init: UserInit, loglevel) -> None:
    """Initialize a process pool worker."""
    # Ignore SIGINT (our parent process will kill us gracefully)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Install SIGBUS handler (so our parent process can abort somewhat gracefully)
    with suppress(AttributeError):  # Windows and Cygwin do not have SIGBUS
        # Windows and Cygwin do not have pthread_sigmask or SIGBUS
        signal.signal(signal.SIGBUS, process_sigbus)

    # Remove any log handlers inherited from the parent process
    root = logging.getLogger()
    remove_all_log_handlers(root)

    # Set up our single log handler to forward messages to the parent
    root.setLevel(loglevel)
    root.addHandler(logging.handlers.QueueHandler(q))

    user_init()
    return


def thread_init(q: Queue, user_init: UserInit, loglevel) -> None:
    """Begin a thread pool worker."""
    del q  # unused but required argument
    del loglevel  # unused but required argument
    # As a thread, block SIGBUS so the main thread deals with it...
    with suppress(AttributeError):
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGBUS})

    user_init()
    return


class StandardExecutor(Executor):
    """Standard OCRmyPDF concurrent task executor."""

    def _execute(
        self,
        *,
        use_threads: bool,
        max_workers: int,
        progress_kwargs: dict,
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
        # If use_threads is False, we are currently guilty of creating a thread before
        # forking on Linux, which is not recommended. However, we take a big
        # performance hit in pdfinfo if we can't fork. Long term solution is to
        # replace most of this with an asyncio implementation, and probably to
        # migrate some of pdfinfo into C++ or Rust.
        listener = threading.Thread(target=log_listener, args=(log_queue,))
        listener.start()

        with (
            self.pbar_class(**progress_kwargs) as pbar,
            executor_class(
                max_workers=max_workers,
                initializer=initializer,
                initargs=(log_queue, worker_initializer, logging.getLogger("").level),
            ) as executor,
        ):
            futures = [executor.submit(task, *args) for args in task_arguments]
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
    """Return the default executor."""
    return StandardExecutor(pbar_class=progressbar_class)


RICH_CONSOLE = RichConsole(stderr=True)


@hookimpl
def get_progressbar_class():
    """Return the default progress bar class."""

    def partial_RichProgressBar(*args, **kwargs):
        return RichProgressBar(*args, **kwargs, console=RICH_CONSOLE)

    return partial_RichProgressBar


@hookimpl
def get_logging_console():
    """Return the default logging console handler."""
    return RichLoggingHandler(console=RICH_CONSOLE)
