# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Protect the real standard output from corruption by stray writes.

When OCRmyPDF writes its final PDF to standard output (``ocrmypdf in.pdf -``),
the bytes on stdout must be exactly the PDF and nothing else. Any accidental
write to file descriptor 1 anywhere in the process -- from a third-party
library, a plugin, or a stray ``print()`` -- would silently corrupt the output.

This module enforces that guarantee at the operating system level. It saves a
private duplicate of the real stdout and points file descriptor 1 at standard
error, so that anything that writes to stdout lands harmlessly on stderr. Only
OCRmyPDF's final "produce the PDF" step writes to the preserved real stdout, via
:func:`get_protected_stdout_fd`.
"""

from __future__ import annotations

import os
import sys
import threading

_lock = threading.Lock()
_saved_fd: int | None = None
_active = False


def protect_stdout() -> bool:
    """Redirect file descriptor 1 to stderr and preserve the real stdout.

    After this call, any write to file descriptor 1 -- including ``print()`` and
    writes from third-party C libraries -- is redirected to standard error and
    cannot corrupt the real standard output. The real stdout is preserved on a
    private file descriptor available from :func:`get_protected_stdout_fd`.

    This mutates process-global state and affects the whole process. It must be
    called once, early, before any plugins are loaded or any worker
    process/thread is started, so that all of them inherit the redirected
    descriptor.

    Returns:
        True if protection was installed (or was already active). False if
        stdout is not backed by a real OS file descriptor -- for example under
        a test harness that captures stdout -- in which case nothing is changed.
    """
    global _saved_fd, _active
    with _lock:
        if _active:
            return True
        try:
            fd1 = sys.stdout.fileno()
        except (AttributeError, OSError, ValueError):
            # stdout is not backed by a real file descriptor (e.g. captured by
            # a test harness or replaced with an in-memory stream).
            return False
        try:
            sys.stdout.flush()
            saved = os.dup(fd1)
            os.dup2(2, fd1)  # point stdout at stderr
        except OSError:
            return False
        _saved_fd = saved
        _active = True
        return True


def get_protected_stdout_fd() -> int | None:
    """Return the preserved real stdout file descriptor, or None if inactive."""
    return _saved_fd if _active else None


def protected_stdout_isatty() -> bool | None:
    """Whether the preserved real stdout is a terminal.

    Returns None if protection is not active, in which case the caller should
    fall back to ``sys.stdout.isatty()``. When protection is active,
    ``sys.stdout`` reports the terminal status of stderr (its descriptor was
    redirected), so this consults the saved real-stdout descriptor instead.
    """
    if not _active or _saved_fd is None:
        return None
    return os.isatty(_saved_fd)
