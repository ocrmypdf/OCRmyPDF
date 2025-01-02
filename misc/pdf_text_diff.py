# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Compare text in PDFs."""

from __future__ import annotations

from subprocess import run
from tempfile import NamedTemporaryFile
from typing import Annotated

import typer


def main(
    pdf1: Annotated[typer.FileBinaryRead, typer.Argument()],
    pdf2: Annotated[typer.FileBinaryRead, typer.Argument()],
    engine: Annotated[str, typer.Option()] = 'pdftotext',
):
    """Compare text in PDFs."""

    text1 = run(
        ['pdftotext', '-layout', '-', '-'], stdin=pdf1, capture_output=True, check=True
    )
    text2 = run(
        ['pdftotext', '-layout', '-', '-'], stdin=pdf2, capture_output=True, check=True
    )

    with NamedTemporaryFile() as f1, NamedTemporaryFile() as f2:
        f1.write(text1.stdout)
        f1.flush()
        f2.write(text2.stdout)
        f2.flush()
        diff = run(
            ['diff', '--color=always', '--side-by-side', f1.name, f2.name],
            capture_output=True,
        )
        run(['less', '-R'], input=diff.stdout, check=True)
        if text1.stdout.strip() != text2.stdout.strip():
            return 1

    return 0


if __name__ == '__main__':
    typer.run(main)
