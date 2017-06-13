#!/usr/bin/env python3
# © 2016 James R. Barlow: github.com/jbarlow83

import sys
import os
import hashlib
import shutil
import subprocess


"""Cache output of tesseract to speed up test suite

The cache is keyed by a hash that includes the tesseract version, some of
the command line, and the binary dump of the input file, and this file itself.
 Therefore any updates to this file invalidate cache. Uses SHA-1 because it is
 fast and defeating a hash collision here is not exactly a priority. :P

The output files, stdout, and stderr are replicated on a cache hit. The output
files are either a .pdf and .txt or .hocr and .txt.

Page orientation checks are also cached (-psm 0 stdout)

Errors and crashes are not cached. If the arguments don't match a known
caching template then real tesseract is called with the same arguments.

Things not checked:
-changes to tesseract installation that don't affect --version

Assumes Tesseract 3.04 or higher.

Will fail on Tesseract 3.02.02 in "hocr" mode because it doesn't produce
the incorrect file extension. Will fail on 3.03 because that has no sidecar
text support. Will fail to replicate a 3.04 bug if wrong parameter order is
given.

"""


CACHE_PATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'cache'))


def real_tesseract():
    tess_args = ['tesseract'] + sys.argv[1:]
    os.execvp("tesseract", tess_args)
    return  # Not reachable

def main():
    operation = sys.argv[-2]
    sidecar = False
    if sys.argv[-1] == 'txt':
        sidecar = True
    elif sys.argv[-1] == 'stdout':
        operation = 'stdout'

    # For anything unexpected operation, defer to real tesseract binary
    # Currently this includes all use of "--tesseract-config"
    if operation != 'hocr' and operation != 'pdf' and operation != 'stdout':
        real_tesseract()
        return  # Not reachable

    try:
        os.makedirs(CACHE_PATH)
    except FileExistsError:
        pass

    m = hashlib.sha1()

    tess_version = subprocess.check_output(
        ['tesseract', '--version'],
        stderr=subprocess.STDOUT)

    m.update(tess_version)

    # Insert this source file into the hash function, to ensure that any
    # changes to this file invalidate previous hashes
    with open(__file__, 'rb') as f:
        m.update(f.read())

    m.update(operation.encode())

    try:
        lang = sys.argv[sys.argv.index('-l') + 1]
        m.update(lang.encode())
    except ValueError:
        m.update(b'default-lang')

    try:
        textonly = sys.argv[sys.argv.index('-c') + 1]
        m.update(textonly.encode())
    except ValueError:
        m.update(b'textonly_pdf=0')

    psm_arg = ''
    if '--psm' in sys.argv:
        psm_arg = '--psm'
    elif '-psm' in sys.argv:
        psm_arg = '-psm'
    if psm_arg:
        try:
            psm = sys.argv[sys.argv.index(psm_arg) + 1]
            m.update(psm.encode())
        except ValueError:
            m.update(b'default-psm')
    else:
        m.update(b'default-psm')

    if operation == 'stdout' and psm != '0':
        real_tesseract()
        return

    if operation == 'stdout':
        # tesseract [--options] ... input stdout
        input_file = sys.argv[-2]
        output_file = 'stdout'
        sidecar_file = ''
    else:
        # tesseract [--options] ... input output txt hocr|pdf
        input_file = sys.argv[-4]
        output_file = sys.argv[-3]
        sidecar_file = sys.argv[-3]

    if operation == 'hocr':
        output_file += '.hocr'
        sidecar_file += '.txt'
    elif operation == 'pdf':
        output_file += '.pdf'
        sidecar_file += '.txt'

    with open(input_file, 'rb') as f:
        m.update(f.read())
    cache_name = os.path.join(CACHE_PATH, m.hexdigest())
    print(cache_name)
    if os.path.exists(cache_name):
        # Cache hit
        print("Tesseract cache hit", file=sys.stderr)
        if operation != 'stdout':
            shutil.copy(cache_name, output_file)
            if sidecar:
                shutil.copy(cache_name + '.sidecar', sidecar_file)

        # Replicate output
        with open(cache_name + '.stdout', 'rb') as f:
            sys.stdout.buffer.write(f.read())
        with open(cache_name + '.stderr', 'rb') as f:
            sys.stderr.buffer.write(f.read())
        sys.exit(0)

    # Cache miss
    print("Tesseract cache miss", file=sys.stderr)

    # Call tesseract
    p = subprocess.Popen(
            ['tesseract'] + sys.argv[1:],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        # Do not cache errors or crashes
        print("Tesseract error", file=sys.stderr)
        sys.stdout.buffer.write(stdout)
        sys.stderr.buffer.write(stderr)
        return p.returncode

    with open(cache_name + '.stdout', 'wb') as f:
        f.write(stdout)
    with open(cache_name + '.stderr', 'wb') as f:
        f.write(stderr)
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)

    # Insert file into cache
    if output_file != 'stdout':
        if os.path.exists(output_file):
            shutil.copy(output_file, cache_name)
        else:
            print("Could not find output file", file=sys.stderr)
        if sidecar and os.path.exists(sidecar_file):
            shutil.copy(sidecar_file, cache_name + '.sidecar')
    else:
        open(cache_name, 'w').close()


if __name__ == '__main__':
    main()
