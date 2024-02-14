# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Support functions."""

from __future__ import annotations

import logging
import multiprocessing
import os
import shutil
import warnings
from collections.abc import Callable, Iterable, Sequence
from contextlib import suppress
from decimal import Decimal
from io import StringIO
from math import isclose, isfinite
from pathlib import Path
from statistics import harmonic_mean
from typing import (
    Any,
    Generic,
    TypeVar,
)

import img2pdf
import pikepdf
from deprecation import deprecated

log = logging.getLogger(__name__)

IMG2PDF_KWARGS = dict(engine=img2pdf.Engine.pikepdf, rotation=img2pdf.Rotation.ifvalid)


T = TypeVar('T', float, int, Decimal)


class Resolution(Generic[T]):
    """The number of pixels per inch in each 2D direction.

    Resolution objects are considered "equal" for == purposes if they are
    equal to a reasonable tolerance.
    """

    x: T
    y: T

    __slots__ = ('x', 'y')

    def __init__(self, x: T, y: T):
        """Construct a Resolution object."""
        self.x = x
        self.y = y

    # rel_tol after converting from dpi to pixels per meter and saving
    # as integer with rounding, as many file formats
    CONVERSION_ERROR = 0.002

    def round(self, ndigits: int) -> Resolution:
        """Round to ndigits after the decimal point."""
        return Resolution(round(self.x, ndigits), round(self.y, ndigits))

    def to_int(self) -> Resolution[int]:
        """Round to nearest integer."""
        return Resolution(int(round(self.x)), int(round(self.y)))

    @classmethod
    def _isclose(cls, a, b):
        return isclose(a, b, rel_tol=cls.CONVERSION_ERROR)

    @property
    def is_square(self) -> bool:
        """True if the resolution is square (x == y)."""
        return self._isclose(self.x, self.y)

    @property
    def is_finite(self) -> bool:
        """True if both x and y are finite numbers."""
        return isfinite(self.x) and isfinite(self.y)

    def to_scalar(self) -> float:
        """Return the harmonic mean of x and y as a 1D approximation.

        In most cases, Resolution is 2D, but typically it is "square" (x == y) and
        can be approximated as a single number. When not square, the harmonic mean
        is used to approximate the 2D resolution as a single number.
        """
        return harmonic_mean([float(self.x), float(self.y)])

    def _take_minmax(
        self, vals: Iterable[Any], yvals: Iterable[Any] | None, cmp: Callable
    ) -> Resolution:
        """Return a new Resolution object with the maximum resolution of inputs."""
        if yvals is not None:
            return Resolution(cmp(self.x, *vals), cmp(self.y, *yvals))
        cmp_x, cmp_y = self.x, self.y
        for x, y in vals:
            cmp_x = cmp(x, cmp_x)
            cmp_y = cmp(y, cmp_y)
        return Resolution(cmp_x, cmp_y)

    def take_max(
        self, vals: Iterable[Any], yvals: Iterable[Any] | None = None
    ) -> Resolution:
        """Return a new Resolution object with the maximum resolution of inputs."""
        return self._take_minmax(vals, yvals, max)

    def take_min(
        self, vals: Iterable[Any], yvals: Iterable[Any] | None = None
    ) -> Resolution:
        """Return a new Resolution object with the minimum resolution of inputs."""
        return self._take_minmax(vals, yvals, min)

    def flip_axis(self) -> Resolution[T]:
        """Return a new Resolution object with x and y swapped."""
        return Resolution(self.y, self.x)

    def __getitem__(self, idx: int | slice) -> T:
        """Support [0] and [1] indexing."""
        return (self.x, self.y)[idx]

    def __str__(self):
        """Return a string representation of the resolution."""
        return f"{self.x:f}×{self.y:f}"

    def __repr__(self):  # pragma: no cover
        """Return a repr() of the resolution."""
        return f"Resolution({self.x!r}, {self.y!r})"

    def __eq__(self, other):
        """Return True if the resolution is equal to another resolution."""
        if isinstance(other, tuple) and len(other) == 2:
            other = Resolution(*other)
        if not isinstance(other, Resolution):
            return NotImplemented
        return self._isclose(self.x, other.x) and self._isclose(self.y, other.y)


@deprecated(deprecated_in='15.4.0')
class NeverRaise(Exception):
    """An exception that is never raised."""


