#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

from functools import partial
from collections.abc import Iterable
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
        except:
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
