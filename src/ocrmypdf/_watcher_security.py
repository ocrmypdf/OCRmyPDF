# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Security checks for the watched-folder helper (``misc/watcher.py``).

The watcher exposes three *data* directories -- input, output and archive --
that may be writable by less-privileged users, and it drives OCRmyPDF using
settings (including plugins) that can originate from an attacker-influenced
``OCR_JSON_SETTINGS`` blob. Because a plugin supplied as a ``.py`` path is
executed (``exec_module``), and relative plugin/``.env`` paths resolve against
the current working directory, the data directories must never overlap the
code/interpreter zone.

These helpers enforce a "Harvard architecture": data and code never comingle.
They are deliberately kept in the installed package (rather than beside the
script) so that they import identically whether the watcher is run as
``misc/watcher.py`` or via the ``/app/watcher.py`` symlink used in the Docker
image, and so they can be unit-tested and type-checked with the rest of the
package.

Residual risks that are not portably closable and are accepted here:

* TOCTOU -- a regular file that passes :func:`is_safe_regular_file` can be
  swapped for a symlink before OCRmyPDF opens it. The check is repeated as late
  as possible to shrink, not eliminate, the window.
* Hardlinks -- a hardlink to a file outside the watched tree is
  indistinguishable from an ordinary regular file via ``lstat``.
