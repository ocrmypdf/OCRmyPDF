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

from subprocess import CalledProcessError, run
from tempfile import TemporaryFile
import sys
import os
import shutil

from ..exceptions import ExitCode


def convert(input_file, output_file):
    args_jbig2 = [
        'jbig2',
        '-s',
        input_file
    ]

    with TemporaryFile(mode='w+b') as tmp:
        proc = run(args_jbig2, stdout=tmp)
        
        if proc.returncode == 0:
            with open(output_file, 'wb') as output:
                shutil.copyfileobj(tmp, output)
