# © 2018 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Interface to pngquant executable"""

from os import fspath
from tempfile import NamedTemporaryFile

from PIL import Image

from ocrmypdf.exceptions import MissingDependencyError
from ocrmypdf.subprocess import get_version, run


def version():
    return get_version('pngquant', regex=r'(\d+(\.\d+)*).*')


def available():
    try:
        version()
    except MissingDependencyError:
        return False
    return True


def quantize(input_file, output_file, quality_min, quality_max):
    input_file = fspath(input_file)
    output_file = fspath(output_file)
    if input_file.endswith('.jpg'):
        with Image.open(input_file) as im, NamedTemporaryFile(suffix='.png') as tmp:
            im.save(tmp)
            args = [
                'pngquant',
                '--force',
                '--skip-if-larger',
                '--output',
                output_file,
                '--quality',
                f'{quality_min}-{quality_max}',
                '--',
                tmp.name,
            ]
            run(args)
    else:
        args = [
            'pngquant',
            '--force',
            '--skip-if-larger',
            '--output',
            output_file,
            '--quality',
            f'{quality_min}-{quality_max}',
            '--',
            input_file,
        ]
        run(args)
