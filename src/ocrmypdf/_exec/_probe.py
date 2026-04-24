# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0
"""Probe helper for external executables.

Each ``ocrmypdf._exec.<tool>`` module describes its external program with a
module-level :class:`ToolProbe` and delegates ``version()`` / ``available()``
to it. This separates the "is the tool installed and suitable?" question
(probing) from the "run the tool" question (execution). Work functions stay
as pure module-level functions so they are trivially picklable for use in
subprocess workers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from packaging.version import Version

from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import get_version


@dataclass(frozen=True)
class ToolProbe:
    """Describes how to detect an external executable and its version.

    Attributes:
        program: The program name as it appears on PATH (or a full path).
        version_arg: The argument that elicits a version string.
        version_regex: A regex with a capturing group that extracts the
            version from the program's output.
        version_cls: A :class:`packaging.version.Version` subclass, used for
            tools with non-standard version strings (e.g. Tesseract).
        env: Optional environment overrides applied when probing the version.
        also_catch: Additional exception types that should be treated as
            "not available" by :meth:`available`. :class:`OSError` is useful
            for tools like verapdf whose launcher may fail with non-standard
            errors when the JVM is missing.
    """

    program: str
    version_arg: str = '--version'
    version_regex: str = r'(\d+(\.\d+)*)'
    version_cls: type[Version] = Version
    env: Mapping[str, str] | None = None
    also_catch: tuple[type[BaseException], ...] = ()

    def version(self) -> Version:
        """Return the installed version of the program.

        Raises:
            MissingDependencyError: if the program cannot be found or its
                version string cannot be parsed.
        """
        raw = get_version(
            self.program,
            version_arg=self.version_arg,
            regex=self.version_regex,
            env=self.env,
        )
        return self.version_cls(raw)

    def available(self) -> bool:
        """Return whether a usable version of the program is installed."""
        try:
            self.version()
        except MissingDependencyError:
            return False
        except self.also_catch:
            return False
        return True
