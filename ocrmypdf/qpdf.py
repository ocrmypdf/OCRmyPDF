#!/usr/bin/env python3
# © 2015 James R. Barlow: github.com/jbarlow83

from subprocess import CalledProcessError, check_output, STDOUT

from . import ExitCode


def repair(input_file, output_file, log):
    args_qpdf = [
        'qpdf', input_file, output_file
    ]
    try:
        check_output(args_qpdf, stderr=STDOUT, universal_newlines=True)
    except CalledProcessError as e:
        if e.returncode == 3 and e.output.find("operation succeeded"):
            log.debug('qpdf found and fixed errors:')
            log.debug(e.output)
            print(e.output)
            return

        if e.returncode == 2:
            print("{0}: not a valid PDF, and could not repair it.".format(
                    input_file))
            print("Details:")
            print(e.output)
            sys.exit(ExitCode.input_file)
        else:
            print("{0}: unknown error".format(
                    input_file))
            print(e.output)
            sys.exit(ExitCode.unknown)