"""

from __future__ import annotations

import os
import site
import stat
import sys
import sysconfig
from collections.abc import Iterable, Mapping
from pathlib import Path

from ocrmypdf.exceptions import ExitCode, ExitCodeException


class WatcherConfigError(ExitCodeException):
    """The watcher was asked to run in an unsafe or invalid configuration."""

    exit_code = ExitCode.invalid_config


def _norm(path: str | os.PathLike[str]) -> Path:
    """Return a canonical path for containment comparisons.

    Resolves symlinks and ``..`` (``os.path.realpath`` tolerates non-existent
    tail components) and case-folds on case-insensitive platforms via
    ``os.path.normcase`` so that comparisons on Windows/macOS are not defeated
    by case differences.
    """
    return Path(os.path.normcase(os.path.realpath(os.fspath(path))))


def _paths_overlap(a: Path, b: Path) -> bool:
    """Return True if ``a`` and ``b`` are equal or one contains the other.

    Both arguments must already be normalized with :func:`_norm`.
    """
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def resolve_critical_paths() -> frozenset[Path]:
    """Collect every filesystem location that belongs to the code zone.

    The result is the set of paths an attacker must not be able to reach: the
    interpreter binary, the (virtual) environment prefixes, everything on
    ``sys.path`` and the standard site/sysconfig locations, and every directory
    on ``$PATH``. The current working directory is always included, because a
    relative plugin path or ``.env`` file resolves there; an empty
    ``sys.path``/``$PATH`` entry also denotes the working directory.
    """
    cwd = str(Path.cwd())
    candidates: list[str] = [
        sys.executable,
        sys.prefix,
        sys.base_prefix,
        sys.exec_prefix,
        sys.base_exec_prefix,
        cwd,
    ]

    # sys.path -- an empty entry means the current working directory.
    candidates.extend(p or cwd for p in sys.path)

    # site-packages locations may be unavailable in some virtualenv layouts.
    for getter in (site.getsitepackages, site.getusersitepackages):
        try:
            result = getter()
        except Exception:  # noqa: BLE001 - defensive; layouts vary
            continue
        if isinstance(result, str):
            candidates.append(result)
        else:
            candidates.extend(result)

    # Standard library / headers / scripts directories for this interpreter.
    candidates.extend(sysconfig.get_paths().values())

    # Everything on $PATH -- an empty segment means the working directory.
    candidates.extend(p or cwd for p in os.environ.get('PATH', '').split(os.pathsep))

    return frozenset(_norm(p) for p in candidates if p)


def assert_data_dirs_isolated(
    data_dirs: Mapping[str, Path], critical: Iterable[Path]
) -> None:
    """Refuse to run if any data directory overlaps the code zone.

    Overlap is bidirectional: a data directory that *contains* a critical path
    would let an attacker replace the interpreter or venv, while a data
    directory that *lives inside* a critical path comingles data with code
    (e.g. a writable directory on ``sys.path``). Either is rejected.

    Args:
        data_dirs: Mapping of human label ("input", "output", ...) to directory.
        critical: Normalized critical paths from :func:`resolve_critical_paths`.

    Raises:
        WatcherConfigError: If any data directory overlaps a critical path.
    """
    critical = list(critical)
    for label, directory in data_dirs.items():
        normalized = _norm(directory)
        for code_path in critical:
            if _paths_overlap(normalized, code_path):
                raise WatcherConfigError(
                    f"Refusing to run: the {label} directory {directory} overlaps "
                    f"the interpreter/code path {code_path}. Input, output and "
                    f"archive directories must be completely separate from the "
                    f"Python interpreter, virtual environment and $PATH."
                )


def assert_no_watch_loop(input_dir: Path, output_dir: Path, archive_dir: Path) -> None:
    """Refuse configurations that would feed OCR output back into the watcher.

    The input directory is watched recursively, so if the output or archive
    directory is the input directory itself or a descendant of it, every file
    OCRmyPDF writes there -- and every original moved there on success -- would
    be detected as a new input file and processed again, forming an endless
    loop. ``is_relative_to`` is reflexive, so this also rejects the case where
    the directories are identical.

    Raises:
        WatcherConfigError: If output or archive is inside the input directory.
    """
    input_norm = _norm(input_dir)
    for label, directory in (('output', output_dir), ('archive', archive_dir)):
        if _norm(directory).is_relative_to(input_norm):
            raise WatcherConfigError(
                f"Refusing to run: the {label} directory {directory} is inside "
                f"the watched input directory {input_dir}. OCRmyPDF output written "
                f"there would be detected as new input and reprocessed endlessly. "
                f"Choose a {label} directory outside the input directory."
            )


def is_safe_regular_file(path: Path, within_dir: Path) -> bool:
    """Return True if ``path`` is a real regular file inside ``within_dir``.

    Uses ``lstat`` (never ``stat``) so a symlink is reported as a symlink and
    rejected, along with every non-regular type (fifo, socket, device,
    directory). Additionally requires that the fully resolved path stays within
    the resolved watched directory, so a symlinked ancestor directory cannot
    redirect processing outside the tree.
    """
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode):
        return False
    return _norm(path).is_relative_to(_norm(within_dir))


def is_safe_write_target(path: Path, within_dir: Path) -> bool:
    """Return True if it is safe to write OCR output to ``path``.

    The parent directory (after resolving symlinks) must stay within
    ``within_dir`` -- this catches a symlinked year/month component that would
    redirect the write outside the output tree -- and, if ``path`` already
    exists, it must be an ordinary regular file so we never write into a fifo,
    device or other unusual object.
    """
    if not _norm(path.parent).is_relative_to(_norm(within_dir)):
        return False
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return stat.S_ISREG(st.st_mode)


def assert_settings_file_safe(path: Path, data_dirs: Iterable[Path]) -> None:
    """Validate an ``OCR_JSON_SETTINGS`` file supplied as a path.

    The settings file governs how OCRmyPDF runs, so it must live outside the
    attacker-writable data directories, must be an ordinary regular file, and
    (on POSIX) must not be group- or world-writable.

    Raises:
        WatcherConfigError: If the file is unsafe.
    """
    normalized = _norm(path)
    for directory in data_dirs:
        if normalized.is_relative_to(_norm(directory)):
            raise WatcherConfigError(
                f"Refusing to read settings file {path}: it is inside a data "
                f"directory ({directory}) and could be modified by an attacker."
            )

    try:
        st = os.lstat(path)
    except OSError as e:
        raise WatcherConfigError(f"Cannot access settings file {path}: {e}") from e
    if not stat.S_ISREG(st.st_mode):
        raise WatcherConfigError(f"Settings file {path} is not a regular file.")

    if os.name != 'nt' and (st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)):
        raise WatcherConfigError(
            f"Refusing to read settings file {path}: it is group- or "
            f"world-writable (mode {stat.filemode(st.st_mode)}). Restrict it to "
            f"owner-only write access (e.g. chmod 600)."
        )


def assert_plugins_safe(
    plugins: Iterable[Path | str], data_dirs: Iterable[Path]
) -> None:
    """Refuse plugins that would load code from a data directory.

    Mirrors the file-vs-module decision made by
    :class:`ocrmypdf._plugin_manager.OcrmypdfPluginManager`: a plugin is loaded
    from a file (and therefore executed directly) iff it is a ``Path`` or a
    string ending in ``.py``. Such a path is resolved -- a relative ``.py``
    resolves against the working directory -- and rejected if it lands inside a
    data directory. Bare dotted module names are left alone: ``import_module``
    rejects path separators and can only resolve via ``sys.path``, which the
    :func:`assert_data_dirs_isolated` check already keeps clear of data dirs.

    Raises:
        WatcherConfigError: If a plugin file resolves inside a data directory.
    """
    normalized_dirs = [_norm(directory) for directory in data_dirs]
    for name in plugins:
        is_file_plugin = isinstance(name, Path) or (
            isinstance(name, str) and name.endswith('.py')
        )
        if not is_file_plugin:
            continue
        plugin_path = _norm(name)
        for directory in normalized_dirs:
            if plugin_path.is_relative_to(directory):
                raise WatcherConfigError(
                    f"Refusing to load plugin {name}: it resolves inside a data "
                    f"directory ({directory}). Plugins must not live in the "
                    f"input, output or archive directories."
                )
