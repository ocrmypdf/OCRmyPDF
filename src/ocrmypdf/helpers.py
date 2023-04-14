# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Support functions."""

from __future__ import annotations

import logging
import multiprocessing
import os
import shutil
import warnings
from collections.abc import Iterable
from contextlib import suppress
from io import StringIO
from math import isclose, isfinite
from pathlib import Path
from typing import Any, Generic, Sequence, SupportsFloat, SupportsRound, TypeVar

import img2pdf
import pikepdf
from packaging.version import Version

log = logging.getLogger(__name__)

if Version(img2pdf.__version__) < Version('0.4.0'):
    IMG2PDF_KWARGS = dict(without_pdfw=True)
elif Version(img2pdf.__version__) < Version('0.4.3'):
    IMG2PDF_KWARGS = dict(engine=img2pdf.Engine.pikepdf)
else:
    IMG2PDF_KWARGS = dict(
        engine=img2pdf.Engine.pikepdf, rotation=img2pdf.Rotation.ifvalid
    )


T = TypeVar('T', bound=SupportsRound[Any])


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
        if isinstance(self.x, SupportsFloat) and isinstance(self.y, SupportsFloat):
            return isfinite(self.x) and isfinite(self.y)
        return True

    def take_max(
        self, vals: Iterable[Any], yvals: Iterable[Any] | None = None
    ) -> Resolution:
        """Return a new Resolution object with the maximum resolution of inputs."""
        if yvals is not None:
            return Resolution(max(self.x, *vals), max(self.y, *yvals))
        max_x, max_y = self.x, self.y
        for x, y in vals:
            max_x = max(x, max_x)
            max_y = max(y, max_y)
        return Resolution(max_x, max_y)

    def flip_axis(self) -> Resolution[T]:
        """Return a new Resolution object with x and y swapped."""
        return Resolution(self.y, self.x)

    def __getitem__(self, idx: int | slice) -> T:
        """Support [0] and [1] indexing."""
        return (self.x, self.y)[idx]

    def __str__(self):
        """Return a string representation of the resolution."""
        return f"{self.x:f}x{self.y:f}"

    def __repr__(self):  # pragma: no cover
        """Return a repr() of the resolution."""
        return f"Resolution({self.x}x{self.y} dpi)"

    def __eq__(self, other):
        """Return True if the resolution is equal to another resolution."""
        if isinstance(other, tuple) and len(other) == 2:
            other = Resolution(*other)
        if not isinstance(other, Resolution):
            return NotImplemented
        return self._isclose(self.x, other.x) and self._isclose(self.y, other.y)


class NeverRaise(Exception):
    """An exception that is never raised."""


def safe_symlink(input_file: os.PathLike, soft_link_name: os.PathLike):
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
            "No symbolic link created. You are using  the original data directory "
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


def samefile(file1: os.PathLike, file2: os.PathLike):
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


def clamp(n, smallest, largest):  # mypy doesn't understand types for this
    """Clamps the value of ``n`` to between ``smallest`` and ``largest``."""
    return max(smallest, min(n, largest))


def remove_all_log_handlers(logger):
    """Remove all log handlers, usually used in a child process.

    The child process inherits the log handlers from the parent process when
    a fork occurs. Typically we want to remove all log handlers in the child
    process so that the child process can set up a single queue handler to
    forward log messages to the parent process.
    """
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()  # To ensure handlers with opened resources are released


def pikepdf_enable_mmap():
    """Enable pikepdf mmap."""
    # try:
    #     if pikepdf._qpdf.set_access_default_mmap(True):
    #         log.debug("pikepdf mmap enabled")
    # except AttributeError:
    #     log.debug("pikepdf mmap not available")
    # We found a race condition probably related to pybind issue #2252 that can
    # cause a crash. For now, disable pikepdf mmap to be on the safe side.
    # Fix is not in pybind11 2.6.0
    # log.debug("pikepdf mmap disabled")
    return
