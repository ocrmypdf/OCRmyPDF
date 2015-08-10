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
'gs'.
'''


def pdfa_param(arg):
    if arg.startswith('-sPDFA'):
        return True
    if arg.startswith('-dPDFA'):
        return True
    if arg.endswith('.ps'):
        return True
    return False


if __name__ == '__main__':
    args = [arg for arg in sys.argv[1:]
            if not pdfa_param(arg)]

    print("Fake Ghostscript wrapper", file=sys.stderr)

    exec_path = os.environ['PATH'].split(os.pathsep)
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join(exec_path[1:])

    print("Calling real Ghostscript with modified args and env",
          file=sys.stderr)
    print(args, file=sys.stderr)
    print(env['PATH'], file=sys.stderr)

    sys.stderr.flush()
    os.execvpe('gs', ['gs'] + args, env)
