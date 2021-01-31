# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import threading
from abc import ABC, abstractmethod
from functools import partial
from typing import Callable, Iterable, Optional

from tqdm import tqdm


def _task_noop(*_args, **_kwargs):
    return


class Executor(ABC):
    pool_lock = threading.Lock()

    def __call__(
        self,
        *,
        use_threads: bool,
        max_workers: int,
        tqdm_kwargs: dict,
        worker_initializer: Optional[Callable] = None,
        task: Optional[Callable] = None,
        task_arguments: Optional[Iterable] = None,
        task_finished: Optional[Callable] = None,
    ) -> None:
        """
        Args:
            use_threads: If False, the workload is the sort that will benefit from
                running in a multiprocessing context (for example, it uses Python
                heavily, and parallelizing it with threads is not expected to be
                performant).
            max_workers: The maximum number of workers that should be run.
            tdqm_kwargs: Arguments to set up the progress bar.
            worker_initializer: Called when the worker is initialized, in the worker's
                execution context. Must be possible to marshall to the worker.
            task: Called when the worker starts a new task, in the worker's execution
                context. Must be possible to marshallable to the worker.
            task_finished: Called when a worker finishes a task, in the parent's
                context.
            task_arguments: An iterable that generates a group of parameters for each
                task. This runs in the parent's context, but the parameters must be
                marshallable to the worker.
        """

        if not task_arguments:
            return  # Nothing to do!
        if not worker_initializer:
            worker_initializer = _task_noop
        if not task_finished:
            task_finished = _task_noop
        if not task:
            task = _task_noop

        with self.pool_lock:
            self._execute(
                use_threads=use_threads,
                max_workers=max_workers,
                tqdm_kwargs=tqdm_kwargs,
                worker_initializer=worker_initializer,
                task=task,
                task_arguments=task_arguments,
                task_finished=task_finished,
            )

    @abstractmethod
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
        """Custom executors should override this method."""


def setup_executor(plugin_manager) -> Executor:
    return plugin_manager.hook.get_executor()


class SerialExecutor(Executor):
    """Implements a purely sequential executor using the parallel protocol.

    The current process/thread will be the worker that executes all tasks
    in order. As such, ``worker_initializer`` will never be called.
    """

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
        with tqdm(**tqdm_kwargs) as pbar:
            for args in task_arguments:
                result = task(args)
                task_finished(result, pbar)