def safe_symlink(input_file: os.PathLike, soft_link_name: os.PathLike) -> None:
    """Create a symbolic link at ``soft_link_name``, which references ``input_file``.

    Think of this as copying ``input_file`` to ``soft_link_name`` with less overhead.

    Use symlinks safely. Self-linking loops are prevented. On Windows, file copy is
    used since symlinks may require administrator privileges. An existing link at the
    destination is removed.
    """
    input_file = os.fspath(input_file)
    soft_link_name = os.fspath(soft_link_name)

    # Guard against soft linking to oneself
    if input_file == soft_link_name:
        log.warning(
            "No symbolic link created. You are using the original data directory "
            "as the working directory."
        )
        return

    # Soft link already exists: delete for relink?
    if os.path.lexists(soft_link_name):
        # do not delete or overwrite real (non-soft link) file
        if not os.path.islink(soft_link_name):
            raise FileExistsError(f"{soft_link_name} exists and is not a link")
        os.unlink(soft_link_name)

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"trying to create a broken symlink to {input_file}")

    if os.name == 'nt':
        # Don't actually use symlinks on Windows due to permission issues
        shutil.copyfile(input_file, soft_link_name)
        return

    log.debug("os.symlink(%s, %s)", input_file, soft_link_name)

    # Create symbolic link using absolute path
    os.symlink(os.path.abspath(input_file), soft_link_name)


def samefile(file1: os.PathLike, file2: os.PathLike) -> bool:
    """Return True if two files are the same file.

    Attempts to account for different relative paths to the same file.
    """
    if os.name == 'nt':
        return file1 == file2
    else:
        return os.path.samefile(file1, file2)


def is_iterable_notstr(thing: Any) -> bool:
    """Is this is an iterable type, other than a string?"""
    return isinstance(thing, Iterable) and not isinstance(thing, str)


def monotonic(seq: Sequence) -> bool:
    """Does this sequence increase monotonically?"""
    return all(b > a for a, b in zip(seq, seq[1:]))


def page_number(input_file: os.PathLike) -> int:
    """Get one-based page number implied by filename (000002.pdf -> 2)."""
    return int(os.path.basename(os.fspath(input_file))[0:6])


def available_cpu_count() -> int:
    """Returns number of CPUs in the system."""
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        pass
    warnings.warn(
        "Could not get CPU count. Assuming one (1) CPU. Use -j N to set manually."
    )
    return 1


def is_file_writable(test_file: os.PathLike) -> bool:
    """Intentionally racy test if target is writable.

    We intend to write to the output file if and only if we succeed and
    can replace it atomically. Before doing the OCR work, make sure
    the location is writable.
    """
    try:
        p = Path(test_file)
        if p.is_symlink():
            p = p.resolve(strict=False)

        # p.is_file() throws an exception in some cases
        if p.exists() and (p.is_file() or p.samefile(os.devnull)):
            return os.access(
                os.fspath(p),
                os.W_OK,
                effective_ids=(os.access in os.supports_effective_ids),
            )

        try:
            fp = p.open('wb')
        except OSError:
            return False
        else:
            fp.close()
            with suppress(OSError):
                p.unlink()
        return True
    except (OSError, RuntimeError) as e:
        log.debug(e)
        log.error(str(e))
        return False


def check_pdf(input_file: Path) -> bool:
    """Check if a PDF complies with the PDF specification.

    Checks for proper formatting and proper linearization. Uses pikepdf (which in
    turn, uses QPDF) to perform the checks.
    """
    try:
        pdf = pikepdf.open(input_file)
    except pikepdf.PdfError as e:
        log.error(e)
        return False
    else:
        with pdf:
            messages = pdf.check()
            success = True
            for msg in messages:
                if 'error' in msg.lower():
                    log.error(msg)
                    success = False
                elif (
                    "/DecodeParms: operation for dictionary attempted on object "
                    "of type null" in msg
                ):
                    pass  # Ignore/spurious warning
                else:
                    log.warning(msg)
                    success = False

            sio = StringIO()
            linearize_msgs = ''
            try:
                # If linearization is missing entirely, we do not complain. We do
                # complain if linearization is present but incorrect.
                pdf.check_linearization(sio)
            except (RuntimeError, pikepdf.ForeignObjectError):
                pass
            else:
                linearize_msgs = sio.getvalue()
                if linearize_msgs:
                    log.warning(linearize_msgs)

            if success and not linearize_msgs:
                return True
            return False


def clamp(n: T, smallest: T, largest: T) -> T:
    """Clamps the value of ``n`` to between ``smallest`` and ``largest``."""
    return max(smallest, min(n, largest))


def remove_all_log_handlers(logger: logging.Logger) -> None:
    """Remove all log handlers, usually used in a child process.

    The child process inherits the log handlers from the parent process when
    a fork occurs. Typically we want to remove all log handlers in the child
    process so that the child process can set up a single queue handler to
    forward log messages to the parent process.
    """
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()  # To ensure handlers with opened resources are released


def pikepdf_enable_mmap() -> None:
    """Enable pikepdf memory mapping."""
    try:
        pikepdf._core.set_access_default_mmap(True)
        log.debug(
            "pikepdf mmap "
            + (
                'enabled'
                if pikepdf._core.get_access_default_mmap()  # type: ignore[attr-defined]
                else 'disabled'
            )
        )
    except AttributeError:
        log.debug("pikepdf mmap not available")
