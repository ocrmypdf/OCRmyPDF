# © 2016 James R. Barlow: github.com/jbarlow83

from functools import partial
from collections.abc import Iterable
from contextlib import suppress, contextmanager
from pathlib import Path
import sys
import os


def re_symlink(input_file, soft_link_name, log=None):
    """
    Helper function: relinks soft symbolic link if necessary
    """

    if log is None:
        prdebug = partial(print, file=sys.stderr)
    else:
        prdebug = log.debug

    # Guard against soft linking to oneself
    if input_file == soft_link_name:
        prdebug("Warning: No symbolic link made. You are using " +
                "the original data directory as the working directory.")
        return

    # Soft link already exists: delete for relink?
    if os.path.lexists(soft_link_name):
        # do not delete or overwrite real (non-soft link) file
        if not os.path.islink(soft_link_name):
            raise FileExistsError(
                "%s exists and is not a link" % soft_link_name)
        try:
            os.unlink(soft_link_name)
        except OSError:
            prdebug("Can't unlink %s" % (soft_link_name))

    if not os.path.exists(input_file):
        raise FileNotFoundError(
            "trying to create a broken symlink to %s" % input_file)

    prdebug("os.symlink(%s, %s)" % (input_file, soft_link_name))

    # Create symbolic link using absolute path
    os.symlink(
        os.path.abspath(input_file),
        soft_link_name
    )


def is_iterable_notstr(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, str)


def page_number(input_file):
    return int(os.path.basename(input_file)[0:6])


def is_file_writable(test_file):
    """Intentionally racy test if target is writable.

    We intend to write to the output file if and only if we succeed and
    can replace it atomically. Before doing the OCR work, make sure
    the location is writable.
    """
    p = Path(test_file)

    if p.is_symlink():
        # Python 3.5 does not accept parameters for Path.resolve() and behaves
        # as if strict=True (throws an exception on failure). Python 3.6 
        # defaults to strict=False. This implements strict=False like behavior
        # for Python 3.5.
        if sys.version_info[0:2] <= (3, 5):
            p = Path(os.path.realpath(str(p)))
        else:
            p = p.resolve(strict=False)

    # p.is_file() throws an exception in some cases
    if p.exists() and p.is_file():
        return os.access(
            str(p), os.W_OK,
            effective_ids=(os.access in os.supports_effective_ids))
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


if sys.version_info[0:2] <= (3, 5):
    def universal_open(p, *args, **kwargs):
        "Work around Python 3.5's inability to open(pathlib.Path())"
        try:
            return p.open(*args, **kwargs)
        except AttributeError:
            return open(p, *args, **kwargs)


    def fspath(path):
        import pathlib
        '''https://www.python.org/dev/peps/pep-0519/#os'''
        if isinstance(path, (str, bytes)):
            return path

        # Work from the object's type to match method resolution of other magic
        # methods.
        path_type = type(path)
        try:
            path = path_type.__fspath__(path)
        except AttributeError:
            # Added for Python 3.5 support.
            if isinstance(path, pathlib.Path):
                return str(path)
            elif hasattr(path_type, '__fspath__'):
                raise
        else:
            if isinstance(path, (str, bytes)):
                return path
            else:
                raise TypeError("expected __fspath__() to return str or bytes, "
                                "not " + type(path).__name__)

        raise TypeError(
            "expected str, bytes, pathlib.Path or os.PathLike object, not "
            + path_type.__name__)

else:
    universal_open = open
    fspath = os.fspath
