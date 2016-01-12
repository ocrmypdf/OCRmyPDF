#!/usr/bin/env python3
import sys
import os
import hashlib
import shutil
import subprocess


CACHE_PATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'cache'))


def main():
    operation = sys.argv[-1]
    # For anything except a hocr or pdf, defer to real tesseract
    if operation != 'hocr' and operation != 'pdf':
        tess_args = ['tesseract'] + sys.argv[1:]
        os.execvp("tesseract", tess_args)
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

    input_file = sys.argv[-3]
    output_file = sys.argv[-2]

    if operation == 'hocr':
        output_file += '.hocr'
    elif operation == 'pdf':
        output_file += '.pdf'

    with open(input_file, 'rb') as f:
        m.update(f.read())

    cache_name = os.path.join(CACHE_PATH, m.hexdigest())
    if os.path.exists(cache_name):
        # Cache hit
        print("Tesseract cache hit", file=sys.stderr)
        shutil.copy(cache_name, output_file)
        sys.exit(0)

    # Cache miss
    print("Tesseract cache miss", file=sys.stderr)

    # Call tesseract
    subprocess.check_call(['tesseract'] + sys.argv[1:])

    # Insert file into cache
    if os.path.exists(output_file):
        shutil.copy(output_file, cache_name)
    else:
        print("Could not find output file", file=sys.stderr)


if __name__ == '__main__':
    main()
