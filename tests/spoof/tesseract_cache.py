#!/usr/bin/env python3
import sys
import os
import hashlib
import shutil
import subprocess


"""Cache output of tesseract to speed up test suite

The cache is keyed by a hash that includes the tesseract version, some of
the command line, and the binary dump of the input file. The output file,
stdout, and stderr are replicated on a cache hit.

Page orientation checks are also cached (-psm 0 stdout)

Errors and crashes are not cached.

Things not checked:
-changes to tesseract installation that don't affect --version

Will fail on Tesseract 3.02.02 in "hocr" mode because it doesn't produce
the incorrect file extension.

"""


CACHE_PATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'cache'))


def real_tesseract():
    tess_args = ['tesseract'] + sys.argv[1:]
    os.execvp("tesseract", tess_args)
    return  # Not reachable

def main():
    operation = sys.argv[-1]
    # For anything unexpected operation, defer to real tesseract binary
    if operation != 'hocr' and operation != 'pdf' and operation != 'stdout':
        real_tesseract()
        return  # Not reachable

    try:
        os.makedirs(CACHE_PATH)
    except FileExistsError:
        pass

    m = hashlib.sha1()

    version = subprocess.check_output(
        ['tesseract', '--version'],
        stderr=subprocess.STDOUT)

    m.update(version)
    m.update(operation.encode())

    try:
        lang = sys.argv[sys.argv.index('-l') + 1]
        m.update(lang.encode())
    except ValueError:
        pass
    try:
        psm = sys.argv[sys.argv.index('-psm') + 1]
        m.update(psm.encode())
    except ValueError:
        pass

    if operation == 'stdout' and psm != '0':
        real_tesseract()
        return

    if operation == 'stdout':
        input_file = sys.argv[-2]
        output_file = 'stdout'
    else:
        input_file = sys.argv[-3]
        output_file = sys.argv[-2]

    if operation == 'hocr':
        output_file += '.hocr'
    elif operation == 'pdf':
        output_file += '.pdf'

    with open(input_file, 'rb') as f:
        m.update(f.read())
    cache_name = os.path.join(CACHE_PATH, m.hexdigest())
    print(cache_name)
    if os.path.exists(cache_name):
        # Cache hit
        print("Tesseract cache hit", file=sys.stderr)
        if operation != 'stdout':
            shutil.copy(cache_name, output_file)

        # Replicate output
        with open(cache_name + '.stdout', 'r') as f:
            print(f.read(), end='')
        with open(cache_name + '.stderr', 'r') as f:
            print(f.read(), end='', file=sys.stderr)
        sys.exit(0)

    # Cache miss
    print("Tesseract cache miss", file=sys.stderr)

    # Call tesseract
    p = subprocess.Popen(
            ['tesseract'] + sys.argv[1:],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        # Do not cache errors or crashes
        print("Tesseract error", file=sys.stderr)
        print(stdout, end='')
        print(stderr, end='', file=sys.stderr)
        return p.returncode

    with open(cache_name + '.stdout', 'w') as f:
        f.write(stdout)
    with open(cache_name + '.stderr', 'w') as f:
        f.write(stderr)
    print(stdout, end='')
    print(stderr, end='', file=sys.stderr)

    # Insert file into cache
    if output_file != 'stdout':
        if os.path.exists(output_file):
            shutil.copy(output_file, cache_name)
        else:
            print("Could not find output file", file=sys.stderr)
    else:
        open(cache_name, 'w').close()


if __name__ == '__main__':
    main()
