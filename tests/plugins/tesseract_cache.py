# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MIT
"""Cache output of tesseract to speed up test suite.

The cache is keyed by by the input test file The input arguments are slugged
into a hideous filename that more or less represents them literally.  Joined
together, this becomes the name of the cache folder.  A few name files like
stdout, stderr, hocr, pdf, describe the output to reproduce.

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

Certain operations are not cached and routed to Tesseract OCR directly.

Assumes Tesseract 4+.

"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import re
import shutil
import threading
from functools import partial
from pathlib import Path
from subprocess import PIPE, CalledProcessError, CompletedProcess
from unittest.mock import patch

from ocrmypdf import hookimpl
from ocrmypdf.builtin_plugins.tesseract_ocr import TesseractOcrEngine
from ocrmypdf.subprocess import run

log = logging.getLogger(__name__)

TESTS_ROOT = Path(__file__).resolve().parent.parent
CACHE_ROOT = TESTS_ROOT / 'cache'


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


def get_cache_folder(source_pdf, run_args, parsed_args):
    def slugs():
        yield ''  # so we don't start with a '-' which makes rm difficult
        for arg in run_args[1:]:
            if arg == parsed_args.imagename:
                yield Path(parsed_args.imagename).name
            elif arg == parsed_args.outputbase:
                yield Path(parsed_args.outputbase).name
            elif arg == '-c' or arg.startswith('textonly'):
                pass
            else:
                yield arg

    argv_slug = '__'.join(slugs())
    argv_slug = argv_slug.replace('/', '___')

    return Path(CACHE_ROOT) / Path(source_pdf).stem / argv_slug


def cached_run(options, run_args, **run_kwargs):
    run_args = [str(arg) for arg in run_args]  # flatten PosixPaths
    args = parser.parse_args(run_args[1:])

    if args.imagename in ('stdin', '-'):
        return run(run_args, **run_kwargs)

    source_file = options.input_file
    cache_folder = get_cache_folder(source_file, run_args, args)
    cache_folder.mkdir(parents=True, exist_ok=True)

    log.debug(f"Using Tesseract cache {cache_folder}")

    if (cache_folder / 'stderr.bin').exists():
        log.debug("Cache HIT")

        # Replicate stdout/err
        if args.outputbase != 'stdout':
            if not args.configfiles:
                args.configfiles.append('txt')
            for configfile in args.configfiles:
                # cp cache -> output
                tessfile = args.outputbase + '.' + configfile
                shutil.copy(str(cache_folder / configfile) + '.bin', tessfile)
        return CompletedProcess(
            args=run_args,
            returncode=0,
            stdout=(cache_folder / 'stdout.bin').read_bytes(),
            stderr=(cache_folder / 'stderr.bin').read_bytes(),
        )

    log.debug("Cache MISS")

    cache_kwargs = {
        k: v for k, v in run_kwargs.items() if k not in ('stdout', 'stderr')
    }
    assert cache_kwargs['check']
    try:
        p = run(run_args, stdout=PIPE, stderr=PIPE, **cache_kwargs)
    except CalledProcessError as e:
        log.exception(e)
        raise  # Pass exception onward

    # Update cache
    (cache_folder / 'stdout.bin').write_bytes(p.stdout)
    (cache_folder / 'stderr.bin').write_bytes(p.stderr)

    if args.outputbase != 'stdout':
        if not args.configfiles:
            args.configfiles.append('txt')

        for configfile in args.configfiles:
            if configfile not in ('hocr', 'pdf', 'txt'):
                continue
            # cp pwd/{outputbase}.{configfile} -> {cache}/{configfile}
            tessfile = args.outputbase + '.' + configfile
            shutil.copy(tessfile, str(cache_folder / configfile) + '.bin')

    def clean_sys_argv():
        for arg in run_args[1:]:
            yield re.sub(r'.*/ocrmypdf[.]io[.][^/]+[/](.*)', r'$TMPDIR/\1', arg)

    manifest = {
        'tesseract_version': TesseractOcrEngine.version().replace('\n', ' '),
        'system': platform.system(),
        'python': platform.python_version(),
        'argv_slug': cache_folder.name,
        'sourcefile': str(Path(source_file).relative_to(TESTS_ROOT)),
        'args': list(clean_sys_argv()),
    }

    with (Path(CACHE_ROOT) / 'manifest.jsonl').open('a') as f:
        json.dump(manifest, f)
        f.write('\n')
        f.flush()
    return p


class CacheOcrEngine(TesseractOcrEngine):
    # Concurrent threads (with --use-threads) might try to use different parts
    # of the OcrEngine, so we need a lock to protect the state of patched
    # module whenever it's patched. Should refactor ocrmypdf._exec.tesseract so that
    # it does not to be patched at all for testing.
    lock = threading.Lock()

    @staticmethod
    def get_orientation(input_file, options):
        with (
            CacheOcrEngine.lock,
            patch('ocrmypdf._exec.tesseract.run', new=partial(cached_run, options)),
        ):
            return TesseractOcrEngine.get_orientation(input_file, options)

    @staticmethod
    def get_deskew(input_file, options) -> float:
        with (
            CacheOcrEngine.lock,
            patch('ocrmypdf._exec.tesseract.run', new=partial(cached_run, options)),
        ):
            return TesseractOcrEngine.get_deskew(input_file, options)

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        with (
            CacheOcrEngine.lock,
            patch('ocrmypdf._exec.tesseract.run', new=partial(cached_run, options)),
        ):
            TesseractOcrEngine.generate_hocr(
                input_file, output_hocr, output_text, options
            )

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        with (
            CacheOcrEngine.lock,
            patch('ocrmypdf._exec.tesseract.run', new=partial(cached_run, options)),
        ):
            TesseractOcrEngine.generate_pdf(
                input_file, output_pdf, output_text, options
            )


@hookimpl
def get_ocr_engine():
    return CacheOcrEngine()
