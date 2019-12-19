# © 2019 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

from subprocess import PIPE, run

import pytest

pytestmark = pytest.mark.skipif(
    pytest.helpers.running_in_docker(),  # pylint: disable=no-member
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
