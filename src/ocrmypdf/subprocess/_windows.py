# © 2020 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# type: ignore
# Non-Windows mypy now breaks when trying to typecheck winreg

import logging
import os
import shutil
import sys
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Set, Tuple, TypeVar

try:
    import winreg
except ModuleNotFoundError as e:
    raise ModuleNotFoundError("This module is for Windows only") from e


log = logging.getLogger(__name__)

T = TypeVar('T')


def ghostscript_version_key(s: str) -> Tuple[int, int, int]:
    """Compare Ghostscript version numbers."""
    try:
        release = [int(elem) for elem in s.split('.', maxsplit=3)]
        while len(release) < 3:
            release.append(0)
        return (release[0], release[1], release[2])
    except ValueError:
        return (0, 0, 0)


def registry_enum(
    key: winreg.HKEYType, enum_fn: Callable[[winreg.HKEYType, int], T]
) -> Iterator[T]:
    LIMIT = 999
    n = 0
    while n < LIMIT:
        try:
            yield enum_fn(key, n)
            n += 1
        except OSError:
            break
    if n == LIMIT:
        raise ValueError(f"Too many registry keys under {key}")


def registry_subkeys(key: winreg.HKEYType) -> Iterator[str]:
    return registry_enum(key, winreg.EnumKey)


def registry_values(key: winreg.HKEYType) -> Iterator[Tuple[str, Any, int]]:
    return registry_enum(key, winreg.EnumValue)


def registry_path_ghostscript(env=None) -> Iterator[Path]:
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Artifex\GPL Ghostscript"
        ) as k:
            latest_gs = max(
                registry_subkeys(k), key=ghostscript_version_key, default=(0, 0, 0)
            )
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, fr"SOFTWARE\Artifex\GPL Ghostscript\{latest_gs}"
        ) as k:
            _, gs_path, _ = next(registry_values(k))
            yield Path(gs_path) / 'bin'
    except OSError as e:
        log.warning(e)


def registry_path_tesseract(env=None) -> Iterator[Path]:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tesseract-OCR") as k:
            for subkey, val, _valtype in registry_values(k):
                if subkey == 'InstallDir':
                    tesseract_path = Path(val)
                    yield tesseract_path
    except OSError as e:
        log.warning(e)


def program_files_paths(env=None) -> Iterator[Path]:
    if not env:
        env = os.environ
    program_files = env.get('PROGRAMFILES', '')

    def path_walker() -> Iterator[Path]:
        for path in Path(program_files).iterdir():
            if not path.is_dir():
                continue
            if path.name.lower() == 'tesseract-ocr':
                yield path
            elif path.name.lower() == 'gs':
                yield from (p for p in path.glob('**/bin') if p.is_dir())

    return iter(
        sorted(
            (p for p in path_walker()),
            key=lambda p: (p.name, p.parent.name),
            reverse=True,
        )
    )


def paths_from_env(env=None) -> Iterator[Path]:
    return (Path(p) for p in os.get_exec_path(env) if p)


def shim_path(new_paths: Callable[[Any], Iterator[Path]], env=None) -> str:
    if not env:
        env = os.environ
    return os.pathsep.join(str(p) for p in new_paths(env) if p)


SHIMS = [
    paths_from_env,
    registry_path_ghostscript,
    registry_path_tesseract,
    program_files_paths,
]


def fix_windows_args(program: str, args, env):
    """Adjust our desired program and command line arguments for use on Windows"""

    if sys.version_info < (3, 8):
        # bpo-33617 - Windows needs manual Path -> str conversion
        args = [os.fspath(arg) for arg in args]
        program = os.fspath(program)

    # If we are running a .py on Windows, ensure we call it with this Python
    # (to support test suite shims)
    if program.lower().endswith('.py'):
        args = [sys.executable] + args

    # If the program we want is not on the PATH, check elsewhere
    for shim in SHIMS:
        shimmed_path = shim_path(shim, env)
        new_args0 = shutil.which(args[0], path=shimmed_path)
        if new_args0:
            args[0] = new_args0
            break

    return args


def unique_everseen(iterable: Iterable[T], key: Callable[[T], T]) -> Iterator[T]:
    "List unique elements, preserving order."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen: Set[T] = set()
    seen_add = seen.add
    for element in iterable:
        k = key(element)
        if k not in seen:
            seen_add(k)
            yield element


def shim_env_path(env=None):
    if env is None:
        env = os.environ

    shim_paths = chain.from_iterable(shim(env) for shim in SHIMS)
    return os.pathsep.join(
        str(p) for p in unique_everseen(shim_paths, key=lambda p: str.casefold(str(p)))
    )
