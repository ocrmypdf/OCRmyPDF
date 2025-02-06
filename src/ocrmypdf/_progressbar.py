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

    Note:
        The type of events that OCRmyPDF reports to a progress bar may change in
    minor releases.

    Args:
        total (int | float | None):
            The total number of work units expected. If ``None``, the total is unknown.
            For example, if you are processing pages, this might be the number of pages,
            or if you are measuring overall progress in percent, this might be 100.
        desc (str | None):
            A brief description of the current step (e.g. "Scanning contents",
            "OCR", "PDF/A conversion"). OCRmyPDF updates this before each major step.
        unit (str | None):
            A short label for the type of work being tracked (e.g. "page", "%", "image").
        disable (bool):
            If ``True``, progress updates are suppressed (no output). Defaults to ``False``.
        **kwargs:
            Future or extra parameters that OCRmyPDF might pass. Implementations
            should accept and ignore unrecognized keywords gracefully.

    Example:
        A simple plugin implementation could look like this:

        .. code-block:: python

            from ocrmypdf.pluginspec import ProgressBar
            from ocrmypdf import hookimpl

            class ConsoleProgressBar(ProgressBar):
                def __init__(self, *, total=None, desc=None, unit=None, disable=False, **kwargs):
                    self.total = total
                    self.desc = desc
                    self.unit = unit
                    self.disable = disable
                    self.current = 0

                def __enter__(self):
                    if not self.disable:
                        print(f"Starting {self.desc or 'an OCR task'} (total={self.total} {self.unit})")
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    if not self.disable:
                        if exc_type is None:
                            print("Completed successfully.")
                        else:
                            print(f"Task ended with error: {exc_value}")
                    return False  # Let OCRmyPDF raise any exceptions

                def update(self, n=1, *, completed=None):
                    if completed is not None:
                        # If 'completed' is given, you could set self.current = completed
                        # but let's just read it to show usage
                        print(f"Absolute completion reported: {completed}")
                    # Otherwise, we increment by 'n'
                    self.current += n
                    if not self.disable:
                        if self.total:
                            percent = (self.current / self.total) * 100
                            print(f"{self.desc}: {self.current}/{self.total} ({percent:.1f}%)")
                        else:
                            print(f"{self.desc}: {self.current} units done")

            @hookimpl
            def get_progressbar_class():
                return MyProgressBar

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

        This is called once before any work is done. OCRmyPDF supplies the total
        number of units (or None if unknown), a description of the work, and the
        type of units. The ``disable`` parameter can be used to turn off progress
        reporting. Unrecognized keyword arguments should be ignored.

        Args:
            total (int | float | None):
                The total amount of work. If ``None``, the total is unknown.
            desc (str | None):
                A description of the current task. May change for different stages.
            unit (str | None):
                A short label for the unit of work.
            disable (bool):
                If ``True``, no output or logging should be displayed.
            **kwargs:
                Extra parameters that may be passed by OCRmyPDF in future versions.
        """

    def __enter__(self):
        """Enter a progress bar context."""

    def __exit__(self, *args):
        """Exit a progress bar context."""

    def update(self, n: float = 1, *, completed: float | None = None):
        """Increment the progress bar by ``n`` units, or set an absolute completion.

        OCRmyPDF calls this method repeatedly while processing pages or other tasks.
        If your total is known and you track it, you might do something like:

        .. code-block:: python

            self.current += n
            percent = (self.current / total) * 100

        The ``completed`` argument can indicate an absolute position, which is
        particularly helpful if you're tracking a percentage of work (e.g., 0 to 100)
        and want precise updates. In contrast, the incremental parameter ``n`` is
        often more useful for page-based increments.

        Args:
            n (float, optional):
                The amount to increment the progress by. Defaults to 1. May be
                fractional if OCRmyPDF performs partial steps. If you are tracking
                pages, this is typically how many pages have been processed in the
                most recent step.
            completed (float | None, optional):
                The absolute amount of work completed so far. This can override or
                supplement the simple increment logic. It's particularly useful
                for percentage-based tracking (e.g., when ``total`` is 100).
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
