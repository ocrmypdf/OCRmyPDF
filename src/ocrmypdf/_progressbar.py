# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Defines progress bar API."""

from __future__ import annotations

from typing import Protocol

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Column


class ProgressBar(Protocol):
    """The protocol that OCRmyPDF expects progress bar classes to be compatible with.

    In practice this could be used for any time of monitoring, not just a progress bar.

    Calling the class should return a new progress bar object, which is activated
    with ``__enter__`` and terminated with ``__exit__``. An update method is called
    whenever the progress bar is updated. Progress bar objects will not be reused;
    a new one will be created for each group of tasks.

    The progress bar is held in the main process/thread and not updated by child
    process/threads. When a child notifies the parent of completed work, the
    parent updates the progress bar.

    Progress bars should never write to ``sys.stdout``, or they will corrupt the
    output if OCRmyPDF writes a PDF to standard output.

    The type of events that OCRmyPDF reports to a progress bar may change in
    minor releases.
    """

    def __init__(
        self,
        *,
        total: int | float | None,
        desc: str | None,
        unit: str | None,
        disable: bool = False,
        **kwargs,
    ):
        """Initialize a progress bar.

        *total* indicates the total number of work units. If None, the total
        number of work units is unknown. If *disable* is True, the progress bar
        should be disabled. *unit* is a description of the work unit.
        *desc* is a description of the overall task to be performed.

        Unrecognized keyword arguments must be ignored, as the list of keyword
        arguments may grow with time.
        """

    def __enter__(self):
        """Enter a progress bar context."""

    def __exit__(self, *args):
        """Exit a progress bar context."""

    def update(self, n=1, *, completed=None):
        """Update the progress bar by an increment.

        For use within a progress bar context.
        """


class NullProgressBar:
    """Progress bar API that takes no actions."""

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def update(self, _arg=None, *, completed=None):
        return


class RichProgressBar:
    """Display progress bar using rich."""

    def __init__(
        self,
        *,
        console: Console,
        desc: str,
        total: float | None = None,
        unit: str | None = None,
        unit_scale: float | None = 1.0,
        disable: bool = False,
        **kwargs,
    ):
        self._entered = False
        self.progress = Progress(
            TextColumn(
                "[progress.description]{task.description}",
                table_column=Column(min_width=20),
            ),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
            auto_refresh=True,
            redirect_stderr=True,
            redirect_stdout=False,
            disable=disable,
            **kwargs,
        )
        self.unit_scale = unit_scale
        self.progress_bar = self.progress.add_task(
            desc,
            total=total * self.unit_scale
            if total is not None and self.unit_scale is not None
            else None,
            unit=unit,
        )

    def __enter__(self):
        self.progress.start()
        self._entered = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.progress.refresh()
        self.progress.stop()
        return False

    def update(self, n=1, *, completed=None):
        assert self._entered, "Progress bar must be entered before updating"
        if completed is None:
            advance = self.unit_scale if n is None else n
            self.progress.update(self.progress_bar, advance=advance)
        else:
            self.progress.update(self.progress_bar, completed=completed)
