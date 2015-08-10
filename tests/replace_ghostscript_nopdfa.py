#!/usr/bin/env python3
import sys
import os

'''
For testing PDF/A generation failures, this wrapper calls ghostscript
but filters out all PDF/A information so that a regular PDF will be
created instead.

It assumes that it is called from a staged system PATH where the first
item on the PATH contains a file named 'gs' which is a symlink to this
file.  It will strip out the first item on path to invoke the real
'gs'.  That is, it expects this when called

1.   tests/output/[...test name...]/bin/gs is a symlink to this file
2.   tests/output/bin is the first item on PATH
3.   The real executable is on the path

OCRmyPDF also calls "gs --version" and "gs --help".  gs answers both
on stdout so, this wrapper prints to stderr.

'''


def pdfa_param(arg):
    if arg.startswith('-sPDFA'):
        return True
    if arg.startswith('-dPDFA'):
        return True
    if arg.endswith('.ps'):
        return True
    if 'ColorConversionStrategy' in arg:
        return True
    if 'ProcessColorModel' in arg:
        return True
    if 'OutputICCProfile' in arg:
        return True
    return False


if __name__ == '__main__':
    sys_args = sys.argv[1:]

    print("Fake Ghostscript wrapper", file=sys.stderr)

    if any(pdfa_param(arg) for arg in sys_args):
        # We were asked to produce a PDF/A
        # Filter out PDF/A arguments
        args = [arg for arg in sys.argv[1:]
                if not pdfa_param(arg)]

        # Tell Ghostscript to create a PDF 1.3 instead so JHOVE won't
        # think it's a PDF/A
        indexof_pdfwrite = next(n for n, item in enumerate(args)
                                if 'pdfwrite' in item)
        args.insert(indexof_pdfwrite + 1, '-dCompatibilityLevel=1.3')
        print("Rewrote arguments", file=sys.stderr)
    else:
        args = sys_args
        print("Keeping arguments", file=sys.stderr)

    exec_path = os.environ['PATH'].split(os.pathsep)
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join(exec_path[1:])

    print("Calling real Ghostscript with modified args and env",
          file=sys.stderr)
    print(args, file=sys.stderr)
    print(env['PATH'], file=sys.stderr)

    sys.stderr.flush()
    os.execvpe('gs', ['gs'] + args, env)
