# © 2016 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

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
from math import isclose
from pathlib import Path

import pikepdf

log = logging.getLogger(__name__)


class Resolution(namedtuple('Resolution', ('x', 'y'))):
    __slots__ = ()

    def round(self, ndigits):
        return Resolution(round(self.x, ndigits), round(self.y, ndigits))

    def to_int(self):
        return Resolution(int(round(self.x)), int(round(self.y)))

    @property
    def is_square(self):
        return isclose(self.x, self.y, rel_tol=1e-3)

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

    def __repr__(self):
        return f"Resolution({self.x}x{self.y} dpi)"


def safe_symlink(input_file: os.PathLike, soft_link_name: os.PathLike):
    """
    Helper function: relinks soft symbolic link if necessary
    """
    input_file = os.fspath(input_file)
    soft_link_name = os.fspath(soft_link_name)

    # Guard against soft linking to oneself
    if input_file == soft_link_name:
        log.warning(
            "No symbolic link made. You are using "
            "the original data directory as the working directory."
        )
        return

    # Soft link already exists: delete for relink?
    if os.path.lexists(soft_link_name):
        # do not delete or overwrite real (non-soft link) file
        if not os.path.islink(soft_link_name):
            raise FileExistsError(f"{soft_link_name} exists and is not a link")
        try:
            os.unlink(soft_link_name)
        except OSError:
            log.debug("Can't unlink %s", soft_link_name)

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"trying to create a broken symlink to {input_file}")

    if os.name == 'nt':
        # Don't actually use symlinks on Windows due to permission issues
        shutil.copyfile(input_file, soft_link_name)
        return

    log.debug("os.symlink(%s, %s)", input_file, soft_link_name)

    # Create symbolic link using absolute path
    os.symlink(os.path.abspath(input_file), soft_link_name)


def samefile(f1, f2):
    if os.name == 'nt':
        return f1 == f2
    else:
        return os.path.samefile(f1, f2)


def is_iterable_notstr(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, str)


def monotonic(L: Iterable):
    """Does list increase monotonically?"""
    return all(b > a for a, b in zip(L, L[1:]))


def page_number(input_file: os.PathLike):
    """Get one-based page number implied by filename (000002.pdf -> 2)"""
    return int(os.path.basename(os.fspath(input_file))[0:6])


def available_cpu_count():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        pass
    warnings.warn(
        "Could not get CPU count.  Assuming one (1) CPU." "Use -j N to set manually."
    )
    return 1


def is_file_writable(test_file: os.PathLike):
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


def check_pdf(input_file):
    pdf = None
    try:
        pdf = pikepdf.open(input_file)
    except pikepdf.PdfError as e:
        log.error(e)
        return False
    else:
        messages = pdf.check()
        for msg in messages:
            if 'error' in msg.lower():
                log.error(msg)
            else:
                log.warning(msg)

        sio = StringIO()
        linearize = None
        try:
            pdf.check_linearization(sio)
        except RuntimeError:
            pass
        else:
            linearize = sio.getvalue()
            if linearize:
                log.warning(linearize)

        if not messages and not linearize:
            return True
        return False
    finally:
        if pdf:
            pdf.close()


def deprecated(func):
    """Warn that function is deprecated"""

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
