# © 2019 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
from subprocess import PIPE, run

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
            stdout=PIPE,
            stderr=PIPE,
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
            stdout=PIPE,
            stderr=PIPE,
        )
        assert proc.stderr == '', proc.stderr
    except FileNotFoundError:
        pytest.xfail('bash is not installed')
