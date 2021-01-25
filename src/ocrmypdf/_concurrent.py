# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import threading
from typing import Callable, Iterable, Optional

pool_lock = threading.Lock()


def _task_noop(*_args, **_kwargs):
    return


def _model(**_kwargs) -> None:
    raise RuntimeError("Parallel executor not set up")


def set_execution_model(model):
    global _model
    _model = model


def exec_progress_pool(
    *,
    use_threads: bool,
    max_workers: int,
    tqdm_kwargs: dict,
    worker_initializer: Optional[Callable] = None,
    task: Callable,
    task_arguments: Optional[Iterable] = None,
    task_finished: Optional[Callable] = None,
):
    if not worker_initializer:
        worker_initializer = _task_noop
    if not task_finished:
        task_finished = _task_noop

    with pool_lock:
        _model(
            use_threads=use_threads,
            max_workers=max_workers,
            tqdm_kwargs=tqdm_kwargs,
            worker_initializer=worker_initializer,
            task=task,
            task_arguments=task_arguments,
            task_finished=task_finished,
        )
