# © 2016 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import logging
import multiprocessing
import os
import shutil
import warnings
from collections import namedtuple
from collections.abc import Iterable
from contextlib import suppress
from functools import wraps
from io import StringIO
from math import isclose, isfinite
from pathlib import Path
from typing import Any, Sequence

import pikepdf

log = logging.getLogger(__name__)


class Resolution(namedtuple('Resolution', ('x', 'y'))):
    """The number of pixels per inch in each 2D direction."""

    __slots__ = ()

    def round(self, ndigits: int):
        return Resolution(round(self.x, ndigits), round(self.y, ndigits))

    def to_int(self):
        return Resolution(int(round(self.x)), int(round(self.y)))

    @property
    def is_square(self) -> bool:
        return isclose(self.x, self.y, rel_tol=1e-3)

    @property
    def is_finite(self) -> bool:
        return isfinite(self.x) and isfinite(self.y)

    def take_max(self, vals, yvals=None):
        if yvals is not None:
            return Resolution(max(self.x, *vals), max(self.y, *yvals))
        max_x, max_y = self.x, self.y
        for x, y in vals:
            max_x = max(x, max_x)
            max_y = max(y, max_y)
        return Resolution(max_x, max_y)

    def flip_axis(self):
        return Resolution(self.y, self.x)

    def __str__(self):
        return f"{self.x:f}x{self.y:f}"

    def __repr__(self):  # pragma: no cover
        return f"Resolution({self.x}x{self.y} dpi)"


class NeverRaise(Exception):
    """An exception that is never raised"""


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


def samefile(f1: os.PathLike, f2: os.PathLike):
    if os.name == 'nt':
        return f1 == f2
    else:
        return os.path.samefile(f1, f2)


def is_iterable_notstr(thing: Any) -> bool:
    """Is this is an iterable type, other than a string?"""
    return isinstance(thing, Iterable) and not isinstance(thing, str)


def monotonic(L: Sequence) -> bool:
    """Does this sequence increase monotonically?"""
    return all(b > a for a, b in zip(L, L[1:]))


def page_number(input_file: os.PathLike) -> int:
    """Get one-based page number implied by filename (000002.pdf -> 2)"""
    return int(os.path.basename(os.fspath(input_file))[0:6])


def available_cpu_count() -> int:
    """Returns number of CPUs in the system."""
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        pass
    warnings.warn(
        "Could not get CPU count.  Assuming one (1) CPU." "Use -j N to set manually."
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
        if p.exists() and p.is_file():
            return os.access(
                os.fspath(p),
                os.W_OK,
                effective_ids=(os.access in os.supports_effective_ids),
            )
        else:
            try:
                fp = p.open('wb')
            except OSError:
                return False
            else:
                fp.close()
                with suppress(OSError):
                    p.unlink()
            return True
    except (EnvironmentError, RuntimeError) as e:
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
            for msg in messages:
                if 'error' in msg.lower():
                    log.error(msg)
                else:
                    log.warning(msg)

            sio = StringIO()
            linearize_msgs = ''
            try:
                # If linearization is missing entirely, we do not complain. We do
                # complain if linearization is present but incorrect.
                pdf.check_linearization(sio)
            except RuntimeError:
                pass
            except (
                # Workaround for a problematic pikepdf version
                # pragma: no cover
                getattr(pikepdf, 'ForeignObjectError')
                if pikepdf.__version__ == '2.1.0'
                else NeverRaise
            ):
                pass
            else:
                linearize_msgs = sio.getvalue()
                if linearize_msgs:
                    log.warning(linearize_msgs)

            if not messages and not linearize_msgs:
                return True
            return False


def clamp(n, smallest, largest):  # mypy doesn't understand types for this
    """Clamps the value of ``n`` to between ``smallest`` and ``largest``."""
    return max(smallest, min(n, largest))


def remove_all_log_handlers(logger):
    "Remove all log handlers, usually used in a child process."
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()  # To ensure handlers with opened resources are released


def pikepdf_enable_mmap():
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


def deprecated(func):
    """Warn that function is deprecated."""

    @wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func
