# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Find Tesseract and Ghostscript binaries on Windows using the registry."""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, TypeVar

from packaging.version import InvalidVersion, Version

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias  # pragma: no cover

if sys.platform == 'win32':
    # mypy understands 'if sys.platform' better than try/except ModuleNotFoundError
    import winreg  # pylint: disable=import-error

    HKEYType: TypeAlias = winreg.HKEYType
else:
    from unittest.mock import Mock

    winreg = Mock(
        spec=['HKEYType', 'EnumKey', 'EnumValue', 'HKEY_LOCAL_MACHINE', 'OpenKey']
    )
    # mypy does not understand winreg.HKeyType where winreg is a Mock (fair enough!)
    HKEYType: TypeAlias = Any  # type: ignore


log = logging.getLogger(__name__)

T = TypeVar('T')
Tkey = TypeVar('Tkey')


def ghostscript_version_key(s: str) -> tuple[int, int, int]:
    """Compare Ghostscript version numbers."""
    try:
        release = [int(elem) for elem in s.split('.', maxsplit=3)]
        while len(release) < 3:
            release.append(0)
        return (release[0], release[1], release[2])
    except ValueError:
        return (0, 0, 0)


def registry_enum(key: HKEYType, enum_fn: Callable[[HKEYType, int], T]) -> Iterator[T]:
    limit = 999
    n = 0
    while n < limit:
        try:
            yield enum_fn(key, n)
            n += 1
        except OSError:
            break
    if n == limit:
        raise ValueError(f"Too many registry keys under {key}")


def registry_subkeys(key: HKEYType) -> Iterator[str]:
    return registry_enum(key, winreg.EnumKey)


def registry_values(key: HKEYType) -> Iterator[tuple[str, Any, int]]:
    return registry_enum(key, winreg.EnumValue)


def registry_path_ghostscript(env=None) -> Iterator[Path]:
    del env  # unused (but needed for protocol)
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
            for _, gs_path, _ in registry_values(k):
                yield Path(gs_path) / 'bin'
    except OSError as e:
        log.warning(e)


def registry_path_tesseract(env=None) -> Iterator[Path]:
    del env  # unused (but needed for protocol)
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tesseract-OCR") as k:
            for subkey, val, _valtype in registry_values(k):
                if subkey == 'InstallDir':
                    tesseract_path = Path(val)
                    yield tesseract_path
    except OSError as e:
        log.warning(e)


def _gs_version_in_path_key(path: Path) -> tuple[str, Version | None]:
    """Key function for comparing Ghostscript and Tesseract paths.

    Ghostscript installs on Windows:
        %PROGRAMFILES%/gs/gs9.56.1/bin -> ('gs', Version('9.56.1'))
        %PROGRAMFILES%/gs/9.24/bin -> ('gs', Version('9.24'))

    Tesseract looks like:
        %PROGRAMFILES%/Tesseract-OCR -> ('Tesseract-OCR', None)

    Thus ensuring the resulting tuple will order the alternatives correctly,
    e.g. gs10.0 > gs9.99.
    """
    match = re.search(r'gs[/\\]?([0-9.]+)[/\\]bin', str(path))
    if match:
        try:
            version_str = match.group(1)
            version = Version(version_str)
            return 'gs', version
        except InvalidVersion:
            pass
    return path.name, None


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
            key=_gs_version_in_path_key,
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
    """Adjust our desired program and command line arguments for use on Windows."""
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


def unique_everseen(iterable: Iterable[T], key: Callable[[T], Tkey]) -> Iterator[T]:
    """List unique elements, preserving order."""
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen: set[Tkey] = set()
    seen_add = seen.add
    for element in iterable:
        k = key(element)
        if k not in seen:
            seen_add(k)
            yield element


def _casefold_path(path: Path) -> str:
    return str.casefold(str(path))


def shim_env_path(env=None):
    if env is None:
        env = os.environ

    shim_paths = chain.from_iterable(shim(env) for shim in SHIMS)
    return os.pathsep.join(
        str(p) for p in unique_everseen(shim_paths, key=_casefold_path)
    )
