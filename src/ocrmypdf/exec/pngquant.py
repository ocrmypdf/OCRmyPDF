# © 2018 James R. Barlow: github.com/jbarlow83
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

from subprocess import run
from functools import lru_cache

from . import get_version
from ..exceptions import MissingDependencyError


@lru_cache(maxsize=1)
def version():
    return get_version('pngquant', regex=r'(\d+(\.\d+)*).*')


def available():
    try:
        version()
    except MissingDependencyError:
        return False
    return True


def quantize(input_file, output_file, quality_min, quality_max):
    args = [
        'pngquant',
        '--force',
        '--skip-if-larger',
        '--output', output_file,
        '--quality', '{}-{}'.format(quality_min, quality_max),
        '--',
        input_file
    ]
    proc = run(args)
    proc.check_returncode()
