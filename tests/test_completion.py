# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os
from subprocess import run

import pytest

from .conftest import running_in_docker

pytestmark = pytest.mark.skipif(
    running_in_docker(),
    reason="docker can't complete",
)


def test_fish():
    try:
        proc = run(
            ['fish', '-n', 'misc/completion/ocrmypdf.fish'],
            check=True,
            encoding='utf-8',
            capture_output=True,
        )
        assert proc.stderr == '', proc.stderr
    except FileNotFoundError:
        pytest.xfail('fish is not installed')


@pytest.mark.skipif(
    os.name == 'nt', reason="Windows CI workers have bash but are best left alone"
)
def test_bash():
    try:
        proc = run(
            ['bash', '-n', 'misc/completion/ocrmypdf.bash'],
            check=True,
            encoding='utf-8',
            capture_output=True,
        )
        assert proc.stderr == '', proc.stderr
    except FileNotFoundError:
        pytest.xfail('bash is not installed')
