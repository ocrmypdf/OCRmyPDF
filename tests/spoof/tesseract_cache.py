#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Cache output of tesseract to speed up test suite

The cache is keyed by an environment variable that slips the input test file
from tests/resources/ to us.  The input arguments are slugged into a hideous
filename that more or less represents them literally.  Joined together, this
becomes the name of the cache folder.  A few name files like stdout, stderr,
hocr, pdf, describe the output to reproduce.

Changes to tests/resources/ or image processing algorithms don't trigger a
cache miss.  By design, an input image that varies according to platform
differences (e.g. JPEG decoders are allowed to produce differing outputs,
and in practice they do) will still be a cache hit.  By design, an
invocation of tesseract with the same parameters from a different test case
will be a hit.  It's fragile.

The tests/cache/manifest.jsonl is a JSON lines file that contains
information about the system that produced the results used when cache was
generated.  This mainly a log to answer questions about how the files
were produced.

For performance reasons, especially the slow performance of Tesseract on
machines with AVX2, the cache is now bundled.

Certain operations are not cached and routed to tesseract directly.

Assumes Tesseract 4.0.0-alpha or higher.

"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

if '_OCRMYPDF_SAVE_PATH' in os.environ:
    os.environ['PATH'] = os.environ['_OCRMYPDF_SAVE_PATH']

__version__ = subprocess.check_output(
    ['tesseract', '--version'], stderr=subprocess.STDOUT
).decode()


parser = argparse.ArgumentParser(
    prog='tesseract-cache', description='cache output of tesseract'
)
parser.add_argument('-l', '--language', action='append')
parser.add_argument('imagename')
parser.add_argument('outputbase')
parser.add_argument('configfiles', nargs='*')
parser.add_argument('--user-words', type=str)
parser.add_argument('--user-patterns', type=str)
parser.add_argument('-c', action='append')
parser.add_argument('--psm', type=int)
parser.add_argument('--oem', type=int)

TESTS_ROOT = Path(__file__).resolve().parent.parent
CACHE_ROOT = TESTS_ROOT / 'cache'


def real_tesseract():
    tess_args = ['tesseract'] + sys.argv[1:]
    os.execvp("tesseract", tess_args)
    return  # Not reachable


def main():
    if any(
        opt in sys.argv[1:]
        for opt in ('--print-parameters', '--list-langs', '--version')
    ):
        real_tesseract()  # jump into real tesseract, replacing this process

    # Convert non-standard but supported -psm to --psm
    sys.argv = ['--psm' if arg == '-psm' else arg for arg in sys.argv]

    source = os.environ['_OCRMYPDF_TEST_INFILE']  # required
    args = parser.parse_args()

    cache_disabled = os.environ.get('_OCRMYPDF_CACHE_DISABLED', False)

    if args.imagename == 'stdin':
        real_tesseract()

    def slugs():
        yield ''  # so we don't start with a '-' which makes rm difficult
        for arg in sys.argv[1:]:
            if arg == args.imagename:
                yield Path(args.imagename).name
            elif arg == args.outputbase:
                yield Path(args.outputbase).name
            elif arg == '-c' or arg.startswith('textonly'):
                pass
            else:
                yield arg

    argv_slug = '__'.join(slugs())
    argv_slug = argv_slug.replace('/', '___')

    cache_folder = Path(CACHE_ROOT) / Path(source).stem / argv_slug
    cache_folder.mkdir(parents=True, exist_ok=True)

    print(f"Tesseract cache folder {cache_folder} - ", end='', file=sys.stderr)

    if (cache_folder / 'stderr.bin').exists() and not cache_disabled:
        # Cache hit
        print("HIT", file=sys.stderr)

        # Replicate stdout/err
        sys.stdout.buffer.write((cache_folder / 'stdout.bin').read_bytes())
        sys.stderr.buffer.write((cache_folder / 'stderr.bin').read_bytes())
        if args.outputbase != 'stdout':
            if not args.configfiles:
                args.configfiles.append('txt')
            for configfile in args.configfiles:
                # cp cache -> output
                tessfile = args.outputbase + '.' + configfile
                shutil.copy(str(cache_folder / configfile) + '.bin', tessfile)
        sys.exit(0)

    # Cache miss
    print("MISS", file=sys.stderr)

    # Call tesseract
    print(sys.argv[1:])
    p = subprocess.run(
        ['tesseract'] + sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    sys.stdout.buffer.write(p.stdout)
    sys.stderr.buffer.write(p.stderr)

    if p.returncode != 0:
        # Do not cache errors or crashes
        print("Tesseract error", file=sys.stderr)
        return p.returncode

    (cache_folder / 'stdout.bin').write_bytes(p.stdout)

    if args.outputbase != 'stdout':
        if not args.configfiles:
            args.configfiles.append('txt')

        for configfile in args.configfiles:
            if configfile not in ('hocr', 'pdf', 'txt'):
                continue
            # cp pwd/{outputbase}.{configfile} -> {cache}/{configfile}
            tessfile = args.outputbase + '.' + configfile
            shutil.copy(tessfile, str(cache_folder / configfile) + '.bin')

    (cache_folder / 'stderr.bin').write_bytes(p.stderr)

    manifest = {}
    manifest['tesseract_version'] = __version__.replace('\n', ' ')
    manifest['platform'] = platform.platform()
    manifest['python'] = platform.python_version()
    manifest['argv_slug'] = argv_slug
    manifest['sourcefile'] = str(Path(source).relative_to(TESTS_ROOT))

    def clean_sys_argv():
        for arg in sys.argv[1:]:
            yield re.sub(r'.*/com.github.ocrmypdf[^/]+[/](.*)', r'$TMPDIR/\1', arg)

    manifest['args'] = list(clean_sys_argv())

    # pylint: disable=E1101
    with (Path(CACHE_ROOT) / 'manifest.jsonl').open('a') as f:
        json.dump(manifest, f)
        f.write('\n')
        f.flush()


if __name__ == '__main__':
    main()
