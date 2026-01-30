# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Compare text in PDFs."""

from __future__ import annotations

from pathlib import Path
from subprocess import run
from tempfile import NamedTemporaryFile
from typing import Annotated

import cyclopts

app = cyclopts.App()


@app.default
def main(
    pdf1: Annotated[Path, cyclopts.Parameter()],
    pdf2: Annotated[Path, cyclopts.Parameter()],
    *,
    engine: Annotated[str, cyclopts.Parameter()] = 'pdftotext',
):
    """Compare text in PDFs."""
    with open(pdf1, 'rb') as f1, open(pdf2, 'rb') as f2:
        text1 = run(
            ['pdftotext', '-layout', '-', '-'],
            stdin=f1,
            capture_output=True,
            check=True,
        )
        text2 = run(
            ['pdftotext', '-layout', '-', '-'],
            stdin=f2,
            capture_output=True,
            check=True,
        )

    with NamedTemporaryFile() as t1, NamedTemporaryFile() as t2:
        t1.write(text1.stdout)
        t1.flush()
        t2.write(text2.stdout)
        t2.flush()
        diff = run(
            ['diff', '--color=always', '--side-by-side', t1.name, t2.name],
            capture_output=True,
        )
        run(['less', '-R'], input=diff.stdout, check=True)
        if text1.stdout.strip() != text2.stdout.strip():
            return 1

    return 0


if __name__ == '__main__':
    app()
